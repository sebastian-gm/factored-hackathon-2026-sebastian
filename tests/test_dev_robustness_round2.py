"""Structural, no-execution protection of the new pre-run development freeze."""

import asyncio

import pytest

from aclara.llm import dev_robustness_round2
from aclara.llm.dev_robustness_round2_cases import materialize, validate


def test_round_two_freeze_and_independent_bound_gold_are_valid() -> None:
    report = validate()
    assert report["n"] == 60
    assert report["locales"]["pt-BR"] == sum(
        n for locale, n in report["locales"].items() if locale.startswith("es-")
    )


def test_all_written_sequences_fit_the_preregistered_turn_limit() -> None:
    cases, scenarios = materialize()
    for case, scenario in zip(cases, scenarios, strict=True):
        # The customer still confirms a live proposal through the typed endpoint;
        # a scripted denial is not a write confirmation.
        assert all(set(turn) == {"message"} for turn in scenario["turns"])
        expected_confirmations = int(case["outcome"] == "dispute_filed")
        assert 3 <= len(scenario["turns"]) + expected_confirmations <= scenario["max_turns"] == 5


@pytest.mark.parametrize(("provider", "approval"), [("openai_compat", "0"), ("mock", "1")])
def test_mock_entrypoint_refuses_real_configuration_before_reading_fixtures(
    monkeypatch: pytest.MonkeyPatch, provider: str, approval: str
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", approval)
    monkeypatch.setattr(
        dev_robustness_round2,
        "validate",
        lambda: pytest.fail("Input accessed despite a rejected provider configuration"),
    )
    with pytest.raises(RuntimeError, match="mock provider"):
        asyncio.run(dev_robustness_round2.mock())


def test_unsafe_summary_counts_findings_not_the_existence_of_the_map() -> None:
    rows = [
        {
            "language": language,
            "passed": True,
            "outcome": "resolved_by_explanation",
            "unsafe": {"unauthorized_disclosure": False, "policy_violation": unsafe},
            "cost_usd": 0,
        }
        for language, unsafe in [("es", False), ("pt", True)]
    ]
    summary = dev_robustness_round2.summarize(
        rows, {"cases_sha256": "authored", "materialized_sha256": "authored"}
    )
    assert summary["slices"]["all"]["unsafe"] == 1
    assert summary["slices"]["es"]["unsafe"] == 0
    assert summary["slices"]["pt"]["unsafe"] == 1
