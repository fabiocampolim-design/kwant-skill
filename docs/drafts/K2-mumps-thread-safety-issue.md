# DRAFT — K2: threaded `kwant.smatrix` segfaults with the MUMPS solver

> Status: **drafted 2026-08-28 — not sent.** Bug reproduced 2026-08-20 and
> again today; fix + test + docs prepared as
> `docs/drafts/patches/0001-solvers.mumps-serialize-calls-into-MUMPS-which-is-no.patch`
> and validated against the installed 1.5.0 (patched module loaded in place:
> 3/3 threaded runs identical to serial; unpatched control crashes).
> Venue: GitLab issue on kwant/kwant, then the patch as a merge request from a
> fork (or `git send-email`-style to kwant-discuss, which CONTRIBUTE.rst also
> accepts). The owner posts after review; the MR must go out under their GitLab
> account.

---

**Title:** Calling `kwant.smatrix` from several threads segfaults the process when MUMPS is installed

## Description

Kwant releases the GIL around the heavy numerical work, and energy points of
a transport sweep are independent, so the obvious way to speed up a sweep is

```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as pool:
    T = list(pool.map(lambda e: kwant.smatrix(fsyst, e).transmission(1, 0), energies))
```

With MUMPS installed (`kwant.solvers.default` → `kwant.solvers.mumps`) this
kills the interpreter with a segmentation fault within the first few solves.
There is no Python exception to catch; in Jupyter it surfaces as "The Kernel
crashed while executing code in the current cell". MUMPS keeps
library-global state and is not re-entrant, so this happens even when every
thread uses its own `kwant.solvers.mumps.Solver()` (and hence its own
`MUMPSContext`). Serializing the calls into MUMPS behind a `threading.Lock`
makes the same code run correctly; `kwant.solvers.sparse` (SuperLU) is
unaffected.

Nothing in the documentation says that the MUMPS solver may not be used
from several threads; the word "thread" does not occur in the docs.

## Steps to reproduce

```python
import numpy as np, kwant
from concurrent.futures import ThreadPoolExecutor
import kwant.solvers.mumps   # make sure MUMPS is the solver in use

lat = kwant.lattice.square(norbs=1)
syst = kwant.Builder()
syst[(lat(x, y) for x in range(30) for y in range(10))] = 4
syst[lat.neighbors()] = -1
lead = kwant.Builder(kwant.TranslationalSymmetry((-1, 0)))
lead[(lat(0, y) for y in range(10))] = 4
lead[lat.neighbors()] = -1
syst.attach_lead(lead); syst.attach_lead(lead.reversed())
fsyst = syst.finalized()

def T(e): return kwant.smatrix(fsyst, e).transmission(1, 0)
with ThreadPoolExecutor(max_workers=4) as pool:
    print(list(pool.map(T, np.linspace(0.01, 1.0, 64))))
```

→ segmentation fault (exit code 0xC0000005 on Windows) in the first second.
Replace `kwant.smatrix` by `kwant.solvers.sparse.smatrix` and it completes
with results identical to a serial loop.

## Proposed fix

Guard the two entry points into MUMPS in `kwant/solvers/mumps.py`
(`Context.factor` in `_factorized`, `Context.solve` in `_solve_linear_sys`)
with one module-level lock. Threads still overlap in the GIL-free parts of
assembling the linear system; the solves run one at a time, which is the
only correct behaviour available without an MPI build of MUMPS. The attached
patch also adds a threaded-vs-serial test to `solvers/tests/test_solvers.py`
(skips when MUMPS is absent), a paragraph on the `kwant.solvers.mumps`
reference page pointing users to processes for real parallelism, and a
whatsnew entry.

## Environment

kwant 1.5.0 (conda-forge, win-64), python-mumps 0.0.6, numpy 2.5.1,
scipy 1.18.0, Python 3.13.11, Windows 10. Reproducible on every run.
