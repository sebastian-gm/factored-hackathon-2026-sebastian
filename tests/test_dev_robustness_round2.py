"""Structural, no-execution protection of the new pre-run development freeze."""

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
