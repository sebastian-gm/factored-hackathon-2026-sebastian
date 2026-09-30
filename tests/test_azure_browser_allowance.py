"""One explicit browser retry cannot reset the default conversation allowance."""

import json

import pytest
from scripts import azure_llm_smoke as smoke


@pytest.fixture
def checkpoint(tmp_path, monkeypatch):
    folder = tmp_path / "artifacts" / "azure"
    folder.mkdir(parents=True)
    path = folder / "authored-smoke.json"
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    monkeypatch.setattr(smoke, "CHECKPOINT", path)
    monkeypatch.delenv("AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED", raising=False)
    for _ in range(5):
        with smoke.conversation_allowance(1, "authored-default"):
            pass
    return path


def test_default_limit_stays_five(checkpoint):
    with (
        pytest.raises(RuntimeError, match="exhausted"),
        smoke.conversation_allowance(1, "browser-three-surfaces"),
    ):
        pass
    assert json.loads(checkpoint.read_text())["attempted"] == 5


def test_explicit_browser_permission_is_one_use(checkpoint, monkeypatch):
    monkeypatch.setenv("AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED", "1")
    with smoke.conversation_allowance(1, "browser-three-surfaces"):
        pass
    state = json.loads(checkpoint.read_text())
    assert state["attempted"] == 6 and state["extra_browser_attempt_used"]
    assert len(state["runs"]) == 6
    with (
        pytest.raises(RuntimeError, match="exhausted"),
        smoke.conversation_allowance(1, "browser-three-surfaces"),
    ):
        pass
    assert json.loads(checkpoint.read_text()) == state


@pytest.mark.parametrize("count,label", [(1, "es_normal"), (2, "browser-three-surfaces")])
def test_permission_does_not_extend_other_attempts(checkpoint, monkeypatch, count, label):
    monkeypatch.setenv("AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED", "1")
    with pytest.raises(RuntimeError, match="exhausted"), smoke.conversation_allowance(count, label):
        pass
    assert json.loads(checkpoint.read_text())["attempted"] == 5


def test_failed_extra_attempt_is_not_released(checkpoint, monkeypatch):
    monkeypatch.setenv("AZURE_EXTRA_BROWSER_ATTEMPT_APPROVED", "1")
    with (
        pytest.raises(RuntimeError, match="authored failure"),
        smoke.conversation_allowance(1, "browser-three-surfaces"),
    ):
        raise RuntimeError("authored failure")
    with (
        pytest.raises(RuntimeError, match="exhausted"),
        smoke.conversation_allowance(1, "browser-three-surfaces"),
    ):
        pass
    assert json.loads(checkpoint.read_text())["attempted"] == 6
