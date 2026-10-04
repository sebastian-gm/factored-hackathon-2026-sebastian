"""Pure v0.9.1 controls: caller owns authentication, reads, dispatch and settlement.

Use fresh owned recognition facts and post-guard inference text, never spend deltas.
"""

from __future__ import annotations

import json
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlg.grounding import redact_for_model, scan_dlp
from aclara.agent.nlu.structured import ExtractedNlu
from aclara.api.auth_models import Principal
from aclara.api.judge_access import PROFILE_LOCALES
from aclara.llm.config import load_models, load_prices, load_risk_second_opinion_enabled
from aclara.llm.prompts import data_block, load_prompt
from aclara.ops.store import Scope

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_SHA = "0f0e12d"
MINIMUM_RESERVATION = Decimal("0.00000001")
# These pins also protect the reviewed proof that all API clarifications have
# nonempty approved text. builder skips them; DLP retries use client=None.
PINNED_SOURCES = {
    "src/aclara/api/app.py": "8005763e570a23c3e5425becbafd196b4feae116dd32fd4a4b0eede597d40556",
    "src/aclara/api/staff.py": "a24677934e54e37160727ddd6a8622b6a46f7d0e740422d20e3746c915a7fa0d",
    "src/aclara/api/auth_models.py": "411f14672ed19d55682dd5311fc4a7281b26ff68cad3a13bac1d7bd8f3a83be1",
    "src/aclara/api/judge_access.py": "8ecde7737cec64202bfb1e6871026f43811214d8d0dd24f52e55eb5b23b824ac",
    "src/aclara/api/judge_sessions.py": "5645b0637a716d950c449e8544d95769cb6ba6eedb4e4eb3f5ce470a88057a42",
    "src/aclara/agent/ai.py": "d102e999160279c064d4b862d82a4a3472ac35a92ccf515f02cf1ca90f237ec8",
    "src/aclara/agent/contracts.py": "0fa9cedd9977d63e35628d6cfc86df9dfbbb07530e767d7a6c2b2af39cc5512b",
    "src/aclara/agent/nlu/structured.py": "c54a45705010ad3d0f998bbe8fb22416d7095c9544b2423bc20c336f89ca1f4e",
    "src/aclara/agent/nlu/clarification.py": "3d812172f777d11e06a64ab9363cd130b0d552d2edcfbf3d474e5ba3a2366f0d",
    "src/aclara/agent/nlg/builder.py": "33c3127790aca8a7c09e1219c7b0e674541bb17b90a9472c20e709ac6900c0ba",
    "src/aclara/agent/nlg/grounding.py": "f7be60fc57641cd1092b5c943edce24ee472cecd747c9461879bc12e7f471cf8",
    "src/aclara/llm/client.py": "cca4fb06ea2f6c975c4b590301c0ccdbb502c41c33e6052dabc5ab4a4ad60ce5",
    "src/aclara/llm/config.py": "eb43c443ad7275bdd8629f3e3524df392996b88a40f050bf30177742c4a06c44",
    "src/aclara/llm/providers.py": "74e4a2585971e7ddb56f69f16373857ba0d846c2d7812d9e67bb2c9b24cba045",
    "src/aclara/llm/prompts.py": "2b1005f96838d3cb9000d0d079d168f0ca22b8834c62db70c70630350e00707c",
    "src/aclara/llm/types.py": "d043fbd157c726f60beef09691cec61be197d80c76dee92a7815035aff003199",
    "config/models.yaml": "c1d5a6474fcb25319d348fee218452b6c48162d0fca24bb83249a2fdf5b417a0",
    "config/pricing.yaml": "34d2173505ebcf41ad08429bc2c5105d0327f8760ce48998f222900285b0e457",
    "prompts/nlu/v5.md": "e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc",
    "prompts/phrase/v2.md": "96089ad7985a334b8c6b974298856d939e554d431f04c6c1e7a434d75ec71fd9",
    "uv.lock": "2c3452be249a247b2f0333f9fd032e6e69a0ac454359e2b53e29dd176e35b22d",
    "apps/web/src/lib/contracts.ts": "2b1e541e23680df7ffb4b71d345e37866000da034821f5f05d0d125a8dd61867",
    "apps/web/src/app/api/bff/[...path]/route.ts": "9d72681c56e30b9b8c46d39aa4db516ad03ac1c5d6a2993d4ad532eb98fb6663",
}
_CHARGE_FIELDS = {"merchant", "transaction_date", "amount", "currency", "status"}
_ROUTES = {"nlu": "default", "fallback_grok_4_20": "fallback_grok_4_20"}
_BFF_OMITTED_HANDOFF = {
    "conversation_id",
    "customer",
    "customer_statements",
    "policy_evaluations",
    "risk_flags",
    "suggested_next_steps",
    "sla_due_at",
    "transcript_ref",
    "trace_ref",
}
_BFF_OMITTED_ROUTE = {"requested_queue", "assigned_agent_ref", "routing_explanation"}


class ControlFailure(ValueError):
    """Stop before dispatch, or retain the reservation if a receipt is unknown."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ControlFailure(reason)


def verify_pinned_sources(root: Path = REPO_ROOT) -> None:
    """Verify the local reviewed source; caller separately verifies deployed SHA."""
    try:
        for path, expected in PINNED_SOURCES.items():
            _require(
                sha256((root / path).read_bytes()).hexdigest() == expected, "Source pin changed"
            )
        _require(
            not load_risk_second_opinion_enabled(root / "config/models.yaml"),
            "Risk second opinion is outside this approval",
        )
    except OSError:
        raise ControlFailure("Pinned source unavailable") from None


def contextual_nlu_ceiling(
    message: str,
    *,
    awaiting_recognition: bool = False,
    masked_charge: Mapping[str, Any] | None = None,
    root: Path = REPO_ROOT,
) -> Decimal:
    """All two primary + two alternate attempts; risk/phrase are pinned out.

    Use prepare_nlu's actual cleaned text; deterministic requests reserve the
    minimum. Never infer a zero ceiling from model predictions or earlier turns.
    """
    verify_pinned_sources(root)
    _require(isinstance(message, str) and 1 <= len(message) <= 1000, "Invalid inference message")
    _require(type(awaiting_recognition) is bool, "Invalid recognition state")
    allowed: dict[str, str] = {}
    if awaiting_recognition:
        _require(
            masked_charge is not None and masked_charge.keys() >= _CHARGE_FIELDS,
            "Missing owned charge facts",
        )
        assert masked_charge is not None
        for key, value in masked_charge.items():
            if key in _CHARGE_FIELDS:
                redacted = redact_for_model(str(value))[:160]
                allowed[key] = "[REDACTED]" if scan_dlp(redacted) else redacted
    user = "\n".join(
        (
            data_block(
                "record",
                json.dumps(
                    {"awaiting_recognition": awaiting_recognition, "selected_charge": allowed},
                    ensure_ascii=False,
                ),
            ),
            data_block("customer_message", redact_for_model(message)),
        )
    )
    prompt = load_prompt(root / "prompts/nlu/v5.md")
    input_bytes = len(prompt.text.encode("utf-8")) + len(user.encode("utf-8"))
    input_bytes += len(json.dumps(ExtractedNlu.model_json_schema()).encode("utf-8")) + 1024
    models, prices = (
        load_models(root / "config/models.yaml"),
        load_prices(root / "config/pricing.yaml"),
    )
    total = Decimal(0)
    for route in _ROUTES.values():
        model = models[route]
        _require(model.provider == "openai_compat" and model.price_id in prices, "Unreviewed model")
        assert model.price_id is not None
        price = prices[model.price_id]
        total += (
            Decimal(2)
            * (
                Decimal(input_bytes) * Decimal(str(price.input_per_million))
                + Decimal(model.max_output_tokens) * Decimal(str(price.output_per_million))
            )
            / Decimal(1_000_000)
        )
    return total.quantize(MINIMUM_RESERVATION, rounding=ROUND_CEILING)


def verify_judge_identity(
    principal: Principal,
    scope: Scope,
    *,
    profile_id: str,
    username: str,
    trusted_locale: str,
    trusted_role: str,
    identity: Mapping[str, Any],
) -> None:
    """Check principal/public persona and authenticated Scope; grant no authority."""
    _require(
        profile_id in PROFILE_LOCALES
        and PROFILE_LOCALES[profile_id] == trusted_locale
        and trusted_role in {"customer", "agent", "ops"},
        "Unreviewed trusted persona",
    )
    _require(
        principal.judge_reference is not None
        and principal.judge_profile == profile_id == identity.get("judge_profile_id")
        and principal.username == username == identity.get("username")
        and bool(username and scope.customer_id and scope.run_id and scope.sid)
        and principal.customer_id == scope.customer_id
        and principal.run_id == scope.run_id
        and principal.session_id == scope.sid
        and principal.locale == trusted_locale == identity.get("locale")
        and principal.role == trusted_role == identity.get("role")
        and identity.get("language") == ("pt" if trusted_locale == "pt-BR" else "es")
        and identity.get("judge_profiles_enabled") is True
        and identity.get("profile_selection_required", False) is False,
        "Judge identity differs from trusted scope or persona",
    )


@dataclass(frozen=True, slots=True)
class VerifiedTurn:
    execution_ids: tuple[str, ...]
    call_costs: tuple[Decimal, ...]
    degraded: bool

    @property
    def total_usd(self) -> Decimal:
        return sum(self.call_costs, Decimal(0))


def verify_turn(
    previous_ids: Collection[str],
    observed_scoped_records: Mapping[str, Mapping[str, Any]],
    conversation_id: str,
    response: Mapping[str, Any],
    *,
    nlu_expected: bool,
    response_projection: Literal["api", "bff"] = "api",
    root: Path = REPO_ROOT,
) -> VerifiedTurn:
    """Verify a successful turn read independently in its authenticated scope.

    Settle returned known costs before stopping on degradation. Unknown metadata
    raises: retain reservation and stop. Non-200 guards need separate proof.
    API checks the full typed plan. BFF opt-in projects only released Zod handoff
    fields; session-ended refusal and other transformations need separate handling.
    """
    verify_pinned_sources(root)
    _require(response_projection in {"api", "bff"}, "Unknown response projection")
    try:
        plan = ResponsePlan.model_validate(response)
        new = {key: row for key, row in observed_scoped_records.items() if key not in previous_ids}
        _require(
            bool(new)
            and all(row.get("conversation_id") == conversation_id for row in new.values()),
            "Missing or foreign turn receipt",
        )
        primary = [row for row in new.values() if isinstance(row.get("response"), Mapping)]
        auxiliary = [row for row in new.values() if not isinstance(row.get("response"), Mapping)]
        _require(len(primary) == 1 and len(auxiliary) <= 1, "Ambiguous turn receipts")
        row = primary[0]
        _require(
            row.get("system") == "P" and row.get("outcome") == plan.outcome,
            "Turn identity mismatch",
        )
        stored = ResponsePlan.model_validate(row["response"])
        for item in new.values():
            _require(
                isinstance(item.get("events"), list)
                and all(isinstance(event, Mapping) for event in item["events"]),
                "Malformed execution events",
            )
        for extra in auxiliary:
            events = extra["events"]
            _require(
                plan.handoff is not None
                and extra.get("outcome") == "handoff_verified"
                and len(events) == 1
                and events[0].get("event") == "verify_readback"
                and events[0].get("handle") == plan.handoff.handoff_id,
                "Unrelated auxiliary receipt",
            )
        if plan.handoff is not None:
            # Staff commits after saving primary: verified=True + create_handoff
            # once are the only allowed enrichment; require independent readback.
            _require(
                len(auxiliary) == 1 and plan.verified is True and stored.handoff is not None,
                "Missing verified handoff enrichment",
            )
            assert stored.handoff is not None
            actions = stored.handoff.actions_taken
            _require(actions.count("create_handoff") <= 1, "Invalid original handoff actions")
            committed_actions = (
                actions if "create_handoff" in actions else [*actions, "create_handoff"]
            )
            stored = stored.model_copy(
                update={
                    "verified": True,
                    "handoff": stored.handoff.model_copy(
                        update={"actions_taken": committed_actions}
                    ),
                }
            )
        expected_response = stored.model_dump(mode="json", exclude_none=True)
        if response_projection == "bff" and stored.handoff is not None:
            projected_handoff = expected_response["handoff"]
            for field in _BFF_OMITTED_HANDOFF:
                projected_handoff.pop(field, None)
            for field in _BFF_OMITTED_ROUTE:
                projected_handoff["route"].pop(field, None)
        _require(
            expected_response == plan.model_dump(mode="json", exclude_none=True),
            "Response differs from durable receipt",
        )
        events = [event for item in new.values() for event in item["events"]]
        calls = [event for event in events if event.get("event") == "llm_call"]
        _require(nlu_expected or not calls, "Unexpected model call on deterministic path")
        models = load_models(root / "config/models.yaml")
        prompt = load_prompt(root / "prompts/nlu/v5.md")
        seen: set[tuple[str, int]] = set()
        costs: list[Decimal] = []
        for call in calls:
            route, attempt = call.get("route"), call.get("attempt")
            _require(
                route in _ROUTES and type(attempt) is int and attempt in (1, 2),
                "Unreviewed call or attempt",
            )
            _require((route, attempt) not in seen, "Duplicate call attempt")
            _require(
                (attempt == 1 or (route, 1) in seen)
                and (route == "nlu" or ("nlu", 1) in seen)
                and not (route == "nlu" and ("fallback_grok_4_20", 1) in seen),
                "Incomplete or reordered call attempts",
            )
            seen.add((route, attempt))
            model = models[_ROUTES[route]]
            _require(
                call.get("provider") == model.provider
                and call.get("model_id") == model.model_id
                and call.get("prompt_id") == f"{prompt.id}@{prompt.version}"
                and call.get("prompt_hash") == prompt.content_hash
                and call.get("status") in {"valid", "invalid_json", "provider_error", "refusal"},
                "Unreviewed call metadata",
            )
            cost = call.get("cost_usd")
            _require(cost is not None and not isinstance(cost, bool), "Unknown call cost")
            amount = Decimal(str(cost))
            _require(amount.is_finite() and amount >= 0, "Invalid call cost")
            costs.append(amount)
        degraded = plan.degraded or any(
            event.get("event") == "nlu" and event.get("degraded") is True for event in events
        )
        return VerifiedTurn(tuple(new), tuple(costs), degraded)
    except (KeyError, TypeError, InvalidOperation, ValidationError):
        raise ControlFailure("Malformed turn receipt") from None
