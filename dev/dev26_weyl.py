# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 26 dev: Weyl semimetal — nodes, kz-sliced Chern numbers, Fermi arcs, transport."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np

sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])

t, m0 = 1.0, 2.5             # Weyl nodes at (0, 0, +-k0) with cos k0 = m0/t - 2
k0 = np.arccos(m0 / t - 2)   # = pi/3

def h_weyl(kx, ky, kz):
    M = m0 - t * (np.cos(kx) + np.cos(ky) + np.cos(kz))
    return t * np.sin(kx) * sx + t * np.sin(ky) * sy + M * sz

# --- nodes exactly where predicted ------------------------------------------
for kz, expect_gapless in [(k0, True), (-k0, True), (0.0, False), (np.pi, False)]:
    gap = np.abs(np.linalg.eigvalsh(h_weyl(0, 0, kz))).min()
    assert (gap < 1e-12) == expect_gapless, (kz, gap)
print(f"Weyl nodes at (0,0,+-{k0:.4f})  OK")

# --- Chern number of 2D slices: the topological fingerprint ------------------
def chern_slice(kz, n=25):
    ks = np.linspace(0, 2 * np.pi, n, endpoint=False)
    frames = np.empty((n, n), dtype=object)
    for i, kx in enumerate(ks):
        for j, ky in enumerate(ks):
            _, v = np.linalg.eigh(h_weyl(kx, ky, kz))
            frames[i, j] = v[:, :1]
    link = lambda a, b: np.linalg.det(a.conj().T @ b)
    F = 0.0
    for i in range(n):
        for j in range(n):
            u1 = link(frames[i, j], frames[(i+1) % n, j])
            u2 = link(frames[(i+1) % n, j], frames[(i+1) % n, (j+1) % n])
            u3 = link(frames[(i+1) % n, (j+1) % n], frames[i, (j+1) % n])
            u4 = link(frames[i, (j+1) % n], frames[i, j])
            F += np.angle(u1 * u2 * u3 * u4)
    return int(round(F / (2 * np.pi)))

C_in = chern_slice(0.0)          # between the nodes
C_out = chern_slice(2.0)         # outside (|kz| > k0)
print(f"slice Chern numbers: C(kz=0)={C_in}  C(kz=2.0)={C_out}")
assert abs(C_in) == 1 and C_out == 0

# --- Fermi arcs: slab finite in y, momenta (kx, kz) --------------------------
Ny = 30
lat = kwant.lattice.chain(norbs=2)      # chain along y; kx, kz are parameters

def slab_h(kx, kz):
    """Slab Hamiltonian: explicit matrix, hopping in y from cos/sin expansion."""
    on = t * np.sin(kx) * sx + (m0 - t * np.cos(kx) - t * np.cos(kz)) * sz
    hop = -t * (sz + 1j * sy) / 2
    H = np.zeros((2 * Ny, 2 * Ny), dtype=complex)
    for y in range(Ny):
        H[2*y:2*y+2, 2*y:2*y+2] = on
        if y + 1 < Ny:
            H[2*y:2*y+2, 2*y+2:2*y+4] = hop
            H[2*y+2:2*y+4, 2*y:2*y+2] = hop.conj().T
    return H

def surface_zero_mode(kx, kz, esmall=0.05):
    ev, vec = np.linalg.eigh(slab_h(kx, kz))
    i0 = np.argmin(np.abs(ev))
    if abs(ev[i0]) > esmall:
        return False, None
    dens = (np.abs(vec[:, i0])**2).reshape(Ny, 2).sum(axis=1)
    surf = dens[:4].sum() + dens[-4:].sum()
    return True, surf

# between the projected nodes: E~0 state localized on the surface (the arc)
ok, surf = surface_zero_mode(0.0, 0.0)
assert ok and surf > 0.6, (ok, surf)
print(f"kz=0, kx=0: E~0 state with {surf:.2f} weight on surfaces (Fermi arc)  OK")
# outside the projections: gapped
ok, _ = surface_zero_mode(0.0, 2.6)
assert not ok
print("kz=2.6: no zero mode (outside the arc)  OK")

# --- transport: point-node ballistic conductance -----------------------------
lat3 = kwant.lattice.cubic(norbs=2)
hop_x = -t * (sz - 1j * sx) / 2      # from sin kx sx + (-t cos kx) sz
hop_y = -t * (sz - 1j * sy) / 2
hop_z = -t * sz / 2

def weyl_wire(W=8):
    """Wire along z, cross-section W x W."""
    syst = kwant.Builder(kwant.TranslationalSymmetry((0, 0, -1)))
    syst[(lat3(x, y, 0) for x in range(W) for y in range(W))] = m0 * sz
    syst[kwant.builder.HoppingKind((1, 0, 0), lat3, lat3)] = hop_x
    syst[kwant.builder.HoppingKind((0, 1, 0), lat3, lat3)] = hop_y
    syst[kwant.builder.HoppingKind((0, 0, 1), lat3, lat3)] = hop_z
    return syst

lead = weyl_wire()
syst = kwant.Builder()
W = 8
syst[(lat3(x, y, z) for x in range(W) for y in range(W) for z in range(6))] = m0 * sz
syst[kwant.builder.HoppingKind((1, 0, 0), lat3, lat3)] = hop_x
syst[kwant.builder.HoppingKind((0, 1, 0), lat3, lat3)] = hop_y
syst[kwant.builder.HoppingKind((0, 0, 1), lat3, lat3)] = hop_z
syst.attach_lead(lead)
syst.attach_lead(lead.reversed())
fsyst = syst.finalized()

G = {e: kwant.smatrix(fsyst, e).transmission(1, 0) for e in (0.05, 0.6)}
print(f"Weyl wire conductance: G(0.05)={G[0.05]:.2f}  G(0.6)={G[0.6]:.2f}")
assert G[0.6] > G[0.05]          # few states at the nodes, many away from them
print("PASS section 26 (Weyl)")
