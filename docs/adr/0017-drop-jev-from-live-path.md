# ADR-0017: Drop Jev from the live customer path

- Status: Accepted by Sebastian; release pending
- Date: 2026-10-01

## Context and verified evidence

Jev's risk-only `Noul` call was unioned with Gemini flags at probability ≥0.5.
It supplied no slots, arithmetic, phrasing or authority. Sebastian approved
removing it after the external audits. These are **post-v4 fixes, not reflected
in v4 numbers**; the official evaluation measured Gemini **with Jev**.

The zero-cost [saved-record replay](../../evals/studies/llm/jev_live_replay.py) reads
only call/decision metadata from completed P checkpoint results. It never opens
suite rows, exports customer text or requests fresh model outputs. Across 160 P executions it verifies **184 Gemini NLU + 184 Jev risk
calls = 368**, plus 15 Gemini phrasing calls (**383 total P calls**).
**One of 184 union records differs from Gemini**, on `injection_suspected` in
`v4.100`. The handoff's “2 calls” denotes the two calls in this one pair, not
two independent changed unions. No execution is counted twice.

That case's saved outcome is `refused_security`, with `passed=false` and a failed
handoff language-routing check. The added cue changes **zero cue-to-reason
lists** across the replay. The evaluated release `1ec9c2f`'s `risk_reasons`
does not route on `injection_suspected`; the API has independent direct/merchant
injection guards. Removing this union addition therefore changes no recorded
decision or primary pass count (**88/100**) in this flag-only comparison.
This is a metadata/decision-map check, not a new official score or a claim about
future attacks. [Official v4](../evaluation/final-v4-results.md),
[safety analysis](../evaluation/final-v4-safety-analysis.md).

Replay input digest (sorted SHA-256 hashes of the 160 saved P result files):
`ee4488d9851f06ee3c180242cefa1282bd41dd887fa04e143682646c1c9b4308`.
Private aggregate receipt: `artifacts/audit-jev-live-replay.json`.
Reproduce locally with an authorized saved checkpoint directory:

```sh
LLM_PROVIDER=mock LLM_REAL_CALLS_APPROVED=0 \
  uv run --no-sync python -m evals.studies.llm.jev_live_replay --checkpoints /path/to/saved/checkpoints
```

The earlier [150-case synthetic dev comparison](../history/ml/typesafe-jev-comparison.md#supporting-risk-cue-union-replayed-after-sebastians-decision)
also has **Gemini 9/10 = union 9/10** injection detection and **0/140** false flags.
Jev adds two distress flags whose truth has no independent labels. This is a
small, reused dev sample, not proof of equivalence or calibrated safety.

TypeSafe is a third vendor receiving redacted customer text. Its published
no-training claim does not establish standard-account ZDR; that status remains
**unverified**. [Terms record](../data-provenance.md),
[privacy boundaries](../security/privacy-and-retention.md).
Each union invocation adds a call, reservation, timeout and failure mode.
V4's 184 risk calls cost **$0.003823932** from their per-call cost fields.
They run in parallel; removing them is not a measured latency improvement.

## Options and decision

Keep the live union for possible future recall, or remove its unproven marginal
benefit and additional data recipient. **Choose removal.**
Production [configuration](../../config/models.yaml) sets
`routing.risk_second_opinion_enabled: false`; there is no implicit Gemini-ID
activation. Gemini flags, Grok failure-only fallback and deterministic guards
remain. The union adapter, typed questions, study code and comparison evidence
stay behind explicit opt-in. Existing approval and budget gates still apply.
Offline Sonnet/Jev subjective judges remain historical evaluation evidence;
neither judges objective outcomes, and human calibration is still pending.

## Consequences and revisit

The live model-data flow is OpenRouter only. One additional vendor call is
removed per applicable NLU invocation. Mock regressions verify the actual
production config makes no TypeSafe call even with a local TypeSafe key present,
and preserve the explicit opt-in studies and offline judge tests.
The lead includes this change in the next reviewed Azure image-tag release;
merge is not deployment. Before release, the lead must update the Jev-required
`scripts.azure_llm_smoke` assertion to require zero TypeSafe calls for the disabled
config. `scripts.azure_verify` currently requires its secret binding; making that
secret optional is separate lead-owned release wiring. Keeping the secret cannot
activate the disabled flag. V4 metrics and historical provider provenance stay intact.

Revisit only with owner approval, independently labeled marginal recall gains,
verified endpoint data terms and a measured latency/cost trade-off. These results
do not justify weakening deterministic security controls.
