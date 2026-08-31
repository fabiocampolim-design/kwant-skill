# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# --- BUILD-HISTORY GUARD ------------------------------------------------------
# This script was a one-shot step in assembling the notebooks (Aug 2026) and has
# already been applied.  Running it again would duplicate or overwrite cells.
# It is kept as a record of how the notebooks were built.  To run it anyway,
# set KWANT_NB_REBUILD=1 in the environment.
import os as _os, sys as _sys
if _os.environ.get("KWANT_NB_REBUILD") != "1":
    _sys.exit(__file__ + ": already applied; set KWANT_NB_REBUILD=1 to re-run (see dev/build-history/README.md)")
# -----------------------------------------------------------------------------
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Kwant_Theory_and_Practice.ipynb')
nb = json.load(open(PATH, encoding='utf-8'))

# --- cell 45: report the ordering MUMPS actually uses -----------------------
c45 = nb['cells'][45]
src = ''.join(c45['source'])
OLD = """try:
    import kwant.solvers.mumps as mumps
    mumps.options(nrhs=6, ordering='metis')
    print("using MUMPS")
except ImportError:
    print("MUMPS unavailable; using scipy sparse")"""
NEW = """try:
    import kwant.solvers.mumps as mumps
    # The nested-dissection orderings ('metis', 'scotch') are the good ones for
    # 2D lattices, but not every MUMPS build ships them.  Requesting an absent
    # ordering is NOT an error -- MUMPS silently falls back -- so let Kwant pick
    # the best one actually compiled in, and print what was really chosen.
    mumps.options(nrhs=6, ordering='kwant_decides')
    print(f"using MUMPS, ordering = {mumps.default_solver.ordering!r}")
except ImportError:
    print("MUMPS unavailable; using scipy sparse")"""
assert OLD in src, "cell 45 does not contain the expected MUMPS block"
src = src.replace(OLD, NEW)
lines = src.split('\n')
c45['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
c45['outputs'] = []
c45['execution_count'] = None

# --- cell 47: add the thread-safety pitfall ---------------------------------
c47 = nb['cells'][47]
src = ''.join(c47['source'])
assert c47['cell_type'] == 'markdown' and '## 16. Pitfalls' in src
ANCHOR = """**Rebuilding inside a loop.**"""
BULLET = """**`kwant.smatrix` is not thread-safe when MUMPS is installed.** Concurrent calls from a
thread pool corrupt MUMPS's internal state and segfault the interpreter -- in a notebook
that is the dreaded "kernel crashed" with no traceback. One solver instance per thread does
*not* help; the shared state is inside the MUMPS library. Threads: use
`kwant.solvers.sparse` (SuperLU, re-entrant). MUMPS in parallel: one process per worker.
See section 15 and `test_thread_safety.py`.

**Rebuilding inside a loop.**"""
assert ANCHOR in src and 'thread-safe' not in src
src = src.replace(ANCHOR, BULLET)
lines = src.split('\n')
c47['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

json.dump(nb, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print("patched cells 45 and 47")
