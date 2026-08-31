# drafts/ — outward-facing texts, not yet sent

Everything here is a draft for the project owner to review and send under
their own identity (playbook S9). Status headers at the top of each file.

| File | Venue | Depends on |
|---|---|---|
| `K1-magnetic-gauge-numpy25.md` | GitLab issue + kwant-discuss pointer | — |
| `K2-mumps-thread-safety-issue.md` | GitLab issue, then MR | `patches/0001` |
| `B3-kwant-discuss-intro.md` | kwant-discuss (subscribe via kwant-discuss-join@python.org) | K1, K2 filed |
| `patches/0001-*.patch` | MR: lock + test + docs + whatsnew | — |
| `patches/0002-*.patch` | MR: FAQ site_color paragraph | — |
| `patches/0003-*.patch` | MR: wraparound Notes | — |
| `patches/0004-*.patch` | MR: `kwant.plotter` must not reset the global warning filters (K6) | — |

The four patches are `git format-patch` output from branch `contrib/thread-safe-mumps`
in the gitignored clone `upstream/kwant` (base: upstream `main` @ ef12fa0,
2026-01-09). Re-create with `git -C upstream/kwant format-patch main..contrib/thread-safe-mumps`.
To submit: fork on gitlab.kwant-project.org, `git push` the branch, open the MR;
or mail the patches to kwant-discuss (both accepted per CONTRIBUTE.rst).
