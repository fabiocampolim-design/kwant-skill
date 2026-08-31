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
import json

NB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Kwant_Theory_and_Practice.ipynb')
LAST = 72

HEADER = '''import matplotlib
matplotlib.use("Agg")
import ctypes


class _MEMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def _rss():
    c = _MEMC()
    c.cb = ctypes.sizeof(_MEMC)
    ctypes.WinDLL("psapi").GetProcessMemoryInfo(
        ctypes.WinDLL("kernel32").GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.WorkingSetSize / 2**20
'''

nb = json.load(open(NB, encoding='utf-8'))
parts = [HEADER]
for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code' or i > LAST:
        continue
    src = ''.join(c['source'])
    body = '\n'.join('    ' + line for line in src.split('\n'))
    parts.append(
        'print("##### CELL {i} START  rss=%.0fMB" % _rss(), flush=True)\n'
        'try:\n{body}\n'
        'except Exception as _e:\n'
        '    print("##### CELL {i} EXCEPTION:", type(_e).__name__, _e, flush=True)\n'
        'print("##### CELL {i} END    rss=%.0fMB" % _rss(), flush=True)\n'.format(i=i, body=body)
    )
parts.append('print("ALL CELLS COMPLETED", flush=True)\n')
open('runall.py', 'w', encoding='utf-8').write('\n'.join(parts))
print("wrote runall.py")
