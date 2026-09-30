"""Provider diagnostics reveal safe categories only; no network or billable calls."""

from dataclasses import asdict
from datetime import date
from urllib.error import HTTPError, URLError

import pytest
from pydantic import BaseModel

from aclara.llm.client import StructuredClient, provider_failure_code
from aclara.llm.config import Price
from aclara.llm.types import ModelFailure, ModelSpec, ProviderResponse


@pytest.mark.parametrize(
    ("cause", "expected"),
    [
        (
            HTTPError("https://example.invalid", 402, "PRIVATE-PROVIDER-BODY", None, None),
            "http_402",
        ),
        (
            HTTPError("https://example.invalid", 429, "PRIVATE-PROVIDER-BODY", None, None),
            "http_429",
        ),
        (TimeoutError("PRIVATE-PROVIDER-BODY"), "timeout"),
        (URLError("PRIVATE-PROVIDER-BODY"), "network_error"),
    ],
)
def test_wrapped_error_category_never_contains_provider_text(
    cause: Exception, expected: str
) -> None:
    error = ModelFailure("Generic request failure")
    error.__cause__ = cause
    assert provider_failure_code(error) == expected


class Judgment(BaseModel):
    flag: bool = False


class BillingReject:
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        error = HTTPError("https://example.invalid", 402, "PRIVATE-PROVIDER-BODY", None, None)
        raise ModelFailure("Generic request failure") from error


def test_every_failed_attempt_records_safe_code_and_retains_unknown_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")
    monkeypatch.setenv("TEST_MODEL_KEY", "fake-test-credential")
    client = StructuredClient(
        {
            "nlu": ModelSpec(
                provider="openai_compat", model_id="test", key_env="TEST_MODEL_KEY", price_id="test"
            )
        },
        {"test": Price(1, 1, 0, 0, date(2026, 1, 1), "https://example.invalid")},
        budget_usd=1,
    )
    client._adapters["openai_compat"] = BillingReject()
    with pytest.raises(ModelFailure, match="Generic request failure"):
        client.generate("nlu", "approved", "customer", Judgment, prompt_id="nlu@test")
    assert len(client.records) == 2
    assert all(r.stop_reason == "http_402" and r.cost_usd is None for r in client.records)
    assert all(r.status == "provider_error" for r in client.records)
    assert "PRIVATE-PROVIDER-BODY" not in str([asdict(r) for r in client.records])
