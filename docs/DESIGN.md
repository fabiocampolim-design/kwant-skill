# Design notes — Kwant: Theory and Practice

What this repository is trying to be, the decisions that shaped it, what each one cost,
and what was rejected. `README.md` is the product page and `AGENTS.md` the inventory; this
file is the *why*. Who decided what is stated in the CRediT table of the README
("How it was built"): scope, models, presentation and every publication call are the
author's; numerical methods and diagnoses were proposed by the AI assistant and kept only
after the author checked them.

## 1. The problem framing

The Kwant tutorial teaches the API; topocondmat.org teaches topological band theory;
neither puts the derivation, the code and a numerical check side by side for the same
model. This course does exactly that, for quantum transport first (Part I) and then ten
topological models (Part II), with every one of its 68 figures produced live by a
notebook cell and 25 exercises solved and asserted. The target reader is an advanced
undergraduate or a beginning graduate student with Python; the course deck and handout
exist so a lecturer can teach from it without reading the notebooks first.

## 2. Decisions and their trade-offs

| Decision | Why | What it costs / what was rejected |
|---|---|---|
| **Executed notebooks are the unit.** Every figure is a cell output, never pasted; counts of cells, figures and exercises are asserted by the suite and repeated in the prose. | A course whose figures cannot be regenerated cannot be trusted or maintained. | Re-executing all fifteen notebooks takes ~7 minutes on kernel `kwant`; a figure added to chapter *k* shifts the numbering of every later chapter (guarded by `tests/test_notebooks.py`). |
| **Chapter notebooks under 1 MB, each with its own table of contents, figure numbers continuous across chapters** (1.3.0, 2026-09-01). | The two monolithic notebooks reached 7.4 MB with outputs and crashed editors and sessions. | A reader loses the single-file overview; `chapters/00_Contents.ipynb` and the README index replace it. Rejected: stripping outputs (then the figures are not in the record). |
| **Kwant 1.5 pinned, conda-forge only, `numpy<2.5`, `python-mumps` optional.** | pip builds of Kwant are unreliable on Windows; `magnetic_gauge` breaks on newer NumPy; MUMPS is 5–10× faster than SuperLU. | The course lags upstream by design; the Kwant tutorial is the authority for the current API. |
| **No threads around the solver.** `kwant.smatrix` and `kwant.greens_function` are never called from several threads; `test_thread_safety.py` guards it. | MUMPS is not re-entrant: a threaded energy sweep segfaulted the kernel (August 2026) and the diagnosis took a day. | Sweeps run serially or in processes; the SuperLU solver is the threaded fallback. |
| **Installation is proved by physics, not by a version banner.** `verify_kwant.py` checks quantised conductance, unitarity and a sum rule. | A Kwant that imports but computes wrong transport is the failure mode that matters. | One more script to maintain; a wrong pin shows up as a physics failure, which is the point. |
| **The course deck is linear, single-level arrow navigation, with a committed PDF fallback.** | Two-level navigation lost the audience in review; a lecturer must be able to present without a browser. | The deck is regenerated and the PDF re-committed at every content change (a test counts its pages). |
| **Public history is a sanitized branch** (`public`, two commits), not the study repository's history. | The study repo carries upstream clones, drafts and withheld material; rule 3 and rule 18 of the publishing playbook forbid them in published history. | Contributors see a short history; the full one is private. Rejected: rewriting the study history in place. |
| **Apache-2.0 for the course, licence-by-origin in `NOTICE`, explicit non-affiliation with the Kwant project.** | Kwant is BSD; nothing of it is vendored; the trademark is used only to name the program taught. | Findings for Kwant go upstream as issues and merge requests under the author's identity, never from this repository. |
| **Weekly upstream watch by a local scheduled script** (`scripts/watch_upstream.py`, `docs/watch/`). | A pinned course must know when upstream moves. | A report per week to read; nothing is filed automatically. |

## 3. What is deliberately out of scope

Production transport calculations (large sparse systems, KPM at scale — see the
comparison table in the README), a general topological-invariant library (Z2Pack,
WannierBerri), and any Kwant feature beyond 1.5. Part II is the computational companion
to a topology course, not a replacement for one.

## 4. Open questions

The three findings prepared for the Kwant project (see `docs/02-findings-backlog.md`)
await the author's upstream contact. A Linux/macOS installer equivalent to
`install_kwant_windows.ps1` is roadmap. Requests for figure permissions and the
translated READMEs follow the portfolio-wide pins.
