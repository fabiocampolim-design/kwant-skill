# Upstream audit — Kwant (S1/S2 pass, 2026-08-28)

Scope: what the upstream project looks like right now, what our local
environment does against it, and whether the three findings made while
building the notebooks are new. Playbook: the owner's publishing playbook, kept outside this repo
(study-and-contribute S1–S3). Everything below was verified today.

## 1. Upstream state

| Item | Value |
|---|---|
| Canonical repo | https://gitlab.kwant-project.org/kwant/kwant (GitHub is a mirror) |
| Local clone | `upstream/kwant` (gitignored, shallow `--depth 200`) |
| Latest release | **v1.5.0, tagged 2024-06-19** — no release since |
| `main` head | `ef12fa0` 2026-01-09 (Anton Akhmerov, "build-improvements") |
| Activity | Effectively single-maintainer (Akhmerov). Bursts: Sep–Oct 2025 (SPEC-0: drop numpy<2 / scipy<1.12, drop py3.11, test 3.14, "stop using deprecated numpy API"), Jan 2026 (pixi build, meson) |
| Open issues | 32 (oldest 2019); recent: #447 lead plotting (2026-01), #446 max supported versions, #445 MUMPS stability, #444 Ubuntu 24.04, #443 Peierls convention |
| Open MRs | 12, mostly Akhmerov drafts; **!424 "switch MUMPS solver to Schur"** (2026-01-04, 2.8x speedup) is the live one |
| python-mumps | separate project `kwant/python-mumps`; 33 issues; **#30 "Ensure repeated sparse/dense solves work"** (2026-01-05), **#25 "Catch exit calls"** (MUMPS calls `exit()`), #21 "Explore releasing GIL" (closed) |
| Contributing | `CONTRIBUTE.rst` → https://kwant-project.org/contribute : issues on GitLab; MRs via GitLab fork **or** `git format-patch` mailed to the list; PEP 8, NumPy docstrings, tests required, 72-char commit summaries; external contributions are credited explicitly |
| Community | kwant-discuss@python.org (archive https://mail.python.org/archives/list/kwant-discuss@python.org/, join via kwant-discuss-join@python.org); kwant-announce@python.org; Gitter kwant-project/Lobby. Traffic is low (about 1 thread/month; last: "Kwant on colab", 2026-06-18) |

Sources **not yet read end-to-end** (S2 checklist, open): full issue backlog
(only keyword searches so far), MR review threads, Gitter history, the
kwant-discuss archive in full (only keyword searches), the website beyond
docs (authors/citing pages came back EMPTY in the 2026-08-15 mirror —
re-mirror with a different fetcher), sister projects tkwant / qsymm /
kwant-spectrum.

## 2. Local environment vs upstream test suite

`python -m pytest --pyargs kwant -x` (installed kwant 1.5.0, numpy 2.5.1,
scipy 1.18.0, python-mumps 0.0.6, Python 3.13.11; plotter tests deselected):

**160 passed, 4 skipped, 1 xfailed, 1 FAILED** —
`physics/tests/test_gauge.py::test_phases[square-finite-1]`:
`ValueError: Both input arrays must be (arrays of) 3-dimensional vectors, but they are 2 and 2 dimensional instead.`

Runtime confirmation (not just a test artefact):

```python
kwant.physics.magnetic_gauge(square_2d_system)   # -> same ValueError
```

Cause: `kwant/physics/gauge.py:89` calls `np.cross(v1, v2)` on 2-D vectors.
NumPy deprecated 2-D inputs to `cross` in 2.0 and **removed them in 2.5.0
(2026-06-21)**. Upstream `main` already guards it
(`np.cross(v1, v2) if len(v1) == 3 else v1[0]*v2[1] - v1[1]*v2[0]`, commit
"fix numpy deprecation", 2025-01-26) — **but that fix has never been
released**: every conda-forge / pip user of kwant 1.5.0 with numpy >= 2.5 has
a broken `magnetic_gauge` for 2-D systems. The notebook is not affected (it
only mentions `magnetic_gauge` in markdown; the Hofstadter/QHE cells use
explicit Peierls phases). Backlog item **K1**.

## 3. Novelty check of our three build-time findings

| # | Finding | Tracker / list / main | Verdict |
|---|---|---|---|
| F1 | **MUMPS is not re-entrant**: `kwant.smatrix` from a `ThreadPoolExecutor` segfaults the process (confirmed 2026-08-20; `test_thread_safety.py`, repro `dev/thread_repro.py`); per-thread `Solver()` instances do not help; a `threading.Lock` does | GitLab issues: nothing on thread / segfault / re-entrancy (searches "thread", "segfault", "mumps"). kwant-discuss: 0 results for "thread MUMPS crash". python-mumps: #30 (repeated sequential solves corrupt params) and #25 (`exit()` calls) are adjacent, not the same. **Kwant docs never mention threads** (grep of `doc/source`: 0 hits for GIL / thread / multiprocess). | **Novel and unreported.** Best contribution: (a) kwant-discuss post + issue with the repro, (b) docs MR adding a "parallelism" note (processes, not threads) to the solvers page, (c) optionally a lock inside `kwant.solvers.mumps` |
| F2 | `kwant.plot(site_color=callable)`: the callable receives `Site` objects for a `Builder` but **integer site indices** for a finalized system | Documented behaviour, not a bug: `plotter.py:790` docstring; FAQ / graphene tutorial only show the Builder form. Issue #293 (site_size array, closed) is the same asymmetry for arrays. | **Not a bug; a docs gap.** One-paragraph FAQ clarification MR is a low-risk first contribution |
| F3 | `kwant.wraparound` momenta are phases across the primitive vectors (2π-periodic natively); reparametrising via reciprocal vectors is fine for Chern *totals* but not point-wise periodic → contaminates local Berry curvature at the torus seam | #428 (open, 2023: cryptic error when k_x missing), #137 (open: factor BZ logic out), #209 (closed: document pseudo-inverse in plotter) — all about wraparound coordinate conventions, none about this. Docstring `Notes` only says wraparound is stop-gap until Kwant 2.x. | **Novel as a documented pitfall**, not a bug. Candidate for the wraparound docstring / FAQ, attached to #137 |

Also found today, ours to fix: the notebook markdown says "Kwant 1.5 added
`magnetic_gauge`" — it was 1.4. Backlog N1.
