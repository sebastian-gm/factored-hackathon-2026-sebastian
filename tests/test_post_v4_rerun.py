"""The supplementary rerun requires explicit paid selection and an isolated purse."""

from __future__ import annotations

import sys
from decimal import Decimal

import pytest
from evals.studies.llm import dev_post_v4 as study
from evals.studies.llm import post_v4_rerun as rerun


@pytest.mark.parametrize(("args", "stage"), [([], "triage-mock"), (["--real"], "after-real")])
def test_rerun_defaults_to_mock_and_uses_own_lifetime_cap(monkeypatch, tmp_path, args, stage):
    for name in ("ROOT", "OUTPUT", "SCOPE", "RUN_ID", "CAP"):
        monkeypatch.setattr(study, name, getattr(study, name))
    monkeypatch.setattr(study, "ROOT", tmp_path)
    observed = []
    monkeypatch.setattr(study, "main", lambda: observed.append(sys.argv[1]))
    monkeypatch.setattr(sys, "argv", ["post-v4-rerun", *args])
    rerun.main()
    assert observed == [stage]
    assert study.SCOPE == "dev-gate/post-v4-rerun"
    assert study.RUN_ID == "post-v4-rerun" and Decimal("0.08") == study.CAP
    assert tmp_path / "artifacts/post-v4-rerun" == study.OUTPUT
    assert len(study.inventory()) == 36


def test_rerun_preserves_existing_fixture_and_scorer():
    assert rerun.study.fixtures is study.fixtures
    assert rerun.study.score is study.score
    assert study.SCOPE == "dev-gate/post-v4-audit"
