# AGENTS.md — instructions for AI agents working with this repository

You are helping a person use, check or extend the *Kwant — Theory and
Practice* notebook course. This file is the complete, machine-oriented
description: what is here, the commands, the files each command reads and
writes, and the rules you must not break. Humans: hand this file to your agent
("read AGENTS.md, then run the checks"). The human manual is
`docs/USER_MANUAL.md`; `README.md` is the product page.

## What the repository is

Two fully executed Jupyter notebooks and their support files:

| File | What |
|---|---|
| `Kwant_Theory_and_Practice.ipynb` | the course: 86 cells (53 code), 68 figures, 25 exercises, sections 1–27 in two parts (core Kwant API and transport theory; ten topological models) plus a reference shelf |
| `Kwant_Exercises_Solutions.ipynb` | 51 cells (24 code), 18 figures, one section per exercise, 31 `assert`s that encode the expected physics |
| `install_kwant_windows.ps1` / `.bat` | Windows installer: Miniforge + conda-forge `kwant`, `python-mumps`, `numpy<2.5`, Jupyter kernel named `kwant` |
| `verify_kwant.py` | proves an installation works with physics identities (quantised conductance, unitarity, sum rule, …) |
| `test_thread_safety.py` | regression test for the MUMPS re-entrancy crash; threaded SuperLU sweep must equal serial |
| `tests/` | pytest suite: notebook invariants, licence texts + SPDX, withheld-material guard, docs<->CLI guard, manual readback, script CLI contract, cold-kernel execution |
| `dev/` | standalone per-model scripts the notebooks were built from; `dev/build-history/` holds one-shot build scripts that are guarded against re-running |
| `docs/` | user manual (md/html/pdf), review docs, upstream findings backlog and drafts, weekly upstream watch reports (`docs/watch/`) |
| `scripts/` | `watch_upstream.py` (weekly Kwant GitLab + clone watch) and `register_watch_task.ps1` (Windows Task Scheduler entry) |
| `course/` | the undergraduate course: `deck/` (linear reveal.js deck + `slides.html`/`slides.pdf` fallbacks, generated from `deck/content_en.py`), `handout/`, `lecturer_notes.md`, `figures/` (all 68 notebook figures, extracted by `build_course.py`) |
| `VERSION`, `NOTICE` | the one product version (guarded); Apache-2.0 notice with the licence-by-origin of everything used |

## Environment

- Python ≥ 3.11 with `kwant` 1.5.x from conda-forge (pip builds are unreliable
  on Windows), `numpy<2.5` (see rules), `scipy`, `matplotlib`, `sympy`,
  `python-mumps` (optional but 5–10× faster), `ipykernel`, `jupyterlab`,
  `nbconvert`, `pytest`.
- The notebooks are pinned to a Jupyter kernel **named `kwant`**. Register one
  for the environment that has Kwant:
  `python -m ipykernel install --user --name kwant --display-name "Python (kwant)"`.
- Windows: run `install_kwant_windows.bat` (or the `.ps1` with
  `-EnvName kwant -PythonVer 3.13 [-Force] [-SkipInit]`); it does all of the above.

## Commands

```
python verify_kwant.py [--outdir DIR] [--log-dir DIR] [--json] [--verbose|--quiet] [--version]
python test_thread_safety.py [--workers N] [--energies N] [--tol X] [--no-canary]
                             [--canary-timeout S] [--outdir DIR] [--log-dir DIR] [--json] [--verbose|--quiet] [--version]
python -m pytest tests -q                       # fast: invariants, guards, CLI contract (~30 s)
set KWANT_NB_EXECUTE=1 && python -m pytest tests/test_execute_notebooks.py -q   # cmd.exe; ~6 min, needs kernel 'kwant'
$env:KWANT_NB_EXECUTE=1; python -m pytest tests/test_execute_notebooks.py -q     # PowerShell
KWANT_NB_EXECUTE=1 python -m pytest tests/test_execute_notebooks.py -q          # bash
python -m jupyter nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.kernel_name=kwant Kwant_Theory_and_Practice.ipynb   # re-execute in place
python docs/build_manual.py [--outdir DIR] [--strict] [--quiet]   # USER_MANUAL.md -> .html + .pdf, read back
python scripts/watch_upstream.py --weekly --fetch  # Kwant GitLab + clone delta -> docs/watch/YYYY-WW.md
python course/build_course.py [--outdir DIR] [--skip-handout] [--quiet]   # deck + slides.html/pdf + notes + handout from the executed notebook
```

Outputs: both scripts write `<outdir>/logs/<script>_<timestamp>.log` (exact
command line, versions, every message, exit code) and
`<outdir>/<script>_summary.json`. Exit codes: 0 ok, 1 a check failed,
2 (verify) Kwant not importable. `logs/` and `*_summary.json` are gitignored.

## Hard rules

- **Never call `kwant.smatrix` (or any `kwant.solvers.mumps` function) from
  several threads.** MUMPS is not re-entrant; the process segfaults with no
  Python exception. Use `kwant.solvers.sparse` in threads, or processes. The
  notebook's parallel-sweep cell (section 15) does the former on purpose.
- **Keep `numpy<2.5` while Kwant 1.5.0 is the installed release.** numpy 2.5
  removed `np.cross` on 2-vectors and `kwant.physics.magnetic_gauge` breaks on
  every 2-D system. The notebooks do not call it; `verify_kwant.py` reports it
  as a warning. Drop the pin when a Kwant release includes the upstream fix.
- **Do not edit notebook outputs by hand.** Change source cells, then
  re-execute the whole notebook with the `kwant` kernel (command above) so
  outputs, figure numbers and the counts in `tests/test_notebooks.py` stay
  consistent. Figure numbers come from a global counter in cell 2 and are only
  sequential under Run-All.
- **Do not run anything in `dev/build-history/`.** Those scripts already
  rewrote the notebooks once; they exit unless `KWANT_NB_REBUILD=1` is set.
- **Counts are claims.** 86/53/68 cells/code/figures (main), 51/24/18
  (solutions), 25 exercises: `tests/test_notebooks.py` asserts them. If you
  add a cell or figure, update the test, `README.md`, `CITATION.cff` and the
  manual together.
- **Nothing personal in the repository.** No user home-directory paths in
  outputs (`tests/test_notebooks.py` scans sources and outputs), no e-mail
  addresses, no institution names.
- **Upstream contact is the owner's.** `docs/02-findings-backlog.md` and
  `docs/drafts/` hold issue texts and patches for the Kwant project. Do not
  post, mail or open merge requests on anyone's behalf.
- Third-party sources (Kwant tutorial, topocondmat.org, Asbóth *et al.*) are
  credited in the notebook's "Sources, attribution and licence" cell; keep
  exercise-level origin flags when editing exercises.

## Workflows

- *Check an installation*: `python verify_kwant.py --json` → read
  `verify_kwant_summary.json`; `failures == []` means usable; `warnings` lists
  missing optional parts (MUMPS, sympy, plotly, the magnetic_gauge pin).
- *Change a section*: edit the source cell → re-execute in place → run
  `pytest tests -q` → if counts changed, update the four places above.
- *Add an exercise*: add `**E n.m**` with a difficulty mark (◦ • ★) and an
  origin flag in the main notebook, add a `## E n.m — …` section with at least
  one `assert` in the solutions notebook, bump `N_EXERCISES` in the test.
