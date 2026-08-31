# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 25 dev: BBH quadrupole insulator — Wannier bands, nested Wilson loop, corner states."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np

gam, lam = 0.3, 1.0          # intra-cell and inter-cell hopping (topological: gam < lam)

def h_bbh(kx, ky, gam=gam, lam=lam):
    q = np.array([[gam + lam * np.exp(1j * kx), gam + lam * np.exp(1j * ky)],
                  [-(gam + lam * np.exp(-1j * ky)), gam + lam * np.exp(-1j * kx)]])
    z = np.zeros((2, 2))
    return np.block([[z, q], [q.conj().T, z]])

# --- kwant real-space construction, checked against the Bloch matrix ---------
lat = kwant.lattice.square(norbs=4)

H_onsite = np.array([[0, 0, gam, gam],
                     [0, 0, -gam, gam],
                     [gam, -gam, 0, 0],
                     [gam, gam, 0, 0]], dtype=complex)
H_x = np.zeros((4, 4), dtype=complex); H_x[0, 2] = lam; H_x[3, 1] = lam
H_y = np.zeros((4, 4), dtype=complex); H_y[0, 3] = lam; H_y[2, 1] = -lam

import kwant.wraparound
bulk = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs))
bulk[lat(0, 0)] = H_onsite
bulk[kwant.builder.HoppingKind((1, 0), lat, lat)] = H_x
bulk[kwant.builder.HoppingKind((0, 1), lat, lat)] = H_y
wrapped = kwant.wraparound.wraparound(bulk).finalized()
for kx, ky in [(0.3, 1.1), (2.0, -0.7)]:
    hk = wrapped.hamiltonian_submatrix(params=dict(k_x=kx, k_y=ky))
    ha = h_bbh(kx, ky)
    assert np.allclose(np.linalg.eigvalsh(hk), np.linalg.eigvalsh(ha)), (kx, ky)
print("kwant real-space BBH matches the Bloch Hamiltonian  OK")

# --- Wannier bands and nested Wilson loop ------------------------------------
def occupied_frames(gam, lam, N=40):
    ks = np.linspace(0, 2 * np.pi, N, endpoint=False)
    u = np.empty((N, N), dtype=object)
    for i, kx in enumerate(ks):
        for j, ky in enumerate(ks):
            _, v = np.linalg.eigh(h_bbh(kx, ky, gam, lam))
            u[i, j] = v[:, :2]
    return ks, u

def wannier_bands(gam, lam, N=40):
    """Wilson loop along ky at each kx: eigenphases/2pi = Wannier centers."""
    ks, u = occupied_frames(gam, lam, N)
    centers, states = [], []
    for i in range(N):
        W = np.eye(2, dtype=complex)
        for j in range(N):
            F = u[i, j].conj().T @ u[i, (j + 1) % N]
            # unitarize the link (removes discretization leakage)
            uu, _, vv = np.linalg.svd(F)
            W = W @ (uu @ vv)
        ph, vec = np.linalg.eig(W)
        nu = np.angle(ph) / (2 * np.pi)
        order = np.argsort(nu)
        centers.append(nu[order])
        states.append((u[i, 0] @ vec[:, order]))     # Wannier band basis at ky=0
    return ks, np.array(centers), states

ks, nu, wstates = wannier_bands(gam, lam)
print(f"Wannier bands: nu- in [{nu[:,0].min():.3f},{nu[:,0].max():.3f}], "
      f"nu+ in [{nu[:,1].min():.3f},{nu[:,1].max():.3f}]")
# topological: the two Wannier bands are gapped and straddle +-1/4-ish
assert nu[:, 1].min() > 0.05 and nu[:, 0].max() < -0.05, "Wannier gap must be open"

def nested_polarization(states):
    """Polarization of the upper Wannier band along kx (nested Wilson loop)."""
    N = len(states)
    prod = 1.0 + 0j
    for i in range(N):
        w1, w2 = states[i][:, 1], states[(i + 1) % N][:, 1]
        prod *= np.vdot(w1, w2)
    return (-np.angle(prod) / (2 * np.pi)) % 1

p_top = nested_polarization(wstates)
_, _, wstates_triv = wannier_bands(1.0, 0.3)     # gam > lam: trivial
p_tri = nested_polarization(wstates_triv)
print(f"nested polarization: topological={p_top:.4f} (expect 1/2), "
      f"trivial={p_tri:.4f} (expect 0)")
assert abs(p_top - 0.5) < 0.02, p_top
assert min(p_tri, 1 - p_tri) < 0.02, p_tri

# --- corner states in a finite flake -----------------------------------------
def bbh_matrices(gam, lam):
    on = np.array([[0, 0, gam, gam],
                   [0, 0, -gam, gam],
                   [gam, -gam, 0, 0],
                   [gam, gam, 0, 0]], dtype=complex)
    hx = np.zeros((4, 4), dtype=complex); hx[0, 2] = lam; hx[3, 1] = lam
    hy = np.zeros((4, 4), dtype=complex); hy[0, 3] = lam; hy[2, 1] = -lam
    return on, hx, hy

def bbh_flake(gam, lam, Nc=10):
    on, hx, hy = bbh_matrices(gam, lam)
    syst = kwant.Builder()
    syst[(lat(x, y) for x in range(Nc) for y in range(Nc))] = on
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = hx
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = hy
    return syst.finalized()

f_top = bbh_flake(gam, lam)
ev, vec = np.linalg.eigh(f_top.hamiltonian_submatrix())
n_zero = int(np.sum(np.abs(ev) < 0.05))
assert n_zero == 4, n_zero
izero = np.argsort(np.abs(ev))[:4]
dens = (np.abs(vec[:, izero])**2).sum(axis=1).reshape(-1, 4).sum(axis=1)
pos = np.array([s.pos for s in f_top.sites])
Nc = 10
corner_mask = ((pos[:, 0] < 2) | (pos[:, 0] > Nc - 3)) & \
              ((pos[:, 1] < 2) | (pos[:, 1] > Nc - 3))
frac = dens[corner_mask].sum() / dens.sum()
print(f"4 zero modes, {frac:.2f} of weight in the 4 corners")
assert frac > 0.85, frac

ev_tri = np.linalg.eigvalsh(bbh_flake(1.0, 0.3).hamiltonian_submatrix())
assert np.sum(np.abs(ev_tri) < 0.05) == 0, "trivial flake must have no midgap states"
print("trivial flake: no corner modes  OK")
print("PASS section 25 (BBH)")
