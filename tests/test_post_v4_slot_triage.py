"""Authored mock regressions from dev diagnosis, never held-out measurements."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from evals.studies.llm.dev_post_v4 import fixtures, inventory, score
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_workflow_api import message

from aclara.agent.contracts import Intent
from aclara.agent.nlu.structured import ExtractedNlu, parse_amount, postprocess
from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.llm.client import StructuredClient
from aclara.llm.types import ModelSpec

CLOCK = datetime(2026, 6, 18, 6, tzinfo=UTC)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("dezessete reais e quarenta e três centavos", "17.43"),
        ("zero reais e cinco centavos", "0.05"),
        ("cem reais e noventa e nove centavos", "100.99"),
        ("mil e duzentos reais e um centavo", "1200.01"),
        ("diecisiete dólares y cuarenta y tres centavos", "17.43"),
        ("un peso y un centavo", "1.01"),
        ("noventa y nueve centavos", "0.99"),
        ("quarenta e três centavos", "0.43"),
    ],
)
def test_complete_spoken_money_including_cents(expression: str, expected: str) -> None:
    assert parse_amount(expression) == Decimal(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "uns dezessete reais e quarenta centavos",
        "dezessete reais e cem centavos",
        "dezessete reais e quarenta ou cinquenta centavos",
        "menos dezessete reais e três centavos",
        "dezessete reais e três dólares",
        "dezessete reais e quarenta centavos mais taxas",
        "dos compras de diecisiete dólares y tres centavos",
        "diecisiete dólares y ciento un centavos",
        "diecisiete dólares y tres centavos o veinte dólares",
        "17 reais e 43 centavos",
    ],
)
def test_malformed_or_ambiguous_money_stays_unresolved(expression: str) -> None:
    assert parse_amount(expression) is None


def test_cents_alone_do_not_invent_a_currency() -> None:
    result = postprocess(
        ExtractedNlu(
            language="pt",
            intent="charge_inquiry",
            intent_confidence=0.99,
            amount_expr="quarenta e três centavos",
        ),
        country="BR",
        bank_clock=CLOCK,
    )
    assert result.slots.amount_value == Decimal("0.43")
    assert result.slots.currency is None and result.clarification == "currency"


@pytest.mark.parametrize(
    ("language", "text"),
    [
        ("es", "Quiero entender el cargo de Mercado Ensayo por varios dólares, no sé el monto."),
        ("pt", "Quero entender a cobrança da Loja Ensaio por vários reais; não sei o valor."),
    ],
)
def test_explicit_missing_amount_survives_null_model_expression(language: str, text: str) -> None:
    result = postprocess(
        ExtractedNlu(
            language=language,
            intent="charge_inquiry",
            intent_confidence=0.99,
            merchant_expr="Mercado Ensayo",
            currency_expr="BRL" if language == "pt" else "USD",
        ),
        country="BR" if language == "pt" else "MX",
        bank_clock=CLOCK,
        message=text,
    )
    assert result.clarification == "amount"
    assert result.slots.amount_value is None


@pytest.mark.parametrize("language", ["es", "pt"])
def test_missing_amount_control_preserves_valid_value_and_unrelated_requests(language: str) -> None:
    text = "No sé el monto" if language == "es" else "Não sei o valor"
    for intent, amount in [("charge_inquiry", "19.80"), ("out_of_scope", None)]:
        result = postprocess(
            ExtractedNlu(
                language=language, intent=intent, intent_confidence=0.99, amount_expr=amount
            ),
            country="MX",
            bank_clock=CLOCK,
            message=text,
        )
        assert result.clarification is None


@pytest.mark.parametrize(
    ("language", "text", "expression"),
    [
        (
            "es",
            "¿Por qué está pendiente el cargo? Ya lleva un montón de días.",
            "un montón de días",
        ),
        ("pt", "Por que a cobrança está pendente? Já faz muitos dias.", "muitos dias"),
        ("es", "Mi compra sigue pendiente, ya lleva veinte días.", "veinte días"),
        ("pt", "Minha compra continua pendente. Já faz vinte dias.", "vinte dias"),
    ],
)
def test_pending_status_age_does_not_become_a_selection_date(
    language: str, text: str, expression: str
) -> None:
    result = postprocess(
        ExtractedNlu(
            language=language,
            intent="charge_inquiry",
            intent_confidence=0.99,
            amount_expr="17.43",
            currency_expr="USD",
            date_expr=expression,
        ),
        country="BR" if language == "pt" else "MX",
        bank_clock=CLOCK,
        message=text,
    )
    assert result.clarification is None
    assert result.slots.date_start is result.slots.date_end is None
    assert result.extracted.date_expr == expression  # Preserve the model's raw observation.


@pytest.mark.parametrize("expression", ["ayer", "2026-06-12", "un día de aquellos"])
def test_status_complaint_preserves_a_separate_purchase_date(expression: str) -> None:
    result = postprocess(
        ExtractedNlu(
            language="es", intent="charge_inquiry", intent_confidence=0.99, date_expr=expression
        ),
        country="MX",
        bank_clock=CLOCK,
        message=f"La compra de {expression} sigue pendiente. Ya lleva un montón de días.",
    )
    if expression == "un día de aquellos":
        assert result.clarification == "date"
    else:
        assert result.slots.date_start is not None


def test_vague_purchase_age_without_a_pending_status_clause_still_asks_for_date() -> None:
    result = postprocess(
        ExtractedNlu(
            language="es",
            intent="charge_inquiry",
            intent_confidence=0.99,
            date_expr="un montón de días",
        ),
        country="MX",
        bank_clock=CLOCK,
        message="La compra de Mercado Ensayo fue hace un montón de días, no sé cuándo.",
    )
    assert result.clarification == "date"


@pytest.mark.parametrize("language", ["es", "pt"])
def test_family_assistance_is_ordinary_inquiry_when_model_reports_no_unfamiliarity(
    language: str,
) -> None:
    result = postprocess(
        ExtractedNlu(
            language=language,
            intent="charge_inquiry",
            intent_confidence=0.99,
            unfamiliar_charge=False,
        ),
        country="BR" if language == "pt" else "AR",
        bank_clock=CLOCK,
        message=(
            "Minha irmã me ajudou com meu extrato; pode explicar a cobrança?"
            if language == "pt"
            else "Mi hermana me ayudó con mi resumen; ¿me explicás el cargo?"
        ),
    )
    assert result.frame.intent == Intent.CHARGE_INQUIRY
    assert result.extracted.unfamiliar_charge is False


@pytest.mark.parametrize("case_id", ["pt05", "es14", "es18"])
def test_product_gaps_at_authenticated_p_boundary(case_id: str) -> None:
    # Simulated extraction for diagnosis; the real pass did not retain raw NLU.
    # Fixture rows and the scorer belong to the frozen, team-authored dev set.
    case = next(c for c in inventory() if c["id"] == case_id)
    _, repository, extracted = fixtures(case)
    if case_id == "es14":
        extracted["amount_expr"] = None
    elif case_id == "es18":
        extracted["date_expr"] = "un montón de días"
    llm = StructuredClient(
        {r: ModelSpec("mock", "authored-triage") for r in ("nlu", "phrase")},
        {},
        mock_response=lambda *_: json.dumps(extracted),
    )

    async def check() -> None:
        app = create_app(_settings(), repository, runtime=Runtime(system="P"), llm_client=llm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            headers = {"Authorization": f"Bearer {await _sign_in(api)}"}
            result, _ = await message(api, headers, case["text"])
            assert score(case, result)["pass"]
            assert result["degraded"] is False
            assert not result.get("case") and not result.get("proposal")

    asyncio.run(check())


def test_valid_unfamiliarity_paraphrase_is_not_erased_by_a_family_mention() -> None:
    result = postprocess(
        ExtractedNlu(
            language="es", intent="charge_inquiry", intent_confidence=0.99, unfamiliar_charge=True
        ),
        country="AR",
        bank_clock=CLOCK,
        message="Mi hermana me ayuda con el resumen. Este consumo me resulta completamente ajeno.",
    )
    assert result.frame.intent == Intent.CHARGE_INQUIRY
    assert result.extracted.unfamiliar_charge is True
