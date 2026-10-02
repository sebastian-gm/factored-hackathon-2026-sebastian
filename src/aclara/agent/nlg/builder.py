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
from aclara.agent.nlu.rules import detect_language_evidence
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


_STATUS_LABELS = {
    "pending": ("pendiente", "pendente"),
    "reversed": ("reversada", "estornada"),
    "declined": ("rechazada", "recusada"),
    "approved": ("aprobada", "aprovada"),
}
_TYPE_LABELS = {
    "purchase": ("compra", "compra"),
    "withdrawal": ("retiro", "saque"),
    "atmwithdrawal": ("retiro en cajero", "saque no caixa eletrônico"),
    "deposit": ("depósito", "depósito"),
    "payment": ("pago", "pagamento"),
    "transfer": ("transferencia", "transferência"),
    "refund": ("reembolso", "reembolso"),
    "adjustment": ("ajuste", "ajuste"),
    "fee": ("comisión", "tarifa"),
}


def _phrase_fact_value(fact: AllowedFact, language: str) -> str:
    """Localize display enums; canonical source facts stay intact for grounding."""
    labels = _STATUS_LABELS if fact.id == "status" else _TYPE_LABELS
    if fact.id not in {"status", "transaction_type"}:
        return fact.value
    value = labels.get(fact.value.strip().casefold())
    if value is None:
        return "indisponível" if language == "pt" else "no disponible"
    return value[1 if language == "pt" else 0]


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


def render_dispute_offer(
    transaction: TransactionView, *, language: str, country: str | None = None
) -> str:
    """Render an explain/offer sentence only from a scoped transaction read."""
    merchant = (transaction.merchant or "").strip()
    status = transaction.status.casefold()
    statuses = {
        "pending": ("pendente", "pendiente"),
        "reversed": ("estornada", "reversado"),
        "declined": ("recusada", "rechazado"),
        "approved": ("aprovada", "aprobado"),
    }
    if not merchant or status not in statuses or language not in {"es", "pt"}:
        raise ValueError("Dispute offer requires scoped merchant, status, and language")
    amount_date = re.sub(
        r"\b([A-Z]{3})(?=\d)", r"\1 ", _transaction_phrase(transaction, language, country)
    )
    if language == "pt":
        text = (
            f"A cobrança em {merchant}, de {amount_date}, aparece como {statuses[status][0]}. "
            "Você ainda não a reconhece? Se quiser contestar essa cobrança, "
            "posso preparar a proposta para sua confirmação."
        )
    else:
        text = (
            f"El cargo de {merchant}, por {amount_date}, figura como {statuses[status][1]}. "
            "¿Todavía no lo reconoces? Si quieres disputar este cargo, "
            "puedo preparar la propuesta para que la confirmes."
        )
    facts = tuple(
        AllowedFact(key, str(value), "scoped_transaction_read")
        for key, value in transaction.model_dump(mode="json").items()
        if value is not None
        and key in {"merchant", "amount", "currency", "transaction_date", "status"}
    )
    verdict = verify_draft(
        text,
        [fact.id for fact in facts],
        facts,
        known_merchants=(merchant,),
    )
    if not verdict.safe:
        raise ValueError("Dispute offer failed grounding")
    return text


def render_template(plan: ResponsePlan, *, language: str, country: str | None = None) -> str:
    pt = language == "pt"
    kind = plan.response_type
    # The additive response literal is owned by the lead lane's Step 3 contract.
    if str(kind) == "offer_dispute":
        if plan.transaction is None:
            raise ValueError("Dispute offer requires a scoped transaction")
        return render_dispute_offer(plan.transaction, language=language, country=country)
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
    template = render_template(plan, language=language, country=country)
    approved = plan.reply.strip()
    fallback = (
        plan.reply if approved and plan.response_type in {"clarify", "explain_status"} else template
    )
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
        or plan.response_type != "clarify"
        # Code-supplied clarifications carry state-specific questions, including
        # bilingual language help and recognition. Generic safe prose is not a
        # substitute. Keep the existing API recognition guard as well.
        or (plan.response_type == "clarify" and bool(approved))
    ):
        return BuiltReply(plan.model_copy(update={"reply": fallback}), True, ())
    prompt = load_prompt(prompt_path or Path("prompts/phrase/v2.md"))
    context = data_block(
        "response_plan",
        json.dumps(
            {
                "type": plan.response_type,
                "language": language,
                "approved_text": redact_for_model(fallback),
                "facts": [
                    {"id": fact.id, "value": redact_for_model(_phrase_fact_value(fact, language))}
                    for fact in facts
                ],
            },
            ensure_ascii=False,
        ),
    )
    violations: list[str] = []
    merchants = tuple(
        dict.fromkeys(
            (
                *known_merchants,
                *(fact.value for fact in facts if fact.id == "merchant"),
                *(
                    (plan.transaction.merchant,)
                    if plan.transaction and plan.transaction.merchant
                    else ()
                ),
            )
        )
    )
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
            known_merchants=merchants,
            other_customer_names=other_customer_names,
        )
        current = list(verdict.violations)
        # Reject confident opposite-language evidence, not missing evidence.
        evidence = detect_language_evidence(draft.text, ignored_terms=merchants)
        if verdict.safe and evidence != "uncertain" and evidence != language:
            current.append("language_mismatch")
        if not current:
            return BuiltReply(
                plan.model_copy(update={"reply": draft.text}), False, tuple(violations)
            )
        violations.extend(current)
        context += "\nSafety violations to correct: " + ", ".join(current)
    return BuiltReply(plan.model_copy(update={"reply": fallback}), True, tuple(violations))
