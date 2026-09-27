"""Public CLI diagnostics must not expose connection or row-level error details."""

from pathlib import Path

import pytest

from aclara.data.cli import main


def test_serving_failure_is_redacted(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    message = "private fixture connection detail"

    def fail(lake: Path, dsn: str) -> None:
        assert lake == Path.home() / "fixture-lake"
        raise RuntimeError(message)

    monkeypatch.setattr("aclara.data.serving_load.load_serving", fail)
    monkeypatch.setenv("DATA_LOAD_DSN", "fixture-only-connection")
    monkeypatch.setattr("sys.argv", ["aclara", "serve-load", "--lake", "~/fixture-lake"])
    assert main() == 1
    assert "Serving load failed (RuntimeError)" in caplog.text
    assert message not in caplog.text
    assert "fixture-only-connection" not in caplog.text
