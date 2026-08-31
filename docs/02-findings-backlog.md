# Findings backlog — accumulate → confirm → implement

Rule (playbook S3/S9): **nothing is reported or submitted upstream until
verified on this machine and confirmed by the project owner.** Status:
`proposed` → `confirmed` → `drafted` → `sent` / `dropped`.

**2026-08-28:** everything below that can be done locally is done. Outward
steps (posting K1/K2, opening the MR from patches 0001–0003, sending B3) are
the project owner's; the upstream branch `contrib/thread-safe-mumps` in `upstream/kwant`
holds the three commits, exported to `drafts/patches/`.

## K. Upstream (Kwant) — bugs and docs

| # | Candidate | Evidence | Novelty | Status |
|---|---|---|---|---|
| K1 | **kwant 1.5.0 `magnetic_gauge` broken for 2-D systems with numpy >= 2.5** (`np.cross` on 2-vectors removed 2026-06-21). Fixed on `main` 2025-01-26, never released. | `docs/01` §2; test_gauge failure + runtime repro | Not in issues (#388, #391, #382 differ) nor on the list. Fix exists; what is missing is a **release** and/or a `numpy<2.5` **pin** on the 1.5.0 conda-forge/pip metadata. | **drafted** — `drafts/K1-magnetic-gauge-numpy25.md` (issue + list pointer); needs the owner's review and posting |
| K2 | **MUMPS non-reentrancy: threaded `smatrix` segfaults the process** | `test_thread_safety.py`, `dev/thread_repro.py`, notebook §15 (solvers) and §16 (pitfalls) | Novel (docs/01 §3 F1). Adjacent upstream item found by the 2026-W36 watch: #377 "Kwant does not release the GIL when calling Mumps" (2020, closed 2026-01-03) is about *performance* of the old in-tree wrapper, not re-entrancy — and releasing the GIL makes serialisation of the MUMPS calls more necessary, not less; cite it in the issue text | **drafted + patch validated** — `drafts/K2-mumps-thread-safety-issue.md`; fix+test+docs in `drafts/patches/0001-*.patch` (patched module loaded into installed 1.5.0: 3/3 threaded runs == serial; unpatched control segfaults) |
| K3 | FAQ/docstring: `site_color` callable gets `Site` vs index depending on Builder/finalized | docs/01 §3 F2 | docs gap | **patch ready** — `drafts/patches/0002-*.patch` (FAQ paragraph + adapter; adapter verified: unadapted callable raises `AttributeError: 'int' object has no attribute 'family'`) |
| K4 | wraparound momenta convention & seam pitfall for local Berry curvature | notebook §21 (cell 69), docs/01 §3 F3 | novel pitfall | **patch ready** — `drafts/patches/0003-*.patch` (Notes section: phases across primitive vectors, 2π-periodic, reparametrisation caveat; `plot_2d_bands` confirmed to use `pinv` of periods) |
| K6 | **`kwant.plotter` calls `warnings.resetwarnings()`** in `plot()` (3D branch, line 1463) and `spectrum()` (line 2144) after suppressing matplotlib's "mouse rotation disabled" warning — this deletes *all* user-set warning filters process-wide; a notebook's `filterwarnings` in cell 1 silently stops working after the first 3D plot. Present on `main` too. | found 2026-08-29 while fixing audit item A5; reproduced in ipykernel (filter present before `kwant.plot`, gone after) | not in tracker: issue search "warnings" (4 unrelated hits) and MR search "warnings" (9 deprecation-cleanup MRs, none touching plotter filters), checked 2026-08-29 | **patch ready** — `drafts/patches/0004-*.patch` (scope with `warnings.catch_warnings()`) |
| K5 | matplotlib 3.10 friction seen while building (mathtext `\mathbf`, 3D collections) | memory `notebook-presentation-pass` | #436/#440 fixed similar for 3.9 | **dropped 2026-08-28** — both were matplotlib/our-own issues (mathtext, raw strings), not Kwant; #436/#440 already cover the 3D collection changes |

## B. Contributions of the toolkit itself

| # | Proposal | Grounding |
|---|---|---|
| B1 | Offer the **thread-safety regression test** to upstream `kwant/solvers/tests` (skips cleanly when MUMPS is absent, rule 5) | K2 — **done, part of patch 0001** (`test_mumps_threaded_smatrix`) |
| B2 | Offer `install_kwant_windows.ps1` for the website's Windows install page (upstream `README_WINDOWS.txt` is thin) | S9 "start small" — **drafted** inside `drafts/B3-kwant-discuss-intro.md` item 2 |
| B3 | `Kwant_Theory_and_Practice.ipynb` as a community tutorial; the kwant-discuss thread "Your input for a Kwant AI system" (2025-08-31) is a natural place to introduce the work | S9 — **drafted** `drafts/B3-kwant-discuss-intro.md` (send after K1/K2 are filed) |

## N. Our own notebooks

| # | Item | Status |
|---|---|---|
| N1 | Cell 42 says `magnetic_gauge` was added in 1.5 — it was 1.4 | **done** (commit 9f11d88) |
| N2 | Warning box in §14 that `magnetic_gauge` needs numpy < 2.5 on kwant 1.5.0 | **done** (commit 9f11d88; markdown only, no re-execution needed) |

## S8 watch
- Upstream `main`, issues #445/#447, MR !424 (Schur MUMPS), python-mumps #30.
- kwant-discuss latest: 2026-06-18. Re-check monthly (`git -C upstream/kwant pull`).
