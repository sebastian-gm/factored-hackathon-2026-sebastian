"""Authored privacy controls for dotted IDs in model input and staff context."""

import pytest

from aclara.agent.nlg.grounding import redact_for_model, scan_dlp
from aclara.handoff.context import customer_context


@pytest.mark.parametrize(
    "text",
    [
        "Mi DNI es 12.345.678; quiero explicar mi cargo.",
        "Meu CPF é 123.456.789-01; quero entender minha compra.",
        "Mi RUT: 12.345.678-K. Quiero revisar mi compra.",
        "Mi cédula es 1.234.567.890; necesito ayuda.",
        "Consulte pelo CPF 123.456.789-01",
        "Consulta el DNI 12.345.678",
    ],
)
def test_punctuated_identifiers_are_masked_and_flagged(text: str) -> None:
    assert "document_number" in scan_dlp(text)
    masked = redact_for_model(text)
    assert "[REDACTED]" in masked and not scan_dlp(masked)


def test_first_request_and_clarification_history_mask_dotted_self_ids() -> None:
    statements = customer_context(
        [
            {
                "customer_text": "No reconozco el cargo; mi DNI es 12.345.678",
                "response": {"response_type": "clarify"},
            },
            {"customer_text": "Meu CPF é 123.456.789-01; a compra é minha", "response": {}},
        ]
    )
    assert len(statements) == 2
    assert all("[REDACTED]" in statement["quote"] for statement in statements)
    assert "12.345.678" not in str(statements)


@pytest.mark.parametrize(
    "text", ["El cargo es de 17.43 USD el 2026-06-15.", "A compra é de 17,43 BRL."]
)
def test_money_and_dates_without_id_labels_are_not_newly_redacted(text: str) -> None:
    assert redact_for_model(text) == text
