"""No-network checks of candidate injection and the dev-only inventory."""

from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from evals.studies.llm.dev_prompt_study import (
    PromptStudyClient,
    comparison_sample,
    inputs,
    inventory_hash,
    load_study_prompt,
)
from pydantic import BaseModel

from aclara.llm.prompts import load_prompt
from aclara.llm.types import ModelSpec


class Judgment(BaseModel):
    flag: bool = False


def test_candidate_overrides_only_nlu_and_records_its_own_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REAL_CALLS_APPROVED", "0")
    seen: list[str] = []

    def answer(system: str, user: str, schema: type[BaseModel]) -> str:
        seen.append(system)
        return "{}"

    client = PromptStudyClient(
        {name: ModelSpec(provider="mock", model_id="mock") for name in ("nlu", "phrase")},
        {},
        mock_response=answer,
    )
    candidate = load_study_prompt("v5.2")
    client.nlu_prompt = candidate
    client.generate("nlu", "production NLU", "message", Judgment, prompt_id="nlu@v5.1")
    client.generate("phrase", "approved phrase", "message", Judgment, prompt_id="phrase@v2")
    assert seen == [candidate.text, "approved phrase"]
    assert client.records[0].prompt_hash == candidate.content_hash
    assert client.records[0].prompt_id == "nlu@v5.2"
    assert client.records[1].prompt_id == "phrase@v2"
    assert load_prompt(Path("prompts/nlu/v5.md")).version == "v5.3"


def test_archived_candidate_preserves_hash_and_live_prompt_selection() -> None:
    assert not Path("prompts/nlu/v5_2.md").exists()
    candidate = load_study_prompt("v5.2")
    assert candidate.version == "v5.2"
    assert (
        candidate.content_hash == "2ab79a133cd93e2ab413fd278b84a461a9a7a7b8e46f2436fe596d2372c682d2"
    )
    active = load_study_prompt("v5.1")
    assert active.version == "v5.1"
    assert active.content_hash == "e40182de2f232932a12d61d722be5e6356d787217048378fbc2a84f330d241cc"
    assert load_prompt(Path("prompts/phrase/v2.md")).version == "v2.1"


def test_inventory_covers_all_five_sets_without_any_held_out_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Path.read_text

    def allowed_read(path: Path, *args: object, **kwargs: object) -> str:
        assert not any(part.startswith("test-v4") for part in path.parts)
        return original(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", allowed_read)
    cases = inputs()
    assert Counter(c.group for c in cases) == {
        "dev20": 20,
        "confirmation20": 20,
        "robustness40": 40,
        "round2_60": 60,
        "v3_100": 100,
    }
    assert len({c.scenario["id"] for c in cases}) == 240
    assert {c.group for c in cases[:5]} == {c.group for c in cases}
    assert inventory_hash(cases) == inventory_hash(inputs())
    assert all(
        c.binding["customer_id"].startswith("dev-v3-")
        for c in cases
        if c.group == "v3_100" and c.binding is not None
    )


def test_approved_paired_sample_is_frozen_balanced_and_covers_round_two_families() -> None:
    cases = comparison_sample()
    assert Counter(c.group for c in cases) == {
        "dev20": 10,
        "confirmation20": 10,
        "robustness40": 10,
        "round2_60": 10,
        "v3_100": 10,
    }
    assert Counter(c.scenario["language"] for c in cases) == {"es": 25, "pt": 25}
    assert len({c.scenario["id"].split(".")[-1] for c in cases if c.group == "round2_60"}) == 10
    assert len(inputs()) == 240  # Lean v5.2 adoption still needs all five complete sets.


def test_comparison_refuses_changed_inventory_before_any_provider_call() -> None:
    cases = inputs()
    cases[0] = replace(cases[0], scenario={**cases[0].scenario, "language": "changed"})
    with pytest.raises(ValueError, match="inventory changed"):
        comparison_sample(cases)
