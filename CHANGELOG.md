# Changelog

All notable changes to the Kwant — Theory and Practice notebooks. Dates are
commit dates; the project has not been released yet.

## 1.3.4 — 2026-09-02 (community pathways)

- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) and `docs/DESIGN.md`
  (the design decisions and their trade-offs) -- the community pathways a JOSS/JOSE
  review asks for; GITHUBIFY rule 26.
- Vendored conformance checker 1.5.0: rule 25 notebook-size (1 MB warn / 1.5 MB fail),
  rule 26 community-files, large-PDF and LF-pin checks, base64 image payloads no longer
  scanned by the scrub, UTF-8 report output.

## 1.3.3 — 2026-09-01 (code-review follow-ups)

- `dev/build-history/split_chapters.py` reproduces the shipped chapters exactly
  again: the chapter-7 parallel-sweep printout retarget is part of the script,
  and a single-figure chapter's Setup comment reads "figure 34 only" instead of
  "34–34" (chapter 7 re-executed; the test accepts the singular form).
- `tests/test_execute_notebooks.py`: the fifteen-notebooks assertion is its own
  test instead of being repeated in every execution test.

## 1.3.2 — 2026-09-01 (README gallery)

- README: a six-figure gallery under the tagline — the Hofstadter butterfly and
  its Chern-coloured version (ch. 6), the Haldane ribbon (ch. 9), the chiral
  Majorana mode of a p+ip sample (ch. 10), the Weyl slab with its Fermi arc
  (ch. 11) and the surface Dirac cone of the 3D TI (ch. 12); each tile links to
  its chapter. The images are the already-shipped `course/figures/fig-NN.png`;
  no new files.

## 1.3.1 — 2026-09-01 (repository renamed `kwant-skill`)

- The GitHub repository is now `fabiocampolim-design/kwant-skill`, in line with
  the sibling `pythtb-skill`; GitHub redirects the former name. Badge, issue
  link, `CITATION.cff`, the deck's closing slide, the upstream-watch user agent
  and the scheduled task name (`kwant-skill upstream watch`) follow. No change
  to the notebooks.

## 1.3.0 — 2026-09-01 (the course split into chapter notebooks)

- **The two monolithic notebooks are gone.** `Kwant_Theory_and_Practice.ipynb`
  (7.4 MB, 86 cells) crashed editors on opening; it is now twelve chapter
  notebooks under `chapters/` (`01_Foundations` … `12_3D_TI_Exercises_II_and_Beyond`,
  each under 1 MB), plus `00_Contents.ipynb` (chapter map, section table,
  installation, conventions, environment check). `Kwant_Exercises_Solutions.ipynb`
  is now `S1_Solutions_Part_I.ipynb` and `S2_Solutions_Part_II.ipynb`.
- **Every notebook opens with its own table of contents**: a link to every
  heading of the chapter, previous · contents · next links, the part, sections
  and figure range, and the SPDX line; then one Setup cell (imports, solver
  report, muted warnings, `show_fig`).
- **Figure numbering is continuous across the chapters** (chapter 6 starts at
  Figure 29): the numbers in the course deck, `course/figures/` and the
  captions are unchanged from 1.2.0.
- **Chapters are self-contained.** The four cross-chapter dependencies of the
  monolith (the §3 wire for the §15 parallel sweep, the §6 Rashba wire for §10,
  `chern_fhs` for §22–25, `bloch_hamiltonian` for §22–23) are rebuilt by a
  *carried over* cell whose code is the original definition, verbatim. One
  behaviour change: the §15 parallel sweep now runs on the §3 quantum wire it
  describes (in the monolith it silently used whatever `fsyst` was last bound —
  the §9 N-S junction).
- All fifteen notebooks re-executed from a cold kernel; 68 + 18 figures, 25
  exercises, 31 assertions as before. Sections, section numbers and text are
  unchanged apart from the retargeted cross-references.
- `tests/test_notebooks.py` rewritten for the chapter layout: exact file set,
  per-notebook counts, size cap of 1 MB, continuous figure counter, a TOC whose
  links resolve in every chapter, the contents notebook linking every chapter.
  `tests/test_execute_notebooks.py` and `tests/test_license.py` cover all
  fifteen files.
- `course/build_course.py` reads the chapters (`--chapters DIR` replaces
  `--notebook FILE`); `figures.json` records the chapter notebook of every
  figure and the deck, static slides, PDF and lecturer notes cite
  "chapter notebook, cell" instead of a bare cell index. The handout's stale
  description of the deck as a 2-D grid is corrected.
- `dev/build-history/split_chapters.py`: the guarded one-shot that derived the
  chapters from the 1.2.0 monoliths (the record of how the split was made).

## 1.2.0 — 2026-08-31 (linear course deck, PDF fallback, full figure coverage)

- `course/`: the deck is now **one linear sequence** (79 slides) — single-level
  previous/next navigation only, no build animations, reveal's own controls,
  progress bar and slide counter; a generated opener with a level-coloured
  agenda starts each section (playbook rule 22 as amended 2026-08-31).
- **Every one of the notebook's 68 figures appears in the deck** — 24 generated
  figure pages join the authored slides — each under its full notebook caption
  with its section and cell (`figures.json`).
- New fallbacks, committed: `course/deck/slides.pdf` (landscape, one slide per
  page, pandoc + xelatex with DejaVu fonts) and `course/deck/slides.html`
  (the same slides as one static page, no JavaScript).
- `course/shared/nav.js` (the 2-D navigator) removed; `tests/test_course.py`
  rewritten for the linear deck, full figure coverage and the PDF readback.
- The `public` tree no longer carries the internal review documents
  `docs/03-phase1-audit.md` and `docs/04-project-review.md`.

## 1.1.0 — 2026-08-31 (licence protection, guards, upstream watch)

- `NOTICE`, a visible **Disclaimer** and a non-affiliation note under the
  README's Licence section, and `SPDX-License-Identifier: Apache-2.0` headers
  in every script and in both notebooks; `tests/test_license.py` guards them.
- `tests/test_no_held_material.py`: hashed guard that keeps the author's
  unpublished material (the former Part III) out of every tracked file.
- `tests/test_docs_guard.py`: every CLI option of the two scripts must be in
  `AGENTS.md` and the manual (and nothing that is not); every count stated in
  prose must equal the count the suite asserts; one product version
  (`VERSION`) shared by `CITATION.cff`, this changelog and both scripts.
- `tests/test_manual_readback.py`: the committed HTML/PDF manual is read back
  (every heading present; the PDF is the typeset one, not the fallback);
  `docs/build_manual.py` gained a CLI, an audit log and the same readback.
- pyflakes clean over the whole tree (twelve unused imports in `dev/`); CI
  runs it before the suite on Linux, Windows and macOS.
- Installer: the `numpy<2.5` pin is now written to `conda-meta/pinned` and
  repeated on every optional install, so an extra cannot lift numpy past 2.5
  and re-break `magnetic_gauge`; the final check asserts the resolved numpy.
- `course/`: the undergraduate course — a reveal.js deck (10 sections, 46
  slides, speaker notes with one anticipated question each), an A4 handout and
  lecturer notes, all generated by `course/build_course.py` from one content
  source and from the executed notebook (every slide figure is a notebook
  figure); `tests/test_course.py` reads them back.
- `scripts/watch_upstream.py` + `scripts/register_watch_task.ps1`: weekly
  watch of the Kwant GitLab (tags, issues, merge requests) and the local
  clone, written to `docs/watch/YYYY-WW.md`.
- Documentation fixes: `chern_fhs` is defined in section 20, not 21; patch
  0004 listed in `docs/drafts/README.md`; `--version` documented for both
  scripts; Windows syntax for the notebook-execution test; `CITATION.cff`
  carries the repository URL.

## 1.0.0 — 2026-08-29 (pre-publication audit and hardening)

- **Licence changed to Apache License 2.0** (was MIT in the unreleased draft).
- Scope fixed at Parts I–II: 26 sections plus the reference shelf (section
  27), 25 exercises, 31 assertions.

- Both notebooks pinned to the Jupyter kernel named `kwant`, the name the
  installer registers (they were pinned to two different machine-specific
  kernels).
- Exercise count corrected everywhere (25 after the scope fix; 2 are pencil-and-paper).
- Installer pins `numpy<2.5`: numpy 2.5 removed `np.cross` on 2-vectors and
  Kwant 1.5.0's `magnetic_gauge` breaks on every 2-D system (fix exists on
  Kwant's main branch, unreleased). `verify_kwant.py` probes it and warns.
- `verify_kwant.py` and `test_thread_safety.py` gained real CLIs
  (`--help` with defaults, `--outdir`, `--log-dir`, `--json`,
  `--verbose/--quiet`), an audit log per invocation and a JSON summary.
- `tests/`: notebook invariants (kernel, zero error outputs, counts, 25
  exercises matched 1:1 to solutions, no personal data, attribution cell),
  script CLI contract, and an opt-in cold-kernel execution of both notebooks;
  GitHub Actions on Linux and Windows with conda-forge Kwant + MUMPS.
- Apache-2.0 `LICENSE`, `CITATION.cff`, `AGENTS.md`, user manual (md/html/pdf), and a
  "Sources, attribution and licence" cell crediting the Kwant tutorial,
  topocondmat.org and Asbóth *et al.*
- Library deprecation warnings that appeared under six figures are filtered
  narrowly in cell 1 with a comment saying why; the p+ip vortex cell prints
  |E| instead of a run-dependent ±E.
- The nine one-shot build scripts moved to `dev/build-history/` with a guard
  that exits unless `KWANT_NB_REBUILD=1`.
- Upstream findings documented and drafted for the Kwant project
  (`docs/01`, `docs/02`, `docs/drafts/`): the MUMPS thread crash (with a
  patch), the numpy 2.5 breakage, two documentation clarifications.

## 0.3 — 2026-08-21 (exercises and depth)

- 31 exercises with origin and difficulty flags; companion solutions notebook
  with asserted solutions; "physics in more depth" for Part I; four new
  figures; 3D Berry-curvature figure for the Haldane model and a fix of the
  wraparound momentum convention for local curvature densities.

## 0.2 — 2026-08-20/21 (Part II)

- Ten topological models (SSH, Kitaev, Majorana nanowire, Thouless pump,
  Haldane, Kane–Mele, p+ip, BBH, Weyl, 3D TI); presentation pass with captions, geometry
  figures and ~70 literature references.
- Fixed the kernel crash of the parallel sweep: MUMPS is not re-entrant;
  the sweep uses the SuperLU solver in threads; regression test added.

## 0.1 — 2026-08-15 (baseline)

- Part I (core API + transport theory, 16 sections), Windows installer,
  installation-verification script.
