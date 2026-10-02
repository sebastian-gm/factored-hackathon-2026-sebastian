"""The local smoke must stay mock-only even with a contrary ambient provider."""

import asyncio

from scripts.local_mock_concurrency import measure


def test_five_independent_logins_measure_scoped_turns_without_provider_calls(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "1")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Local mock smoke attempted a paid provider")

    monkeypatch.setattr("aclara.llm.providers.urlopen", forbidden)
    result = asyncio.run(measure(5, 0.01))
    assert result["sessions"] == result["nlu_calls"] == result["scoped_execution_records"] == 5
    assert result["concurrent_reads"] == 15
    assert result["nlu_outside_transaction"] is True
    assert result["case_writes"] == result["model_cost_usd"] == 0
