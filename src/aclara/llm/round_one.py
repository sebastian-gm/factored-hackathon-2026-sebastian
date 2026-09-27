"""Reproducible, aggregate-only OpenRouter comparison on the current dev suite."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml  # type: ignore[import-untyped]

from aclara.evals.schema import Scenario, ScenarioSuite
from aclara.llm.client import StructuredClient
from aclara.llm.comparison import ComparisonCase, evaluate_model
from aclara.llm.config import Price
from aclara.llm.prompts import load_prompt
from aclara.llm.types import ModelSpec

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "evals/dev_scenarios.yaml"
PROMPT = ROOT / "prompts/nlu/v1.md"
OUTPUT = ROOT / "artifacts/ai-round-one/summary.json"
CAP_USD = 5.0
MODEL_IDS = (
    "deepseek/deepseek-v4-flash-0731",
    "qwen/qwen3.5-9b",
    "google/gemini-2.5-flash-lite",
    "google/gemini-3-flash-preview",
    "x-ai/grok-4.3",
)
SCORED_SLOTS = ("amount_value", "currency", "merchant_expr")
LOGGER = logging.getLogger(__name__)


class SpendCapReached(RuntimeError):
    """The approved round-one spend has been exhausted."""


def _get_json(url: str, key: str | None = None) -> dict[str, object]:
    headers = {"User-Agent": "Aclara synthetic dev comparison/1.0"}
    if key is not None:
        headers["Authorization"] = f"Bearer {key}"
    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:  # noqa: S310
            value = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("OpenRouter metadata readback failed") from exc
    if not isinstance(value, dict):
        raise RuntimeError("OpenRouter metadata was not an object")
    return value


def _local_key() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.partition("=")[2].strip().strip('"').strip("'")
            if key:
                return key
    raise RuntimeError("Local OpenRouter key is unavailable")


def _catalog(
    model_ids: tuple[str, ...] = MODEL_IDS,
) -> tuple[dict[str, ModelSpec], dict[str, Price]]:
    url = "https://openrouter.ai/api/v1/models?supported_parameters=response_format&zdr=true"
    data = _get_json(url).get("data")
    if not isinstance(data, list):
        raise RuntimeError("OpenRouter model catalog is unavailable")
    found = {item["id"]: item for item in data if isinstance(item, dict) and "id" in item}
    models: dict[str, ModelSpec] = {}
    prices: dict[str, Price] = {}
    for model_id in model_ids:
        item = found.get(model_id)
        if not isinstance(item, dict):
            raise RuntimeError(f"Required ZDR structured-output route is unavailable: {model_id}")
        pricing = item.get("pricing")
        if not isinstance(pricing, dict):
            raise RuntimeError(f"Catalog price is unavailable: {model_id}")
        input_rate = float(pricing["prompt"]) * 1_000_000
        output_rate = float(pricing["completion"]) * 1_000_000
        if input_rate <= 0 or output_rate <= 0:
            raise RuntimeError(f"Positive catalog price is required: {model_id}")
        models[model_id] = ModelSpec(
            provider="openai_compat",
            model_id=model_id,
            base_url="https://openrouter.ai/api/v1",
            key_env="OPENROUTER_API_KEY",
            output_mode="json_schema",
            price_id=model_id,
        )
        prices[model_id] = Price(
            input_per_million=input_rate,
            output_per_million=output_rate,
            cache_read_per_million=input_rate,
            cache_write_per_million=input_rate,
            as_of=datetime.now(UTC).date(),
            source_url=f"https://openrouter.ai/{model_id}",
        )
    return models, prices


def _intent(scenario_id: str) -> str:
    if ".normal." in scenario_id:
        return "charge_inquiry"
    if ".ambiguous." in scenario_id:
        return "dispute_charge" if scenario_id.endswith(".vague.purchase") else "charge_inquiry"
    if ".human.explicit." in scenario_id:
        return "human_request"
    if ".human.fee.dispute" in scenario_id:
        return "fee_dispute"
    if ".human.card.lost" in scenario_id or ".human.fraud" in scenario_id:
        return "card_lost_or_fraud"
    if ".human.out.of.scope" in scenario_id:
        return "out_of_scope"
    raise ValueError(f"No NLU label for scenario {scenario_id}")


def _slots(scenario_id: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    if ".normal." in scenario_id:
        for token, merchant in (
            ("pending", "Café Central"),
            ("reversed", "Loja Sol"),
            ("declined", "Livraria Azul"),
            ("dispute", "Mercado Verde"),
        ):
            if token in scenario_id:
                slots["merchant_expr"] = merchant
                break
    if ".ambiguous.amount." in scenario_id:
        slots["amount_value"] = "250"
        if ".reais" in scenario_id:
            slots["currency"] = "BRL"
        elif ".dollars" in scenario_id:
            slots["currency"] = "USD"
    return slots


def _case(scenario: Scenario) -> ComparisonCase:
    first = scenario.turns[0]
    if not hasattr(first, "message"):
        raise ValueError(f"Scenario has no opening message: {scenario.id}")
    return ComparisonCase(
        message=first.message,
        country="",  # The dev scenario has no country label; do not infer one.
        bank_clock=datetime(2026, 6, 18, 6, tzinfo=UTC),
        gold_intent=_intent(scenario.id),
        gold_slots=_slots(scenario.id),
        language=scenario.language,
        scored_slot_keys=SCORED_SLOTS,
        case_id=scenario.id,
    )


def _cases() -> tuple[list[ComparisonCase], str]:
    source = SUITE.read_bytes()
    suite = ScenarioSuite.model_validate(yaml.safe_load(source))
    cases = [_case(scenario) for scenario in suite.scenarios]
    if len(cases) != 32:
        raise RuntimeError("Current dev scenario count changed; review the mapping before paid use")
    return cases, sha256(source).hexdigest()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--pilot", action="store_true", help="Check one case per model before the full run"
    )
    args = parser.parse_args()
    cases, suite_hash = _cases()
    suite_cases = len(cases)
    if args.pilot and not args.dry_run:
        cases = cases[:1]
    models, prices = _catalog()
    ordered = sorted(
        MODEL_IDS,
        key=lambda model_id: (
            2500 * prices[model_id].input_per_million + 300 * prices[model_id].output_per_million
        ),
    )
    if args.dry_run:
        LOGGER.info("Unreviewed dev scenarios: %d; suite SHA-256: %s", len(cases), suite_hash)
        for model_id in ordered:
            price = prices[model_id]
            LOGGER.info(
                "%s: $%g/M input, $%g/M output",
                model_id,
                price.input_per_million,
                price.output_per_million,
            )
        return 0
    if os.getenv("LLM_REAL_CALLS_APPROVED") != "1":
        raise RuntimeError("Process-local owner approval gate is required")
    key = _local_key()
    os.environ["OPENROUTER_API_KEY"] = key
    output = OUTPUT.with_name("pilot.json") if args.pilot else OUTPUT
    if output.exists():
        raise RuntimeError("Existing run artifact cannot be overwritten; use the follow-up runner")
    prior_spend = 0.0
    for name in ("pilot.json", "summary.json", "baseline-diagnostic.json", "revised.json"):
        path = OUTPUT.with_name(name)
        if not path.exists():
            continue
        previous = json.loads(path.read_text(encoding="utf-8"))
        if "client_recorded_cost_usd" in previous:
            prior_spend += float(previous["client_recorded_cost_usd"])
        else:
            prior_spend += sum(
                float(attempt["cost_usd"])
                for observation in previous["observations"]
                for attempt in observation["attempts"]
            )
    if prior_spend >= CAP_USD:
        raise SpendCapReached("Approved $5 run cap was already reached")
    client = StructuredClient(
        models, prices, budget_usd=CAP_USD - prior_spend, daily_budget_usd=CAP_USD - prior_spend
    )
    prompt = load_prompt(PROMPT)
    rows: list[dict[str, object]] = []
    for model_id in ordered:
        LOGGER.info("Running %s on %d unreviewed dev cases", model_id, len(cases))
        count = 0

        def check_spend() -> None:
            nonlocal count
            count += 1
            if any(record.cost_usd is None for record in client.records):
                raise RuntimeError("Per-call cost missing; stop rather than infer key-level usage")
            spent = prior_spend + client.spent_usd
            if spent >= CAP_USD:
                raise SpendCapReached("Approved $5 run cap reached")
            if count % 8 == 0:
                LOGGER.info("  %d/%d; billed spend so far $%.4f", count, len(cases), spent)

        row = evaluate_model(model_id, cases, client, prompt, after_case=check_spend)
        rows.append(asdict(row))
        if row.valid_json_rate is not None:
            LOGGER.info(
                "  done: intent=%.1f%%, slots=%.1f%%, JSON=%.1f%%",
                100 * row.intent_accuracy,
                100 * row.slot_f1,
                100 * row.valid_json_rate,
            )
        else:
            LOGGER.info("  done: no parseable provider attempts")
    summary = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "suite_path": "evals/dev_scenarios.yaml",
        "suite_sha256": suite_hash,
        "suite_cases": suite_cases,
        "evaluated_cases": len(cases),
        "suite_reviewed": False,
        "run_cap_usd": CAP_USD,
        "prior_per_call_cost_usd": prior_spend,
        "cumulative_per_call_cost_usd": prior_spend + client.spent_usd,
        "client_recorded_cost_usd": client.spent_usd,
        "rows": rows,
        "attempts": len(client.records),
        "invalid_json_attempts": sum(r.status == "invalid_json" for r in client.records),
        "provider_error_attempts": sum(r.status == "provider_error" for r in client.records),
        "refusal_attempts": sum(r.status == "refusal" for r in client.records),
        "model_choice": None,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Aggregate summary: %s", output.relative_to(ROOT))
    LOGGER.info("Cumulative per-call response cost: $%.4f", prior_spend + client.spent_usd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
