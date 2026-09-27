"""Exercise Compose using ignored local credentials; report only aggregate evidence."""

from dotenv import dotenv_values
from scripts.azure_smoke import smoke


def main() -> None:
    values = dotenv_values(".env")
    smoke(
        "http://localhost:" + (values.get("API_HOST_PORT") or "8000"),
        "http://localhost:" + (values.get("WEB_HOST_PORT") or "3000"),
        values.get("DEMO_PASSWORD") or "",
        values.get("DEMO_USERNAME") or "",
    )


if __name__ == "__main__":
    main()
