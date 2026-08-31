# Kwant — Theory and Practice

[![Tests](https://github.com/fabiocampolim-design/kwant-theory-and-practice/actions/workflows/tests.yml/badge.svg)](https://github.com/fabiocampolim-design/kwant-theory-and-practice/actions/workflows/tests.yml)
[![Kwant 1.5](https://img.shields.io/badge/Kwant-1.5-blue)](https://kwant-project.org)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#installation)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

**A complete, executed course on quantum transport with [Kwant](https://kwant-project.org)
in one Jupyter notebook — the physics, the numerics and the API side by side —
with a solutions notebook for its 25 exercises and a one-command Windows
installer.**

> **Feedback is highly appreciated.** This is a course, so the most valuable
> reports are the ones a reader can make: a derivation that skips a step, a
> figure whose caption does not match what you see, an exercise whose solution
> you disagree with, a cell that fails on your installation. Please
> [open an issue](https://github.com/fabiocampolim-design/kwant-theory-and-practice/issues)
> with the section number.

**Why this exists.** Kwant's own tutorial teaches the API on toy systems and
assumes you already know the scattering theory behind `smatrix`;
topocondmat.org teaches topology beautifully but treats the code as a black
box. Learning quantum transport *and* Kwant at the same time meant keeping
three documents open and reconciling them by hand. This notebook is that
reconciliation, written down once: every section states the theory, then
builds the system and computes the quantity the theory predicts, and the two
are compared in the same cell — 68 figures, all generated live, none pasted
in. It was built as part of a condensed-matter physics PhD and is the
foundation the author's own research code is written on, which is where a
course either survives contact with real research or does not.

## Quick start

```bash
# Windows: one command (installs Miniforge if needed, creates env "kwant", registers the kernel)
install_kwant_windows.bat

# Linux / macOS / an existing conda
conda create -n kwant -c conda-forge kwant "numpy<2.5" scipy matplotlib sympy python-mumps ipykernel jupyterlab
conda activate kwant
python -m ipykernel install --user --name kwant --display-name "Python (kwant)"

# then, on every platform
python verify_kwant.py             # proves the installation with physics identities
jupyter lab Kwant_Theory_and_Practice.ipynb
```

Run-All takes about 4½ minutes for the main notebook and 2 minutes for the
solutions on a laptop (with MUMPS). Full reference: [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md)
(also as [HTML](docs/USER_MANUAL.html) and [PDF](docs/USER_MANUAL.pdf)) lists every
section, every feature and every known limitation. Working with an AI agent?
Hand it [`AGENTS.md`](AGENTS.md). Changes are in [`CHANGELOG.md`](CHANGELOG.md).

## What is in the course

**Part I — Kwant and transport theory (sections 1–16).** Discretising the
Schrödinger equation; the object model (`Builder`, sites, symmetries); a first
quantum wire and the conductance staircase; Landauer–Büttiker and Fisher–Lee
derived and then checked numerically (unitarity, sum rule); shapes and runtime
parameters; spin and Rashba; band structures and closed systems; graphene;
BdG superconductivity and Andreev reflection with the discrete symmetries;
density and current operators; visualisation; the kernel polynomial method;
`kwant.continuum`; Peierls phases, Landau levels and the Hofstadter butterfly;
solvers, performance, and how *not* to parallelise; a section of pitfalls.

**Part II — Topological matter (17–26).** Ten models, each with its
invariant computed from the Kwant system itself: SSH (winding), Kitaev chain
(Pfaffian), the Majorana nanowire as a device, the Thouless pump, Haldane
(Chern number by Fukui–Hatsugai–Suzuki and a 3D Berry-curvature plot),
Kane–Mele (Z₂ and the helical edge), p+ip (chiral Majorana edges and vortex
modes), the BBH quadrupole, Weyl semimetals (Fermi arcs from sliced Chern
numbers), the 3D topological insulator (surface Dirac cone).

**Exercises.** 25, at the end of each part, flagged by origin (Kwant tutorial,
topocondmat.org, Asbóth *et al.*, original) and difficulty (◦ • ★); two are
pencil-and-paper. `Kwant_Exercises_Solutions.ipynb` works every one with 31
`assert`s encoding the expected physics. Physics found while validating them:
m₀ = 2 is an exact one-layer-surface sweet spot of the
3D TI model; the vortex-core–edge Majorana splitting oscillates as
cos(k_F R)·exp(−R/ξ).

## Features

- **Executed, and re-executable** — every figure and printed number in the
  repository comes from a cold-kernel run; the test suite re-runs both
  notebooks and requires zero errors and the same figure count.
- **Theory next to the check** — each derivation ends in a cell that computes
  the predicted quantity and compares (S-matrix unitarity to 1e-14, T + R = N,
  Chern numbers as exact integers, Majorana zero-mode energies down to 1e-8).
- **Topological invariants from the Kwant system** — winding numbers,
  Pfaffians, Fukui–Hatsugai–Suzuki Chern numbers, Z₂, sliced Chern numbers for
  Weyl points — all computed from `hamiltonian_submatrix` / `wraparound`, not
  from separate analytic formulas.
- **An undergraduate course** (`course/`): a linear reveal.js deck of 10 sections / 79 slides
  with speaker notes, a landscape PDF of the whole deck as a projector fallback, an A4
  handout and lecturer notes — all 68 figures of the notebook appear, each under its full
  caption, extracted by `course/build_course.py`.
- **25 exercises with asserted solutions** — origin- and difficulty-flagged;
  the solutions notebook is a second, independent executed document.
- **A pitfalls section learned the hard way** — `kwant.smatrix` from several
  threads segfaults when MUMPS is installed (MUMPS is not re-entrant): the
  notebook explains it, `test_thread_safety.py` guards it, and a patch was
  prepared for the Kwant project (`docs/drafts/`).
- **Windows installer that verifies itself** — conda-forge based, registers
  the kernel the notebooks expect, ends with a real transport calculation.
  `verify_kwant.py` checks any installation with physics identities and
  writes an audit log and JSON summary.
- **Standard-library CLIs, logs and a test suite** — both scripts expose every
  input and output on the command line; `tests/` asserts the notebooks'
  invariants (kernel, error-free, counts, 1:1 exercises↔solutions, no personal
  data); CI on Linux and Windows.

## How this compares

| | This course | [Kwant tutorial](https://kwant-project.org/doc/1/tutorial/) | [topocondmat.org](https://topocondmat.org) | [PythTB examples](https://www.physics.rutgers.edu/pythtb/examples.html) |
|---|---|---|---|---|
| Purpose | learn transport theory *and* Kwant together | learn the Kwant API | learn topological band theory | learn tight-binding band structure |
| Theory derivations | yes, next to the code | minimal | yes, lecture-style | minimal |
| Transport (leads, S-matrix) | central | central | occasional | none (no leads) |
| Topological invariants computed | 10 models, all invariants numerical | none | most, in separate notebooks | Berry phase / Chern examples |
| Exercises with solutions | 25 / 25 | none | many, no solutions published | — |
| Maintained by | one author | the Kwant team (authoritative) | TU Delft team | PythTB team |

**Use the Kwant tutorial instead** when you need the authoritative, always-current
description of an API call — this course pins Kwant 1.5 and will lag. **Use
topocondmat.org instead** for the full lecture course on topology with videos;
Part II here is the computational companion, not a replacement. **Use PythTB**
if you have no leads and want the simplest tight-binding band structure code.

## Known limitations and roadmap

- **Windows installer only.** Linux/macOS get the three conda lines above; a
  shell installer with the same self-verification is on the list.
- **`numpy<2.5` pin.** Kwant 1.5.0's `magnetic_gauge` breaks on numpy ≥ 2.5
  (the fix is on Kwant's main branch, unreleased); the notebooks do not use
  it, `verify_kwant.py` warns, the installer pins. Drop the pin when Kwant
  releases.
- **Figure numbers are only sequential under Run-All** (global counter).
- **Tested on one machine** (Windows 10, Python 3.13, conda-forge Kwant 1.5.0
  + MUMPS, numpy 2.5.1 — above the pin; the pinned configuration is the one CI
  installs, on Linux, Windows and macOS). A clean-machine run of the installer
  by someone other than the author is still wanted — the first such report
  closes this line.
- **Not yet:** interactive (plotly) versions of the 3D figures; a Part III on
  time-dependent transport with tkwant; the reference-shelf section as a
  BibTeX file.

## How it was built

In Claude Code, over five working days: August 15 2026 (installer, docs
study, Part I), August 20–21 (the MUMPS crash and its diagnosis, Part II, the
presentation pass, exercises and solutions), August 28–29 (upstream
audit of the Kwant project, pre-publication audit, tests, CI, manuals),
August 31 (licence protection, guards, upstream watch). Every physics result was checked against the
literature or an independent calculation before being kept; three Kwant
findings came out of it and were prepared for the Kwant project. In
[CRediT](https://credit.niso.org/) terms:

| CRediT role | Fabio Campolim | Claude |
|---|---|---|
| **Conceptualization** | A course that teaches theory and Kwant together; extending it to topology; exercises with executed solutions; contributing findings back to Kwant | The section structure (theory → code → check), the invariant-from-the-system approach, the pitfalls section |
| **Methodology** | Selection of the models; the publish-with-audit process this repository follows | Numerical methods (FHS Chern numbers, Pfaffians, KPM), the thread-crash diagnosis |
| **Software** | — | All of it |
| **Validation** | Running the notebook end-to-end in VS Code, reviewing every figure, deciding on each finding | Assertions, cross-checks against the literature, re-execution tests, Crossref spot-checks of citations |
| **Investigation** | Curating the topological-matter literature | Kwant documentation and source study; upstream tracker and mailing-list audit |
| **Writing** | Review and editing | Original draft |
| **Resources · Supervision · Project administration** | All | — |

## Licence

[Apache License 2.0](LICENSE) — see `LICENSE` and `NOTICE`. This course uses
Kwant through its public Python API and contains no Kwant source code, so it
carries its own licence; Kwant itself is © the Kwant authors, BSD-2, and is
installed by you from conda-forge. Sources used as models (the Kwant tutorial,
BSD-2; topocondmat.org, CC BY-SA 4.0 text / BSD-3 code; Asbóth *et al.*'s
book) are credited in the notebook's final "Sources, attribution and licence"
cell; nothing from them is reproduced verbatim. You may use, modify and
redistribute this project, including commercially, provided the licence and
notice travel with it; contributions are accepted under the same terms
(section 5).

### Disclaimer

This software is provided **as is**, without warranties or conditions of any
kind, express or implied, including but not limited to any warranty of
merchantability, fitness for a particular purpose, title or non-infringement.
In no event shall the author be liable for any damages of any character —
direct, indirect, special, incidental or consequential — or for any other
claim or liability, whether in contract, tort or otherwise, arising from, out
of or in connection with the software or its use, even if advised of the
possibility of such damages (Apache License 2.0, sections 7 and 8). The
physics in the notebooks is checked numerically, not refereed: you alone are
responsible for any use of the results, for the software the installer puts on
your machine, and for complying with the licences of Kwant and every other
third-party package this course touches.

This is an independent project. It is not affiliated with, endorsed by or
supported by the Kwant authors, TU Delft (topocondmat.org), the authors of the
works cited, or Anthropic; *Kwant* and the other names are used only to
identify what this course teaches and the tools used to build it.
