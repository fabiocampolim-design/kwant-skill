# AGENTS.md — instructions for AI agents working with this repository

You are helping a person use, check or extend the *Kwant — Theory and
Practice* notebook course. This file is the complete, machine-oriented
description: what is here, the commands, the files each command reads and
writes, and the rules you must not break. Humans: hand this file to your agent
("read AGENTS.md, then run the checks"). The human manual is
`docs/USER_MANUAL.md`; `README.md` is the product page.

## What the repository is

Fifteen fully executed Jupyter notebooks under `chapters/` and their support files:

| File | What |
|---|---|
| `chapters/00_Contents.ipynb` | the contents: chapter map, section table, installation, conventions, the environment check |
| `chapters/01_*.ipynb` … `12_*.ipynb` | the course: twelve chapter notebooks, 112 cells (68 code), 68 figures numbered continuously across the chapters, 25 exercises (posed at the end of chapters 7 and 12), sections 1–27 in two parts (core Kwant API and transport theory; ten topological models) plus a reference shelf. Each chapter opens with a table of contents + prev/contents/next links, then a Setup cell; four chapters carry a "carried over" cell that rebuilds an object defined in an earlier chapter. Every notebook is under 1 MB (the 7.4 MB monolith it replaced crashed editors) |
| `chapters/S1_Solutions_Part_I.ipynb`, `S2_Solutions_Part_II.ipynb` | 54 cells (25 code), 18 figures, one section per exercise, 31 `assert`s that encode the expected physics |
| `install_kwant_windows.ps1` / `.bat` | Windows installer: Miniforge + conda-forge `kwant`, `python-mumps`, `numpy<2.5`, Jupyter kernel named `kwant` |
| `verify_kwant.py` | proves an installation works with physics identities (quantised conductance, unitarity, sum rule, …) |
| `test_thread_safety.py` | regression test for the MUMPS re-entrancy crash; threaded SuperLU sweep must equal serial |
| `tests/` | pytest suite: notebook invariants, licence texts + SPDX, withheld-material guard, docs<->CLI guard, manual readback, script CLI contract, cold-kernel execution |
| `dev/` | standalone per-model scripts the notebooks were built from; `dev/build-history/` holds one-shot build scripts (including `split_chapters.py`, which derived the chapters from the monoliths) that are guarded against re-running |
| `docs/` | user manual (md/html/pdf), review docs, upstream findings backlog and drafts, weekly upstream watch reports (`docs/watch/`) |
| `scripts/` | `watch_upstream.py` (weekly Kwant GitLab + clone watch) and `register_watch_task.ps1` (Windows Task Scheduler entry) |
| `course/` | the undergraduate course: `deck/` (linear reveal.js deck + `slides.html`/`slides.pdf` fallbacks, generated from `deck/content_en.py`), `handout/`, `lecturer_notes.md`, `figures/` (all 68 course figures, extracted from the chapter notebooks by `build_course.py`; `figures.json` maps each to its chapter notebook and cell) |
| `VERSION`, `NOTICE` | the one product version (guarded); Apache-2.0 notice with the licence-by-origin of everything used |

## Environment

- Python ≥ 3.11 with `kwant` 1.5.x from conda-forge (pip builds are unreliable
  on Windows), `numpy<2.5` (see rules), `scipy`, `matplotlib`, `sympy`,
  `python-mumps` (optional but 5–10× faster), `ipykernel`, `jupyterlab`,
  `nbconvert`, `pytest`.
- Every notebook is pinned to a Jupyter kernel **named `kwant`**. Register one
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
set KWANT_NB_EXECUTE=1 && python -m pytest tests/test_execute_notebooks.py -q   # cmd.exe; ~7 min, needs kernel 'kwant'
$env:KWANT_NB_EXECUTE=1; python -m pytest tests/test_execute_notebooks.py -q     # PowerShell
KWANT_NB_EXECUTE=1 python -m pytest tests/test_execute_notebooks.py -q          # bash
cd chapters && python -m jupyter nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.kernel_name=kwant 06_Magnetic_Fields.ipynb   # re-execute one chapter in place
cd chapters && for nb in *.ipynb; do python -m jupyter nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.kernel_name=kwant "$nb"; done                  # all fifteen, one after another (bash)
python docs/build_manual.py [--outdir DIR] [--strict] [--quiet]   # USER_MANUAL.md -> .html + .pdf, read back
python scripts/watch_upstream.py --weekly --fetch  # Kwant GitLab + clone delta -> docs/watch/YYYY-WW.md
python course/build_course.py [--outdir DIR] [--chapters DIR] [--skip-handout] [--quiet]   # deck + slides.html/pdf + notes + handout from the executed chapters
```

Outputs: both scripts write `<outdir>/logs/<script>_<timestamp>.log` (exact
command line, versions, every message, exit code) and
`<outdir>/<script>_summary.json`. Exit codes: 0 ok, 1 a check failed,
2 (verify) Kwant not importable. `logs/` and `*_summary.json` are gitignored.

## Hard rules

- **Never call `kwant.smatrix` (or any `kwant.solvers.mumps` function) from
  several threads.** MUMPS is not re-entrant; the process segfaults with no
  Python exception. Use `kwant.solvers.sparse` in threads, or processes. The
  parallel-sweep cell (chapter 7, section 15) does the former on purpose.
  Execute notebooks one after another, never several at once.
- **Keep `numpy<2.5` while Kwant 1.5.0 is the installed release.** numpy 2.5
  removed `np.cross` on 2-vectors and `kwant.physics.magnetic_gauge` breaks on
  every 2-D system. The notebooks do not call it; `verify_kwant.py` reports it
  as a warning. Drop the pin when a Kwant release includes the upstream fix.
- **Do not edit notebook outputs by hand.** Change source cells, then
  re-execute the whole chapter with the `kwant` kernel (command above, from
  `chapters/`) so outputs, figure numbers and the counts in
  `tests/test_notebooks.py` stay consistent. Figure numbers come from the
  chapter's Setup cell (`_FIG_NO = [start]`), which continues the course-wide
  numbering: adding or removing a figure in chapter *k* shifts the start of
  every later chapter — update their Setup cells and re-execute them too
  (`test_figure_numbering_is_continuous_across_the_chapters` checks the chain).
  Numbers are only sequential under Run-All.
- **Do not run anything in `dev/build-history/`.** Those scripts already
  rewrote the notebooks once; they exit unless `KWANT_NB_REBUILD=1` is set.
- **Counts are claims.** Per-notebook cells/code/figures are the `EXPECTED`
  table of `tests/test_notebooks.py` (112/68/68 over the twelve chapters,
  54/25/18 over the two solutions notebooks), 25 exercises, every notebook
  under 1 MB. If you add a cell or figure, update the test, `README.md`,
  `CITATION.cff` and the manual together.
- **Nothing personal in the repository.** No user home-directory paths in
  outputs (`tests/test_notebooks.py` scans sources and outputs), no e-mail
  addresses, no institution names.
- **Upstream contact is the owner's.** `docs/02-findings-backlog.md` and
  `docs/drafts/` hold issue texts and patches for the Kwant project. Do not
  post, mail or open merge requests on anyone's behalf.
- Third-party sources (Kwant tutorial, topocondmat.org, Asbóth *et al.*) are
  credited in the "Sources, attribution and licence" cell that closes chapter
  12; keep exercise-level origin flags when editing exercises.
- **Every chapter keeps its header contract**: cell 0 is the markdown header
  (title, part/sections/figures line, prev · contents · next links, a table of
  contents linking every `##`/`###` heading of the chapter, the SPDX line),
  cell 1 the Setup cell. Add a heading → add its TOC line
  (`test_chapter_opens_with_a_table_of_contents_and_working_links`).

## Workflows

- *Check an installation*: `python verify_kwant.py --json` → read
  `verify_kwant_summary.json`; `failures == []` means usable; `warnings` lists
  missing optional parts (MUMPS, sympy, plotly, the magnetic_gauge pin).
- *Change a section*: edit the source cell of its chapter → re-execute that
  chapter in place → run `pytest tests -q` → if counts changed, update the four
  places above; if a figure was added or removed, fix the `_FIG_NO` start of
  every later chapter and re-execute them; rebuild the course
  (`python course/build_course.py`).
- *Split a chapter that grew past 1 MB*: new file `NN_Slug.ipynb` with the
  header + Setup cells of its neighbours (copy, then adjust title, links, TOC
  and `_FIG_NO`), renumber the later chapters' file names and links, update
  `EXPECTED` and `00_Contents.ipynb`.
- *Add an exercise*: add `**E n.m**` with a difficulty mark (◦ • ★) and an
  origin flag to the exercises cell of chapter 7 (Part I) or 12 (Part II), add
  a `## E n.m — …` section with at least one `assert` to `S1`/`S2` and a line
  for it in that notebook's TOC, bump `N_EXERCISES` in the test.
