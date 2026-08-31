# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import time
import matplotlib
matplotlib.use("Agg")
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import kwant
import kwant.solvers.sparse as scipy_solver
import kwant.solvers.mumps as mumps_solver

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


def bench(label, fn):
    fn()                      # warm up
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    print(f"{label:<34s} {dt:7.3f} s   T[0]={out[0]:.6f}", flush=True)
    return np.asarray(out)


ref = bench("serial   MUMPS",
            lambda: [mumps_solver.smatrix(fsyst, e).transmission(1, 0) for e in energies])
bench("serial   SciPy/SuperLU",
      lambda: [scipy_solver.smatrix(fsyst, e).transmission(1, 0) for e in energies])

for n in (2, 4, 8):
    def run(n=n):
        with ThreadPoolExecutor(max_workers=n) as pool:
            return list(pool.map(
                lambda e: scipy_solver.smatrix(fsyst, e).transmission(1, 0), energies))
    got = bench(f"{n} threads SciPy/SuperLU", run)
    assert np.abs(got - ref).max() < 1e-9, "results diverged!"

print("all parallel results match serial MUMPS to <1e-9", flush=True)
