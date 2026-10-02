"""Ignored, synthetic human-rating sheet and ordinal judge agreement."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from evals.studies.llm.round_one import ROOT

ARTIFACTS = ROOT / "artifacts/judge"
SHEET = ARTIFACTS / "human-validation-50.csv"
JUDGE_RESULTS = ARTIFACTS / "judge-results-50.csv"
LOGGER = logging.getLogger(__name__)
DIMENSIONS = ("language_register", "clarity", "empathy", "handoff_usefulness")
HUMAN_FIELDS = tuple(f"human_{dimension}" for dimension in DIMENSIONS)
SHEET_FIELDS = (
    "sample_id",
    "language_group",
    "target_locale",
    "customer_message",
    "customer_reply",
    "handoff_summary",
    *HUMAN_FIELDS,
    "human_notes",
)


@dataclass(frozen=True, slots=True)
class Context:
    language_group: str
    target_locale: str
    customer_message: str
    issue: str
    pending_step: str


CONTEXTS = (
    Context(
        "es-MX",
        "es-MX",
        "No ubico un cargo en mi tarjeta y quiero hablar con alguien.",
        "cargo no identificado",
        "revisar el detalle del cargo",
    ),
    Context(
        "es-MX",
        "es-MX",
        "Me cobraron dos veces; ¿me pasas con una persona?",
        "posible cobro duplicado",
        "comparar los dos movimientos",
    ),
    Context(
        "es-CO",
        "es-CO",
        "No entiendo este pago de 20 lucas; necesito asesor.",
        "pago de 20 lucas",
        "aclarar el movimiento",
    ),
    Context(
        "es-CO",
        "es-CO",
        "Me aparece una comisión rara; quiero una persona.",
        "comisión consultada",
        "revisar el concepto de la comisión",
    ),
    Context(
        "es-AR",
        "es-AR",
        "Vi un consumo de tres palos que no me suena; ¿me derivás?",
        "consumo no identificado",
        "revisar el consumo",
    ),
    Context(
        "es-AR",
        "es-AR",
        "Perdí la tarjeta y necesito hablar con alguien ya.",
        "tarjeta extraviada",
        "atender la solicitud de ayuda",
    ),
    Context(
        "pt-BR",
        "pt-BR",
        "Tem uma cobrança que não reconheço; quero falar com atendente.",
        "cobrança não reconhecida",
        "revisar os detalhes da cobrança",
    ),
    Context(
        "pt-BR",
        "pt-BR",
        "Apareceu um estorno e preciso de uma pessoa para explicar.",
        "dúvida sobre estorno",
        "explicar o lançamento",
    ),
    Context(
        "mixed",
        "es-MX",
        "I see un cargo extraño, ¿me conectan con una persona?",
        "cargo consultado",
        "revisar el movimiento",
    ),
    Context(
        "mixed",
        "pt-BR",
        "My card sumiu; preciso falar com alguém.",
        "cartão desaparecido",
        "atender a solicitação de ajuda",
    ),
)


def _wording(context: Context, variant: int) -> tuple[str, str]:
    pt = context.target_locale == "pt-BR"
    if pt:
        replies = (
            "Entendo sua preocupação. Vou encaminhar sua solicitação a uma pessoa da equipe, que poderá ajudar com os próximos passos.",
            "Vou encaminhar sua solicitação a uma pessoa da equipe para continuar o atendimento.",
            "Talvez alguém veja isso depois. Aguarde.",
            "Voy a derivar tu solicitud a una persona del equipo para que pueda ayudarte.",
            "Compreendo que isso pode ser preocupante e quero ajudar; o atendimento poderá continuar com uma pessoa da equipe depois que a solicitação for encaminhada.",
        )
        summaries = (
            f"Cliente pede atendimento humano por {context.issue}. Foi informado sobre o encaminhamento; pendente {context.pending_step}.",
            f"Solicitação sobre {context.issue}; pendente {context.pending_step}.",
            "Problema com conta. Ver depois.",
            "Verificar quando possível.",
            f"Cliente solicita ajuda por {context.issue}; ainda falta {context.pending_step}.",
        )
    else:
        replies = (
            "Entiendo tu preocupación. Voy a derivar tu consulta a una persona del equipo para que te ayude con los siguientes pasos.",
            "Voy a derivar tu consulta a una persona del equipo para continuar la atención.",
            "Quizá alguien lo vea luego. Espera.",
            "Vou encaminhar sua solicitação a uma pessoa da equipe para continuar o atendimento.",
            "Comprendo que esto puede inquietarte y quiero ayudarte; la atención podrá continuar con una persona del equipo después de derivar tu consulta.",
        )
        summaries = (
            f"Cliente solicita atención humana por {context.issue}. Se informó la derivación; queda pendiente {context.pending_step}.",
            f"Consulta sobre {context.issue}; queda pendiente {context.pending_step}.",
            "Problema con cuenta. Ver luego.",
            "Revisar cuando se pueda.",
            f"Cliente pide ayuda por {context.issue}; todavía falta {context.pending_step}.",
        )
    return replies[variant], summaries[(variant * 2) % 5]


def sample_rows() -> list[dict[str, str]]:
    """Generate 50 varied fictional wording examples without outcome gold."""
    rows: list[dict[str, str]] = []
    for context in CONTEXTS:
        for variant in range(5):
            reply, summary = _wording(context, variant)
            rows.append(
                {
                    "language_group": context.language_group,
                    "target_locale": context.target_locale,
                    "customer_message": context.customer_message,
                    "customer_reply": reply,
                    "handoff_summary": summary,
                    **{field: "" for field in HUMAN_FIELDS},
                    "human_notes": "",
                }
            )
    Random(20260927).shuffle(rows)  # noqa: S311 - reproducible sheet order, not security
    for index, row in enumerate(rows, 1):
        row["sample_id"] = f"JVAL-{index:03d}"
    return rows


def prepare_sheet(path: Path = SHEET) -> Path:
    if path.exists():
        raise FileExistsError("Human review sheet already exists; never overwrite ratings")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        writer.writerows(sample_rows())
    path.chmod(0o600)
    return path


def _rating(value: str) -> int | None:
    if not value.strip():
        return None
    if value not in {"1", "2", "3", "4", "5"}:
        raise ValueError("Ratings must be integers from 1 to 5")
    return int(value)


def quadratic_weighted_kappa(pairs: list[tuple[int, int]]) -> float | None:
    """Cohen's κ with squared ordinal disagreement weights on the fixed 1–5 scale."""
    if not pairs:
        return None
    n = len(pairs)
    human = [0] * 5
    judge = [0] * 5
    observed = 0.0
    for left, right in pairs:
        if not 1 <= left <= 5 or not 1 <= right <= 5:
            raise ValueError("Ratings must be integers from 1 to 5")
        human[left - 1] += 1
        judge[right - 1] += 1
        observed += (left - right) ** 2
    observed /= n
    expected = sum(human[i] * judge[j] * (i - j) ** 2 for i in range(5) for j in range(5)) / (n * n)
    return 1 - observed / expected if expected > 0 else None


def agreement(
    human_path: Path = SHEET, judge_path: Path = JUDGE_RESULTS, *, require_complete: bool = True
) -> dict[str, Any]:
    with human_path.open(encoding="utf-8", newline="") as stream:
        human_rows = list(csv.DictReader(stream))
    with judge_path.open(encoding="utf-8", newline="") as stream:
        judge_rows = list(csv.DictReader(stream))
    if len(human_rows) != 50 or len({row["sample_id"] for row in human_rows}) != 50:
        raise ValueError("Validation requires 50 unique human samples")
    if len({row["sample_id"] for row in judge_rows}) != len(judge_rows):
        raise ValueError("Duplicate judge sample ID")
    judges = {row["sample_id"]: row for row in judge_rows}
    results: dict[str, Any] = {}
    for dimension in DIMENSIONS:
        pairs: list[tuple[int, int]] = []
        for row in human_rows:
            candidate = judges.get(row["sample_id"])
            if candidate is None:
                continue
            left = _rating(row[f"human_{dimension}"])
            right = _rating(candidate[dimension])
            if left is not None and right is not None:
                pairs.append((left, right))
        if require_complete and len(pairs) != 50:
            raise ValueError(f"{dimension}: 50 paired ratings required before agreement claim")
        results[dimension] = {
            "paired_n": len(pairs),
            "exact_agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
            "within_one_agreement": sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs)
            if pairs
            else None,
            "quadratic_weighted_kappa": quadratic_weighted_kappa(pairs),
        }
    return {
        "complete": all(value["paired_n"] == 50 for value in results.values()),
        "dimensions": results,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-sheet", action="store_true")
    parser.add_argument("--agreement", action="store_true")
    args = parser.parse_args()
    if args.prepare_sheet:
        prepare_sheet()
        LOGGER.info(
            "Prepared 50 ignored synthetic human-review samples; all human ratings are blank."
        )
    elif args.agreement:
        sys.stdout.write(json.dumps(agreement(), indent=2, sort_keys=True) + "\n")
    else:
        parser.error("Choose --prepare-sheet or --agreement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
