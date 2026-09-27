from dataclasses import replace

from aclara.handoff.routing import AgentDirectory, ServiceAgent


def agent(ref, language="portugués", specialty="Fraudes", load=10, kind="Digital", status="Active"):
    return ServiceAgent(ref, status, kind, language, specialty, load)


def test_pt_fraud_fallback_chain_and_stored_explanations():
    primary = agent("primary")
    general = agent("general", specialty="Quejas y Reclamos")
    spanish = agent("spanish", language="español")
    direct = AgentDirectory((primary, general, spanish)).route("pt", "FRD-01")
    assert direct["assigned_agent_ref"] == "primary"
    assert not direct["fallback_used"] and direct["queue"] == "Fraudes"
    second = AgentDirectory((replace(primary, agent_status="Vacation"), general, spanish)).route(
        "pt", "FRD-01"
    )
    assert second["assigned_agent_ref"] == "general"
    assert second["specialty_fallback"] and not second["language_fallback"]
    assert second["queue"] == "Quejas y Reclamos" and second["requested_queue"] == "Fraudes"
    third = AgentDirectory((spanish,)).route("pt", "FRD-01")
    assert third["language_fallback"] and third["language"] == "es" and third["queue"] == "Fraudes"
    assert "Active" in third["routing_explanation"]
    empty = AgentDirectory(()).route("pt", "FRD-01")
    assert empty["assignment_pending"] and empty["assigned_agent_ref"] is None


def test_active_digital_hybrid_preference_then_load_and_stable_tie():
    rows = (
        agent("phone", load=0, kind="Phone"),
        agent("off", load=0, status="Inactive"),
        agent("hybrid", load=30, kind="Hybrid"),
        agent("b", load=20),
        agent("a", load=20),
        agent("null", load=None),
    )
    route = AgentDirectory(rows).route("pt", "FRD-01")
    assert route["assigned_agent_ref"] == "a"
    assert AgentDirectory(tuple(reversed(rows))).route("pt", "FRD-01") == route
    assert AgentDirectory(
        (agent("spanish", language="español", specialty="Quejas y Reclamos"),)
    ).route("pt", "DSP-03")["language_fallback"]
