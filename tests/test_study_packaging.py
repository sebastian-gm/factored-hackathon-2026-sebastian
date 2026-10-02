"""Offline import/CLI compatibility and runtime packaging boundaries; zero network."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ROOT / "evals/studies/llm"


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "LLM_PROVIDER": "mock",
        "LLM_REAL_CALLS_APPROVED": "0",
        "OPS_BACKEND": "memory",
        "LEDGER_BACKEND": "fixture",
    }


def test_all_relocated_studies_import_without_running_them() -> None:
    for path in STUDIES.glob("*.py"):
        if path.name != "__init__.py":
            module = importlib.import_module(f"evals.studies.llm.{path.stem}")
            assert Path(module.__file__).resolve() == path
            if hasattr(module, "ROOT"):
                assert module.ROOT == ROOT


def test_api_import_does_not_require_offline_studies(tmp_path: Path) -> None:
    code = """
import importlib.abc
import sys
class RuntimeBoundary(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('evals.studies'):
            raise AssertionError('API imports offline studies: ' + fullname)
sys.meta_path.insert(0, RuntimeBoundary())
import aclara.api.app
assert not any(name.startswith('evals.studies') for name in sys.modules)
"""
    subprocess.run(  # noqa: S603 -- fixed interpreter and authored source, no shell.
        [sys.executable, "-c", code], cwd=tmp_path, env=_env(), check=True, capture_output=True
    )


def test_studies_are_outside_the_wheel_and_api_copy_roots() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    assert not any((ROOT / "src/aclara/llm").glob("dev_*"))
    assert not any((ROOT / "src/aclara/llm").glob("round_*"))
    assert not any((ROOT / "src/aclara/llm").glob("*.yaml"))
    assert "evals/studies" in (ROOT / ".dockerignore").read_text().splitlines()
    # A broad COPY would ship the offline package despite wheel exclusion.
    for line in (ROOT / "Dockerfile.api").read_text().splitlines():
        if line.startswith("COPY "):
            sources = line.split()[1:-1]
            assert not any(source in {".", "./", "evals", "evals/studies"} for source in sources)


def test_relocation_keeps_offline_implementation_in_comparison_source_pins() -> None:
    from evals.studies.llm.dev_model_compare import pins

    pinned = pins([])["files"]
    assert all(str(path.relative_to(ROOT)) in pinned for path in STUDIES.glob("*.py"))


@pytest.mark.parametrize("module", ["human_review", "dev_kind_replay", "dev_model_compare"])
def test_relocated_cli_help_does_not_call_a_provider(module: str) -> None:
    # Providers are forbidden even if a future CLI accidentally starts work
    # before processing --help. No keys, model calls or source rows are used.
    code = f"""
import runpy
import sys
from aclara.llm import providers
def forbidden(*args, **kwargs):
    raise AssertionError('CLI help attempted a provider call')
providers.urlopen = forbidden
sys.argv = ['{module}', '--help']
runpy.run_module('evals.studies.llm.{module}', run_name='__main__')
"""
    result = subprocess.run(  # noqa: S603 -- allowlisted module and authored source, no shell.
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "usage:" in result.stdout.lower()
