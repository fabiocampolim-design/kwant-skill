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

## Root-cause mechanism (added 2026-09-19, from reading python-mumps' actual source)

"MUMPS keeps library-global state" above was an inference, not a traced
mechanism. Reading `src/mumps/_mumps.pyx.in` and `src/mumps/mumps.py` at
python-mumps main (gitlab.kwant-project.org/kwant/python-mumps) narrows it:

- Each `<p>mumps` Cython object (`zmumps`/`dmumps`/...) owns a **per-instance**
  `PyThread_type_lock` (`self.lock`, allocated in `__cinit__`). `call()`
  acquires it around every `job`-dispatching call into the Fortran routine
  (`mumps.<p>mumps_c(&self.params)`). This only serializes calls **on the
  same instance** — it does nothing for two different instances (e.g. one
  per thread) calling into the library at once, which is exactly why
  "give each thread its own `Solver()`" does not help: the lock the library
  itself provides is the wrong granularity for the actual shared state
  (inside the Fortran/C library, not the Python object).
- **`__cinit__` (job=-1, instance creation) and `__dealloc__` (job=-2,
  instance teardown) do not acquire even that per-instance lock** — only
  `call()` (used for job=1/2/3/4/6, i.e. analyze/factor/solve) does.
- `mumps.py`'s `Context.set_matrix` creates a **new** `<p>mumps` Cython
  instance every time the dtype changes from the Context's previous state
  (`if self.dtype != dtype: self.mumps_instance = getattr(_mumps, dtype +
  "mumps")(...)`), and Kwant's `_factorized` (patch 0001) creates a **new**
  `MUMPSContext()` on every `kwant.smatrix` call — so every call constructs
  a fresh Cython instance (`__cinit__`, job=-1) and, when the caller's
  reference to the previous call's `Context` is dropped, destroys the old
  one (`__dealloc__`, job=-2).
- Kwant's patch 0001 lock (`_mumps_lock`) wraps `_factorized` (so the job=-1
  construction happens to be covered, since it occurs synchronously inside
  `MUMPSContext().factor(...)`) and wraps the `solve()` call inside
  `_solve_linear_sys`. **It does not, and structurally cannot from pure
  Python, wrap `__dealloc__`**: that call fires wherever CPython's reference
  counting happens to drop the `Context`'s last reference to zero — in
  `kwant.solvers.common.SparseSolver`, that is typically in the *caller's*
  frame, after `_solve_linear_sys` has already returned and released
  `_mumps_lock`. So an unlocked `job=-2` teardown in one thread can run
  concurrently with another thread's lock-protected but simultaneously
  in-flight `job=1/2/3` call in a different `<p>mumps` instance — both touch
  the same underlying Fortran-global MUMPS state, and only one side of that
  race holds any lock at all.

This is a plausible, source-traced explanation for the canary's "hung at
exit" outcomes (1.3.5/1.3.6 of the KWANT course project): a destructor race
at interpreter or thread-pool shutdown, not (only) a factor/solve race,
which the existing lock already prevents.

**Not verified**: whether this specific race is what actually produces the
observed segfault/hang (would need a targeted repro — e.g. forcing a
`Context.__exit__`/garbage-collection in one thread while another holds
`_mumps_lock` in a tight loop — which was not attempted; a false GC trigger
is hard to force deterministically and the existing canary already accepts
segfault/hang as evidence without needing to control timing precisely).

**Refined proposed fix**: extend patch 0001 so `kwant.solvers.mumps` never
lets a `Context` go out of scope without deterministically finalizing it
*inside* `_mumps_lock` first — e.g. `_factorized` returns a wrapper whose
`__del__`/explicit close calls `with _mumps_lock: inst.__exit__(None, None,
None)` before dropping the last reference — rather than relying on GC timing
to run `__dealloc__` at all, locked or not. The real fix (a module-level
lock inside python-mumps' own `__cinit__`/`__dealloc__`, or a documented
"do not let a Context die on a thread other than the one holding your own
lock" contract) belongs upstream in python-mumps, not in Kwant's wrapper;
worth a second, separate issue against `kwant/python-mumps` rather than
folding it into this one.
