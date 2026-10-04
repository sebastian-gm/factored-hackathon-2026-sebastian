# Judge own-visit staff queue — v0.9.2 candidate

## Completed (verified)

- Confirmed the v0.9.1 gap: redemption required a separately authenticated
  Agent/Ops user and explicitly rejected judge sessions.
- Security review's zero-network authored replay verified own-visit binding,
  six revocation variants and cached-claim denial. A profile-switch race found
  during review was reproduced, then fixed by revalidating the actual child
  inside the controller transaction before consuming the invitation.
- `pytest --tb=short`: 1,773 passed, 43 skipped. Disposable non-owner Postgres
  gate: 124 passed. B1 original/reactive dev harnesses: 32/32 each. Ruff,
  strict mypy, frozen interfaces, policy catalog and pre-commit passed.

## Done but not verified

- Queue-only judge redemption and the inline Desk flow are implemented; browser
  and remote CI, live ES/PT redemption and v0.9.2 release are pending.

## Next / blocked

- Merge only after remote CI is green, then perform the authorized image-only
  v0.9.2 release with existing judge access and unchanged production controls.
- Verify masked queue/claim end to end and publish the exact frontend path.
- No v1.0.0 tag or submission email is authorized yet.
