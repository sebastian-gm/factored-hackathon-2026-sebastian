"""Pure authored cost/receipt regressions; no clients, DB, secrets or live traffic."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from docs.evaluation import live_exploration_controls as controls
from docs.evaluation.live_exploration_controls import (
    MINIMUM_RESERVATION,
    REPO_ROOT,
    ControlFailure,
    contextual_nlu_ceiling,
    verify_judge_identity,
    verify_pinned_sources,
    verify_turn,
)

from aclara.api.auth_models import JudgeReference, Principal
from aclara.llm.prompts import load_prompt
from aclara.ops.store import Scope

_PIN_PATHS = [
    "config/models.yaml",
    "config/pricing.yaml",
    "src/aclara/api/app.py",
    "src/aclara/agent/nlg/builder.py",
    "prompts/nlu/v5.md",
]


@pytest.fixture(autouse=True)
def isolate_historical_pins(monkeypatch: pytest.MonkeyPatch) -> None:
    # Historical computation tests use no pins; original guard checks synthetic files below.
    monkeypatch.setattr(controls, "verify_pinned_sources", lambda _root=REPO_ROOT: None)


def _response() -> dict[str, Any]:
    return {"response_type": "clarify", "outcome": "clarification", "reply": "¿Cuál es el monto?"}


def _call(route: str = "nlu", attempt: int = 1, cost: Any = "0.001") -> dict[str, Any]:
    prompt = load_prompt(REPO_ROOT / "prompts/nlu/v5.md")
    return {
        "event": "llm_call",
        "route": route,
        "provider": "openai_compat",
        "model_id": "google/gemini-3-flash-preview" if route == "nlu" else "x-ai/grok-4.20",
        "prompt_id": f"{prompt.id}@{prompt.version}",
        "prompt_hash": prompt.content_hash,
        "attempt": attempt,
        "status": "valid",
        "cost_usd": cost,
    }


def _record(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    row = json.loads("""{
        "conversation_id": "authored-chat", "system": "P", "outcome": "clarification"}""")
    row.update(response=_response(), events=events or [])
    return row


def test_actual_unicode_recognition_context_matches_full_client_framing_and_four_attempts() -> None:
    from aclara.agent.nlg.grounding import redact_for_model, scan_dlp
    from aclara.agent.nlu.structured import ExtractedNlu
    from aclara.llm.prompts import data_block, load_prompt

    message = "Ainda não reconheço essa cobrança & quero revisar."
    charge = json.loads("""{
        "transaction_date": "2026-06-17T09:00:00+00:00", "amount": "17.43",
        "currency": "USD", "status": "Approved", "internal_field": "excluded"}""")
    charge["merchant"] = "Fixture Café & " + "á" * 170
    allowed = {}
    for key, value in charge.items():
        if key == "internal_field":
            continue
        redacted = redact_for_model(value)[:160]
        allowed[key] = "[REDACTED]" if scan_dlp(redacted) else redacted
    record = json.dumps(
        {"awaiting_recognition": True, "selected_charge": allowed}, ensure_ascii=False
    )
    context = (
        data_block("record", record)
        + "\n"
        + data_block("customer_message", redact_for_model(message))
    )
    size = (
        len(load_prompt(REPO_ROOT / "prompts/nlu/v5.md").text.encode())
        + len(context.encode())
        + len(json.dumps(ExtractedNlu.model_json_schema()).encode())
        + 1024
    )
    # Independent released-price arithmetic: two Gemini and two Grok attempts.
    expected = ((Decimal("3.5") * size + 22528) / 1_000_000).quantize(MINIMUM_RESERVATION)
    assert (
        contextual_nlu_ceiling(message, awaiting_recognition=True, masked_charge=charge) == expected
    )
    assert (
        contextual_nlu_ceiling(message, awaiting_recognition=False, masked_charge=charge) < expected
    )


@pytest.mark.parametrize("message", ["", "x" * 1001])
def test_invalid_inference_body_is_never_quoted(message: str) -> None:
    with pytest.raises(ControlFailure, match="Invalid inference message"):
        contextual_nlu_ceiling(message)


@pytest.mark.parametrize("intent", ["charge_inquiry", "dispute_charge"])
def test_collection_context_ceiling_covers_actual_model_framing(intent: str) -> None:
    from aclara.agent.nlu.structured import ExtractedNlu, understand
    from aclara.llm.client import StructuredClient
    from aclara.llm.types import ModelSpec

    framed: list[tuple[str, str]] = []

    def respond(system: str, user: str, _schema: Any) -> str:
        framed.append((system, user))
        return json.dumps(
            dict(
                language="es",
                intent="charge_inquiry",
                intent_confidence=0.98,
                amount_expr="24.00",
                currency_expr="USD",
            )
        )

    client = StructuredClient(
        {"nlu": ModelSpec("mock", "collection-ceiling")},
        {},
        mock_response=respond,
        budget_usd=0,
        risk_second_opinion_enabled=False,
    )
    text = "Perdón, el monto correcto es 24.00 USD."
    understand(
        text,
        country="MX",
        bank_clock=datetime(2026, 6, 18, tzinfo=UTC),
        client=client,
        prompt_path=REPO_ROOT / "prompts/nlu/v5.md",
        masked_charge={"collection_intent": intent},
    )
    system, user = framed[0]
    size = len(system.encode()) + len(user.encode())
    size += len(json.dumps(ExtractedNlu.model_json_schema()).encode()) + 1024
    expected = ((Decimal("3.5") * size + 22528) / 1_000_000).quantize(MINIMUM_RESERVATION)
    assert contextual_nlu_ceiling(text, masked_charge={"collection_intent": intent}) == expected
    assert expected > contextual_nlu_ceiling(text)
    assert client.spent_usd == 0


def test_unknown_recognition_facts_cannot_reuse_noncontextual_ceiling() -> None:
    with pytest.raises(ControlFailure, match="Missing owned charge facts"):
        contextual_nlu_ceiling(
            "Não reconheço", awaiting_recognition=True, masked_charge={"merchant": "Fixture"}
        )


@pytest.mark.parametrize(
    "path,repin", [(path, False) for path in _PIN_PATHS] + [("config/models.yaml", True)]
)
def test_changed_routing_prices_template_guard_or_prompt_fails_closed(
    tmp_path: Path, path: str, repin: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    contents = dict.fromkeys(_PIN_PATHS, "# authored pinned source\n")
    contents["config/models.yaml"] = "routing:\n  risk_second_opinion_enabled: false\n"
    monkeypatch.setattr(
        controls,
        "PINNED_SOURCES",
        {name: sha256(text.encode()).hexdigest() for name, text in contents.items()},
    )
    for source, text in contents.items():
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    verify_pinned_sources(tmp_path)
    target = tmp_path / path
    text = target.read_text()
    target.write_text(
        text.replace("risk_second_opinion_enabled: false", "risk_second_opinion_enabled: true")
        if path == "config/models.yaml"
        else text + "\n# changed\n"
    )
    if repin:  # Independently prove risk is rejected even when its digest matches.
        controls.PINNED_SOURCES[path] = sha256(target.read_bytes()).hexdigest()
    with pytest.raises(
        ControlFailure, match="Risk second opinion" if repin else "Source pin changed"
    ):
        verify_pinned_sources(tmp_path)


def test_all_paid_attempts_are_attributed_even_when_final_response_is_degraded() -> None:
    calls = [
        _call("nlu", 1, "0.001"),
        _call("nlu", 2, "0.002"),
        _call("fallback_grok_4_20", 1, "0.003"),
        _call("fallback_grok_4_20", 2, "0.004"),
    ]
    for call in calls:
        call["status"] = "invalid_json"
    row = _record(calls + [{"event": "nlu", "degraded": True}])
    response = _response()
    response["degraded"] = True
    row["response"] = copy.deepcopy(response)
    verified = verify_turn(
        {"prior"}, {"prior": _record(), "fresh": row}, "authored-chat", response, nlu_expected=True
    )
    assert verified.total_usd == Decimal("0.010")
    assert verified.execution_ids == ("fresh",) and verified.degraded
    assert row["events"] == calls + [{"event": "nlu", "degraded": True}]


def test_source_proven_bypass_with_verified_primary_has_zero_cost() -> None:
    verified = verify_turn(
        [], {"fresh": _record()}, "authored-chat", _response(), nlu_expected=True
    )
    assert verified.total_usd == 0 and not verified.degraded
    assert MINIMUM_RESERVATION > 0


@pytest.mark.parametrize("cost", [None, "NaN", "Infinity", "-0.01", True, "unknown"])
def test_unknown_invalid_or_negative_cost_never_becomes_zero(cost: Any) -> None:
    records = {"fresh": _record([_call(cost=cost)])}
    with pytest.raises(ControlFailure):
        verify_turn([], records, "authored-chat", _response(), nlu_expected=True)


@pytest.mark.parametrize(
    "mutation",
    [
        "foreign",
        "stale",
        "ambiguous",
        "different_response",
        "wrong_prompt",
        "phrase",
        "risk",
        "duplicate",
        "missing_attempt",
        "unexpected_model",
    ],
)
def test_receipt_identity_and_call_bound_are_enforced(mutation: str) -> None:
    records = {"fresh": _record([_call()])}
    previous: list[str] = []
    if mutation == "foreign":
        records["fresh"]["conversation_id"] = "another-chat"
    elif mutation == "stale":
        previous = ["fresh"]
    elif mutation == "ambiguous":
        records["second"] = _record()
    elif mutation == "different_response":
        records["fresh"]["response"]["reply"] = "Outra resposta"
    elif mutation == "duplicate":
        records["fresh"]["events"].append(_call())
    elif mutation == "missing_attempt":
        records["fresh"]["events"] = [_call(attempt=2)]
    else:
        call = records["fresh"]["events"][0]
        if mutation == "wrong_prompt":
            call["prompt_hash"] = "0" * 64
        elif mutation in {"phrase", "risk"}:
            call["route"] = mutation
        elif mutation == "unexpected_model":
            call["model_id"] = "unreviewed-model"
    with pytest.raises(ControlFailure):
        verify_turn(previous, records, "authored-chat", _response(), nlu_expected=True)


def test_model_call_on_deterministic_path_is_rejected() -> None:
    with pytest.raises(ControlFailure, match="Unexpected model call"):
        verify_turn(
            [], {"fresh": _record([_call()])}, "authored-chat", _response(), nlu_expected=False
        )


def _committed_handoff() -> tuple[dict[str, Any], dict[str, Any]]:
    response = json.loads("""{
        "response_type": "offer_human", "outcome": "handoff_created",
        "reply": "Voy a derivar tu solicitud.", "handoff": {
            "schema_version": "1.0", "handoff_id": "HO-FIXTURE",
            "created_at": "2026-10-03T12:00:00Z", "reason_codes": ["ESC-01"],
            "priority": "normal", "route": {
                "queue": "Operaciones", "language": "es", "fallback_used": false},
            "verified_facts": [], "actions_taken": [], "open_questions": []}}""")
    row = _record()
    row.update(outcome=response["outcome"], response=copy.deepcopy(response))  # Pre-commit.
    response["verified"] = True
    response["handoff"]["actions_taken"].append("create_handoff")
    auxiliary = {
        "conversation_id": "authored-chat",
        "outcome": "handoff_verified",
        "events": [{"event": "verify_readback", "handle": "HO-FIXTURE"}],
    }
    records = {"primary": row, "readback": auxiliary}
    return response, records


def _fact() -> dict[str, Any]:
    return json.loads("""{
        "handle": "txn_fixture", "transaction_date": "2026-06-17T09:00:00Z",
        "transaction_type": "Purchase", "amount": 17.43, "currency": "USD",
        "merchant": "Fixture Café", "status": "Approved"}""")


@pytest.mark.parametrize("previously_committed", [False, True])
def test_handoff_auxiliary_readback_belongs_to_the_exact_primary(
    previously_committed: bool,
) -> None:
    response, records = _committed_handoff()
    if previously_committed:
        records["primary"]["response"]["handoff"]["actions_taken"] = ["create_handoff"]
    original = copy.deepcopy(records)
    verified = verify_turn([], records, "authored-chat", response, nlu_expected=False)
    assert verified.total_usd == 0 and verified.execution_ids == ("primary", "readback")
    assert records == original  # Normalize copies; never mutate durable evidence.
    records["readback"]["events"][0]["handle"] = "HO-OTHER"
    with pytest.raises(ControlFailure, match="Unrelated auxiliary"):
        verify_turn([], records, "authored-chat", response, nlu_expected=False)


@pytest.mark.parametrize(
    "mutation",
    ["queue", "facts", "actions", "missing_aux", "unverified", "reply", "duplicate_action"],
)
def test_handoff_enrichment_never_exempts_other_receipt_fields(mutation: str) -> None:
    response, records = _committed_handoff()
    if mutation == "queue":
        response["handoff"]["route"]["queue"] = "Fraudes"
    elif mutation == "facts":
        response["handoff"]["verified_facts"] = [_fact()]
    elif mutation == "actions":
        response["handoff"]["actions_taken"].append("create_dispute")
    elif mutation == "missing_aux":
        del records["readback"]
    elif mutation == "unverified":
        response["verified"] = False
    elif mutation == "reply":
        response["reply"] = "Different reply"
    elif mutation == "duplicate_action":
        response["handoff"]["actions_taken"].append("create_handoff")
    with pytest.raises(ControlFailure):
        verify_turn([], records, "authored-chat", response, nlu_expected=False)


def _bff_handoff_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    response, records = _committed_handoff()
    hidden = json.loads("""{
        "conversation_id": "authored-chat", "customer": {"handle": "authored-customer"},
        "customer_statements": [], "policy_evaluations": [], "risk_flags": [],
        "suggested_next_steps": [], "sla_due_at": "2026-10-18T12:00:00Z",
        "transcript_ref": "/authored/transcript", "trace_ref": "/authored/trace"}""")
    route = dict(
        requested_queue="Operaciones", assigned_agent_ref="agent", routing_explanation="Rule"
    )
    for handoff in (response["handoff"], records["primary"]["response"]["handoff"]):
        handoff.update(copy.deepcopy(hidden))
        handoff["route"].update(route)
    # Released contracts.ts projection, reproduced with actual Zod privately;
    # Python CI needs no Node dependencies for this authored regression.
    for field in hidden:
        del response["handoff"][field]
    for field in route:
        del response["handoff"]["route"][field]
    return response, records


def test_bff_projection_is_explicit_and_preserves_advertised_receipt() -> None:
    response, records = _bff_handoff_fixture()
    with pytest.raises(ControlFailure, match="Response differs"):
        verify_turn([], records, "authored-chat", response, nlu_expected=False)
    verified = verify_turn(
        [], records, "authored-chat", response, nlu_expected=False, response_projection="bff"
    )
    assert verified.total_usd == 0


@pytest.mark.parametrize("mutation", ["facts", "queue", "reply", "actions", "policy"])
def test_bff_projection_keeps_facts_routing_reply_actions_and_policy_exact(mutation: str) -> None:
    response, records = _bff_handoff_fixture()
    if mutation == "facts":
        response["handoff"]["verified_facts"] = [_fact()]
    elif mutation == "queue":
        response["handoff"]["route"]["queue"] = "Fraudes"
    elif mutation == "reply":
        response["reply"] = "Changed reply"
    elif mutation == "actions":
        response["handoff"]["actions_taken"].append("create_dispute")
    else:
        response["policy_rules"] = ["FRD-01"]
    with pytest.raises(ControlFailure, match="Response differs"):
        verify_turn(
            [], records, "authored-chat", response, nlu_expected=False, response_projection="bff"
        )


def _judge_identity(profile: str, role: str) -> tuple[Principal, Scope, dict[str, Any]]:
    locale = "pt-BR" if profile == "pt" else "es-MX"
    now = datetime(2026, 10, 3, 12, tzinfo=UTC)
    identifiers = json.loads("""{
        "session_id": "authored-session", "run_id": "authored-run",
        "customer_id": "authored-customer", "username": "judge.authored"}""")
    principal = Principal(
        **identifiers,
        otp_at=now,
        expires_at=now + timedelta(hours=1),
        role=role,
        locale=locale,
        judge_reference=JudgeReference("ctrl-run", "ctrl-session", "fixture-digest", "binding"),
        judge_profile=profile,
    )
    scope = Scope(principal.customer_id, principal.run_id, principal.session_id)
    identity = dict(username=principal.username, locale=locale, role=role, judge_profile_id=profile)
    identity.update(language="pt" if profile == "pt" else "es", judge_profiles_enabled=True)
    identity["profile_selection_required"] = False
    return principal, scope, identity


@pytest.mark.parametrize("profile", ["mx-es", "pt"])
@pytest.mark.parametrize("role", ["customer", "agent", "ops"])
def test_trusted_es_pt_judge_roles_are_preserved(profile: str, role: str) -> None:
    principal, scope, identity = _judge_identity(profile, role)
    verify_judge_identity(
        principal,
        scope,
        profile_id=profile,
        username="judge.authored",
        trusted_locale=principal.locale,
        trusted_role=role,
        identity=identity,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "customer_id",
        "run_id",
        "sid",
        "role",
        "locale",
        "profile",
        "username",
        "no_judge",
        "controller",
        "public_role",
        "public_locale",
    ],
)
def test_foreign_scope_persona_or_controller_cannot_pass_judge_identity(mutation: str) -> None:
    principal, scope, identity = _judge_identity("pt", "ops")
    principal_changes = json.loads("""{
        "role": {"role": "customer"}, "locale": {"locale": "es-MX"},
        "profile": {"judge_profile": "mx-es"}, "no_judge": {"judge_reference": null}}""")
    if mutation in {"customer_id", "run_id", "sid"}:
        scope = replace(scope, **{mutation: "foreign-scope"})
    elif mutation in principal_changes:
        principal = replace(principal, **principal_changes[mutation])
    elif mutation == "username":
        identity["username"] = "judge.other"
    elif mutation == "controller":
        principal = replace(principal, judge_profile=None, role="customer")
        identity.update(judge_profile_id=None, profile_selection_required=True)
    elif mutation == "public_role":
        identity["role"] = "customer"
    elif mutation == "public_locale":
        identity["locale"] = "es-MX"
    with pytest.raises(ControlFailure):
        verify_judge_identity(
            principal,
            scope,
            profile_id="pt",
            username="judge.authored",
            trusted_locale="pt-BR",
            trusted_role="ops",
            identity=identity,
        )
