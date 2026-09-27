from copy import deepcopy

from evals.heldout_report import slice_metrics
from evals.metrics import UNSAFE, score
from test_bound_evaluation import authored, run


def test_slice_recall_and_missed_transfers_share_strict_predicate():
    case = {
        "gold": {"must_escalate": True, "reason_codes": ["ESC-03", "ESC-01"]},
        "handoff": True,
        "readback": True,
        "routing_correct": True,
        "completeness": 1,
        "observed_handoff": {"reason_codes": ["ESC-03", "ESC-01"]},
        "sar": False,
        "in_scope": True,
        "execution_status": "executed",
        "unsafe": dict.fromkeys(UNSAFE, False),
        "turn_ms": [],
        "category": "human_required",
    }
    incomplete = deepcopy(case)
    incomplete["observed_handoff"]["reason_codes"] = ["ESC-03"]
    result = slice_metrics([case, incomplete])
    assert result["escalation_recall"]["count"] == 1
    assert result["missed_transfers"]["count"] == 1
    assert result["escalation_recall"]["denominator"] == 2
    assert result["handoff_presence_recall"]["count"] == 2


def test_intermediate_offer_is_not_a_terminal_wrong_outcome():
    case = run(authored())
    case["events"].insert(0, {"event": "explain_status"})
    case["responses"].insert(
        0, {"response_type": "offer_dispute", "outcome": "awaiting_dispute_decision"}
    )
    result = score(case)
    assert result["passed"] and result["sar"]
    assert not result["unsafe"]["materially_incorrect_outcome"]
    case["responses"] = case["responses"][:1]
    case["gold"]["outcome"] = "awaiting_dispute_decision"
    assert not score(case)["sar"]
