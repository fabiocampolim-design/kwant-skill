# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 23 dev: Kane-Mele — spin Chern number, helical edges, G=2, Rashba robustness."""
import matplotlib
matplotlib.use("Agg")
import kwant, kwant.wraparound, numpy as np

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])

t1_km, lam_so = 1.0, 0.1
lat = kwant.lattice.honeycomb(norbs=2)          # 2 orbitals = spin
a_sub, b_sub = lat.sublattices

nnn_a = [kwant.builder.HoppingKind(v, a_sub, a_sub)
         for v in [(1, 0), (-1, 1), (0, -1)]]
nnn_b = [kwant.builder.HoppingKind(v, b_sub, b_sub)
         for v in [(1, 0), (-1, 1), (0, -1)]]

def rashba_nn(lam_r):
    def val(s1, s2):
        d = s1.pos - s2.pos
        return t1_km * s0 + 1j * lam_r * (sx * d[1] - sy * d[0])
    return val


def km_bulk(M=0.0, lam_r=0.0):
    syst = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs))
    syst[a_sub(0, 0)] = M * s0
    syst[b_sub(0, 0)] = -M * s0
    syst[lat.neighbors()] = rashba_nn(lam_r)
    for kind in nnn_a:
        syst[kind] = 1j * lam_so * sz
    for kind in nnn_b:
        syst[kind] = -1j * lam_so * sz
    return syst

def bloch_hamiltonian(bulk_builder):
    wrapped = kwant.wraparound.wraparound(bulk_builder).finalized()
    b1, b2 = 2 * np.pi * np.linalg.inv(np.array(lat.prim_vecs)).T
    def hfunc(th1, th2):
        k = (th1 * b1 + th2 * b2) / (2 * np.pi)
        return wrapped.hamiltonian_submatrix(params=dict(k_x=k[0], k_y=k[1]))
    return hfunc

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

# --- spin Chern numbers (Sz conserved when lam_r = 0) ------------------------
h_full = bloch_hamiltonian(km_bulk())
def spin_block(hfunc, s):
    """Extract the spin-s block; basis per site is (up, dn)."""
    idx = np.array([0, 2]) + (0 if s == 'up' else 1)
    return lambda t1, t2: hfunc(t1, t2)[np.ix_(idx, idx)]

C_up = chern_fhs(spin_block(h_full, 'up'), n_occ=1)
C_dn = chern_fhs(spin_block(h_full, 'dn'), n_occ=1)
C_tot = chern_fhs(h_full, n_occ=2)
print(f"C_up={C_up}  C_dn={C_dn}  C_total={C_tot}  -> Z2 = {(C_up - C_dn) // 2 % 2}")
assert C_up == -C_dn and abs(C_up) == 1 and C_tot == 0

# trivial for M > 3 sqrt(3) lam_so
Mc = 3 * np.sqrt(3) * lam_so
h_triv = bloch_hamiltonian(km_bulk(M=1.5 * Mc))
assert chern_fhs(spin_block(h_triv, 'up'), n_occ=1) == 0
print(f"M > 3*sqrt(3)*lam_so = {Mc:.3f} destroys the QSH phase  OK")

# --- ribbon: helical edge states, with and without Rashba --------------------
def km_ribbon(M=0.0, lam_r=0.0, W=12):
    syst = kwant.Builder(kwant.TranslationalSymmetry(lat.vec((1, 0))))
    syst[lat.shape(lambda p: 0 <= p[1] < W * np.sqrt(3) / 2, (0, 0))] = \
        lambda s: (M if s.family == a_sub else -M) * s0
    syst[lat.neighbors()] = rashba_nn(lam_r)
    for kind in nnn_a:
        syst[kind] = 1j * lam_so * sz
    for kind in nnn_b:
        syst[kind] = -1j * lam_so * sz
    return syst

ks = np.linspace(-np.pi, np.pi, 201)
for lam_r, label in ((0.0, "no Rashba"), (0.05, "Rashba 0.05")):
    bands = kwant.physics.Bands(km_ribbon(lam_r=lam_r).finalized())
    min_e = min(np.abs(bands(k)).min() for k in ks)
    print(f"{label}: min |E| across BZ = {min_e:.5f}")
    assert min_e < 0.02          # helical crossing survives TRS-preserving Rashba

# --- transport: G = 2 e^2/h, robust to TRS-preserving disorder ---------------
def km_bar(M=0.0, lam_r=0.0, U0=0.0, W=10, L=16, salt="km"):
    syst = kwant.Builder()
    shape = lambda p: (0 <= p[0] < L) and (0 <= p[1] < W * np.sqrt(3) / 2)
    def onsite(s):
        m = M if s.family == a_sub else -M
        dis = U0 * (kwant.digest.uniform(repr(s.tag) + s.family.name, salt) - 0.5)
        return (m + dis) * s0
    syst[lat.shape(shape, (0, 0))] = onsite
    syst[lat.neighbors()] = rashba_nn(lam_r)
    for kind in nnn_a:
        syst[kind] = 1j * lam_so * sz
    for kind in nnn_b:
        syst[kind] = -1j * lam_so * sz
    syst.eradicate_dangling()
    lead = km_ribbon(M=M, lam_r=lam_r, W=W)
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

E = 0.1                                     # inside the SOC gap (~0.52)
T_clean = kwant.smatrix(km_bar(), E).transmission(1, 0)
T_dirty = kwant.smatrix(km_bar(U0=0.4), E).transmission(1, 0)
T_rash = kwant.smatrix(km_bar(lam_r=0.05, U0=0.4), E).transmission(1, 0)
print(f"T(E={E}): clean={T_clean:.5f}  disorder={T_dirty:.5f}  disorder+Rashba={T_rash:.5f}")
assert abs(T_clean - 2.0) < 1e-6
assert abs(T_dirty - 2.0) < 1e-2
assert abs(T_rash - 2.0) < 1e-2
print("PASS section 23 (Kane-Mele)")
