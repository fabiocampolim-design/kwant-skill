# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Does giving each thread its own kwant MUMPS Solver help?  Or a lock?"""
import sys
import threading
import matplotlib
matplotlib.use("Agg")
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import kwant
import kwant.solvers.mumps as mumps

MODE = sys.argv[1]  # "per-thread-solver" | "locked"

a, t, W, L = 1.0, 1.0, 10, 30
lat = kwant.lattice.square(a, norbs=1)
syst = kwant.Builder()
syst[(lat(x, y) for x in range(L) for y in range(W))] = 4 * t
syst[lat.neighbors()] = -t
lead = kwant.Builder(kwant.TranslationalSymmetry((-a, 0)))
lead[(lat(0, j) for j in range(W))] = 4 * t
lead[lat.neighbors()] = -t
syst.attach_lead(lead)
syst.attach_lead(lead.reversed())
fsyst = syst.finalized()

energies = np.linspace(0.01, 1.0, 64)
_local = threading.local()
_lock = threading.Lock()


def transmission(e):
    if MODE == "per-thread-solver":
        solver = getattr(_local, "solver", None)
        if solver is None:
            solver = _local.solver = mumps.Solver()
        return solver.smatrix(fsyst, e).transmission(1, 0)
    else:  # locked
        with _lock:
            return mumps.smatrix(fsyst, e).transmission(1, 0)


print("mode =", MODE, flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:
    data = np.array(list(pool.map(transmission, energies)))
print("SURVIVED  first five:", np.round(data[:5], 6), flush=True)
