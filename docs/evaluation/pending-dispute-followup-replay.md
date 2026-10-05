# JE-17 return to dispute: post-v4, final build

The saved live JE-17 opening normalizes to inquiry with unfamiliarity, then MATCH
requires a choice. Weather and the subsequent return to dispute invoke no NLU.
Requiring a positive choice remains correct: the customer has not identified a
charge, so no proposal or case may be invented. This does not explain away or
change the historical story failure.

A mock replay of that return wording exposes a further context bug: it consumes
a selection clarification round despite stating only dispute intent. Repeating
the same clear request can then trigger ESC-04 while valid choices remain.
The ES and authored PT replay both fail before the fix (rounds 1 versus 0).

The P-only fix recognizes the bounded positive denial/request clause, retains
the current owned choices and dispute intent, and asks the customer to choose
without consuming a round. It never chooses a target. Later ordinal selection
still runs policy and creates only a proposal; chat assent still returns 409.
The full-clause grammar excludes uncertain wording, new target details,
alternatives and unrelated clauses. Safety/human/cross-customer gates run first.
B1's existing bounded clarification behavior is unchanged.

Raw historical slots/confidence are unavailable. Tests replay retained normalized
opening flags and the absence of follow-up NLU; fixture slots/confidence, PT,
repetition and the eventual explicit selection are authored reconstructions and
controls. The new file passes 22 cases; the combined context/security/starter/
language group passes 197. Ruff and strict mypy pass. Frozen exploration remains
27/30, with all 100 no-write, 109 zero-spend, 14 case and 7 handoff readbacks;
B1 v2 remains 32/32. New spend is $0. No new live outcome is claimed.

This small PR complements #204's positive literal merchant-choice fix. #180,
#185 and #189 are already on main. Lead review/merge/deployment precede the
newly approved single live rerun at <=$0.40 in a new durable AI scope.
