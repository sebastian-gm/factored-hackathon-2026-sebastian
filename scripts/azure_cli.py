#!/usr/bin/env python3
"""Force Terraform's CLI credential helper to the approved sandbox subscription.

Azure CLI --tenant alone can choose a different cached account when several identities
are signed in. Select the subscription instead; its tenant is checked against local inputs.
This executable is linked as `az` only in the Terraform subprocess PATH.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.azure_dev import SUBSCRIPTION, read_variables  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ["version", "--version"]:
        os.execv("/usr/bin/az", ["az", *args])  # noqa: S606
    if args[:2] == ["account", "list"]:
        # The provider enumerates accounts; expose only the approved subscription.
        result = subprocess.run(  # noqa: S603 -- fixed Azure CLI command and sandbox name
            ["/usr/bin/az", "account", "show", "--subscription", SUBSCRIPTION, "-o", "json"],
            check=True,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(json.dumps([json.loads(result.stdout)]))
        return
    values = read_variables()
    for flag in ["--tenant", "-t"]:
        if flag in args:
            index = args.index(flag)
            if args[index + 1] != values["tenant_id"]:
                raise SystemExit("Terraform requested a different tenant")
            del args[index : index + 2]
    if "--subscription" in args:
        selected = args[args.index("--subscription") + 1]
        if selected not in [SUBSCRIPTION, values["subscription_id"]]:
            raise SystemExit("Terraform requested a different subscription")
    else:
        args += ["--subscription", SUBSCRIPTION]
    os.execv("/usr/bin/az", ["az", *args])  # noqa: S606


if __name__ == "__main__":
    main()
