"""Authored timing metadata only; no cloud, credentials or model requests."""

import pytest
from scripts.azure_latency_probe import bff_ms, main, percentiles, summarize
from scripts.release_smoke_budget import run_id


def test_server_timing_requires_duration_only_and_finite_values():
    assert bff_ms("aclara_bff;dur=125.20") == 125.2
    for header in (
        "",
        "provider;dur=42.00",
        "aclara_bff;dur=NaN",
        "aclara_bff;dur=-1.00",
        "aclara_bff;dur=2.00;desc=anything",
    ):
        with pytest.raises(RuntimeError):
            bff_ms(header)


def test_startup_exclusion_removes_first_conversation_not_first_turn_of_every_case():
    turns = [
        {"conversation": 0, "bff_ms": 1000, "client_ms": 1500},
        {"conversation": 0, "bff_ms": 20, "client_ms": 40},
        {"conversation": 1, "bff_ms": 10, "client_ms": 30},
        {"conversation": 1, "bff_ms": 30, "client_ms": 50},
    ]
    report = summarize(turns, [])
    assert report["all_turns_bff"]["n"] == 4
    assert report["startup_excluded_bff"] == {"n": 2, "p50_ms": 20, "p95_ms": 29}
    assert report["startup_excluded_client"]["p50_ms"] == 40
    assert percentiles([]) == {"n": 0, "p50_ms": None, "p95_ms": None}
    assert percentiles([1]) == {"n": 1, "p50_ms": 1, "p95_ms": 1}


def test_smoke_purses_bind_kind_and_full_sha_without_reusing_legacy_run():
    sha = "a" * 40
    assert run_id("release", sha) != run_id("latency", sha)
    for kind, value in (("other", sha), ("latency", "a" * 7)):
        with pytest.raises(ValueError):
            run_id(kind, value)


def test_probe_cannot_access_cloud_before_release_approval(monkeypatch):
    monkeypatch.delenv("AZURE_LATENCY_PROBE_APPROVED", raising=False)
    with pytest.raises(RuntimeError, match="approval"):
        main()


def test_mock_probe_runs_ten_authenticated_conversations_without_persisting_facts(
    tmp_path, monkeypatch
):
    import json
    from contextlib import nullcontext
    from types import SimpleNamespace

    import httpx
    from scripts import azure_latency_probe as probe

    sha = "a" * 40
    monkeypatch.setattr(probe, "ROOT", tmp_path)
    monkeypatch.setenv("AZURE_LATENCY_PROBE_APPROVED", "1")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    receipt = tmp_path / "artifacts/azure/jev-release.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps(
            {
                "implementation_sha": sha,
                "controls_verified": True,
                "real_smoke_verified": True,
                "ci_verified": True,
            }
        )
    )
    monkeypatch.setattr(
        probe.subprocess,
        "check_output",
        lambda argv, **_: (
            "" if argv[-1] == "--porcelain" else "main" if argv[-1] == "--show-current" else sha
        ),
    )
    monkeypatch.setattr(
        probe,
        "read_variables",
        lambda: {"image_tag": sha, "llm_budget_run_id": run_id("latency", sha)},
    )
    monkeypatch.setattr(probe, "connection_string", lambda _: "authored-only")
    monkeypatch.setattr(
        probe,
        "verify",
        lambda *_a, **_k: {"charged_with_reserves_usd": 0.01, "unknown_cost_attempts": 0},
    )
    monkeypatch.setattr(probe, "az", lambda *_: {"value": "authored-password-only"})

    class FakeStore:
        def transaction(self, scope):
            return nullcontext()

        def mapping(self, *args):
            return {
                "fixture": {
                    "conversation_id": "authored-cid",
                    "events": [
                        {"event": "llm_call", "provider": "openai_compat", "status": "valid"}
                    ],
                }
            }

        def close(self):
            pass

    monkeypatch.setattr(probe, "Store", lambda *_: FakeStore())
    monkeypatch.setattr(
        probe,
        "ServingRepository",
        lambda *_: SimpleNamespace(
            personas=lambda: [
                SimpleNamespace(username="demo.es.mx", customer_id="authored-es"),
                SimpleNamespace(username="demo.pt.br", customer_id="authored-pt"),
            ]
        ),
    )
    writes = []

    class FakeClient:
        username = "demo.es.mx"
        cookies = {"aclara_access": "authored-run.authored-session.authored-signature"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, method, path, json=None):
            if method == "POST":
                writes.append(path)
            if path == "config":
                data = {"fixtures": False}
            elif path == "auth/login":
                self.username = json["username"]
                data = {"challenge_id": "authored-challenge"}
            elif path.endswith("/sms"):
                data = {"code": "123456"}
            elif path == "me":
                data = {"username": self.username}
            elif path == "transactions":
                data = [
                    {
                        "merchant": "AUTHORED-SHOP-NEVER-PERSIST",
                        "amount": 20,
                        "currency": "USD",
                        "transaction_date": "2026-06-10T00:00:00Z",
                    }
                ]
            elif path == "chat/sessions":
                data = {"conversation_id": "authored-cid"}
            elif path.endswith("/messages"):
                data = {"outcome": "explained"}
            else:
                data = {}
            return httpx.Response(200, json=data, headers={"Server-Timing": "aclara_bff;dur=1.23"})

    monkeypatch.setattr(probe.httpx, "Client", lambda **_: FakeClient())
    probe.main()
    result = json.loads(next(tmp_path.glob("artifacts/azure/*/latency.json")).read_text())
    assert result["complete"] and result["conversations"] == 10
    assert result["metrics"]["all_turns_bff"]["n"] == 20
    assert result["metrics"]["startup_excluded_bff"]["n"] == 18
    assert all(
        path == "chat/sessions" or path.endswith("/messages") or path.startswith("auth/")
        for path in writes
    )
    assert "AUTHORED-SHOP-NEVER-PERSIST" not in json.dumps(result)
    assert "authored-password-only" not in json.dumps(result)
    with pytest.raises(RuntimeError, match="already attempted"):
        probe.main()
