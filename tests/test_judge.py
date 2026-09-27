"""Judge calibration and paid-call boundaries, without network calls."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from aclara.llm.judge import JudgeScores, run
from aclara.llm.judge_validation import (
    DIMENSIONS,
    SHEET_FIELDS,
    agreement,
    quadratic_weighted_kappa,
    sample_rows,
)


def test_synthetic_human_sheet_has_50_blinded_subjective_samples() -> None:
    rows = sample_rows()
    assert len(rows) == len({row["sample_id"] for row in rows}) == 50
    assert {row["language_group"] for row in rows} == {"es-MX", "es-CO", "es-AR", "pt-BR", "mixed"}
    assert all(row["handoff_summary"] for row in rows)
    assert all(not row[f"human_{dimension}"] for row in rows for dimension in DIMENSIONS)
    assert not any("gold" in field or "outcome" in field for field in SHEET_FIELDS)
    assert set(JudgeScores.model_fields) == set(DIMENSIONS)


def test_quadratic_weighted_kappa_handles_agreement_and_no_variation() -> None:
    assert quadratic_weighted_kappa([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]) == 1
    assert quadratic_weighted_kappa([(1, 5), (5, 1)]) == -1
    assert quadratic_weighted_kappa([(3, 3), (3, 3)]) is None
    with pytest.raises(ValueError, match="1 to 5"):
        quadratic_weighted_kappa([(0, 3)])


def test_agreement_requires_50_paired_human_and_judge_ratings(tmp_path: Path) -> None:
    human = tmp_path / "human.csv"
    judge = tmp_path / "judge.csv"
    rows = sample_rows()
    for index, row in enumerate(rows):
        for dimension in DIMENSIONS:
            row[f"human_{dimension}"] = str(index % 5 + 1)
    with human.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with judge.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("sample_id", *DIMENSIONS))
        writer.writeheader()
        writer.writerows(
            {
                "sample_id": row["sample_id"],
                **{dimension: row[f"human_{dimension}"] for dimension in DIMENSIONS},
            }
            for row in rows
        )
    report = agreement(human, judge)
    assert report["complete"] is True
    assert all(
        value["paired_n"] == 50 and value["quadratic_weighted_kappa"] == 1
        for value in report["dimensions"].values()
    )
    rows[0]["human_clarity"] = ""
    with human.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="50 paired ratings"):
        agreement(human, judge)


def test_judge_paid_call_requires_process_local_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_REAL_CALLS_APPROVED", raising=False)
    with pytest.raises(RuntimeError, match="approval"):
        run(smoke=True, budget_usd=0.49)
