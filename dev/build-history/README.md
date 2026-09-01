# dev/build-history/ — one-shot notebook build steps (do not re-run)

These five scripts assembled, patched and finally split the notebooks in
August–September 2026 and have **already been applied**. Each one starts with a guard that exits unless
`KWANT_NB_REBUILD=1` is set, because running it again would duplicate or
overwrite cells. They are kept as the record of how the notebooks were built
(playbook: "how it was built").

| Script | What it did |
|---|---|
| `gen.py`, `assemble.py` | wrote the first 49-cell notebook from `../cells_a-c.py` |
| `newcell46.py`, `patch_45_47.py` | replaced the parallel-sweep cells after the MUMPS thread crash |
| `split_chapters.py` | 2026-09-01: split the two 1.2.0 monoliths (`Kwant_Theory_and_Practice.ipynb`, 7.4 MB, and `Kwant_Exercises_Solutions.ipynb`) into `chapters/` — twelve chapters + contents + two solutions notebooks, each with a table of contents, a Setup cell continuing the course-wide figure numbering, and verbatim *carried over* cells for the four cross-chapter dependencies. The monoliths were then removed from the tree, so it needs them from git history (`git show b92f0d2:Kwant_Theory_and_Practice.ipynb`) to run again |

The reusable, runnable material is in `dev/` proper: the standalone model
scripts `dev18–27`, `dev_butterfly3d.py`, the cell sources `cells_a–c.py`,
`sol_part1-2.py`, and the thread-safety reproductions.
