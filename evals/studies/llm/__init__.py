"""Historical language studies, available from a development checkout only."""

import sys

from evals.studies.llm import dev_robustness_cases

# The frozen round-two builder hashes its own source and imports this historical
# name. Keep both builder files byte-identical, with this sole offline alias.
# Nothing in aclara or the API image imports this package or installs the alias.
sys.modules.setdefault("aclara.llm.dev_robustness_cases", dev_robustness_cases)
