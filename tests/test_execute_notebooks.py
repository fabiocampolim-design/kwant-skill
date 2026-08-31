# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Execute both notebooks from a cold kernel and require zero errors.

Slow (about 6 minutes on a laptop) and needs the 'kwant' Jupyter kernel, so
it only runs when KWANT_NB_EXECUTE=1 is set (CI sets it).  The executed
copies are written to --basetemp and never touch the tracked notebooks.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [ROOT / "Kwant_Theory_and_Practice.ipynb", ROOT / "Kwant_Exercises_Solutions.ipynb"]

pytestmark = pytest.mark.skipif(os.environ.get("KWANT_NB_EXECUTE") != "1",
                                reason="set KWANT_NB_EXECUTE=1 to run the notebooks (slow)")


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=lambda p: p.stem)
def test_notebook_executes_clean(nb, tmp_path):
    out = tmp_path / nb.name
    cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
           "--ExecutePreprocessor.kernel_name=kwant",
           "--ExecutePreprocessor.timeout=1800", "--allow-errors",
           "--output", str(out), str(nb)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    assert r.returncode == 0, r.stderr[-2000:]
    executed = json.loads(out.read_text(encoding="utf-8"))
    errors = [(i, o.get("ename"), o.get("evalue")) for i, c in enumerate(executed["cells"])
              if c["cell_type"] == "code" for o in c.get("outputs", [])
              if o.get("output_type") == "error"]
    assert errors == []
    figs = sum(1 for c in executed["cells"] if c["cell_type"] == "code"
               for o in c.get("outputs", []) if "image/png" in o.get("data", {}))
    committed = json.loads(nb.read_text(encoding="utf-8"))
    committed_figs = sum(1 for c in committed["cells"] if c["cell_type"] == "code"
                         for o in c.get("outputs", []) if "image/png" in o.get("data", {}))
    assert figs == committed_figs, "a re-execution must reproduce every committed figure"
