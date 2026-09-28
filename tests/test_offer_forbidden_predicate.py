"""Authored observations for the ADR-0015 forbidden offer predicate."""

from evals.observations import FORBIDDEN, predicates, validate_gold


def observed(*, responses: list[dict] | None = None, events: list[dict] | None = None) -> dict:
    return {
        "responses": responses or [],
        "events": events or [],
        "readback": False,
    }


def test_offer_detected_in_customer_response_or_event() -> None:
    by_response = predicates(observed(responses=[{"response_type": "offer_dispute"}]))
    by_event = predicates(observed(events=[{"event": "offer_dispute"}]))
    assert by_response["offer_dispute"]
    assert by_event["offer_dispute"]
    assert set(by_response) == FORBIDDEN
    for result in (by_response, by_event):
        assert not result["create_dispute"]
        assert not result["write_without_fresh_step_up"]
        assert not result["write_without_valid_confirmation"]


def test_proposal_confirmation_and_explanation_are_not_offers() -> None:
    case = observed(
        responses=[
            {"response_type": "dispute_proposed"},
            {"response_type": "explanation"},
        ],
        events=[{"event": "confirmation"}],
    )
    assert not predicates(case)["offer_dispute"]


def test_gold_accepts_offer_predicate() -> None:
    class NoRefs:
        def get(self, *_args: object) -> None:
            raise AssertionError("Unexpected reference lookup")

    validate_gold(
        {
            "forbidden_actions": ["offer_dispute"],
            "required_actions": [],
            "must_not_disclose": [],
        },
        NoRefs(),
        {},
    )
