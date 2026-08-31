# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 21 dev: Rice-Mele Thouless pump — Chern number over (k, phi), edge-mode flow."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np

sigma_x = np.array([[0, 1], [1, 0]])
sigma_z = np.array([[1, 0], [0, -1]])

t0, d0, D0 = 1.0, 0.6, 0.6      # mean hopping, dimerization, staggered onsite

def h_rice_mele(k, phi):
    """Bloch Hamiltonian; pump cycle: (delta, Delta) = (d0 cos phi, D0 sin phi)."""
    t1 = t0 + d0 * np.cos(phi)          # intra-cell hopping
    t2 = t0 - d0 * np.cos(phi)          # inter-cell hopping
    D = D0 * np.sin(phi)                # staggered onsite
    q = t1 + t2 * np.exp(1j * k)
    return np.array([[D, q], [np.conj(q), -D]])

def chern_fhs(hfunc, n_occ, n1=40, n2=40):
    """Chern number by the Fukui-Hatsugai-Suzuki plaquette method.

    hfunc(x1, x2) is a Bloch Hamiltonian periodic in both arguments with
    period 2*pi; the lowest n_occ bands are 'occupied'.
    """
    xs1 = np.linspace(0, 2 * np.pi, n1, endpoint=False)
    xs2 = np.linspace(0, 2 * np.pi, n2, endpoint=False)
    # occupied-state frames on the grid
    frames = np.empty((n1, n2), dtype=object)
    for i, x1 in enumerate(xs1):
        for j, x2 in enumerate(xs2):
            _, v = np.linalg.eigh(hfunc(x1, x2))
            frames[i, j] = v[:, :n_occ]
    def link(a, b):
        m = a.conj().T @ b
        return np.linalg.det(m)
    F_total = 0.0
    for i in range(n1):
        for j in range(n2):
            u1 = link(frames[i, j], frames[(i+1) % n1, j])
            u2 = link(frames[(i+1) % n1, j], frames[(i+1) % n1, (j+1) % n2])
            u3 = link(frames[(i+1) % n1, (j+1) % n2], frames[i, (j+1) % n2])
            u4 = link(frames[i, (j+1) % n2], frames[i, j])
            F_total += np.angle(u1 * u2 * u3 * u4)
    return int(round(F_total / (2 * np.pi)))

C = chern_fhs(h_rice_mele, n_occ=1)
print(f"pumped charge per cycle = Chern number over (k, phi) torus = {C}")
assert abs(C) == 1, C

# no pumping without the onsite modulation (the cycle then encircles nothing)
def h_no_pump(k, phi):
    t1 = t0 + d0 * np.cos(phi)
    t2 = t0 - d0 * np.cos(phi)
    q = t1 + t2 * np.exp(1j * k)
    return np.array([[0, q], [np.conj(q), 0]])

C0 = chern_fhs(h_no_pump, n_occ=1)
assert C0 == 0, C0
print("cycle that does not encircle the gapless point pumps nothing (C=0)  OK")

# --- finite chain: edge modes traverse the gap during the cycle --------------
lat = kwant.lattice.chain(norbs=2)
L = 30

def finite_chain(phi):
    t1 = t0 + d0 * np.cos(phi)
    t2 = t0 - d0 * np.cos(phi)
    D = D0 * np.sin(phi)
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = D * sigma_z + t1 * sigma_x
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        t2 * np.array([[0, 1], [0, 0]])
    return syst.finalized()

phis = np.linspace(0, 2 * np.pi, 61)
spectra = np.array([np.linalg.eigvalsh(finite_chain(p).hamiltonian_submatrix())
                    for p in phis])
# mid-gap states must exist for some phi (edge modes crossing), and the states
# crossing E=0 must be edge-localized
gap_min = np.abs(spectra).min(axis=1)
assert gap_min.min() < 0.05, gap_min.min()
phi_cross = phis[gap_min.argmin()]
h = finite_chain(phi_cross).hamiltonian_submatrix()
ev, vec = np.linalg.eigh(h)
i0 = np.argmin(np.abs(ev))
dens = (np.abs(vec[:, i0])**2).reshape(L, 2).sum(axis=1)
edge_w = dens[:5].sum() + dens[-5:].sum()
assert edge_w > 0.8, edge_w
print(f"edge mode crosses E=0 at phi={phi_cross:.2f}, edge weight {edge_w:.3f}  OK")

# --- Wannier-center flow: polarization winds once per cycle ------------------
def zak_phase(phi, nk=200):
    ks = np.linspace(0, 2 * np.pi, nk, endpoint=False)
    us = [np.linalg.eigh(h_rice_mele(k, phi))[1][:, 0] for k in ks]
    prod = 1.0 + 0j
    for i in range(nk):
        prod *= np.vdot(us[i], us[(i + 1) % nk])
    return -np.angle(prod) / (2 * np.pi)     # polarization in units of e*a

pol = np.unwrap([2 * np.pi * zak_phase(p) for p in phis]) / (2 * np.pi)
winding = pol[-1] - pol[0]
print(f"polarization winding over one cycle: {winding:.4f} (expect +-1)")
assert abs(abs(winding) - 1) < 0.02, winding
print("PASS section 21 (Thouless pump)")
