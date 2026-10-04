# Frontend message validation — October 4, 2026

Post-v4 development change; official v4 evaluation numbers are unchanged.

## Completed (verified)

- Reviewed and adopted the AI lane's BFF proposal and browser boundary tests.
  Supplied patch SHA-256:
  `3b1622fe97067d5114f722bac9b5134923a242ec32e51ece0ff1171bb6f808c0`.
- Invalid chat messages now return `422` / `invalid_message` before forwarding,
  rather than `502` / `invalid_response_or_request`. The 1,000-character limit
  counts Unicode code points, matching the API, including astral emoji.
- Two local mock browser regressions reproduced the original 502 before the fix.
  After the fix, `FRONTEND_E2E_WEB_PORT=3217 FRONTEND_E2E_API_PORT=8217 pnpm
  test:e2e conversation-contract.spec.ts` passed **16 tests in 22.9s**. Eight
  added regressions cover ES/PT ASCII/emoji boundaries and desktop/phone composer
  recovery: rejection retains an editable draft, a corrected message succeeds,
  and no case, confirmation or card-freeze action is created.
- The browser limit is bypassed only within the recovery regression to exercise
  server rejection. The actual BFF is used; message responses are not fulfilled
  by the tests. Runtime input authority and financial confirmation remain separate.
- `pnpm typecheck`, `pnpm lint` and `git diff --check` passed. Validation uses
  authored local fixtures and no paid model calls.
- The separate live-tour PR [#182](https://github.com/sebastian-gm/factored-hackathon-2026-sebastian/pull/182)
  has green remote checks and remains held. Its private live gallery is unchanged;
  the operator's recorded budget halt remains in force.

## Done but not verified

- Remote CI for this message-validation branch is pending at author time.
- Azure deployment and live verification of this fix are pending the lead's next
  release. The existing live gallery records v0.9.1, not this patch.

## Next / blocked

- Hand this small PR to the lead with credit to the AI lane. Keep the merge hold;
  the lead owns release order and deployment.
- Do not resume paid tour calls or alter retained reservations. Charge explanation,
  candidate selection, first receipt, delegated staff claim and Lighthouse remain
  outside the verified live coverage recorded by #182.
