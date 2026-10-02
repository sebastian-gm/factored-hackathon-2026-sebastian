"""Authored statistical/privacy regressions; no official cases or provider calls."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from evals.studies.llm.v4_supplementary import (
    MODEL,
    compact_svg,
    paired_interval,
    reliability,
    saved_report,
    summarize,
)


def case(system: str, identity: str, family: str, passed: bool, scores: list[float]) -> dict:
    return {
        "system": system,
        "id": identity,
        "repeat": 0,
        "in_scope": True,
        "passed": passed,
        "sar": passed,
        "language": "es" if identity.endswith("es") else "pt",
        "category": "authored",
        "gold": {"written_rule_basis": family, "outcome": "resolved_explanation"},
        "events": [
            {
                "event": "llm_call",
                "route": "nlu_risk_second_opinion",
                "judgments": {"gemini_intent_confidence": score},
            }
            for score in scores
        ],
        "responses": [{"reply": "PRIVATE_SENTINEL_NOT_FOR_REPORT"}],
    }


def test_reliability_perfectly_calibrated_bins_and_score_one_boundary() -> None:
    result = reliability([(0.0, False), (0.5, True), (0.5, False), (1.0, True)])
    assert result["ece"] == 0
    assert [g["n"] for g in result["populated_bins"]] == [1, 2, 1]
    assert result["populated_bins"][-1]["lower"] == 0.9
    assert result["populated_bins"][-1]["upper"] == 1.0


@pytest.mark.parametrize("score", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_confidence_is_rejected_instead_of_silently_dropped(score: float) -> None:
    with pytest.raises(ValueError, match="Finite"):
        reliability([(score, True)])


def test_no_scores_are_missing_evidence_instead_of_perfect_calibration() -> None:
    assert reliability([])["ece"] is None


def test_cluster_resampling_retains_the_case_weighted_estimand_with_unequal_sizes() -> None:
    result = paired_interval([1, 1, 1, -1], ["large", "large", "large", "small"])
    assert result["difference"] == 0.5  # Equal family weighting would incorrectly give zero.
    assert result["clusters"] == 2
    assert result["paired_95"] == [-1, 1]


def test_shared_variant_errors_make_cluster_ci_wider_than_independent_case_ci() -> None:
    values = [0, 0, 0, 0, 1, 1, 1, 1]
    groups = ["a", "a", "b", "b", "c", "c", "d", "d"]
    ordinary = paired_interval(values)
    clustered = paired_interval(values, groups)
    assert ordinary["difference"] == clustered["difference"] == 0.5
    assert clustered["paired_95"] == [0, 1]
    assert ordinary["paired_95"] == [0.125, 0.875]


def test_first_score_proxy_excludes_repeats_and_retains_unexecuted_baseline_failure() -> None:
    left = case("B1", "authored.es", "family", False, [])
    left["execution_status"] = "not_executed"
    right = case("P", "authored.es", "family", True, [0.95, 0.7])
    repeated = deepcopy(right)
    repeated["repeat"] = 1
    result = summarize([left, right, repeated, {"judge": "fake"}])
    assert result["comparisons"]["passed"]["case_bootstrap"]["difference"] == 1
    assert result["confidence"]["first_per_case_outcome_proxy"]["n"] == 1
    assert result["confidence"]["all_turns_outcome_proxy_sensitivity"]["n"] == 2
    assert result["true_intent_ece"] is None
    assert "PRIVATE_SENTINEL" not in str(result)


def test_duplicate_and_unpaired_primary_results_fail_instead_of_double_counting() -> None:
    left = case("B1", "authored.es", "family", True, [])
    right = case("P", "authored.es", "family", True, [0.95])
    with pytest.raises(ValueError, match="Duplicate"):
        summarize([left, right, deepcopy(right)])
    with pytest.raises(ValueError, match="paired"):
        summarize([right])


def test_strict_threshold_is_a_score_screen_not_a_claimed_counterfactual_outcome() -> None:
    left = case("B1", "authored.es", "family", False, [])
    right = case("P", "authored.es", "family", False, [0.6])
    result = summarize([left, right])
    threshold = result["confidence"]["thresholds"][0]
    assert threshold["threshold"] == 0.6
    assert threshold["first_cases_flagged"] == 0
    assert result["correctness_label"].endswith("NOT independent intent correctness")


def test_family_proxy_is_predeclared_gold_instead_of_observed_system_behavior() -> None:
    rows = [
        case("B1", "authored.es", "same-contract", False, []),
        case("B1", "authored.pt", "same-contract", True, []),
        case("P", "authored.es", "same-contract", True, [0.95]),
        case("P", "authored.pt", "same-contract", False, [0.98]),
    ]
    result = summarize(rows)
    assert result["families"]["n"] == 1
    assert result["comparisons"]["passed"]["family_proxy_bootstrap"]["paired_95"] == [0, 0]
    rows[-1]["gold"]["outcome"] = "refused_security"
    with pytest.raises(ValueError, match="mixes"):
        summarize(rows)


def test_statistical_module_has_no_provider_or_runtime_adapter_imports() -> None:
    # Reading the helper must never initialize a model client; only numerical
    # and file operations are needed for this supplementary study.
    import ast

    path = Path("evals/studies/llm/v4_supplementary.py")
    tree = ast.parse(path.read_text())
    modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any((name or "").startswith("aclara") for name in modules)


def test_svg_compaction_keeps_multiline_attributes_and_visible_text(tmp_path: Path) -> None:
    from xml.etree import ElementTree

    path = tmp_path / "authored.svg"
    path.write_text("""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
 width="100" height="50">
 <text x="3"
 y="4">Case pass proxy</text>
</svg>
""")
    compact_svg(path)
    root = ElementTree.fromstring(path.read_bytes())  # noqa: S314 -- authored fixture only.
    assert root.attrib == {"width": "100", "height": "50"}
    assert next(iter(root)).text == "Case pass proxy"


def test_saved_loader_crosschecks_validated_outputs_and_preserves_official_bytes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "authored"
    for name, row in (
        ("left", case("B1", "authored.es", "family", False, [])),
        ("right", case("P", "authored.es", "family", True, [0.95])),
    ):
        folder = source / "checkpoints" / name
        folder.mkdir(parents=True)
        (folder / "result.json").write_text(json.dumps(row))
    calls = source / "checkpoints/right/calls-1.jsonl"
    calls.write_text(
        json.dumps(
            {
                "call": {"route": "nlu", "status": "valid", "model_id": MODEL},
                "validated_output": {"intent_confidence": 0.95},
            }
        )
    )
    official = source / "results.json"
    official.write_text(
        json.dumps(
            {
                "paired_comparison": {
                    "primary_single_run": {"difference": 1.0, "paired_95": [1.0, 1.0]}
                }
            }
        )
    )
    original = {p: p.read_bytes() for p in source.rglob("*") if p.is_file()}
    report = saved_report(source)
    assert report["validated_primary_nlu_outputs"] == 1
    assert report["true_intent_ece"] is None
    assert all(path.read_bytes() == raw for path, raw in original.items())
    calls.write_text(calls.read_text().replace("0.95", "0.7"))
    with pytest.raises(ValueError, match="disagree"):
        saved_report(source)
