# Contributing to Kwant -- Theory and Practice (kwant-skill)

Thank you for considering a contribution. This file says how to report a problem, how to
propose a change, and the rules a change has to meet to be merged. The machine-oriented
description of the repository is `AGENTS.md`; the human manual is `docs/USER_MANUAL.md`
where present; the design decisions and their trade-offs are in `docs/DESIGN.md`.

## Reporting

Open an issue in this repository. The most useful reports carry: what you ran (the exact
command or notebook cell), what you expected, what happened (the full traceback or the
figure), your platform and versions (`python verify_kwant.py --version`), and -- for anything physical -- the
reference you checked against. A derivation that skips a step or a figure that disagrees with the literature is a bug here.

## Proposing a change

1. Open an issue first for anything larger than a typo, so the scope is agreed before the
   work is done.
2. Fork, branch, and keep the change to one topic.
3. **Failing-first test.** Every bug fix starts with a test that fails on the current code
   and passes on the fix; every feature comes with its tests. `pyflakes` must be clean over
   the whole tree.
4. Run the suite locally before opening the pull request:

   ```
   python -m pyflakes verify_kwant.py test_thread_safety.py tests dev docs
   python -m pytest tests -q
   # a changed chapter, end to end (kernel 'kwant'):
   cd chapters && python -m jupyter nbconvert --to notebook --execute --inplace \
       --ExecutePreprocessor.kernel_name=kwant NN_Chapter.ipynb
   ```

5. Keep the documentation in step: `README.md`, `AGENTS.md`, `docs/USER_MANUAL.md` and `CHANGELOG.md`
   describe the same repository, and the suite fails when a CLI option, a count or a file
   named in prose drifts from the code.
6. Every new source file carries the SPDX header (`# SPDX-License-Identifier: Apache-2.0`).
7. Do not bump `VERSION`, `CITATION.cff` or tag a release in a pull request; the
   maintainer does that on merge.

## Contributions made with AI assistance

Welcome, on two conditions: say so in the pull request (which tool, what it did), and state
what *you* verified -- the test you ran, the derivation you checked, the figure you looked
at. This repository was itself built with an AI assistant under a check-everything
contract (`README.md`, "How it was built"); the same standard applies to contributions.

## Licensing

By submitting a contribution you agree that it is licensed under the repository's licence
(Apache License 2.0), as section 5 of that licence provides for intentional submissions. Do not
contribute code or text you do not have the right to license that way, and do not add
third-party material (upstream sources, downloaded literature, figures from books) to the
tracked tree.

## Conduct

Everyone interacting in this repository is expected to follow `CODE_OF_CONDUCT.md`.
