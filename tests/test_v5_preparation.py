"""Preparation checks use authored scalar fixtures only, never frozen inputs."""

from decimal import Decimal

import pytest
from scripts import v5_blind_evaluation as runner
from scripts import v5_budget as budget


def test_future_cap_retains_charges_and_unused_allowance():
    assert budget.maximum(Decimal("15.76264898"), Decimal(0)) == Decimal("17.26264898")
    assert budget.maximum(Decimal("15.86264898"), Decimal(".10")) == Decimal("17.26264898")
    for prior, charged in [("17", "0"), ("NaN", "0"), ("-1", "0"), ("15", "1.51")]:
        with pytest.raises(RuntimeError):
            budget.maximum(Decimal(prior), Decimal(charged))


def test_no_suite_merged_go_blocks_before_git_or_frozen_reads(monkeypatch):
    monkeypatch.delenv("V5_SUITE_MERGED_GO", raising=False)
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *a, **k: pytest.fail("git read"))
    with pytest.raises(RuntimeError, match="suite merged GO"):
        runner.implementation()


def test_paired_primary_sar_uses_scope_not_workload_denominator():
    b1 = [
        {"id": "authored.a", "in_scope": True, "sar": False},
        {"id": "authored.b", "in_scope": False, "sar": False},
    ]
    p = [{**c, "sar": c["in_scope"]} for c in b1]
    result = runner.paired(b1, p)
    assert result["n"] == 2 and result["in_scope_n"] == 1
    assert result["difference"] == 1 and result["paired_95"] == [1, 1]
    assert result["bootstrap_draws"] == 10000 and result["seed"] == 20261001
    with pytest.raises(ValueError):
        runner.paired(b1, p[:-1])


def test_fallback_metadata_uses_route_lookup_not_an_attribute(monkeypatch):
    """Exercise the wrapper's actual header after an authored loader boundary."""
    import asyncio
    from contextlib import nullcontext
    from pathlib import Path
    from types import SimpleNamespace

    captured = {}
    monkeypatch.setattr(runner.os, "environ", dict(runner.os.environ))
    monkeypatch.setattr(runner, "access", lambda *a, **k: nullcontext())
    monkeypatch.setattr(runner, "exclusive", lambda *a, **k: nullcontext())
    monkeypatch.setattr(Path, "iterdir", lambda _: iter(()))
    monkeypatch.setattr(Path, "read_bytes", lambda _: b"authored-opaque-bytes")
    marker = object()
    scenario = {"persona": {"customer_ref": "authored"}}
    source = SimpleNamespace(
        temporal_quality_checked=True,
        dataset_version="authored",
        store=SimpleNamespace(close=lambda: None),
    )
    monkeypatch.setattr(runner, "implementation", lambda: "a" * 40)
    monkeypatch.setattr(runner, "serving_pin", lambda _: {"location": "local"})
    monkeypatch.setattr(runner, "verify", lambda _: {})
    monkeypatch.setattr(runner, "verify_envelope", lambda _: {})
    monkeypatch.setattr(runner, "open_serving", lambda: source)
    monkeypatch.setattr(
        runner, "load", lambda *a, **k: ({"scenarios": [scenario] * 100}, {"authored": {}}, marker)
    )
    monkeypatch.setattr(runner, "Store", lambda _: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(runner, "dotenv_values", lambda _: {})
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *a, **k: "b" * 40)
    monkeypatch.setattr(
        runner.ProgramSpec, "release", property(lambda _: Path("artifacts/evaluation-v5-prep"))
    )
    monkeypatch.setattr(runner.OUTPUT.__class__, "exists", lambda _: False)
    from scripts import azure_dev, azure_migrate_ops

    monkeypatch.setattr(azure_dev, "az", lambda *a: {"value": "authored-no-provider-key"})
    monkeypatch.setattr(azure_migrate_ops, "connection_string", lambda _: "authored-dsn")

    class HeaderReached(Exception):
        pass

    def capture_header(output, header):
        captured.update(header)
        raise HeaderReached()

    monkeypatch.setattr(runner, "Checkpoints", capture_header)
    with pytest.raises(HeaderReached):
        asyncio.run(
            runner.run(
                SimpleNamespace(
                    suite="test-v5", bindings="artifacts/authored-bindings", manifest_pin="a" * 64
                )
            )
        )
    from aclara.llm.config import load_fallback_route, load_models

    models = load_models(Path("config/models.yaml"))
    route = load_fallback_route(Path("config/models.yaml"), models)
    assert isinstance(route, str)
    assert captured["fallback"] == models[route].model_id
