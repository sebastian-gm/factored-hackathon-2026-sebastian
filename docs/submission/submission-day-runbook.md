# Submission-day runbook — Sunday, October 4, 2026

**October 3 update:** Sebastian approved and activated Gates A/B in handoff 19.
[v0.9.0 evidence](go-live-2026-10-03.md) records warm/burst replicas, public web
judge login, internal API, $1/UTC-day and $1.60 lifetime judging limits,
backed-up owner maintenance and live checks. **Do not repeat sections 0–3 below:
their OFF-baseline activation recipes are historical preparation.** Publication,
v1.0.0, email, future maintenance and retirement still need their own approvals.
Handoff 19's grouped **Gate C** means publication + v1.0.0 + email; the older
table below names those D/E. Use the new Gate C script/checklist when merged,
after a final release and fresh audit; never infer approval from this runbook.

**Preparation history. Do not execute publication, spending or deletion
from this document without the approvals below.** Publication, email and
teardown remain unexecuted. The October 2 owner-only
v0.7.0 release and capped smoke are recorded separately in
[release notes](../history/evaluation/v0.7-release-notes.md). This is a private
operator document; current-tree scrub must remove private deployment details before publication. Commands run inside this
repository, with Git always `git -C`, only `origin`, and Azure explicitly
**Seb Azure Sandbox**. Never change the CLI default or use `slpnova-azure-main`.

Internal send target: **October 4, 18:00 COT = 23:00 UTC**. Confirm the organizer's
actual cutoff, recipient and format from its email before sending; the brief
records October 5 without a confirmed cutoff timezone. Keep service available
through **October 16 inclusive**. Proposed closure: **October 17, 00:00 COT =
05:00 UTC**; Sebastian approves the exact start/end before activation.

## Approval ledger and execution order

| Gate | Explicit Sebastian OK / scope |
| --- | --- |
| A — warm | **Approved/executed October 3:** both apps min=1 through October 16, API max=3 / HTTP concurrency=5; cost/readback in v0.9.0 evidence. No repeat activation |
| B — judge | **Approved/executed October 3:** public web HTTPS, internal API, four profiles, Key Vault password, $1/UTC-day plus $1.60 lifetime judging run; independent-network checks passed |
| C — final release | **Standing OK already granted:** CI-green main image-tag updates and approved smoke binding. Sebastian approved +$3 on October 2: **$15 cumulative including reserves**, for the final smoke and judging window. Record the final SHA; additional resource/access changes still require a new OK |
| M — owner maintenance | **Fresh approval required for each future reset.** October 3 handoff 19 separately authorized backed-up app-role/FORCE-RLS maintenance; 22 owner cases backed up/reset, HTTP flags stayed OFF. Historical HTTP recipe below is not a fallback authorization |
| D — public repo | **Required:** exact original-repo release SHA, full-history/PR/Actions audit and `sebastian-gm/factored-hackathon-2026-sebastian` only. It stays private until this gate |
| E — send | Sebastian approves the completed email, attachments/links and private credential delivery; the operator does not send on a draft's authority |
| F — retirement | **Required:** exact closure time, scale-down versus irreversible deletion, backup retention/destination and any extra availability/model allowance |

Execute **preflight → step 3 owner-only release → step 1 warm → step 2 judge →
step 4 publish → step 5 send → step 6 keep-alive/retire**. Step 2 depends on the
new backend **and frontend picker/redesign already deployed**. v0.7.0 includes
the picker/redesign, but the fresh-per-login judge realm and customer-map reset
follow-up require the next CI-green image before either mode is enabled.
An access failure stops publication/submission until resolved and reverified.

## 0. Preflight, inputs and receipts

Frontend picker/redesign PRs must be reviewed, merged and remote CI green. Require
browser tests for cookie replacement, old-profile responses/tabs, confirmation,
OTP and cancellation; see [judge API contract](../api/judge-profile-entry.md).
Judge access remains OFF; owner-only UI tests do not prove public judge access.

```bash
set -euo pipefail
set +x
umask 077
export RB_REPO="$PWD"
export RB_OUT="$RB_REPO/artifacts/submission-day"
export RB_SUB='Seb Azure Sandbox'
export RB_RG='rg-aclara-dev-eastus2'
export RB_SUBMISSION='sebastian-gm/factored-hackathon-2026-sebastian'
export RB_REGISTRY="$(az acr show --subscription "$RB_SUB" --resource-group "$RB_RG" --name acraclaradeveastus2 --query loginServer -o tsv)"
export AZURE_WEB_URL="$(.venv/bin/python -c 'from scripts.azure_targets import app_url; print(app_url("web"))')"
test -f "$RB_REPO/AGENTS.md" && test -d "$RB_REPO/infra"
mkdir -p "$RB_OUT"
chmod 700 "$RB_OUT"
git -C "$RB_REPO" fetch origin
git -C "$RB_REPO" switch main
git -C "$RB_REPO" merge --ff-only origin/main
test -z "$(git -C "$RB_REPO" status --porcelain)"
export RB_SHA="$(git -C "$RB_REPO" rev-parse HEAD)"
test "$RB_SHA" = "$(git -C "$RB_REPO" rev-parse origin/main)"
test ! -e "$RB_OUT/prior.tfvars"  # Preserve the original rollback inputs on stops.
cp infra/terraform.tfvars "$RB_OUT/prior.tfvars"
chmod 600 "$RB_OUT/prior.tfvars"
.venv/bin/python - <<'PY'
import os, json, subprocess, urllib.request
from scripts.azure_dev import az, read_variables, private_write, ROOT
v=read_variables(); a=az('account','show')
assert a['name']=='Seb Azure Sandbox' and a['id']==v['subscription_id']
assert a['tenantId']==v['tenant_id'] and a['state']=='Enabled'
with urllib.request.urlopen('https://api.ipify.org',timeout=20) as r: current_ip=r.read().decode().strip()
assert current_ip==v['owner_ipv4'], 'Public IPv4 changed: stop for firewall/connectivity review'
assert not v.get('enable_judge_access') and not v.get('enable_submission_warm')
assert v.get('min_replicas',0)==0
runs=json.loads(subprocess.check_output(['gh','api',
    'repos/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs?head_sha='+os.environ['RB_SHA']+'&per_page=50']))['workflow_runs']
assert all(any(r['name']==n and r['conclusion']=='success' for r in runs) for n in ['ci','safety'])
private_write(ROOT/'artifacts/submission-day/prior.json',json.dumps({
    'image_tag':v['image_tag'],'llm_budget_run_id':v.get('llm_budget_run_id',''),
    'min_replicas':0,'judge_access':False})+'\n')
release=ROOT/'artifacts/azure/jev-release.json'
assert release.is_file()
private_write(ROOT/'artifacts/submission-day/prior-release.json',release.read_text())
print('Sandbox, clean main, CI/safety and testing-mode baseline verified')
PY
terraform -chdir=infra fmt -check apps.tf main.tf variables.tf versions.tf tests/submission.tftest.hcl
terraform -chdir=infra validate
terraform -chdir=infra test -filter=tests/submission.tftest.hcl
```

Expected: matching clean SHA, valid Terraform, **10 mocked plan tests passed**.
No bootstrap/init/provider registration is needed; stop if the existing backend
is unavailable. Private variables, state, plans and logs never enter Git or Actions.
`fmt -check` deliberately lists tracked files; it must not rewrite private tfvars.
Save the previous `jev-release.json` and digests privately for rollback.

### Local helper for variable updates and reviewed plans

Create this **local ignored** helper once. It never selects a subscription through
the global CLI default. Preview mode disables refresh and locking; submission-day
apply mode uses a fresh normally refreshed/locked plan. It prints counts only.

```bash
cat > "$RB_OUT/tf.py" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
from scripts.azure_dev import ROOT, VARIABLES, read_variables, private_write, terraform_environment
folder=ROOT/'artifacts/submission-day'; action=sys.argv[1]; label=sys.argv[2]
if action=='inputs':
    updates=json.loads((folder/(label+'.json')).read_text())
    assert set(updates)<={'image_tag','deploy_apps','enable_real_llm','llm_budget_run_id',
                        'enable_submission_warm','min_replicas','enable_judge_access'}
    values=read_variables(); values.update(updates)
    private_write(VARIABLES,''.join(k+' = '+json.dumps(v)+'\n' for k,v in values.items()))
    print('Private inputs updated'); raise SystemExit(0)
assert action in {'preview','plan','apply'}
env=terraform_environment(); plan=folder/(label+'.tfplan')
if action=='apply':
    assert os.environ.get('RB_APPLY_APPROVED')=='1'
    assert plan.is_file()
    command=['terraform','-chdir=infra','apply','-input=false','-no-color',str(plan)]
else:
    command=['terraform','-chdir=infra','plan','-input=false','-no-color','-out='+str(plan)]
    if action=='preview': command += ['-refresh=false','-lock=false']
p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
private_write(folder/(label+'-'+action+'.log'),p.stdout+p.stderr)
if p.returncode: raise SystemExit('Terraform failed; inspect private log with secrets/IDs suppressed')
if action=='apply': print('Reviewed plan applied; readback still required'); raise SystemExit(0)
plan.chmod(0o600)
p=subprocess.run(['terraform','-chdir=infra','show','-json',str(plan)],cwd=ROOT,env=env,capture_output=True,text=True)
if p.returncode: raise SystemExit('Plan JSON unavailable')
private_write(folder/(label+'.private.json'),p.stdout)
changes=[{'address':x['address'],'actions':x['change']['actions']} for x in json.loads(p.stdout).get('resource_changes',[]) if x['change']['actions']!=['no-op']]
private_write(folder/(label+'-diff.json'),json.dumps(changes,indent=2)+'\n')
print(json.dumps(changes))
PY
```

Invocation: `PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" ...`.
Record a plan hash with `sha256sum "$RB_OUT/<label>.tfplan"`; replace `<label>`
with the actual phase. Each apply requires approval of **that plan's** private diff/hash, not approval of
an earlier preview. Replan after any input/drift change. Never reuse stale plans.

## Plan-only diff and cost delta — measured preparation

Read-only previews on **2026-10-02 UTC**, against existing state, used
`-refresh=false -lock=false`; no state lease, apply or real resource creation.
Private receipt: `artifacts/submission-prep/plan-summary.json`.

| Preview | Create | Update | Delete | Expected effect |
| --- | ---:| ---:| ---:| --- |
| Current OFF | 0 | 0 | 0 | Owner-only web, internal API, min=0/max=1 |
| Warm only, v0.7.0 images | 0 | 2 | 0 | Only API/web min=0 → 1; no environment/access/CPU/max changes |
| Warm + judge ON, same images | 2 | 2 | 0 | Two secret-scoped RBAC grants; API/web min=1/max=1; web IP rule removed; API remains internal HTTPS |

No DB/network/environment/registry/log/state resource or secret **value** is
created by that plan. The two Key Vault values are a separate approved step.
Final image-tag changes also update the same two apps; unexpected replacement,
deletion, extra role scope or public API stops the run. A preview without refresh
does not establish submission-day drift or readiness.

Warm-only preview was refreshed after v0.7.0: private receipt
`artifacts/azure/v0.7/gate-a-plan.json`, plan SHA-256
`e7467400b62ced1ac6a550ce821fd61b14a4c4697f526f334adadf6bc0ce02bb`.
No apply; price refresh at **2026-10-02 19:42:45 UTC** confirmed the rates below.

Live [East US 2 retail API](https://prices.azure.com/api/retail/prices) checked
**2026-10-02 02:28:59 UTC**: active CPU $0.000024/vCPU-second, idle CPU
$0.000003/vCPU-second, memory $0.000003/GiB-second. For **two 0.25-vCPU/0.5-GiB
apps**, rates are $0.0162/hour idle or $0.054/hour active. Idle eligibility depends
on activity; scale-to-zero has no app compute charge.
[Azure billing conditions](https://learn.microsoft.com/en-us/azure/container-apps/billing).

| Estimate, before grants/tax/models | Oct 4–16 inclusive, 312 hours |
| --- | ---: |
| Total app compute, fully idle / fully active | **$5.0544 / $16.8480** |
| Idle warm delta if 100 already-budgeted active hours occur in this window | **$3.4344** for the other 212 hours; do not add the active hours twice |
| Extra activity versus that 100-hour baseline, fully active window | **$11.4480**; usage-dependent, not an idle-replica fixed fee |
| Monthly fixed DB/storage/registry, repriced | **$21.09** (730 B1ms hours, 32 GiB, 30 ACR days) |
| Explicit state/KV/log/egress margin + up to 100k requests | **$8.10 + $0.04** |
| Monthly infrastructure with the above window, no app use outside it | **$34.28–$46.08** |
| Same 730-hour fully warm month, app compute only | **$11.826–$39.420** |

**The upper infrastructure estimate exceeds $40: STOP for Sebastian's explicit
cost OK before warm/judge activation.** The existing `azure_prices` $34.63 gate
assumes 100 active hours; its success does not approve a 312-hour window.
Re-fetch prices October 4. Public web adds request/log/egress exposure and secret
operations, not a dedicated compute SKU; these allowances are not hard Azure caps.
Azure's CAD billing alerts approximate USD 30/50 and notify rather than stop spend.

### Proposed judging model cap — OFF pending Gate B

Sebastian approved **$15 cumulative LLM exposure including reserves** on October 2;
see the [approval ledger](../history/status/model-budget-ledger.md).
The verified v0.8.1 readback on October 3 finds conservative exposure
**$12.40571698**. The original v0.8 smoke
purse retains **$0.088647** unused capacity; the prior v0.7 purse retains
**$0.076661**. Propose **$2.30 lifetime** for judging (supersedes $2.40),
retaining the v0.8.1 smoke purse's **$0.092240** after its $0.00776 charge:
**$12.40571698 + $0.088647 + $0.076661 + $0.092240 + $2.30 = $14.96326498 <= $15**.
All failed conversation attempts and reservations are preserved. Refresh this
arithmetic before preparation; never treat unknown reserves as available money.

Propose **$1 per UTC day**, shared across all profiles/workers/retries/providers,
bounded also by the remaining cumulative allowance and the production key's own
limit. Keep the key limit as an independent hard stop; no top-up/limit increase
or alternate-provider retry on exhaustion. Read free account/key metadata before
and after smoke, without printing keys. Unspent reserves and disabled scopes
are not reset. Stop paid calls at whichever bound is reached first and degrade
deterministically; the service may remain available through October 16.

The window intersects **14 UTC dates**; $1/day therefore does **not** authorize
$14 in judging calls. Approximate conservative upper allocation is $46.08
infrastructure + $2.30 judging models = **$48.38**, before tax/grants and traffic
beyond stated margins; infrastructure still needs its separate cost approval.

**Activation prerequisite:** review and test the $1 daily configuration plus a
durable judging lifetime binding before Gate B. The existing Terraform/readback
snippets below describe today's $3/day configuration and empty judge run binding;
they cannot enforce this proposal. Do not execute judge activation until those
snippets and controls are updated on green CI and the exact plan is approved.
No live cap, replica or access change is made by this proposal.

Refresh rates without model spend:

```bash
.venv/bin/python -m scripts.azure_prices
PYTHONPATH="$RB_REPO" .venv/bin/python artifacts/submission-prep/read_prices.py
```

Expected today's outputs: fixed $21.09, testing estimate $34.63, idle/active app
day $0.3888/$1.296. Recalculate the window rather than approving from these dates.

## Owner demo reset before video and before submission

**Gate M — explicit Sebastian OK each time. OFF now; not exercised live.**
October 2: backups retained, **no Azure records deleted**, MX receipts verified
across logins; the filing smoke used CO instead. Preserving existing receipts is
the default. Reset only the approved persona's **owner** case/card maps and the
maintenance session's operational workspace; historical workspaces, sessions,
append-only audit, organizer ledger, bindings and all judge realms remain.
This is not a general restore tool or a way to erase every old conversation.

Prerequisites: deploy the CI-green customer-map reset follow-up; owner-only
ingress; judge mode OFF; quiesce **all** owner tabs/sessions for the named persona
and keep them quiesced until receipt/readback. A saved proposal in an old tab
must not be confirmed after maintenance. No model call is needed. Do not run the
old private direct-delete helper. A disabled HTTP reset is a stop, not permission
to bypass it.

Create the ignored helper below. `backup` is read-only; `apply` additionally
requires the separately approved flags and `RB_RESET_APPROVED=1`. Both create
new mode-0600 backups, independently decode/check them and output counts/hashes
only. Tokens/passwords are never saved. The apply compares current bank maps
with the reviewed backup before proposal/confirmation.

```bash
cat > "$RB_OUT/owner-reset.py" <<'PY'
import hashlib, json, os, sys
from datetime import UTC, datetime
from pathlib import Path
import httpx
from scripts.azure_dev import ROOT, VAULT, az, private_write
from scripts.azure_migrate_ops import connection_string
from scripts.azure_targets import app_url
from scripts.serving_smoke import check, wait_config
from scripts.azure_llm_smoke import budget_receipt
from aclara.bank.serving import ServingRepository
from aclara.ops.store import Scope, Store
from aclara.settings import Settings

action=sys.argv[1]; username=os.environ['RB_RESET_PERSONA']
assert action in {'backup','apply'}
assert username in {'demo.es.mx','demo.es.co','demo.es.ar','demo.pt.br'}
folder=ROOT/'artifacts/submission-day'; folder.mkdir(mode=0o700,exist_ok=True)
prior=None
if action=='apply':
    assert os.environ.get('RB_RESET_APPROVED')=='1'
    path=Path(os.environ['RB_RESET_BACKUP']).resolve()
    assert path.parent==folder.resolve() and path.stat().st_mode & 0o777==0o600
    assert hashlib.sha256(path.read_bytes()).hexdigest()==os.environ['RB_RESET_BACKUP_SHA256']
    prior=json.loads(path.read_text()); assert prior['username']==username and prior['realm']=='owner'
before=budget_receipt(); store=Store(connection_string('aclara_app'))
try:
    ledger=ServingRepository(store,Settings().bank_clock)
    persona=next(p for p in ledger.personas() if p.username==username)
    web=app_url('web')
    password=az('keyvault','secret','show','--vault-name',VAULT,'--name','demo-password')['value']
    with httpx.Client(base_url=web+'/api/bff/',headers={'Origin':web},timeout=190) as client:
        wait_config(client)
        challenge=check(client.post('auth/login',json={'username':username,'password':password}))
        code=check(client.get('auth/challenges/'+challenge['challenge_id']+'/sms'))['code']
        check(client.post('auth/otp/verify',json={'challenge_id':challenge['challenge_id'],'code':code}))
        identity=check(client.get('me')); assert identity['username']==username and identity['role']=='ops'
        run,sid,_=client.cookies.get('aclara_access').split('.',2)
        scope=Scope(persona.customer_id,run,sid)
        cases=store.customer_mapping('customer_cases',dict,lambda _:'owner',legacy='cases')
        cards=store.customer_mapping('customer_card_states',dict,lambda _:'owner',legacy='card_states')
        tables=('cases','card_states','handoffs','conversations','turns','execution_records','idempotency_keys')
        with store.transaction(scope):
            payload={'username':username,'customer_id':persona.customer_id,'realm':'owner',
                'run_id':run,'sid':sid,'customer_cases':dict(cases),'customer_card_states':dict(cards),
                'workspace':{t:{k:store.get(t,k) for k in store.keys(t)} for t in tables},
                'backed_up_at':datetime.now(UTC).isoformat()}
        path=folder/('owner-reset-'+action+'-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')+'.private.json')
        assert not path.exists(); private_write(path,json.dumps(payload,sort_keys=True)+'\n')
        assert path.stat().st_mode & 0o777==0o600 and json.loads(path.read_text())==payload
        report={'backup_file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'cases':len(payload['customer_cases']),'card_states':len(payload['customer_card_states']),
            'reset':False}
        if action=='apply':
            assert prior['customer_id']==persona.customer_id
            assert all(prior[k]==payload[k] for k in ('customer_cases','customer_card_states'))
            transactions=check(client.get('transactions'))
            challenge=check(client.post('auth/step-up',json={}))
            code=check(client.get('auth/challenges/'+challenge['challenge_id']+'/sms'))['code']
            check(client.post('auth/step-up/verify',json={'challenge_id':challenge['challenge_id'],'code':code}))
            proposal=check(client.post('ops/reset/proposal',json={}))
            body={'proposal_hash':proposal['proposal_hash'],'confirmed':True}
            receipt=check(client.post('ops/reset',json=body))
            assert receipt['reset'] and receipt['verified'] and receipt['remaining_operations']==0
            assert check(client.get('ops/reset/'+receipt['receipt_id']))==receipt
            assert check(client.post('ops/reset',json=body))==receipt
            with store.transaction(scope): assert not cases and not cards
            assert check(client.get('transactions'))==transactions
            report.update(reset=True,remaining_bank_records=0,ledger_readback_unchanged=True)
        check(client.post('auth/logout',json={})); assert client.get('me').status_code==401
    assert budget_receipt()==before
    private_write(folder/(path.stem+'-receipt.json'),json.dumps(report)+'\n')
    print(json.dumps(report))
finally:
    store.close()
PY
export RB_RESET_PERSONA='demo.es.mx'  # Replace only with Sebastian's named scope.
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/owner-reset.py" backup
```

Expected: private filename/hash, existing case/card counts, `reset:false`, no
budget change. Review the **aggregate** receipt, not row values. Record the
approval plus that file/hash in `RB_RESET_BACKUP` / `RB_RESET_BACKUP_SHA256`.
Check both app environment snapshots privately and require the reset variables
to be absent before the following temporary override, so removal restores the
prior state. **These Azure commands need Gate M; image-tag standing OK does not
authorize them.** Save prior app descriptions, then install cleanup before enable:

```bash
az containerapp show --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-api-aclara-dev-eastus2 -o json > "$RB_OUT/reset-api-before.private.json"
az containerapp show --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-web-aclara-dev-eastus2 -o json > "$RB_OUT/reset-web-before.private.json"
PYTHONPATH="$RB_REPO" .venv/bin/python - <<'PY'
import json,os
from pathlib import Path
for app,key in [('api','ALLOW_DEMO_RESET'),('web','FRONTEND_ALLOW_DEMO_RESET')]:
    p=Path(os.environ['RB_OUT'])/('reset-'+app+'-before.private.json'); p.chmod(0o600)
    description=json.loads(p.read_text())
    assert description['properties']['configuration']['ingress']['external']==(app=='web')
    assert all(e['name']!=key for c in description['properties']['template']['containers'] for e in c.get('env',[]))
PY
restore_reset_flags() {
  local failed=0
  az containerapp update --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-api-aclara-dev-eastus2 --remove-env-vars ALLOW_DEMO_RESET --output none || failed=1
  az containerapp update --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-web-aclara-dev-eastus2 --remove-env-vars FRONTEND_ALLOW_DEMO_RESET --output none || failed=1
  return "$failed"  # Attempt both removals even if the first fails under set -e.
}
trap restore_reset_flags EXIT
az containerapp update --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-api-aclara-dev-eastus2 --set-env-vars ALLOW_DEMO_RESET=true --output none
az containerapp update --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-web-aclara-dev-eastus2 --set-env-vars FRONTEND_ALLOW_DEMO_RESET=true --output none
# Require ready revisions for both apps before proceeding. Never retry a write
# blindly if cold startup/network interrupts it: use the proposal receipt path.
RB_RESET_APPROVED=1 PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/owner-reset.py" apply
restore_reset_flags
trap - EXIT
.venv/bin/python -m scripts.azure_verify
```

Expected: verified reset receipt, independent bank-map count zero, unchanged
transaction readback, no provider calls; final image/replica/access readback
unchanged and both reset variables absent. Independently recheck BFF config
`resetEnabled=false` after ready revisions. Retain backup, hash and audit.
No other persona/realm is reset; authored memory/Postgres tests prove that boundary.
**Rollback:** disable both flags even on failure, preserve receipts/backups and
stop. Deleted case/card state is not restored by flag removal. A separate scoped
restore needs Sebastian's explicit OK and independent verification; do not
automatically replay old actions or loosen RLS. A failed cleanup requires owner
attention before video/submission. This recipe is syntax-checked, not live reset
evidence; its source workflow passed authored API/Postgres tests.

## 3. Final release first — owner-only boundary

**Gate C.** Confirm picker/redesign merged; record approved main SHA and image
digests. Keep warm/judge OFF during release and capped real smoke. Do not rerun
v4, change official files, run live judges, load new organizer data or reset budgets.

```bash
docker build -f Dockerfile.api -t "$RB_REGISTRY/aclara-api:$RB_SHA" .
docker build -f apps/web/Dockerfile.azure -t "$RB_REGISTRY/aclara-web:$RB_SHA" apps/web
.venv/bin/python - <<'PY'
import os, json, subprocess, shutil
from scripts.azure_dev import ROOT, az, private_write
sha=os.environ['RB_SHA']; registry=os.environ['RB_REGISTRY']; folder=ROOT/'artifacts/submission-day/docker-auth'
folder.mkdir(mode=0o700,parents=True,exist_ok=False)
context=subprocess.check_output(['docker','context','show'],text=True).strip()
endpoint=json.loads(subprocess.check_output(['docker','context','inspect',context],text=True))[0]['Endpoints']['docker']['Host']
env={**os.environ,'DOCKER_CONFIG':str(folder),'DOCKER_HOST':endpoint}
try:
    token=az('acr','login','--name','acraclaradeveastus2','--expose-token')['accessToken']
    subprocess.run(['docker','login',registry,'--username',
        '00000000-0000-0000-0000-000000000000','--password-stdin'],input=token,
        text=True,capture_output=True,env=env,check=True)
    images={}
    for name in ['api','web']:
        image=registry+'/aclara-'+name+':'+sha
        subprocess.run(['docker','push',image],env=env,check=True)
        images[name]={'tag':image,'digest':az('acr','repository','show',
            '--name','acraclaradeveastus2','--image','aclara-'+name+':'+sha)['digest']}
    private_write(ROOT/'artifacts/submission-day/images.json',json.dumps(images)+'\n')
    print('Both SHA images pushed and digests read back')
finally: shutil.rmtree(folder)
PY
SMOKE_BUDGET_PREPARATION_APPROVED=1 .venv/bin/python -m scripts.release_smoke_budget release --sha "$RB_SHA" --prepare
.venv/bin/python - <<'PY'
import os,json
from scripts.azure_dev import ROOT,private_write
private_write(ROOT/'artifacts/submission-day/release.json',json.dumps({
    'image_tag':os.environ['RB_SHA'],'deploy_apps':True,'enable_real_llm':True,
    'llm_budget_run_id':'pre-v4-release-'+os.environ['RB_SHA'],
    'enable_judge_access':False,'enable_submission_warm':False,'min_replicas':0})+'\n')
PY
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" inputs release
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" plan release
# Review private plan, approve exact hash; then:
RB_APPLY_APPROVED=1 PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" apply release
.venv/bin/python -m scripts.azure_verify
# Receipt wrapper below runs each model/browser gate ONCE and suppresses raw errors.
```

Expected: plan **0 added / 2 updated / 0 destroyed** (new SHA/budget binding
only); both ready images match pushed digests/SHA, standard restricted controls
pass, three model paths pass, three browser surfaces pass, outside-owner web
**403** and API **404**, known smoke cost/exposure **≤$0.10**, zero unknown costs.
Typical previous three-path smoke cost was under $0.01; this is an estimate, not
permission for more than the approved $0.10 lifetime purse. The budget setup may
refuse the conservative $15 calculation; stop, do not reset caps/reservations or
change run IDs to retry. A completed v4 needs no new final-program start.

`azure_smoke` is mock-only and restarts a replica: **do not run it on a real-
provider release or the active judge window**. `serving_browser` must have updated
selectors for the final redesign before SHA freeze. Never mark a failing browser
gate as a UI-only exception or replay paid paths after its five-slot guard expires.

Save a new private `artifacts/azure/jev-release.json` after verifying SHA, image
digests, CI/safety/access run IDs, controls, real/browser smoke exits, budget and
post-v4 disclosure. It must have `controls_verified`, `real_smoke_verified`,
`ci_verified` all true; include the actual run IDs and cost, not copied prior flags.
Archive the original before writing; then append separate warm/judge readbacks.
Use this wrapper in place of the two commented smoke commands above, **before**
the external access workflow. It includes the reviewed post-v4 readback/reason
checks in `artifacts/post-v4/real_smoke.py`; inspect that authored helper against
the final smoke interface first. A failure stops; this is not a retry wrapper.

```bash
AZURE_RELEASE_SMOKE_RUN_ID="pre-v4-release-$RB_SHA" .venv/bin/python - <<'PY'
import json,os,subprocess,sys
from datetime import UTC,datetime
from scripts.azure_dev import ROOT,private_write
for label,command in [('real',[sys.executable,'artifacts/post-v4/real_smoke.py']),
                      ('browser',[sys.executable,'-m','scripts.serving_browser','--target','azure'])]:
    path=ROOT/('artifacts/submission-day/'+label+'.json')
    assert not path.exists(), 'Existing receipt: stop; do not replay smoke'
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    private_write(path.with_suffix('.log'),p.stdout+p.stderr)
    private_write(path,json.dumps({'sha':os.environ['RB_SHA'],'exit_code':p.returncode,
        'verified_at':datetime.now(UTC).isoformat()})+'\n')
    print(json.dumps({'gate':label,'passed':p.returncode==0}))
    if p.returncode: raise SystemExit('Gate failed; no automatic retry; private logs retained')
PY
```

After the owner-only access run succeeds, record the release from actual receipts:

```bash
gh workflow run azure-access.yml --repo sebastian-gm/factored-hackathon-2026-sebastian --ref main
gh run list --limit 10 --json databaseId,name,headSha,status,conclusion
# Wait for this exact access run to complete successfully before the recorder.
.venv/bin/python -m scripts.release_smoke_budget release --sha "$RB_SHA"
.venv/bin/python - <<'PY'
import json,os,subprocess
from datetime import UTC,datetime
from decimal import Decimal
import psycopg
from scripts.azure_dev import ROOT,az,read_variables,private_write
from scripts.azure_migrate_ops import connection_string
from scripts.release_smoke_budget import verify
sha=os.environ['RB_SHA']; out=ROOT/'artifacts/submission-day'
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==sha
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','origin/main'],text=True).strip()==sha
assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip()
v=read_variables(); assert v['image_tag']==sha and not v.get('enable_judge_access')
assert not v.get('enable_submission_warm') and v.get('min_replicas',0)==0
assert v['llm_budget_run_id']=='pre-v4-release-'+sha
assert json.loads((ROOT/'artifacts/azure/verified.json').read_text())=={'controls':'passed','release':sha}
for label in ['real','browser']:
    r=json.loads((out/(label+'.json')).read_text()); assert r['sha']==sha and r['exit_code']==0
images=json.loads((out/'images.json').read_text())
for name in ['api','web']:
    a=az('containerapp','show','--resource-group','rg-aclara-dev-eastus2',
         '--name','ca-'+name+'-aclara-dev-eastus2')['properties']
    assert a['latestReadyRevisionName']==a['latestRevisionName']
    assert a['template']['containers'][0]['image']==images[name]['tag']
    assert az('acr','repository','show','--name','acraclaradeveastus2',
        '--image','aclara-'+name+':'+sha)['digest']==images[name]['digest']
raw=json.loads((ROOT/('artifacts/azure/pre-v4-release-'+sha+'.json')).read_text())
assert raw['release']==sha and len(raw['results'])==3
assert {x['scenario'] for x in raw['results']}=={'es_normal','pt_ambiguous','fraud'}
assert all(x['status']=='passed' for x in raw['results'])
budget=verify(connection_string('aclara_admin'),'release',sha,prepare=False)
assert budget['unknown_cost_attempts']==0 and budget['charged_with_reserves_usd']<=.1
with psycopg.connect(connection_string('aclara_admin')) as db:
    db.execute('SET LOCAL ROLE aclara_owner')
    total=db.execute('SELECT coalesce(sum(charged_usd),0) FROM llm.reservations').fetchone()[0]
    v4=db.execute("SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope='final-evaluation-v4'").fetchone()[0]
extra=total-v4-Decimal(str(budget['all_prior_charged_with_reserves_usd']))
assert extra>=0 and total<=15
maximum=Decimal(str(budget['conservative_maximum_cumulative_usd']))+extra
assert maximum<=15
runs=json.loads(subprocess.check_output(['gh','api',
    'repos/sebastian-gm/factored-hackathon-2026-sebastian/actions/runs?head_sha='+sha+'&per_page=50']))['workflow_runs']
checks={}
for name in ['ci','safety','azure-access']:
    r=max((r for r in runs if r['name']==name and r['head_branch']=='main'),key=lambda r:r['run_number'])
    assert r['status']=='completed' and r['conclusion']=='success'; checks[name]=r['id']
report={'implementation_sha':sha,'controls_verified':True,'real_smoke_verified':True,
    'ci_verified':True,'workflow_runs':checks,'application_images':images,
    'smoke_cost_usd':budget['known_cost_usd'],'cumulative_charged_with_reserves_usd':float(total),
    'conservative_maximum_usd':float(maximum),'min_replicas':0,'judge_access_enabled':False,
    'post_v4_changes_not_reflected_in_v4_results':True,'verified_at':datetime.now(UTC).isoformat()}
private_write(ROOT/'artifacts/azure/jev-release.json',json.dumps(report,indent=2)+'\n')
private_write(out/'jev-release.json',json.dumps(report,indent=2)+'\n')
print(json.dumps({'sha':sha,'flags':[True,True,True],'runs':checks,'smoke_cost_usd':budget['known_cost_usd']}))
PY
```

The historical `artifacts/post-v4/record_release.py` requires different receipts;
do not run both recorders or invoke either testing-mode recorder after judge ON.

**Rollback:** `cp "$RB_OUT/prior.tfvars" infra/terraform.tfvars`, plan `rollback-release`, review/apply that
plan with Gate C, then `scripts.azure_verify` and the old owner-only access check.
Retain the failed SHA's logs/counters; do not restart its real smoke. If the prior
smoke purse is exhausted, rollback verification is read-only until a new spend OK.

## 1. Warm both apps

Optional burst scaling is separately prepared in the
[Gate A concurrency plan](gate-a-scaling-plan.md): API max 3/HTTP threshold 5,
workers 1, defaults OFF, monthly upper estimate $62.93. The commands below are
**warm-only/max 1**. For the burst option, Sebastian must approve the updated
plan/cost; include `enable_submission_scale=true`, verify API max 3 and its HTTP
rule, and include `enable_submission_scale=false` in rollback/retirement.

**Gate A, including the >$40 upper estimate.** Final release must already pass.

```bash
printf '%s\n' '{"enable_submission_warm":true,"min_replicas":1}' > "$RB_OUT/warm.json"
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" inputs warm
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" plan warm
# Expect exactly two in-place app updates; approve this fresh plan/hash.
RB_APPLY_APPROVED=1 PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" apply warm
az containerapp show --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-api-aclara-dev-eastus2 --query '{state:properties.provisioningState,min:properties.template.scale.minReplicas,max:properties.template.scale.maxReplicas,image:properties.template.containers[0].image}' -o json
az containerapp show --subscription "$RB_SUB" --resource-group "$RB_RG" --name ca-web-aclara-dev-eastus2 --query '{state:properties.provisioningState,min:properties.template.scale.minReplicas,max:properties.template.scale.maxReplicas,image:properties.template.containers[0].image}' -o json
```

Expected both `Succeeded`, min=1/max=1 and final SHA image. Check readiness:

```bash
.venv/bin/python - <<'PY'
from scripts.azure_dev import az,GROUP
for name in ['api','web']:
    app='ca-'+name+'-aclara-dev-eastus2'
    p=az('containerapp','show','--resource-group',GROUP,'--name',app)['properties']
    revision=p['latestReadyRevisionName']; assert revision==p['latestRevisionName']
    r=az('containerapp','revision','show','--resource-group',GROUP,'--name',app,'--revision',revision)
    assert r['properties']['healthState']=='Healthy' and r['properties']['runningState']=='Running'
    replicas=az('containerapp','replica','list','--resource-group',GROUP,'--name',app,'--revision',revision)
    assert len(replicas)==1 and all(c['ready'] for c in replicas[0]['properties']['containers'])
print('Both apps: healthy ready revision and one ready replica')
PY
```

Poll these GETs manually while readiness is pending; never reapply to force it.
**The unmodified `azure_verify` expects min=0**;
use step 2's mode-aware readback for warm mode too (judge flag still false).

**Rollback A:** set `enable_submission_warm=false,min_replicas=0` through the
same inputs/plan/review/apply sequence; leave ingress/login unchanged. Read back
min=0/max=1. Actual replicas may stay active until idle; this is not a stop command.

## 2. Enable the judge entry and verify public access

**Deferred live realm gate (v0.8.0):** after Sebastian's Gate B approval and judge
activation, use two independent judge logins/OTP visits, select the same profile
and eligible story in each, and file with confirmation/step-up/readback. Both
must receive distinct verified receipts for the same scoped transaction. Confirm
neither visit can read the other's receipt; switching back in one visit retains
its own case. Preserve traces privately, report aggregates only, use the approved
judging purse. Before activation this is covered only by local/Postgres/CI tests.

**Gate B:** approve exact four source profiles, account, public web, role grants,
the proposed $1/UTC-day plus cumulative judging exposure/window, external check
and any private credential delivery. The budget activation prerequisite above
must be satisfied before executing the remaining commands in this section.
No owner/provider/database password is given to judges. API stays internal.

Privately create `$RB_OUT/judge-definition.json` with exactly `username` and
`profiles`, mapping `mx-es/co-es/ar-es/pt` to the four reviewed serving usernames;
expected locales are `es-MX/es-CO/es-AR/pt-BR`, customers distinct, roles unchanged.
Do not put the password in this file. Run once after approval:

```bash
.venv/bin/python - <<'PY'
import os,json,secrets,hmac
import httpx
from pathlib import Path
from scripts.azure_dev import az,VAULT
d=json.loads((Path(os.environ['RB_OUT'])/'judge-definition.json').read_text())
assert set(d)=={'username','profiles'} and d['username'].startswith('judge.')
assert set(d['profiles'])=={'mx-es','co-es','ar-es','pt'}
token=az('account','get-access-token','--resource','https://vault.azure.net')['accessToken']
base='https://'+VAULT+'.vault.azure.net/secrets/'
try:
    with httpx.Client(headers={'Authorization':'Bearer '+token},timeout=30) as c:
        urls={n:base+n+'?api-version=7.4' for n in ['judge-password','judge-persona']}
        old={n:c.get(u) for n,u in urls.items()}
        # Existing secrets require an explicit rotation/reuse review; no silent reset.
        assert all(r.status_code==404 for r in old.values())
        password=secrets.token_urlsafe(48)
        assert not hmac.compare_digest(password,az('keyvault','secret','show',
            '--vault-name',VAULT,'--name','demo-password')['value'])
        for name,value in [('judge-password',password),('judge-persona',json.dumps(d))]:
            response=c.put(urls[name],json={'value':value,'attributes':{'enabled':True}})
            assert response.status_code==200
            actual=c.get(urls[name]); assert actual.status_code==200
            assert hmac.compare_digest(actual.json()['value'],value)
        print('Two Key Vault-only judge secrets independently verified; no values displayed')
except Exception as error:
    raise SystemExit('Judge secret preparation stopped: '+type(error).__name__) from None
PY
printf '%s\n' '{"enable_judge_access":true,"llm_budget_run_id":""}' > "$RB_OUT/judge.json"
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" inputs judge
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" plan judge
# Approve: two secret-scoped grants + two app updates; API external=false.
RB_APPLY_APPROVED=1 PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" apply judge
```

Expected **2 created / 2 updated / 0 deleted**. Secret values exist only in memory
and Key Vault, not argv/files/.env/Terraform/state/Git/logs. A partial secret setup
or failed readback stops this phase; inspect metadata and get a reuse/rotation OK,
never blindly regenerate. Secret-scoped RBAC propagation/readiness can take time;
poll read-only checks, never automatically replay an unverified write.

### Mode-aware infrastructure/budget readback (no model calls)

```bash
.venv/bin/python - <<'PY'
import json,os
from datetime import UTC,datetime
from decimal import Decimal
import psycopg
from scripts.azure_dev import az,GROUP,read_variables,private_write,ROOT
from scripts.azure_migrate_ops import connection_string
v=read_variables(); judge=v.get('enable_judge_access',False); minimum=v.get('min_replicas',0)
for name in ['api','web']:
    a=az('containerapp','show','--resource-group',GROUP,'--name','ca-'+name+'-aclara-dev-eastus2')
    p=a['properties']; i=p['configuration']['ingress']; t=p['template']; c=t['containers'][0]
    assert p['provisioningState']=='Succeeded' and p['latestReadyRevisionName']==p['latestRevisionName']
    assert p['configuration']['activeRevisionsMode']=='Single'
    assert (t['scale']['minReplicas'] or 0)==minimum and t['scale']['maxReplicas']==1
    assert c['image'].endswith(':'+v['image_tag'])
    assert c['resources']['cpu']==0.25 and c['resources']['memory']=='0.5Gi'
    assert not i.get('allowInsecure',False) and i['external']==(name=='web')
    rules=i.get('ipSecurityRestrictions') or []
    if name=='web' and not judge:
        assert len(rules)==1 and rules[0]['action']=='Allow' and rules[0]['ipAddressRange']==v['owner_ipv4']+'/32'
    else: assert rules==[]
    if name=='api':
        assert '.internal.' in i['fqdn']
        env={e['name']:e for e in c['env']}
        assert env['PGSSLMODE']['value']=='verify-full' and env['PGUSER']['value']=='aclara_app'
        assert env['LLM_DAILY_BUDGET_USD']['value']=='3' and env['OPS_BACKEND']['value']=='postgres'
        assert env['LLM_BUDGET_RUN_ID'].get('value','')==v.get('llm_budget_run_id','')
        if judge:
            assert env['JUDGE_ACCESS_ENABLED']['value']=='true' and not env['LLM_BUDGET_RUN_ID'].get('value','')
            for field,secret in [('JUDGE_PERSONA','judge-persona'),('JUDGE_PASSWORD','judge-password')]:
                assert env[field]['secretRef']==secret and 'value' not in env[field]
                s=next(s for s in p['configuration']['secrets'] if s['name']==secret)
                assert s['keyVaultUrl'].endswith('/secrets/'+secret) and s.get('identity')
                identities=a['identity']['userAssignedIdentities']
                entry=next(x for key,x in identities.items() if key.lower()==s['identity'].lower())
                vault=az('keyvault','show','--resource-group',GROUP,'--name','kv-aclara-dev-eastus2')
                scope=vault['id']+'/secrets/'+secret
                grants=az('role','assignment','list','--assignee-object-id',entry['principalId'],
                          '--scope',scope,'--include-inherited','--fill-principal-name','false')
                assert grants and all(g['scope'].lower()==scope.lower() and
                    g['roleDefinitionName']=='Key Vault Secrets User' for g in grants)
with psycopg.connect(connection_string('aclara_admin')) as db:
    db.execute('SET LOCAL ROLE aclara_owner')
    assert db.execute("SELECT daily_usd,disabled FROM llm.limits WHERE scope='production'").fetchone()==(Decimal('3'),False)
tls=az('postgres','flexible-server','parameter','show','--resource-group',GROUP,
       '--server-name','psql-aclara-dev-eastus2','--name','require_secure_transport')
assert tls['value'].lower()=='on'
receipt={'sha':v['image_tag'],'min_replicas':minimum,'judge_access':judge,
         'api_internal':True,'tls':True,'global_daily_usd':3,'verified':True}
private_write(ROOT/('artifacts/submission-day/mode-controls-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%S')+'.json'),json.dumps(receipt)+'\n')
print(json.dumps(receipt))
PY
```

Expected min=1, judge=true, API internal/TLS true, $3 global, no smoke override.
Check each image digest against step 3 and each role assignment's scope against
exactly the two approved secret IDs (private plan/readback; never vault-wide grants).
Do not reset the production breaker to pass this check. If disabled, stop for the
owner's diagnosis. Existing Azure-services PostgreSQL firewall exception remains
a documented limitation; private networking is future work, not an Oct 4 change.

### Authenticated judge check, zero model calls

The frontend must implement the documented BFF endpoints before this can pass.
It consumes the upstream token and sets only an HttpOnly cookie. Read-only data
responses stay in memory; stdout contains only aggregate counts.

```bash
.venv/bin/python - <<'PY'
import json,os
from pathlib import Path
import httpx
from scripts.azure_dev import az,VAULT
d=json.loads((Path(os.environ['RB_OUT'])/'judge-definition.json').read_text())
web=az('containerapp','show','--resource-group','rg-aclara-dev-eastus2',
       '--name','ca-web-aclara-dev-eastus2')['properties']['configuration']['ingress']['fqdn']
origin='https://'+web; base=origin+'/api/bff/'
password=az('keyvault','secret','show','--vault-name',VAULT,'--name','judge-password')['value']
def checked(r):
    assert r.status_code==200
    return r.json()
try:
    with httpx.Client(base_url=base,headers={'Origin':origin},timeout=90) as c:
        login=checked(c.post('auth/login',json={'username':d['username'],'password':password}))
        sms=checked(c.get('auth/challenges/'+login['challenge_id']+'/sms'))
        verified=checked(c.post('auth/otp/verify',json={'challenge_id':login['challenge_id'],'code':sms['code']}))
        assert 'access_token' not in verified
        assert checked(c.get('me'))['profile_selection_required']
        assert c.get('transactions').status_code==403
        assert len(checked(c.get('auth/judge/profiles'))['profiles'])==4
        old_conversation=None
        for profile in ['mx-es','co-es','ar-es','pt']:
            old_cookies=httpx.Cookies(c.cookies)
            result=checked(c.post('auth/judge/profile',json={'profile_id':profile}))
            assert result['verified'] and 'access_token' not in result
            identity=checked(c.get('me')); assert identity['judge_profile_id']==profile
            rows=checked(c.get('transactions'))
            assert isinstance(rows,list) and rows
            assert all('customer_id' not in r and 'fraud_score' not in r for r in rows)
            with httpx.Client(base_url=base,cookies=old_cookies,timeout=90) as stale:
                assert stale.get('me').status_code==401
            if old_conversation:
                assert c.get('chat/sessions/'+old_conversation+'/trace').status_code==404
            old_conversation=checked(c.post('chat/sessions',json={}))['conversation_id']
        assert checked(c.post('auth/logout',json={}))['verified']
        assert c.get('transactions').status_code==401
    print('Judge login/OTP, four scopes, old-cookie/object rejection and logout: passed; model calls=0')
except Exception as error:
    raise SystemExit('Judge read-only smoke stopped: '+type(error).__name__) from None
PY
```

Also rehearse the **browser** picker/redesign with ES/PT, back/refresh, two tabs,
pending proposal/OTP/cancel and four personas. API smoke is not that UI gate.
Sending chat text invokes models: needs its own estimated-spend OK, shares $3/day
and must fit the approved lifetime/demo allowance. Do not run the legacy real
`serving_browser` in judge mode: it requires a smoke override that judge mode forbids.

### Non-allowlisted GitHub runner check

The existing main `azure-access.yml` expects **403**. For public mode, prepare an
audit-only branch of that existing dispatch workflow, run it once under the capped
Actions budget, then return to frozen main. No credential/OIDC/Key Vault access
is needed in the runner. The branch is never merged or exported. This procedure
is **prepared, not executed/verified here**. [GitHub dispatch/ref documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

```bash
export RB_PROBE_BRANCH="ops/submission-access-${RB_SHA:0:7}"
git -C "$RB_REPO" switch -c "$RB_PROBE_BRANCH" "$RB_SHA"
cat > .github/workflows/azure-access.yml <<'YAML'
name: submission-access
on:
  workflow_dispatch:
    inputs:
      web_url: {required: true, type: string}
      api_url: {required: true, type: string}
      owner_ipv4: {required: true, type: string}
permissions: {contents: read}
jobs:
  outside-owner-network:
    runs-on: ubuntu-latest
    timeout-minutes: 4
    steps:
      - name: Public web requires login; internal API is unavailable
        env:
          WEB_URL: ${{ inputs.web_url }}
          API_URL: ${{ inputs.api_url }}
          OWNER_IP: ${{ inputs.owner_ipv4 }}
        shell: bash
        run: |
          set -euo pipefail
          runner_ip=$(curl -fsS --max-time 30 https://api.ipify.org)
          test "$runner_ip" != "$OWNER_IP"
          test "$(curl -sS --max-time 120 -o /dev/null -w '%{http_code}' "$WEB_URL/")" = 200
          test "$(curl -sS --max-time 60 -o /dev/null -w '%{http_code}' "$WEB_URL/api/bff/transactions")" = 401
          test "$(curl -sS --max-time 60 -o /dev/null -w '%{http_code}' "$API_URL/healthz")" = 404
          echo 'Non-allowlisted runner: web=200, anonymous banking=401, internal API=404'
YAML
git -C "$RB_REPO" add .github/workflows/azure-access.yml
UV_CACHE_DIR="$RB_REPO/artifacts/uv-cache" PRE_COMMIT_HOME="$RB_REPO/artifacts/precommit-cache" git -C "$RB_REPO" commit -m 'chore(access): prepare isolated submission-day probe'
git -C "$RB_REPO" push origin "$RB_PROBE_BRANCH"
.venv/bin/python - <<'PY'
import json,os,subprocess
from scripts.azure_dev import az,GROUP,read_variables
urls={n:'https://'+az('containerapp','show','--resource-group',GROUP,
      '--name','ca-'+n+'-aclara-dev-eastus2')['properties']['configuration']['ingress']['fqdn'] for n in ['web','api']}
payload={'ref':os.environ['RB_PROBE_BRANCH'],'inputs':{
    'web_url':urls['web'],'api_url':urls['api'],'owner_ipv4':read_variables()['owner_ipv4']}}
subprocess.run(['gh','api','repos/sebastian-gm/factored-hackathon-2026-sebastian/actions/workflows/azure-access.yml/dispatches',
    '--method','POST','--input','-'],input=json.dumps(payload),text=True,check=True)
PY
git -C "$RB_REPO" switch main
test "$RB_SHA" = "$(git -C "$RB_REPO" rev-parse HEAD)"
gh run list --limit 10 --json databaseId,name,headBranch,headSha,status,conclusion
# Save the exact probe run ID, branch commit and success in the judge-mode receipt.
```

Expected dispatch accepted, exactly one successful `submission-access` run on the
probe branch, stated HTTP codes and runner different from owner IP. This proves
the external network boundary without handing a password to CI; authenticated
scope/UI checks above remain a separate gate. A portal/config-only assertion is
not a substitute. Stop if it fails; do not relax API ingress or authentication.

**Rollback B:** set judge=false, warm=false/min=0 and restore the previous smoke
binding if desired; make a fresh reviewed plan, apply and run standard owner-only
`azure_verify` plus main's 403/404 `azure-access`. OFF invalidates judge grants.
Separately disable both judge secret versions in Key Vault after ingress rollback
using `az keyvault secret set-attributes --subscription "$RB_SUB" --vault-name
kv-aclara-dev-eastus2 --name <judge-secret> --enabled false --query attributes.enabled
-o tsv` (each secret, no value output); expected false. Re-enable only by explicit OK.
Retain counters/audit. Secrets must be enabled again before a reviewed reactivation.

## 4. Audit the original history; publish only after Gate D

**Supersedes the former snapshot-export procedure (owner decision 2026-10-01).**
The original lab has been renamed to `factored-hackathon-2026-sebastian`, retaining
PRs, commits, releases and CI history. The old snapshot is privately archived as
`factored-hackathon-2026-sebastian-snapshot-archive`; never delete or refresh it.
Sebastian accepts historical email/hostname disclosure. No history rewrite or
second remote is permitted. Current-tree scrub, full-history gitleaks,
PR/comment and Actions-log/artifact audit, password rotation and reproduction
must finish per [public audit](public-release-audit.md) before Gate D.

```bash
export RB_SUBMISSION=sebastian-gm/factored-hackathon-2026-sebastian
test "$(gh api "repos/$RB_SUBMISSION" --jq .private)" = true
test "$RB_SHA" = "$(gh api "repos/$RB_SUBMISSION/commits/main" --jq .sha)"
git -C "$RB_REPO" status --porcelain
gitleaks git "$RB_REPO" --log-opts='--all' --redact --report-format json --report-path "$RB_OUT/full-history-secrets.json"
```

Expected: private, exact released main SHA, clean worktree, gitleaks exits 0.
This scan does not audit PR bodies or Actions logs; require their fresh evidence
in the public audit too. Run the README-only clean-clone reproduction with mock
fixtures, no organizer rows or provider keys, recording commands, time and skips.

**Only after Sebastian's explicit submission-day Gate D for this exact SHA:**

```bash
gh api "repos/$RB_SUBMISSION" --method PATCH -F private=false --jq '{name:.full_name,private:.private}'
test "$(gh api "repos/$RB_SUBMISSION" --jq .private)" = false
gh api "repos/$RB_SUBMISSION/branches/main/protection" --method PUT --input .github/main-protection.json --jq '{pr:.required_pull_request_reviews,checks:.required_status_checks.contexts,force:.allow_force_pushes.enabled,delete:.allow_deletions.enabled}'
curl -fsS -o /dev/null "https://github.com/$RB_SUBMISSION"
```

Expected: public repo accessible signed out; main protection requires PR and
`invariants`, `postgres`, `web`, disallows force pushes/deletion, enforces admins.
The private plan previously returned HTTP 403; apply protection immediately on
publication. Verify README, PRs, releases and tags from a logged-out browser;
no secrets, private credentials or bindings. Keep archived snapshot private.

Tag **v1.0.0 on the exact released SHA** only on submission day, after verification:

```bash
git -C "$RB_REPO" tag -a v1.0.0 "$RB_SHA" -m 'Aclara final submission release'
git -C "$RB_REPO" push origin refs/tags/v1.0.0
gh api "repos/$RB_SUBMISSION/git/ref/tags/v1.0.0" --jq .ref
gh release create v1.0.0 --repo "$RB_SUBMISSION" --title 'Aclara v1.0.0' --notes-file "$RB_OUT/submission-release-notes.md"
```

Prepare/review factual notes first, including post-v4 changes and official v4
limitations. If tag exists, verify its commit instead of overwriting. Expected:
release tag resolves to the exact image tag and deployed SHA.

**Rollback D:** only on explicit owner incident instruction, make repo private;
expect true, inform Sebastian, rotate any exposed credential and remediate/audit.
Privacy cannot retract downloads. Never delete the archived snapshot or rewrite
historical evidence. Publication failure stops submission until resolved.

## 5. Submission email — owner sends after Gate E

- [ ] Confirm `hackathon.admin@factored.ai` and deadline/format from current
  organizer email; this address is from [brief §2.3](../00-build-brief.md).
- [ ] Subject/team: `Factored Hackathon 2026 — Sebastian — Aclara`; solo entrant
  name and approved reply contact. No fictitious teammates or second/team repo.
- [ ] Public repo: `https://github.com/sebastian-gm/factored-hackathon-2026-sebastian`,
  exact tagged release SHA, reproducible fixture/mock README and exclusions.
- [ ] Deployed **web** URL obtained from the verified web ingress. No internal
  API/DB/Key Vault/provider URL or token is supplied as a judge endpoint.
- [ ] Six-slide exported deck/PDF and accessible video link, **≤3 minutes**;
  check final links/attachments signed out, permission scope, duration and hashes.
  Verify every number against official v4 aggregates; fixes/picker/redesign are
  post-v4, not reflected in those numbers. Human/PT limitations remain visible.
- [ ] Judge instructions: one account, password + simulated OTP once, choose
  MX-ES/CO-ES/AR-ES/PT speaker, ES explanation / PT choice-confirm / fraud-handoff
  stories as gated; separate confirmation/action OTP still apply. Login expiry
  can require signing in again. State synthetic demo, not real-bank service.
- [ ] **Deliver judge username/password privately through Sebastian's approved
  recipient/channel**, separate from public assets if appropriate. Retrieve the
  judge password from Key Vault using the authenticated portal; never put it in
  Git, slides, video, README, CI, chat, command history or plaintext attachments.
  Do not send owner/demo, DB, provider or Azure credentials. Simulated OTP is not
  independent MFA and there is no implemented extra access-code gate to advertise.
- [ ] Availability through Oct 16, contact for access issues, global usage cap,
  exact deployed/recording SHA and post-v4 disclosure. Do not advertise free-tier
  keys or promise unlimited calls.
- [ ] Sebastian reviews/sends by **18:00 COT Oct 4**; save send time, message ID
  and delivery confirmation privately. A draft/failed send is not “submitted.”

**Verification:** owner confirms delivery and all judge links work externally.
**Rollback E:** send a clearly labeled correction with approved updated links or
credentials; retain the original receipt. No email tool is invoked by this runbook.

## 6. Keep alive through October 16; close October 17

**Gate B covers only the approved availability window. Gate F covers retirement.**
Once daily, from the owner workstation, run mode-aware controls/budget readback,
check web login availability/replicas, Key Vault account enabled and provider
credit/budget **metadata only**. Check daily actual spend plus retained unknown
reserves; a daily-cap refusal is expected containment, not permission to refill.
No routine chat/model probe, evaluation rerun or new nightly paid job. Check
Azure billing/US$30–50 alert delivery (CAD conversion) and traffic/log exposure.
No scheduled resource/automation is created by this document.

Free provider/production metadata check, writing a **new receipt**, never
overwriting the official v4 preflight:

```bash
.venv/bin/python - <<'PY'
import json
from datetime import UTC,datetime
import httpx,psycopg
from scripts.azure_dev import ROOT,VAULT,az,private_write
from scripts.azure_migrate_ops import connection_string
from scripts.openrouter_preflight import inspect
try:
    key=az('keyvault','secret','show','--vault-name',VAULT,'--name','openrouter-api-key')['value']
    with httpx.Client(timeout=30,follow_redirects=False) as client: receipt=inspect(client,key)
    with psycopg.connect(connection_string('aclara_admin')) as db:
        db.execute('SET LOCAL ROLE aclara_owner')
        receipt['global_cap']=float(db.execute("SELECT daily_usd FROM llm.limits WHERE scope='production'").fetchone()[0])
        receipt['production_disabled']=db.execute("SELECT disabled FROM llm.limits WHERE scope='production'").fetchone()[0]
        receipt['day_charged_with_reserves_usd']=float(db.execute("SELECT coalesce(sum(charged_usd),0) FROM llm.reservations WHERE scope='production' AND day=%s",(datetime.now(UTC).date(),)).fetchone()[0])
    assert receipt['global_cap']==3 and not receipt['production_disabled']
    private_write(ROOT/('artifacts/submission-day/provider-budget-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%S')+'.json'),json.dumps(receipt)+'\n')
    print(json.dumps(receipt))
except Exception as error: raise SystemExit('Metadata check stopped: '+type(error).__name__) from None
PY
```

Expected cap=3, breaker enabled, numeric balances/costs only and zero calls.
This conservative `inspect` check stops when balance or key limit falls below
$4; do not top up or raise a provider limit automatically. Ask Sebastian what
availability allowance remains. A daily usage refusal is not a connectivity bug.

Escalate failures to Sebastian with sanitized status/class/counts only. Apply
Rollback B on suspicious access or unexpected spend; keep records. Availability
extension after the approved end, model allowance increase or new public asset
needs a new explicit OK. Do not silence audit, reclassify unknown costs or loosen
RLS/login/API ingress to repair the demo.

### F1. Preserve data, close judges, return to scale-to-zero

After **Oct 16 ends**, with Gate F:

```bash
printf '%s\n' '{"enable_judge_access":false,"enable_submission_warm":false,"min_replicas":0,"llm_budget_run_id":""}' > "$RB_OUT/retire.json"
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" inputs retire
PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" plan retire
RB_APPLY_APPROVED=1 PYTHONPATH="$RB_REPO" .venv/bin/python "$RB_OUT/tf.py" apply retire
.venv/bin/python -m scripts.azure_verify
gh workflow run azure-access.yml --repo sebastian-gm/factored-hackathon-2026-sebastian --ref main
```

Expected judge RBAC grants removed, both apps min=0/max=1, web owner rule restored,
API internal, standard controls passed and outside-owner **403/404**. Disable
judge secret versions as in Rollback B; old judge grants must fail. Retain the
public source repo/slides/video unless the organizer/owner explicitly approves
their removal. App compute falls to zero **when idle**, not immediately on input
change. Fixed DB/storage/registry remains about **$21.09/month**, plus KV/state/
logs/egress and any owner usage/model calls; scale-to-zero is not full teardown.

Optional DB stop **requires Gate F and ends live availability**:

```bash
az postgres flexible-server stop --subscription "$RB_SUB" --resource-group "$RB_RG" --name psql-aclara-dev-eastus2
az postgres flexible-server show --subscription "$RB_SUB" --resource-group "$RB_RG" --name psql-aclara-dev-eastus2 --query state -o tsv
```

Expected `Stopped`; compute saving about **$0.408/day** at today's B1ms rate.
Storage/backup and ACR/state/log costs continue. Azure automatically starts it
after **7 days**; set a human follow-up for Oct 24 or choose an approved deletion,
do not claim permanent savings. [Azure stop/start limits](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-limits).
Rollback stop: `az postgres flexible-server start --subscription "$RB_SUB"
--resource-group "$RB_RG" --name psql-aclara-dev-eastus2`, expect `Ready`, then
reverify TLS/non-owner DB, images, controls and owner-only login. Reopening public
access/warm replicas remains a separate new approval.

### F2. Irreversible teardown alternative

**Explicit destructive Gate F required for the exact resource inventory and
retention plan.** Not an automatic October 17 action. Terraform has PostgreSQL
`prevent_destroy=true`; do not remove that protection just to make `destroy` work.
The bootstrap resource group/state store are outside Terraform's runtime state.

1. First F1 closes judges. Preserve official results, receipts, append-only audit,
   serving data and durable cases/sessions/handoffs/budget records according to
   an approved private retention plan. Export encrypted DB backup with PostgreSQL
   16 tooling, independent restore verification, ciphertext checksum and securely
   retained encryption key; no raw dump/password or row output in Git/logs.
2. Privately export remote state/Blob versions and inventory. The current
   `scripts.backup_restore` is **local authored rehearsal only**, not an Azure
   backup command. Run the encrypted export below, then independently restore it
   and verify complete serving/ops/llm row digests, RLS and audit-chain integrity
   in an owner-approved **local disposable** database. A successful dump or
   `pg_restore --list` alone is not restore proof. These Azure backup/restore
   checks have **not been executed** in this preparation; stop deletion if their
   evidence/destination/retention approval is absent.
   Do not delete state while resources are still being managed or backups depend
   on this group. Backups must be retained outside the group being removed.

   Encrypted DB export recipe, **Gate F only**: install reviewed `age` and native
   PostgreSQL **16** client tools first. Sebastian supplies `RB_AGE_RECIPIENT`
   (public recipient) and retains its private decryption key outside Azure/the
   repo. Only encrypted bytes are written; no key is printed or generated here.

   ```bash
   test -n "${RB_AGE_RECIPIENT:-}"
   .venv/bin/python - <<'PY'
   import hashlib,json,os,subprocess
   from pathlib import Path
   from scripts.azure_dev import ROOT,VAULT,az,private_write
   target=ROOT/'artifacts/submission-day/aclara-final.pgdump.age'
   assert not target.exists()
   assert subprocess.check_output(['pg_dump','--version'],text=True).startswith('pg_dump (PostgreSQL) 16.')
   from scripts.azure_targets import database_host
   environment={**os.environ,'PGHOST':database_host(),
       'PGPORT':'5432','PGDATABASE':'aclara','PGUSER':'aclara_admin','PGSSLMODE':'verify-full',
       'PGSSLROOTCERT':'/etc/ssl/certs/ca-certificates.crt',
       'PGPASSWORD':az('keyvault','secret','show','--vault-name',VAULT,'--name','postgres-admin')['value']}
   # pg_dump's default row_security=off must succeed; never work around an RLS error.
   dump=subprocess.Popen(['pg_dump','--format=custom','--no-password'],env=environment,
       stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
   assert dump.stdout is not None
   encrypted=subprocess.run(['age','--recipient',os.environ['RB_AGE_RECIPIENT'],'--output',str(target)],
       stdin=dump.stdout,capture_output=True)
   dump.stdout.close(); dump_code=dump.wait()
   if encrypted.returncode or dump_code:
       target.unlink(missing_ok=True); raise SystemExit('Backup failed; deletion forbidden; details suppressed')
   target.chmod(0o600)
   private_write(ROOT/'artifacts/submission-day/backup-ciphertext.json',json.dumps({
       'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
       'restore_verified':False})+'\n')
   print('Encrypted backup created; independent restore NOT yet verified')
   PY
   # Retention-approved target/key paths only; no dump/restore stdout in public logs.
   # Gate F must include the retention destination and who can decrypt it.
   age --decrypt --identity "$RB_AGE_IDENTITY_FILE" "$RB_OUT/aclara-final.pgdump.age" | pg_restore --list > "$RB_OUT/backup-table-of-contents.private.txt"
   # REQUIRED before delete: independent full restore + digest/RLS/audit proof.
   # This stream performs the restore ONLY against a reviewed local empty database.
   age --decrypt --identity "$RB_AGE_IDENTITY_FILE" "$RB_OUT/aclara-final.pgdump.age" | PGSSLMODE=disable pg_restore --exit-on-error --no-owner --no-privileges --host 127.0.0.1 --port "$RB_RESTORE_PORT" --username "$RB_RESTORE_USER" --dbname "$RB_RESTORE_DATABASE" > "$RB_OUT/restore.private.log" 2>&1
   PYTHONPATH="$RB_REPO" .venv/bin/python - <<'PY'
   import os,subprocess
   from scripts.azure_dev import ROOT,terraform_environment,private_write
   p=subprocess.run(['terraform','-chdir=infra','state','pull'],cwd=ROOT,
       env=terraform_environment(),capture_output=True,text=True)
   assert p.returncode==0
   private_write(ROOT/'artifacts/submission-day/final-state.private.json',p.stdout)
   print('State exported privately; retain encrypted copy outside deleted resource group')
   PY
   age --recipient "$RB_AGE_RECIPIENT" --output "$RB_OUT/final-state.json.age" "$RB_OUT/final-state.private.json"
   rm "$RB_OUT/final-state.private.json"
   sha256sum "$RB_OUT/aclara-final.pgdump.age" "$RB_OUT/final-state.json.age"
   ```

   The local restore needs matching policy roles (no-login, no-bypass), a local
   admin supplied privately via `.pgpass`/environment, and sufficient disk; keep
   organizer records in ignored directories. Do not point it at the application
   DB or Azure. On any failure stop, retain encrypted receipts, and resolve the
   backup permission/restore issue without weakening production RLS. Copy and
   checksum the ciphertext/receipts to Sebastian's approved persistent retention
   destination before deletion. The age identity remains outside Git/cloud RG.

3. After backup/restore and separate deletion confirmation, inventory and delete
   **only the named sandbox group**:

   ```bash
   az resource list --subscription "$RB_SUB" --resource-group "$RB_RG" --query '[].{name:name,type:type}' -o table
   # Owner confirms every item belongs to this demo, with no retained dependency.
   az group delete --subscription "$RB_SUB" --name "$RB_RG" --yes
   az group exists --subscription "$RB_SUB" --name "$RB_RG" -o tsv
   ```

   Expected `false`, billing inventory no remaining active demo resources, no
   usable deployed links, retained encrypted backups/receipts still accessible.
   Key Vault soft-delete retention can prevent same-name recreation; do not purge
   it without another explicit approval. No partial `terraform destroy` retry.

**Rollback F2:** there is no undelete guarantee. Recovery means newly approved
resources/spend, trusted state/backup restore and full release/RLS/access checks;
it is not a rollback command. Deletion ends ongoing compute/storage/registry
charges for removed resources; historical bills, separately retained backups and
soft-deleted/retained resources may still have costs. Confirm billing readback.

## Evidence checklist and preparation limits

Keep an ignored mode-0600 receipt per step: approval reference/date/window, source
SHA and image digests, private plan hash/diff/apply outcome, control and network
run IDs, budget/cost metadata, four-profile API/browser checks, audited original history
SHA/ref inventory/Gitleaks config/hash/zero findings/negative controls, clean-clone
commands/counts/timings, send receipt and closure verification. Never attach raw
plans, state, credentials, bindings, row traces or audit payloads publicly.

Prepared and verified in this session: tracked Terraform fmt/validate, mocked
plans, fresh no-refresh/no-lock OFF/ON diff and live public price reads. Document
snippets are syntax-checked only. **Future activation, customer-map maintenance,
judge-mode external/auth/browser checks, final-main audit and encrypted Azure
backup/restore are not claimed as executed.** Missing prerequisites stop the
affected step; this runbook is not their approval or proof.
