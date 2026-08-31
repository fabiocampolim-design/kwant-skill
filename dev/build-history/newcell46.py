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
NEW_46 = '''# --- Parallel parameter sweep -------------------------------------------------
# Energy points are independent, so an energy sweep is embarrassingly parallel.
# But HOW you parallelise it matters, and the obvious way crashes the kernel:
#
#   !!! NEVER call kwant.smatrix from several threads at once. !!!
#
# `kwant.smatrix` dispatches to MUMPS whenever MUMPS is installed, and MUMPS is
# not re-entrant: concurrent solves corrupt its internal state and abort the
# *process*.  In a notebook that surfaces as
#     "The Kernel crashed while executing code in the current cell..."
# It is a segfault, not a Python exception, so try/except cannot catch it, and
# giving each thread its own Solver() instance does not help either -- the
# shared state lives inside the MUMPS library, not in Kwant.
#
# Two safe options:
#   (a) threads + the SciPy/SuperLU solver, which IS re-entrant  -> shown below
#   (b) one process per worker, each with its own MUMPS          -> note at end

import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import kwant
import kwant.solvers.sparse as scipy_solver   # SuperLU: safe to call from threads

energies = np.linspace(0.01, 1.0, 64)


def transmission(e):
    # NOTE: scipy_solver.smatrix, *not* kwant.smatrix -- see the warning above.
    return scipy_solver.smatrix(fsyst, e).transmission(1, 0)


t0 = time.perf_counter()
data_serial = np.array([transmission(e) for e in energies])
t_serial = time.perf_counter() - t0

t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=4) as pool:
    data_par = np.array(list(pool.map(transmission, energies)))
t_par = time.perf_counter() - t0

assert np.allclose(data_par, data_serial), "parallel result disagrees with serial!"

print(f"serial     {t_serial:6.2f} s")
print(f"4 threads  {t_par:6.2f} s   ->  speedup x{t_serial / t_par:.2f}")
print("first five:", np.round(data_par[:5], 6))

# Do not be surprised if the speedup is close to 1x -- or even below it.
# SuperLU holds the GIL for much of the factorisation, and NumPy/SciPy are
# already linked against a multithreaded BLAS that is using every core, so
# Python-level threads mostly add contention.  Measure before you believe.
#
# For a genuine speedup on a long sweep, use PROCESSES.  On Windows the worker
# must be importable, so put it in a module (e.g. sweep_worker.py) rather than
# in a notebook cell, and drive it from a script:
#
#     # sweep_worker.py
#     import kwant
#     _F = None
#     def transmission(e):
#         global _F
#         if _F is None:
#             _F = make_wire()          # each process builds its own system
#         return kwant.smatrix(_F, e).transmission(1, 0)   # MUMPS is fine here:
#                                                          # one solver per process
#     # driver.py
#     from concurrent.futures import ProcessPoolExecutor
#     from sweep_worker import transmission
#     if __name__ == "__main__":                            # required on Windows
#         with ProcessPoolExecutor(max_workers=4) as pool:
#             data = list(pool.map(transmission, energies, chunksize=4))
'''

import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Kwant_Theory_and_Practice.ipynb')
nb = json.load(open(PATH, encoding='utf-8'))

cell = nb['cells'][46]
assert cell['cell_type'] == 'code', cell['cell_type']
assert 'ThreadPoolExecutor' in ''.join(cell['source']), "cell 46 is not the sweep cell"

lines = NEW_46.split('\n')
cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
cell['outputs'] = []
cell['execution_count'] = None

json.dump(nb, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print("cell 46 replaced")
