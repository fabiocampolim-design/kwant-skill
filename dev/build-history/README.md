# dev/build-history/ — one-shot notebook build steps (do not re-run)

These four scripts assembled and patched the notebooks in August 2026 and have
**already been applied**. Each one starts with a guard that exits unless
`KWANT_NB_REBUILD=1` is set, because running it again would duplicate or
overwrite cells. They are kept as the record of how the notebooks were built
(playbook: "how it was built").

| Script | What it did |
|---|---|
| `gen.py`, `assemble.py` | wrote the first 49-cell notebook from `../cells_a-c.py` |
| `newcell46.py`, `patch_45_47.py` | replaced the parallel-sweep cells after the MUMPS thread crash |

The reusable, runnable material is in `dev/` proper: the standalone model
scripts `dev18–27`, `dev_butterfly3d.py`, the cell sources `cells_a–c.py`,
`sol_part1-2.py`, and the thread-safety reproductions.
