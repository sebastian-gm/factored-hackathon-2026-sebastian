"""Authored, offline fixtures: blinded exports and partial saved-judge pairing."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from evals.studies.llm import human_review
from evals.studies.llm.human_review import DIMENSIONS, FIELDS, build_page, import_ratings, metric


def sheet(path: Path, *, scored: bool = False) -> list[dict[str, str]]:
    rows = [
        {
            "sample_id": f"authored-{index}",
            "target_locale": "pt-BR" if index % 2 else "es-AR",
            "customer_message": 'Consulta de prueba, "con comillas"\ny otra línea.',
            "customer_reply": "Respuesta de prueba.",
            "handoff_summary": "Resumen de prueba." if index % 2 else "",
            **{
                "human_" + name: "4"
                if scored and (name != "handoff_usefulness" or index % 2)
                else ""
                for name in DIMENSIONS
            },
            "human_notes": "",
        }
        for index in range(20)
    ]
    write_sheet(path, rows)
    return rows


def write_sheet(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def saved(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    source, scored = tmp_path / "source.csv", tmp_path / "scored.csv"
    rows = sheet(source)
    sheet(scored, scored=True)
    inputs = tmp_path / "judge-inputs.json"
    inputs.write_text(json.dumps([{k: r[k] for k in FIELDS[:5]} for r in rows]))
    checkpoints = tmp_path / "checkpoints"
    # Two available pairs among twenty items, rather than invented missing scores.
    for index in (0, 1):
        directory = checkpoints / str(index)
        directory.mkdir(parents=True)
        scores = {
            name: 4 if name != "handoff_usefulness" or index % 2 else None for name in DIMENSIONS
        }
        (directory / "result.json").write_text(
            json.dumps(
                {
                    "sample_id": f"authored-{index}",
                    "sonnet_scores": scores,
                    "jev_scores": {**scores, "empathy": 2},
                }
            )
        )
    return scored, source, inputs, checkpoints


def test_page_preserves_blinding_and_escapes_untrusted_html(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(human_review, "ROOT", tmp_path)
    source = tmp_path / "source.csv"
    rows = sheet(source)
    injection = '</script><script>alert("untrusted")</script>\u2028'
    rows[0]["customer_message"] = injection
    write_sheet(source, rows)
    rubric = tmp_path / "rubric.md"
    rubric.write_text("Rúbrica local de prueba")
    output = tmp_path / "artifacts/review/page.html"
    assert build_page(source, rubric, output)["items"] == 20
    html = output.read_text()
    assert injection not in html and "\\u003c/script>" in html
    encoded = html.partition('<script id="review-data" type="application/json">')[2].partition(
        "</script>"
    )[0]
    payload = json.loads(encoded)
    assert payload["rows"][0]["customer_message"] == injection
    assert payload["fields"] == list(FIELDS)
    assert all(set(row) == set(FIELDS) for row in payload["rows"])
    assert "connect-src 'none'" in html
    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ValueError, match="ignored artifacts"):
        build_page(source, rubric, tmp_path / "published.html")


@pytest.mark.parametrize("version", ["v3", "v4"])
def test_page_labels_the_selected_version_and_isolates_autosave(tmp_path, monkeypatch, version):
    monkeypatch.setattr(human_review, "ROOT", tmp_path)
    source = tmp_path / "source.csv"
    sheet(source)
    rubric = tmp_path / "rubric.md"
    rubric.write_text("Rúbrica local de prueba")
    output = tmp_path / "artifacts/review/page.html"
    assert build_page(source, rubric, output, version=version)["version"] == version
    html = output.read_text()
    assert f"<title>Aclara — revisión humana {version}</title>" in html
    assert f"20 respuestas ({version})" in html
    assert "__VERSION__" not in html
    encoded = html.partition('<script id="review-data" type="application/json">')[2].partition(
        "</script>"
    )[0]
    assert json.loads(encoded)["version"] == version
    assert "'aclara-human-'+payload.version+':'+payload.source_sha256" in html


def test_v4_cli_default_output_preserves_the_v3_page(tmp_path, monkeypatch):
    monkeypatch.setattr(human_review, "ROOT", tmp_path)
    source = tmp_path / "source.csv"
    sheet(source)
    rubric = tmp_path / "rubric.md"
    rubric.write_text("Rúbrica local de prueba")
    v3 = tmp_path / "artifacts/human-judge/v3-score.html"
    v3.parent.mkdir(parents=True)
    v3.write_text("Existing v3 page")
    monkeypatch.setattr(
        human_review.sys,
        "argv",
        [
            "human_review",
            "build",
            "--source",
            str(source),
            "--rubric",
            str(rubric),
            "--version",
            "v4",
        ],
    )
    assert human_review.main() == 0
    assert v3.read_text() == "Existing v3 page"
    assert "20 respuestas (v4)" in (v3.parent / "v4-score.html").read_text()


def test_partial_judges_intersect_ids_and_exclude_na(tmp_path) -> None:
    result = import_ratings(*saved(tmp_path))
    assert result["human_complete"]
    assert result["sheet_items_with_saved_judges"] == 2
    comparisons = result["comparisons"]
    assert comparisons["human_vs_sonnet"]["all"]["clarity"] == {
        "paired_n": 2,
        "exact": 1,
        "within_one": 1,
        "greater_than_one_n": 0,
        "quadratic_weighted_kappa": None,  # no variance is undefined, not perfect
    }
    assert comparisons["human_vs_jev"]["all"]["empathy"]["within_one"] == 0
    assert comparisons["sonnet_vs_jev"]["all"]["empathy"]["exact"] == 0
    assert comparisons["human_vs_sonnet"]["all"]["handoff_usefulness"]["paired_n"] == 1
    assert comparisons["human_vs_sonnet"]["es"]["handoff_usefulness"]["paired_n"] == 0


def test_missing_model_score_is_not_zero(tmp_path) -> None:
    paths = saved(tmp_path)
    checkpoint = paths[3] / "1/result.json"
    row = json.loads(checkpoint.read_text())
    row["jev_scores"] = None
    checkpoint.write_text(json.dumps(row))
    result = import_ratings(*paths)
    assert result["comparisons"]["human_vs_jev"]["all"]["empathy"]["paired_n"] == 1
    assert result["comparisons"]["human_vs_sonnet"]["all"]["empathy"]["paired_n"] == 2


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("customer_reply", "Altered wording", "changed the original wording"),
        ("human_clarity", "6", "integers 1–5"),
        ("human_empathy", "", "Finish all applicable"),
        ("human_handoff_usefulness", "5", "No-handoff"),
    ],
)
def test_import_rejects_changed_text_invalid_missing_or_inapplicable_ratings(
    tmp_path, field, value, error
) -> None:
    paths = saved(tmp_path)
    rows = human_review.read_sheet(paths[0])
    rows[0][field] = value
    write_sheet(paths[0], rows)
    with pytest.raises(ValueError, match=error):
        import_ratings(*paths)


def test_empty_agreement_and_variance_are_explicit() -> None:
    assert metric([]) == {
        "paired_n": 0,
        "exact": None,
        "within_one": None,
        "greater_than_one_n": 0,
        "quadratic_weighted_kappa": None,
    }
    assert metric([(1, 1), (5, 5)])["quadratic_weighted_kappa"] == 1
