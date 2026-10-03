# Realm-scoped staff queue

**Post-v4 improvement; not reflected in v4.** Requires migration
`0005_staff_realm_queue` and lead security review before release. No live migration
or deployment is performed by this PR.

1. A signed-in customer (with a selected judge profile) posts
   `/handoffs/realm-invitations`. The response contains a five-minute, opaque
   invitation and `expires_at`, verified by read-back. Treat it as a temporary
   capability: do not log it, store it in a transcript, or send it to a model.
2. A **separately signed-in agent/ops persona**, using its own OTP session, posts
   `{"invitation": "…"}` to `/agent/handoff-realm`. An invitation grants no staff
   role. Judge-profile sessions cannot redeem it, even if their source demo
   persona has an ops role. Each invitation is redeemable by one staff session;
   retries from that session are idempotent.
3. Existing `/agent/handoffs` and `/agent/handoffs/{id}` then return that realm's
   masked queue, with `scope="current_realm"`. All customer profiles in one judge
   visit share the queue; a new judge login has a different realm. Without a
   membership, the previous `current_workspace` view remains available to staff.
4. Claim uses the existing `/agent/handoffs/{id}/claim` request
   (`expected_version`, `idempotency_key`). It commits an audited version change,
   reads it back, and returns the committed packet. Concurrent claimants get one
   winner; stale versions or changed idempotency payloads return 409.

Membership expires at the earlier customer/staff session expiry. Customer/root
logout revokes it. Each invitation redemption and delegated queue/claim request
also validates the stored controller through the current judge-authentication
binding/configuration checks. Judge access OFF, password/persona rotation or a
changed dataset binding revokes delegation, including cached claim replay;
invalid membership returns 403 rather than falling back to a workspace view.
The controller's current child digest/revision keeps legitimate profile switching
within the same visit valid, including after an unchanged-config restart. A new
invitation can switch staff to another realm, replacing the previous membership.
Invitation consumption and membership activation use separate existing session
transactions: a crash between them is recoverable by the same staff session.

Only the new masked queue has realm visibility. Its table has **FORCE RLS**;
staff can update only claim-state columns. A narrow owner function publishes or
refreshes a source customer's masked payload under that customer's realm RLS;
staff cannot invoke it in staff context or directly mutate payloads or realms.
Verified action updates preserve claim ownership and advance the packet version;
idempotent claim replay reads the latest verified snapshot.
Banking tables, transcripts, traces and existing session RLS are unchanged. The
realm is derived from trusted server identity, never a client-supplied selector.
Queue payloads omit raw customer/session IDs and recursively redact direct
identifiers from prose; generated masked handoff/fact IDs remain intact.
Claimants use an opaque staff reference. Trace/transcript
links are omitted because queue permission does not grant those routes.

The customer handoff is published only after its original read-back. Publication
is also read back; failure returns 503 rather than claiming queue success. New
queue packets begin at deployment; this change does not backfill earlier sessions.
The realm queue supports **claim only**; existing workspace resolve stays intact.
Staff sign-in/OTP remains the restricted demo identity system, not production IAM.

[Mock authorization tests](../tests/test_staff_realm_queue.py) cover sharing,
masking, other-realm/customer denial, replay, expiry and logout.
[Disposable Postgres tests](../tests/test_staff_realm_queue_postgres.py) cover
FORCE RLS, immutable payload/realm, cross-replica claim races and audited state.
The frontend can implement the invitation handoff and existing queue/claim API;
do not present the invitation as a permission to access banking data.

[Controller revocation regressions](../tests/test_staff_realm_revocation.py) replay
OFF, password/config/dataset rotation, fresh/cached claims and stale invitations
against both memory (local/unit gate) and disposable Postgres (integration gate),
with valid restart/profile-switch controls.
