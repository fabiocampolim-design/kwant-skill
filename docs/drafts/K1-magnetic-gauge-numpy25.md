# DRAFT — K1: kwant 1.5.0 `magnetic_gauge` broken on numpy ≥ 2.5

> Status: **drafted 2026-08-28 — not sent.** Verified on this machine
> (kwant 1.5.0 conda-forge, numpy 2.5.1, scipy 1.18.0, Python 3.13.11,
> Windows 10). To be posted by the owner after review. Two venues, same text:
> (1) GitLab issue on kwant/kwant, (2) a short pointer on kwant-discuss,
> because the practical remedy (a release or a repodata pin) is a maintainer
> decision and the list is where Anton reads.

---

**Title:** `magnetic_gauge` fails for every 2-D system with numpy ≥ 2.5 in the released 1.5.0 — fix is on `main` but unreleased

## Description

With numpy 2.5.0 (released 2026-06-21) `numpy.cross` no longer accepts
2-dimensional vectors (deprecated in 2.0, removed in 2.5).
`kwant/physics/gauge.py` line 89 in the released 1.5.0 still does

```python
n = np.cross(v1, v2)
```

on 2-vectors, so `kwant.physics.magnetic_gauge` raises for any 2-D system:

```
ValueError: Both input arrays must be (arrays of) 3-dimensional vectors, but they are 2 and 2 dimensional instead.
```

`main` already has the fix (commit "fix numpy deprecation", 2025-01-26):

```python
n = np.cross(v1, v2) if len(v1) == 3 else v1[0] * v2[1] - v1[1] * v2[0]
```

but there has been no release since 1.5.0 (2024-06-19), and the 1.5.0
packages on conda-forge and PyPI do not pin `numpy<2.5`, so a fresh
`conda install kwant` today gives a broken `magnetic_gauge`. Kwant's own
test suite shows it: `physics/tests/test_gauge.py::test_phases[square-finite-1]`
fails with the same error.

## Steps to reproduce

```python
import kwant, numpy as np
print(kwant.__version__, np.__version__)      # 1.5.0 2.5.1
lat = kwant.lattice.square(norbs=1)
syst = kwant.Builder()
syst[(lat(i, j) for i in range(4) for j in range(4))] = 4
syst[lat.neighbors()] = -1
gauge = kwant.physics.magnetic_gauge(syst.finalized())   # raises
```

## Suggested remedies (either works for users)

1. Tag a 1.5.1 from `main` (the fix is a one-liner and `main` already
   targets SPEC-0 versions), or
2. add `numpy<2.5` to the run requirements of the existing 1.5.0 build on
   conda-forge via a repodata patch, and mark the PyPI metadata the same way.

Happy to open the conda-forge repodata-patch PR if that is the preferred
route.

## Environment

kwant 1.5.0 (conda-forge, win-64), python-mumps 0.0.6, numpy 2.5.1,
scipy 1.18.0, Python 3.13.11, Windows 10.
