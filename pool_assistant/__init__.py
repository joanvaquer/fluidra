"""Multi-agent technical assistant for pool technicians.

The files are numbered in the order they come into use, so each file only uses files with a
lower number (and the agents/ folder sits between 4_llm.py and 5_orchestrator.py):

    1_config  2_schemas  3_knowledge  4_llm  agents/  5_orchestrator  6_cli  7_webapp
    agents/:  0_common  1_triage  2_retriever  3_diagnostician  4_writer  5_verifier

Python's `import` can't use a name that starts with a number (`import 1_config` is a syntax
error), so the rule below lets every file be imported by its name without the number:
`from pool_assistant import config` loads 1_config.py, and
`from pool_assistant.agents.common import ...` loads agents/0_common.py.
"""

import sys
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
from pathlib import Path


class NumberedFiles:
    """Finds `pool_assistant.<name>` (or `pool_assistant.agents.<name>`) in the file `N_<name>.py`.

    Python asks it before its usual search; for any other name it answers None, and Python
    carries on as normal.
    """

    def find_spec(self, fullname: str, path=None, target=None) -> ModuleSpec | None:
        package, _, name = fullname.rpartition(".")
        if not package.startswith(__name__) or not path:
            return None  # not one of ours (path is the package's folder, for a module inside one)
        for folder in path:
            matches = sorted(Path(folder).glob(f"[0-9]_{name}.py"))
            if matches:
                return spec_from_file_location(fullname, matches[0])
        return None


sys.meta_path.insert(0, NumberedFiles())
