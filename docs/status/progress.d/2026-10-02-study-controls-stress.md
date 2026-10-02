# 2026-10-02 — Adversarial ablation supplement (AI lane)

## Completed (verified)

- New 20-case synthetic ES/PT attack inventory and protocol hash-committed at `867ed55` before any inference on it. Explicitly authored after seeing the first ablation, with the PT guard fix applied before this arm.
- Research-only driver uses its own `dev-gate/controls-stress` / `controls-stress`, $0.10 lifetime cap; estimated $0.06–$0.08. First study and official v4 checkpoints remain unchanged.
- Both source ledgers now accept the same authored merchant field; the runtime and original default fixtures are unchanged. Guard-exposure counts are recorded separately from safety counters.
- No changes to `agent/ai.py`, `llm/client.py` or production defaults; no actual banking write capability in the naive arm.

## Done but not verified

- Twenty P mock scenarios completed; 11 new isolation/attack regressions pass. Full local mock checks, B1 32/32, Ruff, strict mypy and snapshots pass. Production credit preflight and one approved paid pass remain pending; no real measurements claimed yet.

## Next / blocked

- Report all results or partial completion without selecting/relabeling cases or spending beyond the dedicated cap.
- PR depends on #143; merge hold until #137 then #140 land and clearance is announced.
- Staff queue #138 is green and still needs lead security review. Human agreement awaits the exported v4 CSV.
