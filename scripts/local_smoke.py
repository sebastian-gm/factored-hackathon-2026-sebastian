"""Verify Compose serving through the live web BFF; emit no source rows."""

# ruff: noqa: T201 -- aggregate checks and exception frame locations only.

from dotenv import dotenv_values
from evals.serving import open_serving
from scripts.serving_smoke import smoke


def main() -> None:
    values = dotenv_values(".env")
    ledger = open_serving()
    try:
        smoke(
            "http://localhost:" + (values.get("WEB_HOST_PORT") or "3000"),
            values.get("DEMO_PASSWORD") or "",
            ledger,
        )
    finally:
        ledger.store.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        print(
            type(exc).__name__,
            [(f.name, f.lineno) for f in traceback.extract_tb(exc.__traceback__)],
        )  # noqa: T201
        raise SystemExit(1) from None
