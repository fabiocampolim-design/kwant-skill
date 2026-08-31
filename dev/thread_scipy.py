# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Same threaded sweep, but forced onto kwant's SciPy (SuperLU) solver."""
import matplotlib
matplotlib.use("Agg")
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import kwant
import kwant.solvers.sparse as sparse_solver

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


def transmission(e):
    return sparse_solver.smatrix(fsyst, e).transmission(1, 0)


print("scipy solver, serial reference...", flush=True)
ref = np.array([transmission(e) for e in energies])
print("serial OK", flush=True)
print("parallel sweep (4 threads)...", flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:
    data = np.array(list(pool.map(transmission, energies)))
print("max |parallel - serial| =", np.abs(data - ref).max(), flush=True)
print("SURVIVED", flush=True)
