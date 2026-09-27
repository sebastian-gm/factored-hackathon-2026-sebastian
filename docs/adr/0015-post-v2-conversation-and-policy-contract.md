# ADR-0015: Explain, offer a dispute, and preserve policy evidence

- Status: Accepted specification; implementation pending Step 3
- Date: 2026-09-27
- Decision owner: Sebastian; implementation and contract detail: lead

## Context

Sebastian chose an explanation followed by a dispute offer for an unfamiliar
charge, while explicit denial still enters dispute review directly. Final v2
remains the official result, including its post-hoc analysis. Its failures also
exposed mismatched handoff reason semantics, business-date gold, and rule order.
A new independent suite must have a written specification before its authors
freeze gold; implementation outcomes cannot define that gold.

## Options

1. Treat unfamiliarity as an immediate dispute request. This omits the requested
   opportunity to recognize the explained charge.
2. End every unfamiliarity inquiry after explanation. This omits the requested
   dispute offer and can prematurely count success.
3. Explain trusted facts, offer a dispute, and await a clear customer response.
   Preserve independent confirmation, OTP, policy checks and durable readback.

## Decision

Choose option 3 for both B1 and P. Adopt the normative
[conversation and policy contract](../../contracts/interfaces/conversation-policy-v3.md).
It defines the state transitions, outcome/SAR semantics, security actions,
reason sets, policy order and worked business-date examples.

- The dispute offer is nonterminal. Recognition ends in explanation; denial or
  a filing request enters ordinary policy review, proposal, confirmation, fresh
  OTP and readback. Neither NLU output nor an offer reply confirms a write.
- Preserve dispute intent and the selected owned transaction across clarification.
- Handoffs carry every applicable routing/control/cause reason. Routing uses a
  documented primary reason; a control reason does not assert completion.
- Refuse and log every cross-customer attempt; on the second attempt also end
  the session and persist/read back a security handoff.
- Retain ADR-0006's bank business-date anchor. An author subtracts age from that
  date, not from the UTC calendar date of `BANK_CLOCK`.
- For a known unsupported transaction type under dispute review, its type rule
  takes routing precedence over missing/inconsistent intake data. Preserve any
  applicable data reason in the same packet. Core ownership/auth checks always
  precede transaction processing.

## Consequences

The API adds a nonterminal offer response and optional explicit primary handoff
reason. The AI lane adds contextual recognition extraction and grounded ES/PT
offer templates; the lead integrates state, gates and scoring. The shared JSON
snapshots will be regenerated with implementation, before the v3 structural
freeze; this specification PR changes no executable behavior.

B1's amount extraction and unfamiliarity flow will change and must be disclosed
in the fresh-suite comparison. A readback alias and strict slice escalation
correction do not permit rerunning v2. Any saved-v2 slice correction is a separate,
labeled aggregate artifact; official v2 files stay unchanged.

Lead and AI implementers must never open suite-v3 rows. Independent authors use
this contract, fresh customers/transactions where available, new utterances and
structural validation only. No system runs on v3 before its manifest/bindings
freeze and Sebastian's later release/run approval.

## Revisit when

Human review or independent new evidence warrants a new version of this contract.
Never revise it to fit v3 outcomes. Dev validation uses the newly capped
`dev-gate/after-v2` scope; no release or v3 run is authorized by this ADR.
