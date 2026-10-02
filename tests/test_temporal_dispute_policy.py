"""Authored DQ-01 regressions; no organizer inputs or paid models."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from test_api_security import _settings, _sign_in
from test_dev_acceptance import ledger
from test_workflow_api import message

from aclara.agent.runtime import Runtime
from aclara.api.app import create_app
from aclara.handoff.context import refresh_summary
from aclara.handoff.packet import create_packet
from aclara.ops.store import Scope
from aclara.policy.engine import PolicyContext, evaluate
from aclara.settings import Settings

REASONS = (
    "before_product_open",
    "after_bank_clock",
    "product_updated_after_clock",
    "customer_updated_after_clock",
)


@pytest.mark.parametrize("reason", (*REASONS, "unknown_future_reason", ""))
@pytest.mark.parametrize("status", ("Approved", "Pending", "Reversed", "Declined"))
def test_flagged_transaction_can_be_explained_but_not_auto_disputed(reason, status):
    row = replace(ledger()._rows[0], transaction_status=status)
    facts = PolicyContext(temporal_quality_reason=reason)
    explanation = evaluate(row, Settings().bank_clock, False, facts)
    assert explanation.decision == "explain"
    assert "DQ-01" in explanation.rule_ids
    dispute = evaluate(row, Settings().bank_clock, True, facts)
    assert dispute.decision == "handoff"
    assert "DQ-01" in dispute.rule_ids
    assert dispute.inputs_snapshot["temporal_quality_checked"] is True


def test_missing_temporal_check_only_disables_automation_and_passed_null_stays_eligible():
    row, clock = ledger()._rows[0], Settings().bank_clock
    unknown = PolicyContext(temporal_quality_checked=False)
    assert evaluate(row, clock, False, unknown).decision == "explain"
    assert evaluate(row, clock, True, unknown).rule_ids == ("DQ-01",)
    assert evaluate(row, clock, True, PolicyContext()).decision == "eligible"
    # A process date after the bank clock is an explainable anomaly, not an
    # authority to write. Transaction ownership/window is still checked.
    row = replace(row, process_date=(clock + timedelta(days=1)).date())
    flag = PolicyContext(temporal_quality_reason="after_bank_clock")
    assert evaluate(row, clock, False, flag).decision == "explain"
    assert evaluate(row, clock, True, flag).decision == "handoff"


def test_quality_gate_preserves_urgent_routing_and_existing_case_reads():
    row, clock = ledger()._rows[0], Settings().bank_clock
    facts = PolicyContext(temporal_quality_reason="before_product_open", fraud_score=31)
    fraud = evaluate(row, clock, True, facts)
    assert fraud.decision == "freeze_offer"
    assert {"FRD-01", "DQ-01"} <= set(fraud.rule_ids)
    assert fraud.rule_ids[0] == "FRD-01"
    restricted = evaluate(row, clock, True, replace(facts, customer_status="Closed"))
    assert {"DSP-05", "FRD-01", "DQ-01"} <= set(restricted.rule_ids)
    assert (
        evaluate(
            row,
            clock,
            True,
            PolicyContext(temporal_quality_checked=False, existing_case_id="authored"),
        ).decision
        == "status"
    )
    foreign = evaluate(row, clock, True, replace(facts, product_owned=False))
    assert foreign.decision == "handoff" and foreign.rule_ids[0] == "DATA-01"


@pytest.mark.parametrize("language", ("es", "pt"))
def test_data_quality_questions_name_each_anomaly_and_survive_summary_refresh(language):
    packets = [create_packet(language, "DQ-01", quality_reason=reason) for reason in REASONS]
    assert len({p["open_questions"][0] for p in packets}) == len(REASONS)
    for packet in packets:
        before = packet["open_questions"][:]
        assert before and packet["suggested_next_steps"]
        refresh_summary(packet, "dispute_charge")
        assert packet["open_questions"] == before
        assert packet["primary_reason"] == "DQ-01"
        assert packet["route"]["requested_queue"] == "Quejas y Reclamos"
    old = create_packet(language, "DQ-01", quality_reason="not_checked")
    assert old["open_questions"][0] not in {p["open_questions"][0] for p in packets}


@pytest.mark.parametrize("language", ("es", "pt"))
@pytest.mark.parametrize("reason", (*REASONS, None))
def test_flagged_and_older_load_disputes_handoff_with_precise_verified_packet(language, reason):
    async def check():
        repo = ledger()
        row = repo._rows[0]
        repo.policy_fields[row.record_id] = {
            "temporal_quality_reason": reason,
            "temporal_quality_checked": reason is not None,
        }
        app = create_app(_settings(), repo, Runtime(system="B1"))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            token = await _sign_in(api)
            headers = {"Authorization": "Bearer " + token}
            query = (
                "O que é a cobrança de Taller Prisma por 17.43 USD?"
                if language == "pt"
                else "¿Qué es el cargo de Taller Prisma por 17.43 USD?"
            )
            explained, _ = await message(api, headers, query)
            assert explained["outcome"] == "explained"
            denial = (
                "Não fui eu, quero contestar a cobrança de Taller Prisma por 17.43 USD"
                if language == "pt"
                else "Yo no fui, quiero disputar el cargo de Taller Prisma por 17.43 USD"
            )
            result, cid = await message(api, headers, denial)
            assert result["outcome"] == "handoff_created" and result["verified"]
            packet = result["handoff"]
            expected = create_packet(language, "DQ-01", quality_reason=reason or "not_checked")
            assert packet["reason_codes"] == ["DQ-01"]
            assert packet["open_questions"] == expected["open_questions"]
            assert packet["verified_facts"][0]["handle"] == "txn_1"
            again, _ = await message(api, headers, "sí" if language == "es" else "sim", cid)
            assert again["handoff"]["open_questions"] == packet["open_questions"]
            principal = app.state.sessions[token]
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                assert not app.state.cases
                assert app.state.conversations[cid].proposal is None

    asyncio.run(check())


@pytest.mark.parametrize("checked", (True, False))
def test_temporal_quality_change_between_proposal_and_confirmation_prevents_write(checked):
    async def check():
        repo = ledger()
        app = create_app(_settings(), repo, Runtime(system="B1"))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
            token = await _sign_in(api)
            headers = {"Authorization": "Bearer " + token}
            proposed, cid = await message(api, headers, "No hice el cargo de Taller Prisma")
            assert proposed["outcome"] == "dispute_proposed"
            repo.policy_fields[repo._rows[0].record_id] = {
                "temporal_quality_reason": "before_product_open" if checked else None,
                "temporal_quality_checked": checked,
            }
            result = await api.post(
                f"/chat/sessions/{cid}/confirm",
                headers=headers,
                json={"confirmed": True, "proposal_hash": proposed["proposal"]["proposal_hash"]},
            )
            assert result.status_code == 200
            assert result.json()["outcome"] == "handoff_created" and result.json()["verified"]
            assert result.json()["handoff"]["reason_codes"] == ["DQ-01"]
            principal = app.state.sessions[token]
            with app.state.store.transaction(
                Scope(principal.customer_id, principal.run_id, principal.session_id)
            ):
                assert not app.state.cases and app.state.conversations[cid].proposal is None

    asyncio.run(check())
