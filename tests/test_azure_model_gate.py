"""Authored offline smoke metadata. No Azure connection or provider calls."""

from copy import deepcopy
from pathlib import Path

import pytest
from scripts.azure_llm_smoke import open_transaction_ids, verify_live_model_calls

from aclara.llm.config import load_risk_second_opinion_enabled


def call(provider="openai_compat"):
    return {"provider": provider, "status": "valid", "prompt_id": "nlu@v5.1"}


def test_production_config_requires_zero_typesafe_calls():
    assert not load_risk_second_opinion_enabled(Path("config/models.yaml"))
    assert verify_live_model_calls([{"degraded": False}], [call()], risk_enabled=False) == 0
    with pytest.raises(AssertionError, match="Disabled"):
        verify_live_model_calls(
            [{"degraded": False}], [call(), call("typesafe")], risk_enabled=False
        )


@pytest.mark.parametrize(
    "nlu,calls", [([], [call()]), ([{"degraded": True}], [call()]), ([{"degraded": False}], [])]
)
def test_model_proof_stays_required(nlu, calls):
    with pytest.raises(AssertionError):
        verify_live_model_calls(nlu, calls, risk_enabled=False)


def test_opt_in_second_opinion_requires_valid_union():
    jev = {
        **call("typesafe"),
        "judgments": {
            "degradation": None,
            "gemini_raw_flags": {"fraud": False},
            "jev_threshold_flags": {"fraud": True},
            "union_flags": {"fraud": True},
        },
    }
    assert verify_live_model_calls([{"degraded": False}], [call(), jev], risk_enabled=True) == 1
    wrong = deepcopy(jev)
    wrong["judgments"]["union_flags"]["fraud"] = False
    with pytest.raises(AssertionError):
        verify_live_model_calls([{"degraded": False}], [call(), wrong], risk_enabled=True)


def test_smoke_excludes_only_canonical_open_business_cases():
    assert open_transaction_ids(
        [
            {"transaction_id": "open", "status": "received"},
            {"transaction_id": "closed", "status": "resolved"},
            {"transaction_id": "historic", "status": "received", "_canonical": False},
        ]
    ) == {"open"}
