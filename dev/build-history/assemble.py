# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# --- BUILD-HISTORY GUARD ------------------------------------------------------
# This script was a one-shot step in assembling the notebooks (Aug 2026) and has
# already been applied.  Running it again would duplicate or overwrite cells.
# It is kept as a record of how the notebooks were built.  To run it anyway,
# set KWANT_NB_REBUILD=1 in the environment.
import os as _os, sys as _sys
if _os.environ.get("KWANT_NB_REBUILD") != "1":
    _sys.exit(__file__ + ": already applied; set KWANT_NB_REBUILD=1 to re-run (see dev/build-history/README.md)")
# -----------------------------------------------------------------------------
import os
# -*- coding: utf-8 -*-
"""Insert Part II (sections 17-26) into the notebook; old section 17 -> 27."""
import ast
import json

import cells_a
import cells_b
import cells_c

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Kwant_Theory_and_Practice.ipynb')

ALL = cells_a.CELLS + cells_b.CELLS + cells_c.CELLS
for kind, src in ALL:
    if kind == "code":
        ast.parse(src)
print(f"{len(ALL)} cells, all code parses")

nb = json.load(open(PATH, encoding='utf-8'))
cells = nb['cells']
assert len(cells) == 49, len(cells)
closing = ''.join(cells[48]['source'])
assert '## 17. Where to go next' in closing, closing[:40]

def make_cell(kind, src):
    lines = src.split('\n')
    source = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    if kind == 'code':
        return {'cell_type': 'code', 'execution_count': None, 'metadata': {},
                'outputs': [], 'source': source}
    return {'cell_type': 'markdown', 'metadata': {}, 'source': source}

new_cells = [make_cell(k, s) for k, s in ALL]

# renumber the closing section and insert Part II before it
cells[48]['source'] = [l.replace('## 17. Where to go next',
                                 '## 27. Where to go next')
                       for l in cells[48]['source']]
nb['cells'] = cells[:48] + new_cells + [cells[48]]

json.dump(nb, open(PATH, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"inserted {len(new_cells)} cells; notebook now has {len(nb['cells'])} cells")
