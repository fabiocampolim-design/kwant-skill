# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 24 dev: p+ip superconductor — BdG Chern number, chiral Majorana edge."""
import matplotlib
matplotlib.use("Agg")
import kwant, kwant.wraparound, numpy as np

tau_x = np.array([[0, 1], [1, 0]])
tau_y = np.array([[0, -1j], [1j, 0]])
tau_z = np.array([[1, 0], [0, -1]])

t, Delta = 1.0, 0.5
lat = kwant.lattice.square(norbs=2)             # Nambu (particle, hole)

def pip_bulk(mu):
    syst = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs))
    syst[lat(0, 0)] = -mu * tau_z
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = \
        -t * tau_z - 0.5j * Delta * tau_x
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = \
        -t * tau_z - 0.5j * Delta * tau_y
    return syst

def bloch_hamiltonian_square(bulk_builder):
    wrapped = kwant.wraparound.wraparound(bulk_builder).finalized()
    return lambda kx, ky: wrapped.hamiltonian_submatrix(
        params=dict(k_x=kx, k_y=ky))

def chern_fhs(hfunc, n_occ, n1=30, n2=30):
    xs = [np.linspace(0, 2 * np.pi, n, endpoint=False) for n in (n1, n2)]
    frames = np.empty((n1, n2), dtype=object)
    for i, x1 in enumerate(xs[0]):
        for j, x2 in enumerate(xs[1]):
            _, v = np.linalg.eigh(hfunc(x1, x2))
            frames[i, j] = v[:, :n_occ]
    link = lambda a, b: np.linalg.det(a.conj().T @ b)
    F = 0.0
    for i in range(n1):
        for j in range(n2):
            u1 = link(frames[i, j], frames[(i+1) % n1, j])
            u2 = link(frames[(i+1) % n1, j], frames[(i+1) % n1, (j+1) % n2])
            u3 = link(frames[(i+1) % n1, (j+1) % n2], frames[i, (j+1) % n2])
            u4 = link(frames[i, (j+1) % n2], frames[i, j])
            F += np.angle(u1 * u2 * u3 * u4)
    return int(round(F / (2 * np.pi)))

# --- BdG Chern number vs mu: transitions at mu = -4t, 0, +4t -----------------
expected = {-5.0: 0, -2.0: None, 2.0: None, 5.0: 0}   # inner two: +-1, opposite
C = {mu: chern_fhs(bloch_hamiltonian_square(pip_bulk(mu)), n_occ=1)
     for mu in expected}
print("Chern numbers:", C)
assert C[-5.0] == 0 and C[5.0] == 0
assert abs(C[-2.0]) == 1 and C[2.0] == -C[-2.0]

# --- strip: chiral Majorana edge mode dispersion -----------------------------
def pip_strip(mu, W=25):
    syst = kwant.Builder(kwant.TranslationalSymmetry((-1, 0)))
    syst[(lat(0, y) for y in range(W))] = -mu * tau_z
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = \
        -t * tau_z - 0.5j * Delta * tau_x
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = \
        -t * tau_z - 0.5j * Delta * tau_y
    return syst.finalized()

ks = np.linspace(-np.pi, np.pi, 201)
bands_top = kwant.physics.Bands(pip_strip(-2.0))
bands_tri = kwant.physics.Bands(pip_strip(-5.0))
min_top = min(np.abs(bands_top(k)).min() for k in ks)
min_tri = min(np.abs(bands_tri(k)).min() for k in ks)
print(f"min |E| in strip: topological={min_top:.5f}  trivial={min_tri:.5f}")
assert min_top < 0.02                     # chiral Majorana crosses E=0
assert min_tri > 0.2                      # trivial strip is fully gapped

# edge-localization of the E~0 mode
import scipy.sparse.linalg as sla
W, L = 25, 25
fin = kwant.Builder()
fin = kwant.Builder()
fin[(lat(x, y) for x in range(L) for y in range(W))] = 2.0 * tau_z  # -mu tau_z, mu=-2
fin[kwant.builder.HoppingKind((1, 0), lat, lat)] = -t * tau_z - 0.5j * Delta * tau_x
fin[kwant.builder.HoppingKind((0, 1), lat, lat)] = -t * tau_z - 0.5j * Delta * tau_y
ffin = fin.finalized()
ham = ffin.hamiltonian_submatrix(sparse=True).tocsc()
ev, vec = sla.eigsh(ham, k=8, sigma=0)
i0 = np.argmin(np.abs(ev))
dens = (np.abs(vec[:, i0])**2).reshape(-1, 2).sum(axis=1)
pos = np.array([s.pos for s in ffin.sites])
edge_mask = ((pos[:, 0] < 3) | (pos[:, 0] > L - 4) |
             (pos[:, 1] < 3) | (pos[:, 1] > W - 4))
edge_frac = dens[edge_mask].sum() / dens.sum()
print(f"lowest state E={ev[i0]:.4f}, {edge_frac:.2f} of weight on the boundary")
assert edge_frac > 0.7
print("PASS section 24 (p+ip)")
