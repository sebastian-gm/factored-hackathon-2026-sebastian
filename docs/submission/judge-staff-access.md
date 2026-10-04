# Judge access to the masked staff queue

The judge signs in with the judge password and OTP once, selects a customer
profile, and creates a handoff in chat. In **Agent Desk**, choose
**Open this visit's queue**. The browser creates and redeems a
short-lived invitation using that same authenticated visit, then reads back the
membership and displays the existing masked queue and verified claim controls.
No separate staff credential is needed for this judge path.

## API and session contract

1. `POST /handoffs/realm-invitations` creates a five-minute invitation tied to
   the live judge controller and its masked handoff realm.
2. `POST /agent/handoff-realm`, with `{"invitation": "<private capability>"}`,
   redeems it. A selected judge may redeem only its own controller's invitation.
   The response is `{"joined": true, "verified": true}` after independent readback.
3. `GET /agent/handoffs` and `GET /agent/handoffs/{id}` return only masked packets
   in that visit's realm. Transcript and trace references are absent/null.
4. `POST /agent/handoffs/{id}/claim` requires the observed version and an
   idempotency key. Its receipt is checked by an independent packet readback.
   Realm queue resolution remains unavailable.

The grant is stored under the controller's existing RLS scope. It does not mint
a new login, change cookies, extend expiry, change the profile's trusted role, or
grant new banking, transcript, Ops or reset authority. Valid profile switching
preserves the visit grant and rotates the selected customer's capability. Reload
recovers membership from a server read rather than a browser flag.

## Threat checks

- **Session fixation:** caller-supplied identity, realm and role are not accepted.
  Redemption validates the actual selected capability inside the controller
  transaction before consuming the invitation, including concurrent switching.
- **Cross-profile data:** the shared queue contains masked handoff packets from
  this visit; customer ledger and case APIs retain each profile's separate scope.
  Another judge visit or an owner-demo invitation cannot be self-redeemed.
- **Replay:** an invitation is bound to one member/controller. Repeating the same
  live controller's redemption is idempotent; another member is denied. Claims
  retain version checks and idempotency without duplicate mutation.
- **Revocation:** logout, expiry, judge OFF, password/configuration/binding
  rotation revoke membership and cached claim replay. An unchanged restart and
  legitimate profile switch preserve it. Every queue request revalidates the
  live controller; a missing judge grant never falls back to an owner workspace.

Separately authenticated Agent/Ops users may still use the existing invitation
workflow. Sharing an invitation never grants the holder banking access.

This is a post-v4 change; the official v4 metrics remain unchanged.
