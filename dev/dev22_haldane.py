# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 22 dev: Haldane model — Chern number, chiral edge states, quantized G."""
import matplotlib
matplotlib.use("Agg")
import kwant, kwant.wraparound, numpy as np

t1_h, t2_h = 1.0, 0.15          # NN and NNN hopping strengths
lat = kwant.lattice.honeycomb(norbs=1)
a_sub, b_sub = lat.sublattices

nnn_a = [kwant.builder.HoppingKind(v, a_sub, a_sub)
         for v in [(1, 0), (-1, 1), (0, -1)]]
nnn_b = [kwant.builder.HoppingKind(v, b_sub, b_sub)
         for v in [(1, 0), (-1, 1), (0, -1)]]

def haldane_bulk(M, phi):
    syst = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs))
    syst[a_sub(0, 0)] = M
    syst[b_sub(0, 0)] = -M
    syst[lat.neighbors()] = t1_h
    for kind in nnn_a:
        syst[kind] = t2_h * np.exp(1j * phi)
    for kind in nnn_b:
        syst[kind] = t2_h * np.exp(-1j * phi)
    return syst

def bloch_hamiltonian(bulk_builder):
    """H(theta1, theta2) with theta_i the phase across primitive vector i."""
    wrapped = kwant.wraparound.wraparound(bulk_builder).finalized()
    b1, b2 = 2 * np.pi * np.linalg.inv(np.array(lat.prim_vecs)).T
    def hfunc(th1, th2):
        k = (th1 * b1 + th2 * b2) / (2 * np.pi)
        return wrapped.hamiltonian_submatrix(params=dict(k_x=k[0], k_y=k[1]))
    return hfunc

def chern_fhs(hfunc, n_occ, n1=30, n2=30):
    xs1 = np.linspace(0, 2 * np.pi, n1, endpoint=False)
    xs2 = np.linspace(0, 2 * np.pi, n2, endpoint=False)
    frames = np.empty((n1, n2), dtype=object)
    for i, x1 in enumerate(xs1):
        for j, x2 in enumerate(xs2):
            _, v = np.linalg.eigh(hfunc(x1, x2))
            frames[i, j] = v[:, :n_occ]
    def link(a, b):
        return np.linalg.det(a.conj().T @ b)
    F = 0.0
    for i in range(n1):
        for j in range(n2):
            u1 = link(frames[i, j], frames[(i+1) % n1, j])
            u2 = link(frames[(i+1) % n1, j], frames[(i+1) % n1, (j+1) % n2])
            u3 = link(frames[(i+1) % n1, (j+1) % n2], frames[i, (j+1) % n2])
            u4 = link(frames[i, (j+1) % n2], frames[i, j])
            F += np.angle(u1 * u2 * u3 * u4)
    return int(round(F / (2 * np.pi)))

# --- phase diagram checks: |M| < 3 sqrt(3) t2 sin(phi) is topological --------
Mc = 3 * np.sqrt(3) * t2_h            # ~0.779 at phi = pi/2
C_top = chern_fhs(bloch_hamiltonian(haldane_bulk(0.0, np.pi / 2)), n_occ=1)
C_tri = chern_fhs(bloch_hamiltonian(haldane_bulk(1.3 * Mc, np.pi / 2)), n_occ=1)
C_opp = chern_fhs(bloch_hamiltonian(haldane_bulk(0.0, -np.pi / 2)), n_occ=1)
print(f"Chern: M=0 phi=+pi/2 -> {C_top};  M=1.3Mc -> {C_tri};  phi=-pi/2 -> {C_opp}")
assert abs(C_top) == 1 and C_tri == 0 and C_opp == -C_top

# --- zigzag ribbon: chiral edge states crossing the bulk gap -----------------
def haldane_ribbon(M, phi, W=12):
    sym = kwant.TranslationalSymmetry(lat.vec((1, 0)))
    syst = kwant.Builder(sym)
    ribbon = lambda pos: 0 <= pos[1] < W * np.sqrt(3) / 2
    syst[lat.shape(ribbon, (0, 0))] = \
        lambda s: M if s.family == a_sub else -M
    syst[lat.neighbors()] = t1_h
    for kind in nnn_a:
        syst[kind] = t2_h * np.exp(1j * phi)
    for kind in nnn_b:
        syst[kind] = t2_h * np.exp(-1j * phi)
    return syst

frib = haldane_ribbon(0.0, np.pi / 2).finalized()
bands = kwant.physics.Bands(frib)
# somewhere in the BZ a chiral edge mode must cross E=0 inside the bulk gap
ks = np.linspace(-np.pi, np.pi, 201)
min_abs_e = min(np.abs(bands(k)).min() for k in ks)
print(f"lowest |E| across ribbon BZ: {min_abs_e:.4f} (bulk gap ~ {Mc:.2f})")
assert min_abs_e < 0.05 * Mc

# --- transport: quantized two-terminal conductance, robust to disorder -------
def haldane_bar(M, phi, W=10, L=16, U0=0.0, salt="a"):
    syst = kwant.Builder()
    shape = lambda pos: (0 <= pos[0] < L) and (0 <= pos[1] < W * np.sqrt(3) / 2)
    def onsite(s):
        m = M if s.family == a_sub else -M
        return m + U0 * (kwant.digest.uniform(repr(s.tag) + s.family.name, salt) - 0.5)
    syst[lat.shape(shape, (0, 0))] = onsite
    syst[lat.neighbors()] = t1_h
    for kind in nnn_a:
        syst[kind] = t2_h * np.exp(1j * phi)
    for kind in nnn_b:
        syst[kind] = t2_h * np.exp(-1j * phi)
    syst.eradicate_dangling()
    lead = haldane_ribbon(M, phi, W=W)
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

E = 0.15                                   # well inside the bulk gap
T_clean = kwant.smatrix(haldane_bar(0.0, np.pi / 2), E).transmission(1, 0)
T_dirty = kwant.smatrix(haldane_bar(0.0, np.pi / 2, U0=0.6), E).transmission(1, 0)
print(f"T(E={E}): clean={T_clean:.6f}  disordered(U0=0.6)={T_dirty:.6f}")
assert abs(T_clean - 1.0) < 1e-6
assert abs(T_dirty - 1.0) < 1e-3          # chiral edge cannot backscatter
print("PASS section 22 (Haldane)")
