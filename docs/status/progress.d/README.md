# Lane progress fragments

Concurrent lanes write `YYYY-MM-DD-branch.md` here instead of editing
`../../history/status/progress-log.md`. Use a short branch label with slashes replaced by hyphens.
Keep one fragment per lane/branch so unrelated work does not conflict.

Each fragment includes:

- **Completed (verified):** exact command, result and aggregate evidence.
- **Done but not verified:** specific checks or environments still untested.
- **Next / blocked:** remaining work and owner decisions/cost approvals.

No credentials, organizer rows, connection strings, private customer bindings or
model thinking. Mark post-v4 changes as not reflected in official v4 numbers.

The lead folds fragments into the canonical log in `docs/history/status/progress-log.md` while preparing the merge
candidate, then removes the folded files in that same feature-branch commit.
Git history retains them. The final remote CI must cover the folded candidate;
never edit main directly or add a commit after CI without another green gate.
Do not fold someone else's unfinished notes or personal study material.
