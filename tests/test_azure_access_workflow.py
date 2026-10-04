"""Check the credential-free boundary and temporary-capability runner contract."""

from pathlib import Path

import yaml


def test_authenticated_access_probe_matches_bff_logout_and_never_uses_password():
    workflow = yaml.safe_load(Path(".github/workflows/azure-access.yml").read_text())
    probe = workflow["jobs"]["outside-owner-network"]["steps"][1]
    assert "inputs.mode == 'judge'" in probe["if"]
    assert "inputs.authenticated_judge" in probe["if"]
    assert set(probe["env"]) == {"WEB_URL", "JUDGE_CONTROLLER"}
    script = probe["run"].split("python - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    compile(script, "authenticated-access-probe", "exec")
    assert "logout['signed_out']" in script
    assert "logout['verified']" not in script
    assert "request('me')[0] == 401" in script
    assert "request('auth/judge/profile', {'profile_id': 'mx-es'})" in script
    assert "request('transactions')" in script
    assert "finally:" in script
    assert "::add-mask::" in script
    assert "auth/login" not in script and "messages" not in script
