"""P integration boundary: extraction/phrasing never supplies identity or action authority."""

from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlg.builder import build_reply
from aclara.agent.nlg.grounding import AllowedFact, scan_dlp
from aclara.agent.nlu.structured import NluResult, understand
from aclara.agent.runtime import Runtime
from aclara.llm.client import StructuredClient
from aclara.llm.config import load_models, load_prices
from aclara.settings import Settings

ROOT = Path(__file__).resolve().parents[3]


class AgentAI:
    def __init__(
        self, settings: Settings, runtime: Runtime, client: StructuredClient | None = None
    ):
        self.runtime = runtime
        if client is None:
            models = load_models(ROOT / "config/models.yaml")
            if settings.llm_provider != "mock":
                route = os.getenv("LLM_MODEL_ROUTE", "")
                if route not in models or models[route].provider != settings.llm_provider:
                    raise ValueError(
                        "Select an explicit reviewed model route matching LLM_PROVIDER"
                    )
                models["nlu"] = models["phrase"] = models[route]
            client = StructuredClient(
                models,
                load_prices(ROOT / "config/pricing.yaml"),
                budget_usd=float(os.getenv("LLM_RUN_BUDGET_USD", "0")),
            )
        self.client = client
        self.cursor = 0

    def records(self) -> None:
        for record in self.client.records[self.cursor :]:
            self.runtime.record("llm_call", **asdict(record))
        self.cursor = len(self.client.records)

    def understand(self, message: str, clock: datetime) -> NluResult:
        outage = self.runtime.fault("llm_outage", "nlu")
        result = understand(
            message,
            country=self.runtime.country,
            bank_clock=clock,
            client=None if outage else self.client,
            prompt_path=ROOT / "prompts/nlu/v1.md",
        )
        if self.runtime.fault("unsupported_language", "nlu"):
            result = result.model_copy(update={"clarification": "language", "degraded": False})
        self.records()
        self.runtime.record(
            "nlu",
            degraded=result.degraded,
            intent=result.frame.intent.value,
            language=result.extracted.language,
            clarification=result.clarification,
        )
        return result

    def reply(
        self, value: dict[str, Any], language: str, *, deterministic: bool = False
    ) -> dict[str, Any]:
        plan = ResponsePlan.model_validate(value)
        facts: list[AllowedFact] = []
        if plan.transaction:
            for key, item in plan.transaction.model_dump(mode="json").items():
                if item is not None:
                    facts.append(AllowedFact(key, str(item), "scoped_transaction_read"))
        if self.runtime.system == "P":
            built = build_reply(
                plan,
                language=language,
                country=self.runtime.country,
                facts=tuple(facts),
                client=None if deterministic else self.client,
                prompt_path=ROOT / "prompts/phrase/v1.md",
            )
            # Retain the policy-specific deterministic explanation when phrasing falls back.
            if not built.used_template:
                plan = built.plan
            self.runtime.record(
                "phrasing", used_template=built.used_template, violations=list(built.violations)
            )
            self.records()
        dlp_text = plan.reply
        if plan.case and plan.verified:
            dlp_text = dlp_text.replace(plan.case.case_id, "[VERIFIED_CASE]")
        if scan_dlp(dlp_text):
            # No unsafe candidate text leaves this boundary. Keep typed facts/action result.
            self.runtime.record("dlp_block")
            fallback = build_reply(plan, language=language, country=self.runtime.country).plan
            plan = fallback
        return plan.model_dump(mode="json", exclude_none=True)
