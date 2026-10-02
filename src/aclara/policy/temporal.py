"""Temporal serving checks: display is allowed; unchecked intake is not."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aclara.policy.engine import PolicyContext

TEMPORAL_REASONS = (
    "before_product_open",
    "after_bank_clock",
    "product_updated_after_clock",
    "customer_updated_after_clock",
)


def quality_issue(facts: PolicyContext) -> str | None:
    if not facts.temporal_quality_checked:
        return "not_checked"
    if facts.temporal_quality_reason is None:
        return None
    return (
        facts.temporal_quality_reason
        if facts.temporal_quality_reason in TEMPORAL_REASONS
        else "invalid_reason"
    )


def quality_guidance(reason: str | None, language: str) -> tuple[str, str, str]:
    """Return bounded localized cause/question/step; never interpolate row values."""
    copies = {
        "before_product_open": (
            (
                "El movimiento tiene una fecha anterior a la apertura del producto.",
                "¿Puede confirmar la fecha de apertura del producto y la fecha del movimiento?",
            ),
            (
                "A transação tem uma data anterior à abertura do produto.",
                "Pode confirmar a data de abertura do produto e a data da transação?",
            ),
        ),
        "after_bank_clock": (
            (
                "Una fecha del movimiento es posterior al corte de los datos.",
                "¿Puede verificar por qué la fecha del movimiento es posterior al corte de los datos?",
            ),
            (
                "Uma data da transação é posterior à data de corte dos dados.",
                "Pode verificar por que a data da transação é posterior à data de corte dos dados?",
            ),
        ),
        "product_updated_after_clock": (
            (
                "Los datos del producto se actualizaron después del corte de los datos.",
                "¿Puede verificar el estado del producto en la fecha de corte de los datos?",
            ),
            (
                "Os dados do produto foram atualizados após a data de corte dos dados.",
                "Pode verificar o status do produto na data de corte dos dados?",
            ),
        ),
        "customer_updated_after_clock": (
            (
                "Los datos del cliente se actualizaron después del corte de los datos.",
                "¿Puede verificar el estado del cliente en la fecha de corte de los datos?",
            ),
            (
                "Os dados do cliente foram atualizados após a data de corte dos dados.",
                "Pode verificar o status do cliente na data de corte dos dados?",
            ),
        ),
    }
    index = int(language == "pt")
    fallback = (
        (
            "La validación temporal de los datos no está disponible.",
            "¿Puede validar las fechas y los estados del cliente y del producto antes de tramitar la disputa?",
        ),
        (
            "A validação temporal dos dados não está disponível.",
            "Pode validar as datas e os status do cliente e do produto antes de tratar a contestação?",
        ),
    )
    cause, question = copies.get(reason or "", fallback)[index]
    step = (
        "Verificar a inconsistência temporal na fonte antes de qualquer contestação; não prometer reembolso."
        if index
        else "Verificar la inconsistencia temporal en la fuente antes de tramitar una disputa; no prometer reembolso."
    )
    return cause, question, step
