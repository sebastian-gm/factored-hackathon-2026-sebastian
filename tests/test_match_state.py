from __future__ import annotations

import shutil
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from aclara.agent.matching import MatchState
from aclara.agent.nlu.structured import NormalizedSlots
from aclara.bank.repository import TransactionRepository
from aclara.settings import Settings


def test_exported_thresholds_cover_three_actions_and_reject_other_customer() -> None:
    settings = Settings()
    rows = TransactionRepository().for_customer(settings.demo_customer_id, settings.bank_clock)
    matcher = MatchState()
    precise = NormalizedSlots(
        amount_value=Decimal("145.50"),
        currency="USD",
        merchant_expr="Mercado Verde",
        date_start=date(2026, 6, 9),
        date_end=date(2026, 6, 9),
        type_expr="Purchase",
    )
    assert (
        matcher.match(precise, rows, settings.demo_customer_id, settings.bank_clock).action
        == "propose"
    )
    choice = matcher.match(
        precise.model_copy(update={"date_start": None, "date_end": None, "type_expr": None}),
        rows,
        settings.demo_customer_id,
        settings.bank_clock,
    )
    assert choice.action == "choose" and len(choice.transaction_ids) == 3
    absent = precise.model_copy(
        update={"amount_value": Decimal("999999"), "merchant_expr": "Never Present"}
    )
    assert (
        matcher.match(absent, rows, settings.demo_customer_id, settings.bank_clock).action == "none"
    )
    with pytest.raises(ValueError, match="unauthorized"):
        matcher.match(
            precise,
            [("txn_1", replace(rows[0][1], customer_id="another"))],
            settings.demo_customer_id,
            settings.bank_clock,
        )


def test_matcher_rejects_corrupt_artifact(tmp_path: Path) -> None:
    shutil.copytree("models/charge_matcher/v1", tmp_path / "model")
    (tmp_path / "model/model.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        MatchState(tmp_path / "model")
