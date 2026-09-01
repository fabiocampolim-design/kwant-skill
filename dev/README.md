# dev/ — development scripts

Standalone scripts from which the notebooks were assembled (Aug 20–21 2026).
Rescued on 2026-08-28 from the Claude Code scratchpad
(a purgeable temp directory). They are kept as the per-model, runnable reference for each notebook section.

| Files | Purpose |
|---|---|
| `thread_repro.py`, `thread_scipy.py`, `thread_variants.py`, `proc_test.py`, `bench.py` | MUMPS thread-safety crash reproduction and solver alternatives (→ `test_thread_safety.py`) |
| `newcell46.py`, `patch_45_47.py` | Fixes to the parallel-sweep cells |
| `dev18_ssh.py` … `dev27_ti3d.py` | Part II topological models (SSH, Kitaev, nanowire, pump, Haldane, Kane–Mele, p+ip, BBH, Weyl, 3D TI) |
| `dev_butterfly3d.py` | Hofstadter butterfly / 3D Chern terrace |
| `cells_a.py` … `cells_c.py` | Cell sources (assembled by `build-history/gen.py`) |
| `build-history/` | One-shot build scripts, already applied, guarded against re-running (see its README) |
| `sol_part1.py`, `sol_part2.py` | Worked solutions → `chapters/S1_Solutions_Part_I.ipynb`, `S2_Solutions_Part_II.ipynb` |

The scripts assume the `kwant` environment the installer creates (see
`../README.md`, Installation) and resolve the notebooks relative to the
repository root; run them from there.
