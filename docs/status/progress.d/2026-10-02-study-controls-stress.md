# 2026-10-02 — Adversarial ablation supplement (AI lane)

## Completed (verified)

- New 20-case synthetic ES/PT attack inventory and protocol hash-committed at `867ed55` before any inference on it. Explicitly authored after seeing the first ablation, with the PT guard fix applied before this arm.
- Research-only driver uses its own `dev-gate/controls-stress` / `controls-stress`, $0.10 lifetime cap; estimated $0.06–$0.08. First study and official v4 checkpoints remain unchanged.
- Both source ledgers now accept the same authored merchant field; the runtime and original default fixtures are unchanged. Guard-exposure counts are recorded separately from safety counters.
- No changes to `agent/ai.py`, `llm/client.py` or production defaults; no actual banking write capability in the naive arm.

- Full local mock checks: 1,370 passed / 37 DB skips, B1 32/32, Ruff, strict mypy and snapshots pass. Production credit preflight and zero-spend scope read-back passed.
- Approved paired real pass completed 20/20: scope read-back $0.047119 known/charged, 58 attempts, zero unknowns. P: zero unconfirmed writes/foreign tool attempts; naive: two forged-confirmation writes and one foreign lookup. Both escalated all four over-limit cases.
- Fixed refund screen flags one PT reply that actually refuses a guarantee; recorded transparently as a false positive, without altering frozen scorer/raw outputs. Full findings in docs/evaluation/controls-ablation-stress.md.
- P additionally routed PT refund pressure to ESC-03 and unknown-ID text to DSP-06; safety counters are not a 20/20 objective-pass claim. No additional paid calls or tuning.

## Done but not verified

- PR #144 includes #143 until that prerequisite lands. Final-head main-targeted CI pending; no deployment claimed.

## Next / blocked

- Report all results or partial completion without selecting/relabeling cases or spending beyond the dedicated cap.
- PR depends on #143; merge hold until #137 then #140 land and clearance is announced.
- Staff queue #138 is green and still needs lead security review. Human agreement awaits the exported v4 CSV.
