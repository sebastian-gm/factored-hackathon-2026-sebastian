"""Capped, synthetic-only local P-path and phrasing development studies.

This module never reads the frozen held-out suite. Per-case details stay in ignored
artifacts; docs receive aggregates only. Run only with the owner's paid-call approval.
"""

# ruff: noqa: T201 -- aggregate-only development CLI output.

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from copy import deepcopy
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from statistics import mean
from typing import Any, cast

from dotenv import load_dotenv
from pydantic import BaseModel
from typesafe_sdk import RetryPolicy, TypeSafeClient

from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact, redact_for_model
from aclara.llm.client import StructuredClient
from aclara.llm.config import load_fallback_route, load_models, load_prices
from aclara.llm.prompts import load_prompt
from aclara.llm.providers import Provider
from aclara.llm.types import ModelFailure, ModelSpec, ProviderResponse
from aclara.llm.typesafe import MODEL_ID as JEV_MODEL_ID
from aclara.llm.typesafe import TypeSafeAdapter
from aclara.llm.typesafe_questions import judge_questions
from evals.studies.llm.judge import _score

ROOT = Path(__file__).resolve().parents[3]
DEV = ROOT / "evals/dev_scenarios_v2.yaml"
LIMIT_USD = 0.50


class ForcedGeminiFailure:
    """Inject two no-network Gemini errors to exercise the real Grok fallback once."""

    def __init__(self, delegate: Provider) -> None:
        self.delegate = delegate
        self.remaining = 2

    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        if spec.model_id == "google/gemini-3-flash-preview" and self.remaining:
            self.remaining -= 1
            raise ModelFailure("Synthetic primary-provider fault for dev fallback check")
        return self.delegate.complete(spec, system, user, schema, key)


def _client(remaining_usd: float, *, template_only: bool, force_grok: bool) -> StructuredClient:
    models = load_models(ROOT / "config/models.yaml")
    selected = models["default"]
    models["nlu"] = selected
    models["phrase"] = models["phrase"] if template_only else selected
    fallback = load_fallback_route(ROOT / "config/models.yaml", models)
    client = StructuredClient(
        models,
        load_prices(ROOT / "config/pricing.yaml"),
        budget_usd=remaining_usd,
        daily_budget_usd=remaining_usd,
        fallback_routes={"nlu": fallback, "phrase": fallback} if fallback else None,
        call_timeout_seconds=45,
    )
    if force_grok:
        client._adapters["openai_compat"] = ForcedGeminiFailure(client._adapters["openai_compat"])
    return client


async def _case(scenario: dict[str, Any], client: StructuredClient) -> dict[str, Any]:
    """Exercise the real local ASGI P flow with generated fixture records."""
    from aclara.agent.runtime import Runtime
    from aclara.bank.repository import TransactionRepository
    from aclara.settings import Settings

    reactive: Any = import_module("evals.reactive")
    runner: Any = import_module("evals.runner")

    original = runner._new_authenticated_client

    async def inject(
        settings: Settings | None = None,
        repository: TransactionRepository | None = None,
        runtime: Runtime | None = None,
        *,
        llm_client: StructuredClient | None = None,
    ) -> tuple[Any, Any, str, str]:
        return cast(
            tuple[Any, Any, str, str],
            await original(settings, repository, runtime, llm_client=client),
        )

    runner._new_authenticated_client = inject
    try:
        return cast(dict[str, Any], await reactive.execute(scenario, "P"))
    finally:
        runner._new_authenticated_client = original


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def _save(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    pending.chmod(0o600)
    pending.replace(path)
    path.chmod(0o600)


def _record_summary(client: StructuredClient) -> dict[str, Any]:
    return {
        "known_cost_usd": sum(record.cost_usd or 0.0 for record in client.records),
        "charged_usd": client.spent_usd,
        "unknown_cost_attempts": sum(record.cost_usd is None for record in client.records),
        "calls": [
            {
                "route": record.route,
                "model_id": record.model_id,
                "provider": record.provider,
                "status": record.status,
                "cost_usd": record.cost_usd,
                "latency_ms": record.latency_ms,
                "judgments": record.judgments if record.provider == "typesafe" else None,
            }
            for record in client.records
        ],
    }


def _scenarios(mode: str) -> list[dict[str, Any]]:
    suite = import_module("yaml").safe_load(DEV.read_text())
    cases: list[dict[str, Any]] = suite["scenarios"]
    if mode == "latency":
        chosen = [case for case in cases if not case.get("faults")]
        if len(chosen) != 20:
            raise ValueError("The 20 no-fault dev scenarios changed")
        return chosen
    if mode == "ablation_tail":
        paraphrases = {
            "es.pending.v2": "Quisiera entender la autorización de Café Central.",
            "es.reversed.v2": "¿Me explicas qué pasó con la compra de Loja Sol?",
            "es.declined.v2": "¿Por qué figura rechazado el cargo de Livraria Azul?",
            "es.choose.v2": "¿Me explicas ese cargo por 250 dólares?",
            "pt.pending.v2": "Pode explicar a cobrança pendente do Café Central?",
            "pt.reversed.v2": "O que aconteceu com a compra na Loja Sol?",
            "pt.declined.v2": "Por que aparece a cobrança recusada da Livraria Azul?",
            "pt.choose.v2": "Pode me explicar a cobrança de 250 dólares?",
        }
        result = []
        for case in cases:
            if case["id"] in paraphrases:
                revised = deepcopy(case)
                revised["id"] += ".paraphrase"
                revised["turns"][0]["message"] = paraphrases[case["id"]]
                result.append(revised)
        if len(result) != 8:
            raise ValueError("The eight exploratory paraphrase cases changed")
        return result
    chosen = [
        case
        for case in cases
        if case["id"] not in {"es.session_expired.v2", "pt.session_expired.v2"}
    ]
    if len(chosen) != 30:
        raise ValueError("The 30-case ablation selection changed")
    return chosen


def _judge(row: dict[str, str], remaining_usd: float, adapter: TypeSafeAdapter) -> dict[str, Any]:
    models = load_models(ROOT / "config/models.yaml")
    spec = replace(models["openrouter_sonnet"], max_output_tokens=256)
    if remaining_usd <= 0.015:
        raise RuntimeError("Ablation cap has no room for the paired judges")
    client = StructuredClient(
        {spec.model_id: spec},
        load_prices(ROOT / "config/pricing.yaml"),
        budget_usd=remaining_usd - 0.01,
        daily_budget_usd=remaining_usd - 0.01,
    )
    sonnet: dict[str, Any] | None = None
    jev: dict[str, Any] | None = None
    jev_cost: float | None = None
    jev_charged = 0.0
    try:
        sonnet = _score(client, row, load_prompt(ROOT / "prompts/judge/v1.md")).model_dump()
        state = {
            "target_locale": row["target_locale"],
            "customer_message": redact_for_model(row["customer_message"]),
            "customer_reply": redact_for_model(row["customer_reply"]),
            "handoff_summary": None,
        }
        result = adapter.ask(state, judge_questions(has_handoff=False))
        jev = {
            name: min(5, max(1, 1 + math.floor(value.score + 0.5)))
            for name, value in result.scores.items()
        }
        jev_cost = result.cost_usd
        jev_charged = jev_cost if jev_cost is not None else 0.01
    except Exception as exc:
        return {
            "sonnet": sonnet,
            "jev": jev,
            "error_type": type(exc).__name__,
            "known_cost_usd": sum(r.cost_usd or 0.0 for r in client.records) + (jev_cost or 0),
            "charged_usd": client.spent_usd + (jev_charged or 0.01 if sonnet else 0),
            "unknown_cost_attempts": sum(r.cost_usd is None for r in client.records),
        }
    return {
        "sonnet": sonnet,
        "jev": jev,
        "known_cost_usd": sum(r.cost_usd or 0.0 for r in client.records) + (jev_cost or 0),
        "charged_usd": client.spent_usd + jev_charged,
        "unknown_cost_attempts": sum(r.cost_usd is None for r in client.records)
        + int(jev_cost is None),
    }


async def run(mode: str, output: Path) -> dict[str, Any]:
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Owner approval is required for dev paid calls")
    if output.exists():
        raise FileExistsError("Study output exists; inspect checkpoint before any paid rerun")
    scenarios = _scenarios(mode)
    ledger: dict[str, Any] = {"mode": mode, "cap_usd": LIMIT_USD, "cases": []}
    charged = 0.0
    if mode == "ablation_tail":
        prior = json.loads((output.parent / "ablation.json").read_text())
        charged = float(prior["charged_usd"])
        ledger["prior_charged_usd"] = charged
    adapter: TypeSafeAdapter | None = None
    raw_jev: TypeSafeClient | None = None
    if mode != "latency":
        key = os.getenv("TYPESAFE_API_KEY")
        if not key:
            raise RuntimeError("TypeSafe key is needed for paired dev judging")
        raw_jev = TypeSafeClient(
            api_key=key, model=JEV_MODEL_ID, retry=RetryPolicy(max_retries=0), timeout=20
        )
        adapter = TypeSafeAdapter(raw_jev)
    try:
        for index, scenario in enumerate(scenarios):
            remaining = LIMIT_USD - charged
            if remaining <= 0.065:
                break
            client = _client(
                remaining,
                template_only=mode != "latency",
                force_grok=mode == "latency" and index == 0,
            )
            item: dict[str, Any] = {"id": scenario["id"]}
            try:
                case = await _case(scenario, client)
                item.update(
                    turn_ms=case["turn_ms"],
                    case_ms=sum(case["turn_ms"]),
                    passed=case["passed"],
                    outcome=case["outcome"],
                    final=case["responses"][-1] if case["responses"] else None,
                    customer_message=scenario["turns"][0].get("message", ""),
                    language=scenario["language"],
                    phrasing_events=[e for e in case["events"] if e["event"] == "phrasing"],
                )
            except Exception as exc:
                item["error_type"] = type(exc).__name__
            item.update(_record_summary(client))
            charged += client.spent_usd
            if mode != "latency" and item.get("final"):
                final = ResponsePlan.model_validate(item["final"])
                template_text = final.reply
                llm_text = template_text
                violations: tuple[str, ...] = ()
                phrase_cost = 0.0
                if (
                    final.response_type in {"clarify", "explain_status"}
                    and LIMIT_USD - charged > 0.02
                ):
                    phrase_client = _client(
                        LIMIT_USD - charged, template_only=False, force_grok=False
                    )
                    facts: tuple[AllowedFact, ...] = ()
                    if final.transaction:
                        facts = tuple(
                            AllowedFact(key, str(value), "scoped_transaction_read")
                            for key, value in final.transaction.model_dump(mode="json").items()
                            if value is not None
                        )
                    try:
                        built = build_reply(
                            final,
                            language=scenario["language"],
                            country="MX",
                            facts=facts,
                            client=phrase_client,
                        )
                        if not built.used_template:
                            llm_text = built.plan.reply
                        violations = built.violations
                    except Exception as exc:
                        item["phrase_error_type"] = type(exc).__name__
                    phrase_cost = phrase_client.spent_usd
                    charged += phrase_cost
                    item["phrase_calls"] = _record_summary(phrase_client)
                item["phrase_violations"] = list(violations)
                item["phrase_charged_usd"] = phrase_cost
                item["phrasing_changed"] = llm_text != template_text
                item["template_reply"] = template_text
                item["llm_reply"] = llm_text
                assert adapter is not None
                for arm, reply in (("template", template_text), ("llm", llm_text)):
                    if arm == "llm" and reply == template_text:
                        item["llm_judges"] = item.get("template_judges")
                        continue
                    if LIMIT_USD - charged <= 0.015:
                        item[f"{arm}_judges"] = {"error_type": "cap_reached"}
                        continue
                    row = {
                        "target_locale": "pt-BR" if scenario["language"] == "pt" else "es-MX",
                        "customer_message": item["customer_message"],
                        "customer_reply": reply,
                        "handoff_summary": "",
                    }
                    judged = _judge(row, LIMIT_USD - charged, adapter)
                    charged += judged["charged_usd"]
                    item[f"{arm}_judges"] = judged
            ledger["cases"].append(item)
            ledger["charged_usd"] = charged
            _save(output, ledger)
            if charged > LIMIT_USD + 1e-9:
                raise RuntimeError("Development-study hard cap exceeded")
    finally:
        if raw_jev is not None:
            raw_jev.close()
    ledger["completed"] = len(ledger["cases"])
    ledger["known_cost_usd"] = sum(
        item["known_cost_usd"]
        + (item.get("phrase_calls") or {}).get("known_cost_usd", 0)
        + sum(
            (item.get(f"{arm}_judges") or {}).get("known_cost_usd", 0)
            for arm in ("template", "llm")
            if not (arm == "llm" and not item.get("phrasing_changed"))
        )
        for item in ledger["cases"]
    )
    _save(output, ledger)
    return ledger


def summary(ledger: dict[str, Any]) -> dict[str, Any]:
    cases = ledger["cases"]
    turns = [duration for item in cases for duration in item.get("turn_ms", [])]
    case_ms = [item["case_ms"] for item in cases if "case_ms" in item]
    costs = [item["known_cost_usd"] for item in cases]
    return {
        "mode": ledger["mode"],
        "completed": len(cases),
        "passed": sum(bool(item.get("passed")) for item in cases),
        "turns": len(turns),
        "turn_p50_ms": _percentile(turns, 0.5),
        "turn_p95_ms": _percentile(turns, 0.95),
        "case_p50_ms": _percentile(case_ms, 0.5),
        "case_p95_ms": _percentile(case_ms, 0.95),
        "mean_known_cost_per_conversation_usd": mean(costs) if costs else None,
        "known_cost_usd": ledger["known_cost_usd"],
        "charged_usd": ledger["charged_usd"],
        "grok_calls": sum(
            call["model_id"] == "x-ai/grok-4.20" for item in cases for call in item.get("calls", [])
        ),
        "jev_calls": sum(
            call["provider"] == "typesafe" and call["status"] == "valid"
            for item in cases
            for call in item.get("calls", [])
        ),
        "changed_phrasing": sum(bool(item.get("phrasing_changed")) for item in cases),
        "grounding_catches": sum(bool(item.get("phrase_violations")) for item in cases),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("latency", "ablation", "ablation_tail"))
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    output = ROOT / "artifacts" / "dev-studies" / f"{args.mode}.json"
    result = asyncio.run(run(args.mode, output))
    print(json.dumps(summary(result)))


if __name__ == "__main__":
    main()
