"""ADR-0015 handoff reason sets and deterministic routing precedence."""

from collections.abc import Iterable

ROUTING_PRECEDENCE = (
    "SEC-01",
    "FRD-01",
    "ESC-02",
    "ESC-03",
    "DSP-05",
    "DQ-01",
    "DSP-03",
    "DSP-04",
    "DATA-01",
    "BRD-01",
    "DSP-01",
    "DSP-07",
    "DSP-02",
    "TXN-02",
    "ESC-04",
    "ESC-01",
    "SCOPE-01",
)


def handoff_reasons(reasons: str | Iterable[str]) -> tuple[str, ...]:
    values = {reasons} if isinstance(reasons, str) else set(reasons)
    if "FRD-01" in values:
        values.add("AUTH-02")
    if "SEC-01" in values:
        values.add("AUTH-03")
    ordered = [reason for reason in ROUTING_PRECEDENCE if reason in values]
    if not ordered:
        raise ValueError("A handoff needs an evidenced routing reason")
    return tuple(ordered + sorted(values - set(ordered)))
