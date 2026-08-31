# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Is process-based parallelism a working alternative on Windows?"""
import os
import pickle
import time
import numpy as np
import kwant


def make_wire(W=30, L=120, t=1.0):
    lat = kwant.lattice.square(1.0, norbs=1)
    syst = kwant.Builder()
    syst[(lat(x, y) for x in range(L) for y in range(W))] = 4 * t
    syst[lat.neighbors()] = -t
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1.0, 0)))
    lead[(lat(0, j) for j in range(W))] = 4 * t
    lead[lat.neighbors()] = -t
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()


_FSYST = None


def transmission(e):
    global _FSYST
    if _FSYST is None:
        _FSYST = make_wire()
    return kwant.smatrix(_FSYST, e).transmission(1, 0)


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor

    fsyst = make_wire()
    try:
        blob = pickle.dumps(fsyst)
        print(f"finalized system IS picklable ({len(blob)/1024:.0f} KiB)")
    except Exception as exc:
        print("finalized system NOT picklable:", type(exc).__name__, exc)

    energies = np.linspace(0.01, 1.0, 32)

    t0 = time.perf_counter()
    ref = np.array([kwant.smatrix(fsyst, e).transmission(1, 0) for e in energies])
    t_serial = time.perf_counter() - t0
    print(f"serial (MUMPS)            {t_serial:6.2f} s")

    for n in (2, 4):
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=n) as pool:
            got = np.array(list(pool.map(transmission, energies, chunksize=4)))
        dt = time.perf_counter() - t0
        ok = np.abs(got - ref).max()
        print(f"{n} processes (MUMPS)       {dt:6.2f} s   speedup x{t_serial/dt:.2f}   maxdiff={ok:.2e}")

    print("SURVIVED, cpus =", os.cpu_count())
