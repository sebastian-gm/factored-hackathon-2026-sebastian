"""Deterministic staff guidance and bounded, redacted customer context."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aclara.agent.nlg.grounding import redact_for_model, scan_dlp
from aclara.policy.rules import rule
from aclara.policy.rules.guards import cross_customer, injection

# Each entry is (cause, open question, next step), in ES then pt-BR.
_GUIDANCE = {
    "DSP-07": (
        (
            "El monto supera el límite de disputa automática.",
            "¿Qué resultado buscas para este cargo?",
            "Revisar el monto y la elegibilidad para gestionar la disputa manualmente.",
        ),
        (
            "O valor supera o limite de contestação automática.",
            "Qual resultado você espera para esta cobrança?",
            "Revisar o valor e a elegibilidade para tratar a contestação manualmente.",
        ),
    ),
    "ESC-04": (
        (
            "No se pudo identificar la solicitud con suficiente confianza.",
            "¿Qué dato falta aclarar para identificar el cargo o la solicitud?",
            "Revisar las aclaraciones previas y pedir solo el dato que siga faltando.",
        ),
        (
            "Não foi possível identificar a solicitação com confiança suficiente.",
            "Qual informação falta esclarecer para identificar a cobrança ou a solicitação?",
            "Revisar os esclarecimentos anteriores e pedir apenas a informação que ainda falta.",
        ),
    ),
    "TXN-02": (
        (
            "El cargo lleva más de 14 días pendiente.",
            "¿Ha cambiado el estado del cargo desde la consulta?",
            "Consultar la pendencia con el equipo responsable sin prometer una fecha de resolución.",
        ),
        (
            "A cobrança está pendente há mais de 14 dias.",
            "O status da cobrança mudou desde a consulta?",
            "Consultar a pendência com a equipe responsável sem prometer uma data de resolução.",
        ),
    ),
    "FRD-01": (
        (
            "Se requiere revisión de seguridad por posible fraude o pérdida de tarjeta.",
            "¿Qué ocurrió y sigue siendo necesario proteger la tarjeta?",
            "Revisar los indicios y el resultado del bloqueo; solicitar verificación y consentimiento si aún hace falta bloquear.",
        ),
        (
            "É necessária uma análise de segurança por possível fraude ou perda do cartão.",
            "O que aconteceu e ainda é necessário proteger o cartão?",
            "Revisar os indícios e o resultado do bloqueio; solicitar verificação e consentimento se ainda for necessário bloquear.",
        ),
    ),
    "ESC-01": (
        (
            "El cliente pidió atención humana.",
            "¿Qué necesitas resolver con la persona que te atienda?",
            "Retomar la solicitud y las aclaraciones sin pedir al cliente que repita todo.",
        ),
        (
            "O cliente pediu atendimento humano.",
            "O que você precisa resolver com a pessoa que atender você?",
            "Retomar a solicitação e os esclarecimentos sem pedir que o cliente repita tudo.",
        ),
    ),
    "ESC-02": (
        (
            "La solicitud requiere atención legal o regulatoria prioritaria.",
            "¿Qué respuesta o trámite legal o regulatorio solicitas?",
            "Revisar la solicitud con el equipo especializado, sin dar asesoría legal ni prometer un resultado.",
        ),
        (
            "A solicitação exige atendimento jurídico ou regulatório prioritário.",
            "Qual resposta ou procedimento jurídico ou regulatório você solicita?",
            "Revisar a solicitação com a equipe especializada, sem dar aconselhamento jurídico nem prometer um resultado.",
        ),
    ),
    "ESC-03": (
        (
            "El cliente expresó angustia y requiere atención humana.",
            "¿Qué apoyo necesitas ahora para continuar con esta solicitud?",
            "Atender con empatía, confirmar la necesidad inmediata y evitar pedir datos innecesarios.",
        ),
        (
            "O cliente expressou sofrimento e precisa de atendimento humano.",
            "De que apoio você precisa agora para continuar com esta solicitação?",
            "Atender com empatia, confirmar a necessidade imediata e evitar pedir dados desnecessários.",
        ),
    ),
    "SEC-01": (
        (
            "Se rechazaron intentos de acceso a información de otra persona.",
            "¿La solicitud pendiente se refiere únicamente a tus propios productos?",
            "Revisar el evento de seguridad sin revelar información ajena; verificar la identidad antes de retomar una solicitud propia.",
        ),
        (
            "Foram recusadas tentativas de acesso a informações de outra pessoa.",
            "A solicitação pendente se refere apenas aos seus próprios produtos?",
            "Revisar o evento de segurança sem revelar informações alheias; verificar a identidade antes de retomar uma solicitação própria.",
        ),
    ),
}


def guidance(language: str, reasons: Iterable[str]) -> tuple[list[str], list[str], list[str]]:
    reasons = tuple(reasons)
    index = 1 if language == "pt" else 0
    copies = [_GUIDANCE[reason][index] for reason in reasons if reason in _GUIDANCE]
    if not copies:
        copies = [
            (
                getattr(rule(next(iter(reasons))), "pt" if index else "es"),
                "Qual resultado você espera?" if index else "¿Qué resultado buscas?",
                "Revisar os fatos e a regra aplicável."
                if index
                else "Revisar los hechos y la regla aplicable.",
            )
        ]
    causes, questions, steps = (list(dict.fromkeys(copy[i] for copy in copies)) for i in range(3))
    return causes, questions, steps


def safe_quote(text: str | None) -> str | None:
    if not text or cross_customer(text) or injection(text):
        return None
    masked = redact_for_model(text)
    if scan_dlp(masked) or any(
        word in masked.casefold()
        for word in ("fraud_score", "is_fraud", "score", "puntua", "pontua")
    ):
        return None
    return masked[:240]


def customer_context(turns: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    statements: list[dict[str, Any]] = []
    preceding: dict[str, Any] = {}
    for turn in turns:
        response = turn.get("response", {})
        quote = safe_quote(turn.get("customer_text"))
        in_scope = response.get("outcome") not in {"abstained_out_of_scope", "refused_security"}
        if quote and in_scope and not statements:
            statements.append({"quote": quote, "verified": False, "source": "initial_request"})
        elif (
            quote
            and in_scope
            and preceding.get("response_type") in {"clarify", "choose_transaction", "offer_dispute"}
        ):
            statement: dict[str, Any] = {
                "quote": quote,
                "verified": False,
                "source": "clarification",
            }
            question = safe_quote(preceding.get("reply"))
            if question:
                statement["question"] = question
            statements.append(statement)
        preceding = response
    # Retain the initial request even when bounding a long clarification history.
    return statements[:1] + statements[-9:] if len(statements) > 10 else statements


def refresh_summary(packet: dict[str, Any], intent: str | None = None) -> None:
    pt = packet["route"]["language"] == "pt"
    causes, questions, steps = guidance("pt" if pt else "es", packet["reason_codes"])
    packet["open_questions"], packet["suggested_next_steps"] = questions, steps
    request = {
        "charge_inquiry": "Explicação da cobrança." if pt else "Explicación del cargo.",
        "dispute_charge": "Contestação da cobrança." if pt else "Disputa del cargo.",
    }.get(
        intent or "",
        "Atendimento humano da solicitação." if pt else "Revisión humana de la solicitud.",
    )
    statements = packet.get("customer_statements", [])
    if statements:
        request += " “" + statements[0]["quote"] + "”"
    parts = [("Solicitação: " if pt else "Solicitud: ") + request]
    status_labels = {
        "Approved": ("aprobado", "aprovado"),
        "Pending": ("pendiente", "pendente"),
        "Declined": ("rechazado", "recusado"),
        "Reversed": ("reversado", "estornado"),
    }
    for fact in packet.get("verified_facts", []):
        merchant = safe_quote(fact.get("merchant")) or "—"
        status = status_labels.get(fact["status"], ("no disponible", "indisponível"))[int(pt)]
        parts.append(
            ("Cobrança verificada: " if pt else "Cargo verificado: ")
            + f"{merchant}, {fact['amount']} {fact['currency']}, {fact['transaction_date'][:10]}; "
            + ("status " if pt else "estado ")
            + status
            + "."
        )
    if not packet.get("verified_facts"):
        parts.append(
            "Cobrança não identificada com segurança."
            if pt
            else "Cargo sin identificar con certeza."
        )
    actions = []
    for action in packet["actions_taken"]:
        if action == "create_dispute":
            actions.append(
                "contestação registrada e verificada" if pt else "disputa registrada y verificada"
            )
        elif action == "create_handoff":
            actions.append(
                "encaminhamento registrado e verificado"
                if pt
                else "derivación registrada y verificada"
            )
    freeze = packet.get("freeze_outcome")
    if freeze == "verified":
        actions.append("bloqueio do cartão verificado" if pt else "bloqueo de tarjeta verificado")
    elif freeze in {"unverified", "offered", "unavailable"}:
        actions.append(
            "bloqueio do cartão não verificado" if pt else "bloqueo de tarjeta sin verificar"
        )
    parts.append(
        ("Ações: " if pt else "Acciones: ")
        + ("; ".join(actions) or ("nenhuma ação verificada" if pt else "ninguna acción verificada"))
        + "."
    )
    parts.append(
        ("Motivo do encaminhamento: " if pt else "Motivo de derivación: ") + " ".join(causes)
    )
    packet["request_summary"] = {
        "text": " ".join(parts),
        "generated_by": {"model": "rules", "prompt": "none"},
        "label": "rule_based_summary",
    }
