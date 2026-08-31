# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Reproduce cell 46: concurrent kwant.smatrix from a ThreadPoolExecutor."""
import sys
import matplotlib
matplotlib.use("Agg")
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import kwant

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4

import kwant.solvers.mumps as mumps
mumps.options(nrhs=6, ordering='metis')   # exactly what cell 45 does
print("using MUMPS, workers =", WORKERS, flush=True)

# --- cell 7's system --------------------------------------------------------
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
    return kwant.smatrix(fsyst, e).transmission(1, 0)


print("serial reference...", flush=True)
ref = np.array([transmission(e) for e in energies])
print("serial OK", flush=True)

print("parallel sweep starting...", flush=True)
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    data_par = np.array(list(pool.map(transmission, energies)))
print("parallel finished", flush=True)
print("max |parallel - serial| =", np.abs(data_par - ref).max(), flush=True)
print("first five:", np.round(data_par[:5], 6), flush=True)
print("SURVIVED", flush=True)
