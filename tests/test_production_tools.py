"""Credential transfer and smoke limits tested entirely with local fixtures."""

import json
import subprocess

import pytest
from dotenv import dotenv_values
from scripts import azure_llm_smoke, azure_openrouter_key


@pytest.mark.parametrize("failure", [None, "upload", "readback"])
def test_key_transfer_only_removes_local_value_after_matching_readback(
    tmp_path, monkeypatch, capsys, failure
):
    (tmp_path / "artifacts/azure").mkdir(parents=True)
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=fixture-only-value\nLLM_PROVIDER=mock\n")
    monkeypatch.setattr(azure_openrouter_key, "ROOT", tmp_path)

    def cli(args, **kwargs):
        assert "fixture-only-value" not in args
        assert args[args.index("--subscription") + 1] == "Seb Azure Sandbox"
        if "set" in args:
            from pathlib import Path

            path = Path(args[args.index("--file") + 1])
            assert path.read_text() == "fixture-only-value"
            assert path.stat().st_mode & 0o777 == 0o600
            return subprocess.CompletedProcess(args, int(failure == "upload"), "", "")
        return subprocess.CompletedProcess(
            args, 0, "mismatch" if failure == "readback" else "fixture-only-value\n", ""
        )

    monkeypatch.setattr(azure_openrouter_key.subprocess, "run", cli)
    if failure:
        with pytest.raises(RuntimeError):
            azure_openrouter_key.main()
        assert dotenv_values(env)["OPENROUTER_API_KEY"] == "fixture-only-value"
    else:
        azure_openrouter_key.main()
        assert "OPENROUTER_API_KEY" not in dotenv_values(env)
    assert dotenv_values(env)["LLM_PROVIDER"] == "mock"
    assert not list((tmp_path / "artifacts/azure").iterdir())
    assert "fixture-only-value" not in capsys.readouterr().out


def test_smoke_limit_persists_before_work_even_on_failure(tmp_path, monkeypatch):
    (tmp_path / "artifacts/azure").mkdir(parents=True)
    path = tmp_path / "artifacts/azure/checkpoint.json"
    monkeypatch.setattr(azure_llm_smoke, "ROOT", tmp_path)
    monkeypatch.setattr(azure_llm_smoke, "CHECKPOINT", path)
    with pytest.raises(RuntimeError), azure_llm_smoke.conversation_allowance(3, "fixture"):
        assert json.loads(path.read_text())["attempted"] == 3
        raise RuntimeError("interrupted")
    with azure_llm_smoke.conversation_allowance(2, "fixture"):
        pass
    with (
        pytest.raises(RuntimeError, match="exhausted"),
        azure_llm_smoke.conversation_allowance(1, "fixture"),
    ):
        pytest.fail("Work must not start past the approved conversation count")
