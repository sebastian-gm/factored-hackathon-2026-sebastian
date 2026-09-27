"""Seeded human-like synthetic expressions; never reads the human spot-check.

Template extraction followed by the serving NLU postprocessor models a noisy
slot boundary. It is not a claim of real-model language understanding quality.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from aclara.agent.nlu.structured import ExtractedNlu, postprocess
from aclara.ml.charge_matcher.types import Candidate, Query, Slots

HUMAN_FAMILIES = (
    "approx_cerca",
    "approx_casi",
    "approx_como",
    "thousands",
    "k_suffix",
    "typo",
    "merchant_type",
    "urgency",
)


def read_queries(path: Path) -> list[Query]:
    queries = []
    for line in path.read_text().splitlines():
        raw = json.loads(line)
        slots = raw.pop("slots")
        for key in ("date_start", "date_end"):
            slots[key] = date.fromisoformat(slots[key]) if slots[key] else None
        candidates = tuple(
            Candidate(
                **{
                    **row,
                    "transaction_date": datetime.fromisoformat(row["transaction_date"]),
                    "process_date": date.fromisoformat(row["process_date"]),
                }
            )
            for row in raw.pop("candidates")
        )
        raw["as_of"] = datetime.fromisoformat(raw["as_of"])
        queries.append(Query(**raw, slots=Slots(**slots), candidates=candidates))
    return queries


def serving_query(query: Query) -> Query:
    """Mirror MatchState's projection without changing source records or labels."""
    return replace(
        query,
        candidates=tuple(
            replace(row, category=None, channel="", country="") for row in query.candidates
        ),
        slots=replace(query.slots, category=None, channel=None),
    )


def merchant_type(category: str | None) -> str:
    category = (category or "").casefold()
    for tokens, hint in (
        (("hardware", "home", "ferreter"), "una ferretería"),
        (("food", "restaurant", "dining"), "un restaurante"),
        (("grocery", "supermarket"), "un supermercado"),
        (("health", "pharmacy"), "una farmacia"),
        (("travel", "hotel"), "un hotel"),
    ):
        if any(token in category for token in tokens):
            return hint
    return "una tienda"


def expression_noise(query: Query, family: str, seed: int) -> tuple[Query, dict[str, Any]]:
    if family not in HUMAN_FAMILIES:
        raise ValueError("unknown synthetic expression family")
    rng = random.Random(seed)  # noqa: S311 -- reproducible synthetic noise.
    target = next((row for row in query.candidates if row.transaction_id == query.target_id), None)
    source = (
        Slots(
            amount=target.amount,
            currency=target.currency,
            merchant=target.merchant if target.transaction_type == "Purchase" else None,
            transaction_type=target.transaction_type,
            category=target.category,
        )
        if target
        else query.slots
    )
    amount = source.amount
    if amount is not None and family.startswith("approx_"):
        amount *= 1 + rng.choice((-1, 1)) * rng.uniform(0.03, 0.20)
        magnitude = 10 ** max(0, len(str(int(abs(amount)))) - 2)
        amount = round(amount / magnitude) * magnitude
    amount_expr = f"{amount:.2f}" if amount is not None else None
    if amount is not None:
        if family == "thousands":
            amount_expr = f"{round(amount):,}"
        elif family == "k_suffix":
            amount_expr = f"{amount / 1000:.1f}k"
        elif family.startswith("approx_"):
            prefixes = {"approx_cerca": "cerca de", "approx_casi": "casi", "approx_como": "como"}
            amount_expr = f"{prefixes[family]} {amount:g}"
    # Merchant omission is common; a type hint is not a fabricated merchant identity.
    merchant = source.merchant if rng.random() < 0.25 else None
    type_expr = (
        "compra" if source.transaction_type == "Purchase" and rng.random() < 0.25 else "cobro"
    )
    if family == "merchant_type" and source.transaction_type == "Purchase":
        merchant = merchant_type(source.category)
    if family == "typo":
        type_expr = "cobor"
        merchant = source.merchant
        if merchant and len(merchant) > 2:
            index = rng.randrange(1, len(merchant) - 1)
            merchant = merchant[:index] + merchant[index + 1 :]
    extracted = ExtractedNlu(
        language="es",
        intent="charge_inquiry",
        intent_confidence=1.0,
        amount_expr=amount_expr,
        currency_expr=source.currency,
        merchant_expr=merchant,
        type_expr=type_expr,
    )
    normalized = postprocess(
        extracted, country=query.customer_country, bank_clock=query.as_of
    ).slots
    slots = Slots(
        amount=float(normalized.amount_value) if normalized.amount_value is not None else None,
        currency=normalized.currency,
        merchant=normalized.merchant_expr,
        transaction_type=normalized.type_expr,
    )
    prefix = "Necesito ayuda urgente, " if family == "urgency" else "Hola, "
    if family == "typo":
        prefix = "hola me llego una notifiacion, "
    utterance = prefix + "no entiendo este " + type_expr
    if amount_expr:
        utterance += " de " + amount_expr
    if source.currency:
        utterance += " " + source.currency
    if merchant:
        utterance += " en " + merchant
    utterance += ", pueden revisar?"
    query_id = hashlib.sha256(
        f"human-noise-v2:{query.query_id}:{family}:{seed}".encode()
    ).hexdigest()
    result = serving_query(
        replace(query, query_id=query_id, slots=slots, noise_family=f"human_{family}")
    )
    return result, {
        "query_id": query_id,
        "origin": "template-generated, not human or real-model authored",
        "family": family,
        "utterance": utterance,
        "synthetic_extraction": extracted.model_dump(mode="json"),
        "normalized_slots": asdict(slots),
    }


def augment(queries: list[Query], output: Path, seed: int) -> list[Query]:
    """Three variants per source query, with stable per-query random streams."""
    output.parent.mkdir(parents=True, exist_ok=True)
    result = []
    with output.open("x") as stream:
        for query in queries:
            result.append(serving_query(query))
            key = int(hashlib.sha256(f"{seed}:{query.query_id}".encode()).hexdigest()[:16], 16)
            for offset in (0, 1):
                family = HUMAN_FAMILIES[(key + offset * 3) % len(HUMAN_FAMILIES)]
                variant, evidence = expression_noise(query, family, key + offset)
                result.append(variant)
                stream.write(json.dumps(evidence, ensure_ascii=False, default=str) + "\n")
    return result
