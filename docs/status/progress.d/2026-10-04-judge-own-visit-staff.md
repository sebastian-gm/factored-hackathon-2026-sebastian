# Judge own-visit staff queue — v0.9.2 released

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
- PR #178 merged on green remote gates. Exact deployed main CI/safety
  37198199416 / 37198199250 and independent access 37200217827 succeeded.
  Remote browser checks: 217, including 3 new real API/BFF mock judge journeys.
- Tagged/released v0.9.2 at `f9d1796ddd661883c131359c1881bea67f9a0c49`;
  live ES/PT own-visit masked queue, claim readbacks, switching, cross-visit
  denial and logout passed. Azure browser journey passed 2 claims / 13 stages.
- Real cost $0.003879; browser $0. A verifier-stop $0.01 reserve remains retained;
  original operator stops/history preserved. Conservative maximum $14.91264898
  <= $15. No resource/access/budget change or demo reset.
- [Detailed evidence and disclosures](../../submission/v0.9.2-release-evidence.md).

## Done but not verified

- Complete frontend live exploration, accessibility and latency SLA are not
  established by this bounded smoke; official v4 results are unchanged.

## Next / blocked

- Frontend can rehearse the published path in its existing approved scope;
  credentials remain ignored/untracked 0600, with no second staff account.
- No v1.0.0 tag or submission email is authorized yet.
