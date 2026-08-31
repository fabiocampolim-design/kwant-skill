# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 27 dev: 3D topological insulator — Fu-Kane parity invariant, surface Dirac cone, transport."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np
from itertools import product

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])
k4 = np.kron

# H(k) = m(k) tau_z x s_0 + lam * sum_i sin(k_i) tau_x x s_i,  m = m0 - t*sum cos k_i
t, lam = 1.0, 1.0
G0 = k4(sz, s0)
Gx, Gy, Gz = k4(sx, sx), k4(sx, sy), k4(sx, sz)

def h_ti(kx, ky, kz, m0):
    m = m0 - t * (np.cos(kx) + np.cos(ky) + np.cos(kz))
    return (m * G0 + lam * (np.sin(kx) * Gx + np.sin(ky) * Gy
                            + np.sin(kz) * Gz))

# --- Fu-Kane: parity products at the 8 TRIM ----------------------------------
def fu_kane_nu0(m0):
    P = G0                                  # inversion operator
    prod = 1.0
    for trim in product((0.0, np.pi), repeat=3):
        h = h_ti(*trim, m0)
        assert np.allclose(h @ P - P @ h, 0)          # [H, P] = 0 at TRIM
        ev, vec = np.linalg.eigh(h)
        occ = vec[:, :2]
        # parity of the (doubly degenerate) occupied Kramers pair
        par = np.linalg.eigvalsh(occ.conj().T @ P @ occ)
        assert np.allclose(np.abs(par), 1)
        prod *= par[0]                     # one representative per Kramers pair
    return 0 if prod > 0 else 1            # nu0 = 1 <=> strong TI

nu_top = fu_kane_nu0(2.0)
nu_tri = fu_kane_nu0(4.0)
print(f"Fu-Kane nu0: m0=2 -> {nu_top} (strong TI);  m0=4 -> {nu_tri} (trivial)")
assert nu_top == 1 and nu_tri == 0

# --- slab: surface Dirac cone -------------------------------------------------
Nz = 20

def slab_h(kx, ky, m0):
    on = ((m0 - t * np.cos(kx) - t * np.cos(ky)) * G0
          + lam * (np.sin(kx) * Gx + np.sin(ky) * Gy))
    hop = -t * G0 / 2 + lam * Gz / (2j)     # from -t cos kz G0 + lam sin kz Gz
    H = np.zeros((4 * Nz, 4 * Nz), dtype=complex)
    for z in range(Nz):
        H[4*z:4*z+4, 4*z:4*z+4] = on
        if z + 1 < Nz:
            H[4*z:4*z+4, 4*z+4:4*z+8] = hop
            H[4*z+4:4*z+8, 4*z:4*z+4] = hop.conj().T
    return H

# gapless at Gamma-bar for the TI, gapped for the trivial phase
e_top = np.abs(np.linalg.eigvalsh(slab_h(0, 0, 2.0))).min()
e_tri = np.abs(np.linalg.eigvalsh(slab_h(0, 0, 4.0))).min()
print(f"slab gap at Gamma-bar: TI={e_top:.5f}  trivial={e_tri:.3f}")
assert e_top < 5e-3 and e_tri > 0.3

# surface localization and linear (Dirac) dispersion
ev, vec = np.linalg.eigh(slab_h(0, 0, 2.0))
i0 = np.argmin(np.abs(ev))
dens = (np.abs(vec[:, i0])**2).reshape(Nz, 4).sum(axis=1)
surf = dens[:4].sum() + dens[-4:].sum()
assert surf > 0.7, surf
dk = 0.05
e_dk = np.abs(np.linalg.eigvalsh(slab_h(dk, 0, 2.0))).min()
v_num = e_dk / dk
print(f"surface weight {surf:.2f}; Dirac velocity ~ {v_num:.3f} (lam = {lam})")
assert abs(v_num - lam) < 0.15 * lam        # E = lam*|k| near the cone

# --- transport: surface states conduct through the bulk gap -------------------
lat3 = kwant.lattice.cubic(norbs=4)
hop_dir = {(1, 0, 0): -t * G0 / 2 + lam * Gx / (2j),
           (0, 1, 0): -t * G0 / 2 + lam * Gy / (2j),
           (0, 0, 1): -t * G0 / 2 + lam * Gz / (2j)}

def ti_bar(m0, W=6, L=8):
    def fill(syst, rng):
        syst[(lat3(x, y, z) for x in range(W) for y in range(W) for z in rng)] \
            = m0 * G0
        for d, v in hop_dir.items():
            syst[kwant.builder.HoppingKind(d, lat3, lat3)] = v
    syst = kwant.Builder()
    fill(syst, range(L))
    lead = kwant.Builder(kwant.TranslationalSymmetry((0, 0, -1)))
    fill(lead, [0])
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

E = 0.2                                     # inside the bulk gap (gap ~ 1)
G_top = kwant.smatrix(ti_bar(2.0), E).transmission(1, 0)
G_tri = kwant.smatrix(ti_bar(4.0), E).transmission(1, 0)
print(f"G(E={E}): TI={G_top:.3f} (surface modes)  trivial={G_tri:.2e}")
assert G_top > 1.0
assert G_tri < 1e-6
print("PASS section 27 (3D TI)")
