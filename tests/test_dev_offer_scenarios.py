"""The dev adapter may map, but cannot silently rewrite, frozen customer replies."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aclara.llm import dev_offer_scenarios


def test_offer_scenarios_preserve_frozen_replies_and_require_the_offer() -> None:
    source = yaml.safe_load(Path(dev_offer_scenarios.CASES).read_text())["cases"]
    suite = dev_offer_scenarios.load_offer_suite()
    assert suite["version"] == 2
    scenarios = suite["scenarios"]
    assert len(scenarios) == 20
    for original, scenario in zip(source, scenarios, strict=True):
        assert scenario["id"] == original["id"]
        assert scenario["turns"] == [{"message": original["opening"]}]
        assert scenario["reactive_replies"]["offer_dispute"] == [
            {"message": original["after_offer"]}
        ]
        assert "offer_dispute" in {a["type"] for a in scenario["gold"]["required_actions"]}
        assert scenario["expected"] == scenario["gold"]["outcome"]


def test_offer_scenario_adapter_rejects_changed_frozen_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    changed = tmp_path / "changed.yaml"
    changed.write_bytes(dev_offer_scenarios.CASES.read_bytes() + b"\n")
    monkeypatch.setattr(dev_offer_scenarios, "CASES", changed)
    with pytest.raises(ValueError, match="Frozen offer confirmation cases changed"):
        dev_offer_scenarios.load_offer_scenarios()
