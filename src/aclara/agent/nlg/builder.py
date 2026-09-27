"""Approved ES/PT templates; optional phrasing is checked and can degrade safely."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from aclara.agent.contracts import ResponsePlan, TransactionView
from aclara.agent.nlg.grounding import AllowedFact, redact_for_model, scan_dlp, verify_draft
from aclara.llm.client import StructuredClient
from aclara.llm.prompts import data_block, load_prompt
from aclara.llm.types import ModelFailure


class ReplyDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    cited_fact_ids: list[str]


@dataclass(frozen=True, slots=True)
class BuiltReply:
    plan: ResponsePlan
    used_template: bool
    violations: tuple[str, ...]


def _locale(language: str, country: str | None) -> str:
    if language == "pt":
        return "pt_BR"
    return {"MX": "es_MX", "CO": "es_CO", "AR": "es_AR"}.get(country or "", "es_MX")


def _transaction_phrase(txn: TransactionView, language: str, country: str | None) -> str:
    locale = _locale(language, country)
    format_currency = import_module("babel.numbers").format_currency
    format_date = import_module("babel.dates").format_date
    amount = format_currency(txn.amount, txn.currency, locale=locale)
    day = format_date(txn.transaction_date.date(), format="medium", locale=locale)
    return f"{amount}, {day}"


def render_template(plan: ResponsePlan, *, language: str, country: str | None = None) -> str:
    pt = language == "pt"
    kind = plan.response_type
    if kind == "report_case":
        if plan.case is None or plan.verified is not True:
            raise ValueError("Cannot report an unverified case")
        if not re.fullmatch(r"DSP-[A-Za-z0-9-]{1,32}", plan.case.case_id):
            raise ValueError("Invalid verified case reference")
        return (
            f"O caso {plan.case.case_id} foi registrado e confirmado no sistema."
            if pt
            else f"El caso {plan.case.case_id} quedó registrado y confirmado en el sistema."
        )
    if kind == "confirm_action":
        if plan.transaction is None:
            raise ValueError("Transaction required")
        amount = _transaction_phrase(plan.transaction, language, country)
        return (
            f"Confirma que deseja registrar uma contestação para a transação de {amount}?"
            if pt
            else f"¿Confirmas que deseas registrar una disputa por la transacción de {amount}?"
        )
    if kind == "explain_status":
        if plan.transaction is None:
            raise ValueError("Transaction required")
        amount = _transaction_phrase(plan.transaction, language, country)
        status = plan.transaction.status.lower()
        if status not in {"pending", "reversed", "declined", "approved"}:
            return (
                f"O status da transação de {amount} não está disponível."
                if pt
                else f"El estado de la transacción de {amount} no está disponible."
            )
        status_text = {
            "pending": ("está pendente", "está pendiente"),
            "reversed": ("aparece como estornada", "aparece como reversada"),
            "declined": ("foi recusada", "fue rechazada"),
            "approved": ("aparece aprovada", "aparece aprobada"),
        }[status]
        return (
            f"A transação de {amount} {status_text[0]}."
            if pt
            else f"La transacción de {amount} {status_text[1]}."
        )
    simple = {
        "cancelled": ("A solicitação foi cancelada.", "La solicitud fue cancelada."),
        "offer_human": (
            "Encaminhei sua solicitação para uma pessoa da equipe.",
            "Derivé tu solicitud a una persona del equipo.",
        ),
        "abstain": (
            "Posso ajudar com cobranças não reconhecidas ou encaminhar você a uma pessoa da equipe.",
            "Puedo ayudar con cargos no reconocidos. Puedo derivarte a una persona.",
        ),
        "choose_transaction": (
            "Escolha a transação correspondente na lista.",
            "Elige la transacción correspondiente de la lista.",
        ),
        "clarify": (
            "Pode informar o valor, a moeda ou a data aproximada?",
            "¿Puedes indicar el monto, la moneda o la fecha aproximada?",
        ),
    }
    return simple[kind][0 if pt else 1]


def build_reply(
    plan: ResponsePlan,
    *,
    language: str,
    country: str | None = None,
    facts: tuple[AllowedFact, ...] = (),
    known_merchants: tuple[str, ...] = (),
    other_customer_names: tuple[str, ...] = (),
    client: StructuredClient | None = None,
    prompt_path: Path | None = None,
) -> BuiltReply:
    fallback = render_template(plan, language=language, country=country)
    dlp_text = (
        fallback.replace(plan.case.case_id, "[VERIFIED_CASE_ID]")
        if plan.response_type == "report_case" and plan.case
        else fallback
    )
    fallback_violations = scan_dlp(dlp_text, other_customer_names=other_customer_names)
    if fallback_violations:
        raise ValueError("Approved template contains sensitive content")
    if (
        client is None
        or (client.models["phrase"].provider == "mock" and not client.mock_configured)
        or plan.response_type not in {"clarify", "explain_status"}
    ):
        return BuiltReply(plan.model_copy(update={"reply": fallback}), True, ())
    prompt = load_prompt(prompt_path or Path("prompts/phrase/v1.md"))
    context = data_block(
        "response_plan",
        json.dumps(
            {
                "type": plan.response_type,
                "language": language,
                "facts": [{"id": fact.id, "value": redact_for_model(fact.value)} for fact in facts],
            },
            ensure_ascii=False,
        ),
    )
    violations: list[str] = []
    for _ in range(2):
        try:
            draft = client.generate(
                "phrase",
                prompt.text,
                context,
                ReplyDraft,
                prompt_id=f"{prompt.id}@{prompt.version}",
                prompt_hash=prompt.content_hash,
            )
        except ModelFailure:
            break
        verdict = verify_draft(
            draft.text,
            draft.cited_fact_ids,
            facts,
            known_merchants=known_merchants,
            other_customer_names=other_customer_names,
        )
        if verdict.safe:
            return BuiltReply(
                plan.model_copy(update={"reply": draft.text}), False, tuple(violations)
            )
        violations.extend(verdict.violations)
        context += "\nSafety violations to correct: " + ", ".join(verdict.violations)
    return BuiltReply(plan.model_copy(update={"reply": fallback}), True, tuple(violations))
