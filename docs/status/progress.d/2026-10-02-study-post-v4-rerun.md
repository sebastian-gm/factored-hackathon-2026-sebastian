# 2026-10-02 — Post-v4 dev rerun (AI lane)

## Completed (verified)

- Dedicated mock-by-default driver preserves the 36 authored inputs, fixtures and scorer.
- Real dev rerun: **34/36** versus 32/36 earlier; ES 18/18, PT 16/18; zero detected unsafe outcomes or language errors. Supplementary dev evidence, not reflected in v4.
- Scope `dev-gate/post-v4-rerun`, run `post-v4-rerun`, $0.08 lifetime cap: read back **$0.0538905**, 28 valid attempts, zero unknown costs. Production-key credit preflight passed. No production banking writes.
- Full local mock checks: **1,351 passed / 37 DB skips**, Ruff, strict mypy, interface snapshots, B1 **32/32**.
- Controls ablation #135 is merged; staff queue #138 remains open for lead security review. Combined new ablation/rerun cost is $0.098062.

## Done but not verified

- Both remaining PT failures match the correct amount but offer dispute follow-up for an ordinary inquiry. Raw model extractions were not retained; precise field-level cause is unproven.
- Rerun PR remote checks pending. No prompt change or extra paid retry in this round.

## Next / blocked

- Merge hold until the lead lands #137 then #140 and announces clearance.
- PT injection regression fix, then separately preregistered 20-case stress arm (own $0.10 cap).
- Human agreement awaits Sebastian's exported v4 CSV.
