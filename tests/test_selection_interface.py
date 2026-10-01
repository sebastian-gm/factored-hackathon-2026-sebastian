"""Author-supplied envelope vocabulary; authored IDs only, no frozen files."""

import json
from collections import Counter
from copy import deepcopy

import pytest
from evals.program_spec import CATEGORIES, LANGUAGES, selection_payload, selections


def authored():
    sample_categories = {
        "normal": 11,
        "ambiguous_unsupported": 6,
        "human_required": 6,
        "security_robustness": 7,
    }
    sample_languages = {"es": 14, "pt": 14, "mixed": 2}
    categories = [k for k, n in sample_categories.items() for _ in range(n)] + [
        k for k, n in CATEGORIES.items() for _ in range(n - sample_categories[k])
    ]
    languages = [k for k, n in sample_languages.items() for _ in range(n)] + [
        k for k, n in LANGUAGES.items() for _ in range(n - sample_languages[k])
    ]
    rows = [
        {"id": f"authored-{i}", "category": c, "language": language}
        for i, (c, language) in enumerate(zip(categories, languages, strict=True))
    ]
    shared = {
        "seed": "authored-seed",
        "category_counts": sample_categories,
        "language_counts": sample_languages,
    }
    ids = [r["id"] for r in rows[:30]]
    legacy = {
        **deepcopy(shared),
        "method": "authored-stratified",
        "n": 30,
        "scenario_ids": ids.copy(),
    }
    current = {
        **deepcopy(shared),
        "purpose": "authored-repeat",
        "selection": "authored-stratified",
        "case_ids": ids.copy(),
    }
    return {"scenarios": rows}, legacy, current


@pytest.mark.parametrize("forms", [(1, 1), (2, 2), (1, 2), (2, 1)])
def test_both_declared_envelopes_preserve_exact_members(tmp_path, forms):
    suite, legacy, current = authored()
    for name, index in zip(("repeat-selection.json", "judge-selection.json"), forms, strict=True):
        (tmp_path / name).write_text(json.dumps((suite, legacy, current)[index]))
    repeat, judge = selections(suite, tmp_path)
    assert repeat == judge == set(current["case_ids"])


@pytest.mark.parametrize(
    "fault",
    [
        "both_id_fields",
        "missing_field",
        "unknown_field",
        "string_ids",
        "numeric_id",
        "duplicate",
        "wrong_size",
        "boolean_n",
        "wrong_n",
        "wrong_text_type",
        "blank_text",
        "boolean_count",
        "unknown_stratum",
        "wrong_total",
    ],
)
def test_malformed_selection_envelopes_fail_before_execution(fault):
    _, legacy, current = authored()
    value = deepcopy(legacy if fault in {"boolean_n", "wrong_n"} else current)
    if fault == "both_id_fields":
        value["scenario_ids"] = current["case_ids"]
    elif fault == "missing_field":
        del value["purpose"]
    elif fault == "unknown_field":
        value["unsupported"] = "authored"
    elif fault == "string_ids":
        value["case_ids"] = "authored"
    elif fault == "numeric_id":
        value["case_ids"][0] = 7
    elif fault == "duplicate":
        value["case_ids"][0] = value["case_ids"][1]
    elif fault == "wrong_size":
        value["case_ids"].pop()
    elif fault == "boolean_n":
        value["n"] = True
    elif fault == "wrong_n":
        value["n"] = 29
    elif fault == "wrong_text_type":
        value["selection"] = 1
    elif fault == "blank_text":
        value["seed"] = " "
    elif fault == "boolean_count":
        value["category_counts"]["normal"] = True
    elif fault == "unknown_stratum":
        value["language_counts"]["unsupported"] = 0
    elif fault == "wrong_total":
        value["language_counts"]["es"] = 13
    with pytest.raises(ValueError):
        selection_payload(value)


@pytest.mark.parametrize(
    "fault", ["outside_suite", "wrong_category_counts", "wrong_language_counts"]
)
def test_membership_and_actual_strata_are_checked(tmp_path, fault):
    suite, _, payload = authored()
    if fault == "outside_suite":
        payload["case_ids"][0] = "authored-outside-suite"
    else:
        field = "category_counts" if fault == "wrong_category_counts" else "language_counts"
        keys = list(payload[field])
        payload[field][keys[0]] -= 1
        payload[field][keys[1]] += 1
        assert sum(payload[field].values()) == 30
    for name in ("repeat-selection.json", "judge-selection.json"):
        (tmp_path / name).write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        selections(suite, tmp_path)


def test_authored_suite_matches_full_envelope():
    suite, _, _ = authored()
    assert Counter(r["category"] for r in suite["scenarios"]) == CATEGORIES
    assert Counter(r["language"] for r in suite["scenarios"]) == LANGUAGES
