"""Typed YAML scenario-suite contract used by the local B1 harness."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MessageTurn(StrictScenarioModel):
    message: str = Field(min_length=1, max_length=1000)


class ConfirmationTurn(StrictScenarioModel):
    confirm: bool


class Scenario(StrictScenarioModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
    language: Literal["es", "pt"]
    turns: list[MessageTurn | ConfirmationTurn] = Field(min_length=1)
    expected: Literal[
        "explained",
        "dispute_filed",
        "choose_transaction",
        "handoff_created",
        "abstained_out_of_scope",
        "clarification",
        "dispute_proposed",
        "cancelled",
    ]


class ScenarioSuite(StrictScenarioModel):
    version: Literal[1]
    description: str = Field(min_length=1)
    scenarios: list[Scenario] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_scenario_ids(self) -> ScenarioSuite:
        identifiers = [scenario.id for scenario in self.scenarios]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("scenario ids must be unique")
        return self
