# Clean-clone reproduction

## Historical September 30 reproduction

The following records the earlier d23fa5a export. The October 1 post-v4
refresh is recorded separately below; these earlier counts are not current gates.

## Scope

A fresh clone of this private snapshot was tested without organizer data, private
bindings, a lake, cloud credentials or model keys. Mock calls only; model spend
**$0**. This export still derives from source d23fa5a; it is not the newer Insights
release or a reproduction of official held-out scores. No held-out rows were read.

Environment: Linux, Python 3.12, uv 0.11.2, Node 22.20.0, pnpm 10.30.1 and Docker Compose v2.36.0.
Source and Python/web dependencies were fresh. Docker layers and Chromium were
already cached on the workstation; initial hooks used an existing tool cache.
Times below are observed, not promises for a cold judge workstation.

## Initial README test and setup gaps

| Step | Time | Result |
|---|---:|---|
| Clone private snapshot 5cc68a8 | 1.47 s | Passed |
| `uv sync --extra dev --extra data-ml` | 32.72 s | Passed |
| `pnpm --dir apps/web install --frozen-lockfile` | 14.87 s | Passed; missing from initial README |
| Mock `make checks` | 122.05 s | 454 Python passed, 20 skipped; B1 32/32; hooks/contracts green |
| `make up`, no organizer data, template serving default | 19.33 s | Failed: API startup `UndefinedTable`, missing promoted serving tables |
| `make up`, explicit fixture mode | 22.46 s | Postgres/API/web healthy |
| Disposable Postgres tests | 34.25 s | 23/23 passed |
| Web build / lint / typecheck | 42.00 / 9.08 / 7.20 s | Passed |
| Chromium install (already cached) | 0.87 s | Passed |
| Browser fixture / live API / staff suites | 143.18 / 41.01 / 16.07 s | 80/80 + 12/12 + 1/1 passed |

The initial README documented the full-data path and offline checks but omitted
an executable no-data application path. Snapshot provenance incorrectly implied
Compose selected authored fixtures automatically. Missing promoted tables are an
expected fail-closed behavior, not a reason to silently fall back in serving mode.
The no-data path must explicitly select `LEDGER_BACKEND=fixture`; staff views also
need the fixture-only `DEMO_ROLE=ops`. The README now supplies the exact commands,
local password generation, unique project/ports, browser prerequisites, checks and
persistent-volume cleanup boundaries. Hook cache defaults now stay in the checkout.

The new local smoke was validated against the authored API: login/OTP, explanation,
non-recognition offer, explicit denial, separate confirmation, committed case
readback, human handoff, Desk/Ops reads and logout passed at $0. It compares typed
case views so equivalent timestamp encodings do not produce a false failure.
Its initial development failures (role configuration, endpoint/status assumptions,
and raw JSON timestamp comparison) were corrected in the smoke script; product
behavior was unchanged. It prints only aggregates and sanitized error locations.

## Corrected instructions

The README now separates **A: fixture/mock** from **B: authorized organizer data**.
A second fresh clone of **bcdebe00fbb8b74ad0d0d4c21b42bac7bcb9c9b3** followed
the corrected README, executing its local `.env` setup block unchanged. No copied
venv, `.env`, organizer data, private binding or model credential was used.

| Corrected-clone step | Time | Result |
|---|---:|---|
| Fresh clone | 1.44 s | Passed |
| Locked Python dependencies | 46.60 s | Passed |
| Locked web dependencies | 32.35 s | Passed |
| README local credential/fixture setup | 0.17 s | Passed; no credentials printed |
| `make up` | 34.99 s | Postgres/API/web healthy |
| `python -m scripts.fixture_smoke` | 5.26 s | Login/OTP, case + handoff readbacks, staff, logout passed |
| Mock `make checks` | 130.82 s | 454 passed / 20 skipped, B1 32/32, hooks/contracts green |

The listed commands total **251.63 s (~4m12s)**. Independent installs and checks
were overlapped; this is command time, not total engineering/diagnosis time or a
cold-install guarantee. First-clone browser/persistence checks above execute the
same unchanged product tree; they were not replayed in the second clone. Frozen
release-dependent tests remain skipped. Dependency/tool cache locations are now
inside the checkout except the already installed workstation Chromium/image cache.
Local reproduction containers were stopped after verification; evidence retained.

Without organizer data: authored Chat/Desk/Ops, mock B1 and P paths, Python
contracts, local persistence/RLS tests and authored browser suites are runnable.
With complete authorized organizer files: the bronze/silver/gold pipeline and
serving loader can populate the full demo's 120-day scoped ledger. That full-data
path is **not verified in this clean clone**. Dataset-dependent and omitted private
release tests are skips, not passes; official evaluation is not reproduced.

Actions stay disabled and this repository stays private. Publication requires the
owner's separate approval. No Azure resources or access settings were changed.

## Post-v4 clean clone

On 2026-10-01 UTC, a fresh clone of private snapshot
**aea3d72c7c6333644ffe02a0fbfc74ee5718ebf4** followed README A. Delivered source
is **b8c13059e1332f974279ffd61ecb2e6b19c35876**. All 118 product/prompt/config
files are byte-identical to that source. No copied venv, node_modules, .env, lake,
organizer records, private bindings or provider credentials. Mock only, **$0** model
spend; no Azure change. This is not reproduction or improvement of v4 scores.

Python 3.12.13, uv 0.11.2, Node 22.20.0, pnpm 10.30.1, Compose 2.36.0-desktop.1.
Dependencies/hooks and Chromium were installed into fresh checkout-local caches;
Docker image layers and Linux browser libraries already existed. OS package
installation on a bare machine is **not verified**. The tested Chromium-only
install and optional cache variables are now explicit in README; use its separate
`--with-deps` prerequisite only when libraries are missing. Source/default models,
policy thresholds, confirmation and OTP were not changed to pass this test.

### Export failures and corrections

1. First driver was stopped manually before OS-package installation; dependency
   setup and Compose readiness had passed. Its unfinished smoke is not counted.
   Only its disposable project was stopped, preserving the volume.
2. Fresh snapshot 3011d74 passed setup and authenticated fixture smoke, but
   `make checks` failed collection of two runner test modules: the export had
   withheld their generic `evals/suites/tools/validate_release.py` dependency.
   Retained only that byte-identical, aggregate-only validator. Authoring tools,
   frozen suites/selections and bindings remain withheld.
3. With collection repaired, tests exposed five model-study tests requiring the
   withheld, previously seen v3 development input: 829 passed, five failed,
   23 skipped. Those five export tests now explicitly skip when the input directory
   is absent. All other provider, budget and runner tests remain active. Missing
   inputs are skips, not passes; no source product or evaluation score changed.
4. The final fresh clone below ran all README application/check commands
   successfully. README's stale extra results-table cell was also removed.
   No undocumented application configuration or organizer input was needed.

### Corrected fresh-clone measurements

| README step | Seconds | Verified result |
|---|---:|---|
| `uv sync --extra dev --extra data-ml` | 27.78 | Fresh locked dependencies |
| `pnpm --dir apps/web install --frozen-lockfile` | 14.02 | Fresh locked dependencies |
| Local credential/fixture setup | 0.09 | Random ignored credentials, mode 0600 |
| `make up` | 26.02 | Postgres/API/web healthy |
| `python -m scripts.fixture_smoke` | 3.74 | Login/OTP, case/handoff readbacks, staff, logout |
| `make checks` | 101.35 | **829 passed / 28 skipped**, hooks/types/contracts, B1 32/32 |
| Explicit B1 dev harness | 2.67 | **32/32**, safety guards/readbacks |
| `python -m scripts.test_postgres` | 29.29 | **31/31**, disposable DB/persistence/RLS |
| Web typecheck / lint / build | 4.36 / 5.83 / 35.73 | All passed |
| `playwright install chromium` | 34.18 | Fresh checkout-local browser download |
| Fixture / live API / staff browsers | 213.11 / 32.06 / 11.94 | **111 + 12 + 1 = 124 passed** |
| `make down` | 1.58 | Only this project's containers stopped; volume preserved |

Sequential setup/check command wall time: **543.74 s (~9m04s)**,
excluding clone transfer, diagnosis, failed attempts and documentation. No
cold-machine speed promise. The five export-only missing-input skips add to 23
normal optional skips; source candidate checks were separately **834/23**.
Disposable DB tests are verified separately, not silently included as passes in
those skips. Browser development generated only `apps/web/next-env.d.ts`, left
uncommitted in the disposable clone. README documents rebuilding before a later
production typecheck; no generated test state is exported.

Subsequent snapshot changes record this evidence and README/cache/prerequisite
clarifications only. The tested setup and product tree remain unchanged. Full-data
README B, frozen-suite reproduction, cold OS provisioning, human rating agreement
and public/submission-day access are **not verified** here. Actions stay OFF and
visibility PRIVATE; publication needs separate owner approval.
