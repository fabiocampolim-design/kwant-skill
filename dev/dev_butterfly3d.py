# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import os
"""Dev: 3D colored Hofstadter butterfly — gaps at height = Chern number."""
import matplotlib
matplotlib.use("Agg")
import numpy as np
from math import gcd
from matplotlib import pyplot
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib import cm, colors as mcolors


def harper(p, q, k1, k2):
    m = np.arange(q)
    H = np.diag(2 * np.cos(k2 + 2 * np.pi * p / q * m)).astype(complex)
    H += np.diag(np.ones(q - 1), 1) + np.diag(np.ones(q - 1), -1)
    H[0, q - 1] += np.exp(-1j * q * k1)
    H[q - 1, 0] += np.exp(1j * q * k1)
    return H


segs, cherns = [], []
QMAX, TMAX = 36, 5
for q in range(2, QMAX + 1):
    for p in range(1, q):
        if gcd(p, q) != 1:
            continue
        allev = np.array([np.linalg.eigvalsh(harper(p, q, k1, k2))
                          for k1 in (0, np.pi / (2 * q), np.pi / q)
                          for k2 in (0, np.pi / 2, np.pi)])   # (9, q) sorted rows
        top = allev.max(axis=0)      # upper edge of band r
        bot = allev.min(axis=0)      # lower edge of band r
        pbar = pow(p, -1, q)
        for r in range(1, q):        # gap after r filled bands
            if bot[r] <= top[r - 1] + 1e-9:
                continue             # gap closed
            t = (r * pbar) % q
            if t > q / 2:
                t -= q
            if abs(t) > TMAX:
                continue
            segs.append([(p / q, top[r - 1], t), (p / q, bot[r], t)])
            cherns.append(t)

print(f"{len(segs)} gap segments, Chern range "
      f"{min(cherns)}..{max(cherns)}")

norm = mcolors.Normalize(vmin=-TMAX, vmax=TMAX)
cmap = cm.RdBu_r
fig = pyplot.figure(figsize=(9.5, 7.5))
ax = fig.add_subplot(projection='3d')
lc = Line3DCollection(segs, colors=cmap(norm(np.array(cherns))), lw=1.1)
ax.add_collection3d(lc)
ax.set_xlim(0, 1)
ax.set_ylim(-4, 4)
ax.set_zlim(-TMAX, TMAX)
ax.set_xlabel(r'$\phi$')
ax.set_ylabel('energy  $[t]$')
ax.set_zlabel(r'Chern number $C$')
ax.view_init(elev=22, azim=-58)
fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.55,
             label=r'$C$')
ax.set_title('The coloured butterfly: every gap at its Chern number')
fig.savefig(os.path.join('plots6', 'butterfly_chern_dev.png'),
            dpi=100, bbox_inches='tight')
print("saved dev figure")

# sanity: phi=1/3 gaps carry C = +1 and -1
q, p = 3, 1
pbar = pow(p, -1, q)
ts = []
for r in (1, 2):
    t = (r * pbar) % q
    ts.append(t - q if t > q / 2 else t)
assert ts == [1, -1], ts
print("Diophantine check at phi=1/3: C = +1, -1  OK")
