# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# -*- coding: utf-8 -*-
"""Part II cells, sections 24-26 (BBH, Weyl, 3D TI) + closing renumber."""

BBH_MD = r'''---
## 24. The BBH quadrupole — higher-order topology

Benalcazar, Bernevig & Hughes [Science **357**, 61 (2017)] found insulators
whose boundary is *also* gapped, yet still topological: the protected states
live two dimensions down, at the **corners**.  The model is a square lattice
with four sites per cell, $\pi$ flux per plaquette, intra-cell hopping
$\gamma$ and inter-cell hopping $\lambda$:

$$H(\mathbf{k}) = \begin{pmatrix} 0 & q(\mathbf{k}) \\ q^\dagger(\mathbf{k}) & 0
\end{pmatrix},\qquad
q = \begin{pmatrix} \gamma + \lambda e^{ik_x} & \gamma + \lambda e^{ik_y} \\
 -(\gamma + \lambda e^{-ik_y}) & \gamma + \lambda e^{-ik_x} \end{pmatrix}.$$

The dipole (Chern/polarization) invariants all vanish.  The right invariant is
*nested*: first a Wilson loop over $k_y$ at each $k_x$ gives the **Wannier
bands** $\nu_\pm(k_x)$ — themselves gapped, like an effective 1D spectrum —
then the polarization *of a Wannier band* gives the quadrupole moment

$$q_{xy} = \tfrac{1}{2}\ (\gamma < \lambda), \qquad 0\ (\gamma > \lambda).$$

Bulk–boundary correspondence, twice removed: $q_{xy}=1/2$ forces four
zero-energy corner states carrying charge $\pm e/2$ each.'''

BBH_CODE = r'''# --- BBH quadrupole: Wannier bands, nested Wilson loop, corner states ---------
import kwant, numpy as np
from matplotlib import pyplot

gam, lam = 0.3, 1.0                 # topological: gam < lam

def h_bbh(kx, ky, gam=gam, lam=lam):
    q = np.array([[gam + lam * np.exp(1j * kx), gam + lam * np.exp(1j * ky)],
                  [-(gam + lam * np.exp(-1j * ky)), gam + lam * np.exp(-1j * kx)]])
    z = np.zeros((2, 2))
    return np.block([[z, q], [q.conj().T, z]])

def wannier_bands(gam, lam, N=40):
    """Wilson loop over ky at each kx; eigenphases/2pi = Wannier centers."""
    ks = np.linspace(0, 2 * np.pi, N, endpoint=False)
    u = np.empty((N, N), dtype=object)
    for i, kx in enumerate(ks):
        for j, ky in enumerate(ks):
            u[i, j] = np.linalg.eigh(h_bbh(kx, ky, gam, lam))[1][:, :2]
    centers, states = [], []
    for i in range(N):
        W = np.eye(2, dtype=complex)
        for j in range(N):
            F = u[i, j].conj().T @ u[i, (j + 1) % N]
            uu, _, vv = np.linalg.svd(F)        # unitarize the link
            W = W @ (uu @ vv)
        ph, vec = np.linalg.eig(W)
        nu = np.angle(ph) / (2 * np.pi)
        order = np.argsort(nu)
        centers.append(nu[order])
        states.append(u[i, 0] @ vec[:, order])  # Wannier-band basis
    return ks, np.array(centers), states

def nested_polarization(states):
    """Polarization of the upper Wannier band along kx: the quadrupole q_xy."""
    N = len(states)
    prod = 1.0 + 0j
    for i in range(N):
        prod *= np.vdot(states[i][:, 1], states[(i + 1) % N][:, 1])
    return (-np.angle(prod) / (2 * np.pi)) % 1

ks, nu, wst = wannier_bands(gam, lam)
_, nu_t, wst_t = wannier_bands(1.0, 0.3)        # trivial: gam > lam
print(f"quadrupole q_xy:  topological = {nested_polarization(wst):.4f}  "
      f"trivial = {nested_polarization(wst_t):.4f}")

pyplot.plot(ks, nu[:, 0], 'C0', lw=2, label=r'$\nu_-$')
pyplot.plot(ks, nu[:, 1], 'C1', lw=2, label=r'$\nu_+$')
pyplot.plot(ks, nu_t, 'gray', lw=1, ls='--')
pyplot.xlabel(r"$k_x$"); pyplot.ylabel(r"Wannier center $\nu(k_x)$")
pyplot.title("Gapped Wannier bands (colour: topological, dashed: trivial)")
pyplot.legend(); pyplot.grid(alpha=.3); pyplot.show()

# corner states of a finite flake
lat = kwant.lattice.square(norbs=4)

def bbh_flake(gam, lam, Nc=10):
    on = np.array([[0, 0, gam, gam],
                   [0, 0, -gam, gam],
                   [gam, -gam, 0, 0],
                   [gam, gam, 0, 0]], dtype=complex)
    hx = np.zeros((4, 4), dtype=complex); hx[0, 2] = lam; hx[3, 1] = lam
    hy = np.zeros((4, 4), dtype=complex); hy[0, 3] = lam; hy[2, 1] = -lam
    syst = kwant.Builder()
    syst[(lat(x, y) for x in range(Nc) for y in range(Nc))] = on
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = hx
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = hy
    return syst.finalized()

f_top = bbh_flake(gam, lam)
ev, vec = np.linalg.eigh(f_top.hamiltonian_submatrix())
izero = np.argsort(np.abs(ev))[:4]
print("four in-gap corner modes at E =", np.round(ev[izero], 5))

fig, (ax1, ax2) = pyplot.subplots(1, 2, figsize=(11, 4))
ax1.plot(np.arange(len(ev)), ev, 'k.', ms=3)
ax1.plot(izero, ev[izero], 'r.', ms=8)
ax1.set_xlabel("state index"); ax1.set_ylabel("energy")
ax1.set_title("Flake spectrum: 4 zero modes in the gap")
ax1.grid(alpha=.3)
dens = (np.abs(vec[:, izero]) ** 2).sum(axis=1).reshape(-1, 4).sum(axis=1)
kwant.plotter.density(f_top, dens, ax=ax2, cmap='inferno')
ax2.set_title("...and they live on the corners")
pyplot.tight_layout(); pyplot.show()

ev_tri = np.linalg.eigvalsh(bbh_flake(1.0, 0.3).hamiltonian_submatrix())
print(f"trivial flake: smallest |E| = {np.abs(ev_tri).min():.3f}  (no midgap states)")'''

WEYL_MD = r'''---
## 25. Weyl semimetals — Fermi arcs from sliced Chern numbers

A Weyl semimetal needs no gap at all: its band structure holds isolated
touching points that act as **monopoles of Berry curvature** with chirality
$\pm 1$ [Wan *et al.*, PRB **83**, 205101 (2011); Armitage *et al.*, RMP
**90**, 015001 (2018)].  The minimal two-band lattice model

$$H(\mathbf{k}) = t\sin k_x\,\sigma_x + t\sin k_y\,\sigma_y +
\left[m_0 - t(\cos k_x + \cos k_y + \cos k_z)\right]\sigma_z$$

has two Weyl nodes at $(0,0,\pm k_0)$, $\cos k_0 = m_0/t - 2$.  The key
construction: freeze $k_z$ and regard $H(k_x, k_y; k_z)$ as a family of 2D
insulators.  The slice Chern number $C(k_z)$ **jumps by the chirality** when
$k_z$ sweeps through a node — nonzero exactly *between* the nodes.  Each
nontrivial slice contributes one chiral edge state at $E=0$; strung together
over $|k_z|<k_0$ they form the open **Fermi arc** connecting the projected
nodes on a surface — an object impossible in any isolated 2D system.
(A Kwant-based transport study of this model: the
[WEYLFET repository](https://github.com/GUANGZECHEN/WEYLFET).)'''

WEYL_CODE = r'''# --- Weyl semimetal: nodes, sliced Chern numbers, Fermi arcs, transport -------
import kwant, numpy as np
from matplotlib import pyplot

sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])
t, m0 = 1.0, 2.5
k0 = np.arccos(m0 / t - 2)                  # nodes at (0, 0, +-pi/3)

def h_weyl(kx, ky, kz):
    M = m0 - t * (np.cos(kx) + np.cos(ky) + np.cos(kz))
    return t * np.sin(kx) * sx + t * np.sin(ky) * sy + M * sz

print(f"gap at (0,0,+-k0): {np.abs(np.linalg.eigvalsh(h_weyl(0, 0, k0))).min():.1e}"
      f"   (k0 = {k0:.4f})")

# Chern number of each kz slice: +-1 between the nodes, 0 outside
kzs = np.linspace(-np.pi, np.pi, 41)
Cs = [chern_fhs(lambda kx, ky, kz=kz: h_weyl(kx, ky, kz),
                n_occ=1, n1=18, n2=18) for kz in kzs]
pyplot.step(kzs, Cs, where='mid', lw=2)
pyplot.axvline(-k0, color='r', ls=':'); pyplot.axvline(k0, color='r', ls=':')
pyplot.xlabel(r"$k_z$"); pyplot.ylabel(r"$C(k_z)$")
pyplot.title("Slice Chern number jumps by the chirality at each Weyl node")
pyplot.grid(alpha=.3); pyplot.show()

# Fermi arc: slab finite in y; scan (kx, kz) for E~0 surface states
Ny = 30
hop_y = -t * (sz + 1j * sy) / 2             # from -t cos(ky) sz + t sin(ky) sy

def slab_h(kx, kz):
    on = t * np.sin(kx) * sx + (m0 - t * np.cos(kx) - t * np.cos(kz)) * sz
    H = np.zeros((2 * Ny, 2 * Ny), dtype=complex)
    for y in range(Ny):
        H[2*y:2*y+2, 2*y:2*y+2] = on
        if y + 1 < Ny:
            H[2*y:2*y+2, 2*y+2:2*y+4] = hop_y
            H[2*y+2:2*y+4, 2*y:2*y+2] = hop_y.conj().T
    return H

kxs = np.linspace(-1.5, 1.5, 61)
kzs = np.linspace(-np.pi, np.pi, 61)
arc = np.zeros((len(kxs), len(kzs)))
for i, kx in enumerate(kxs):
    for j, kz in enumerate(kzs):
        ev, vec = np.linalg.eigh(slab_h(kx, kz))
        i0 = np.argmin(np.abs(ev))
        if abs(ev[i0]) < 0.05:                       # a state at the Fermi level
            d = (np.abs(vec[:, i0]) ** 2).reshape(Ny, 2).sum(axis=1)
            arc[i, j] = d[:4].sum() + d[-4:].sum()   # ...on the surface?

pyplot.pcolormesh(kzs, kxs, arc, shading='auto', cmap='magma')
pyplot.colorbar(label="surface weight of the E=0 state")
pyplot.plot([-k0, k0], [0, 0], 'c*', ms=12, label="Weyl node projections")
pyplot.xlabel(r"$k_z$"); pyplot.ylabel(r"$k_x$")
pyplot.title("The Fermi arc connects the projected Weyl nodes")
pyplot.legend(); pyplot.show()

# ballistic transport through a Weyl wire: little at the nodes, much away
lat3 = kwant.lattice.cubic(norbs=2)
hops = {(1, 0, 0): -t * (sz + 1j * sx) / 2,
        (0, 1, 0): -t * (sz + 1j * sy) / 2,
        (0, 0, 1): -t * sz / 2}

def weyl_wire(W=8, L=6):
    def fill(syst, rng):
        syst[(lat3(x, y, z) for x in range(W) for y in range(W) for z in rng)] \
            = m0 * sz
        for d, v in hops.items():
            syst[kwant.builder.HoppingKind(d, lat3, lat3)] = v
    syst = kwant.Builder()
    fill(syst, range(L))
    lead = kwant.Builder(kwant.TranslationalSymmetry((0, 0, -1)))
    fill(lead, [0])
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

fw = weyl_wire()
for e in (0.05, 0.3, 0.6):
    print(f"E={e}:  G = {kwant.smatrix(fw, e).transmission(1, 0):.2f} e^2/h")'''

TI3D_MD = r'''---
## 26. The 3D topological insulator — a Dirac cone on every surface

The 3D strong TI [Fu, Kane & Mele, PRL **98**, 106803 (2007); realized in
Bi₂Se₃, Zhang *et al.*, Nat. Phys. **5**, 438 (2009)] is described near the
band inversion by the lattice-regularized Dirac model

$$H(\mathbf{k}) = m(\mathbf{k})\,\tau_z\!\otimes\!\sigma_0
 + \lambda\sum_{i=x,y,z}\sin k_i\ \tau_x\!\otimes\!\sigma_i,
 \qquad m(\mathbf{k}) = m_0 - t\!\sum_i \cos k_i .$$

With inversion symmetry ($P = \tau_z$) the strong $\mathbb{Z}_2$ index
follows from the **Fu–Kane parity criterion**: the product of the occupied
parity eigenvalues over the 8 time-reversal-invariant momenta,

$$(-1)^{\nu_0} = \prod_{\Lambda}\ \prod_{n \in \text{occ}} \xi_n(\Lambda).$$

For $1 < m_0/t < 3$ the band inversion happens at $\Gamma$ alone and
$\nu_0 = 1$.  The surface then *must* carry an odd number of Dirac cones —
a "half" graphene that cannot be gapped by any TRS-preserving perturbation.
Below: the parity count, the surface Dirac cone of a slab (with its
wavefunctions glued to the surfaces), and ballistic surface conduction
through the bulk gap of a 3D bar — absent in the trivial phase.'''

TI3D_CODE = r'''# --- 3D TI: Fu-Kane parities, surface Dirac cone, surface transport -----------
import kwant, numpy as np
from itertools import product
from matplotlib import pyplot

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])
k4 = np.kron

t, lam = 1.0, 1.0
G0, Gx, Gy, Gz = k4(sz, s0), k4(sx, sx), k4(sx, sy), k4(sx, sz)

def h_ti(kx, ky, kz, m0):
    m = m0 - t * (np.cos(kx) + np.cos(ky) + np.cos(kz))
    return m * G0 + lam * (np.sin(kx) * Gx + np.sin(ky) * Gy + np.sin(kz) * Gz)

def fu_kane_nu0(m0):
    prod_par = 1.0
    for trim in product((0.0, np.pi), repeat=3):
        h = h_ti(*trim, m0)
        occ = np.linalg.eigh(h)[1][:, :2]
        par = np.linalg.eigvalsh(occ.conj().T @ G0 @ occ)   # inversion op = G0
        prod_par *= par[0]              # one representative per Kramers pair
    return 0 if prod_par > 0 else 1

for m0 in (2.0, 4.0):
    print(f"m0 = {m0}:  Fu-Kane nu0 = {fu_kane_nu0(m0)}"
          + ("   (strong TI)" if fu_kane_nu0(m0) else "   (trivial)"))

# slab: the surface Dirac cone, coloured by where the state lives
Nz = 20
hop_z = -t * G0 / 2 + lam * Gz / (2j)

def slab_h(kx, ky, m0):
    on = ((m0 - t * np.cos(kx) - t * np.cos(ky)) * G0
          + lam * (np.sin(kx) * Gx + np.sin(ky) * Gy))
    H = np.zeros((4 * Nz, 4 * Nz), dtype=complex)
    for z in range(Nz):
        H[4*z:4*z+4, 4*z:4*z+4] = on
        if z + 1 < Nz:
            H[4*z:4*z+4, 4*z+4:4*z+8] = hop_z
            H[4*z+4:4*z+8, 4*z:4*z+4] = hop_z.conj().T
    return H

kxs = np.linspace(-0.8, 0.8, 81)
fig, axes = pyplot.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, m0, label in zip(axes, (2.0, 4.0), ("strong TI", "trivial")):
    for kx in kxs:
        ev, vec = np.linalg.eigh(slab_h(kx, 0, m0))
        sel = np.abs(ev) < 1.0
        surf = (np.abs(vec[:, sel]) ** 2).reshape(Nz, 4, -1).sum(axis=1)
        w = surf[:3].sum(axis=0) + surf[-3:].sum(axis=0)
        ax.scatter([kx] * sel.sum(), ev[sel], c=w, s=4, cmap='coolwarm',
                   vmin=0, vmax=1)
    ax.set_title(f"$m_0 = {m0}$ ({label})"); ax.set_xlabel(r"$k_x$")
axes[0].set_ylabel("energy $[t]$")
fig.suptitle("Slab spectrum, coloured by surface weight (red = surface)")
pyplot.show()

# transport: in-gap conductance carried by the surface, zero when trivial
lat3 = kwant.lattice.cubic(norbs=4)
hops = {(1, 0, 0): -t * G0 / 2 + lam * Gx / (2j),
        (0, 1, 0): -t * G0 / 2 + lam * Gy / (2j),
        (0, 0, 1): hop_z}

def ti_bar(m0, W=6, L=8):
    def fill(syst, rng):
        syst[(lat3(x, y, z) for x in range(W) for y in range(W) for z in rng)] \
            = m0 * G0
        for d, v in hops.items():
            syst[kwant.builder.HoppingKind(d, lat3, lat3)] = v
    syst = kwant.Builder()
    fill(syst, range(L))
    lead = kwant.Builder(kwant.TranslationalSymmetry((0, 0, -1)))
    fill(lead, [0])
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

E = 0.2                                      # inside the bulk gap
G_top = kwant.smatrix(ti_bar(2.0), E).transmission(1, 0)
G_tri = kwant.smatrix(ti_bar(4.0), E).transmission(1, 0)
print(f"G(E={E}) through a 3D bar:  TI = {G_top:.3f} e^2/h  "
      f"(surface states);  trivial = {G_tri:.2e}")
assert G_top > 1.0 and G_tri < 1e-6'''

CELLS = [
    ("markdown", BBH_MD),
    ("code", BBH_CODE),
    ("markdown", WEYL_MD),
    ("code", WEYL_CODE),
    ("markdown", TI3D_MD),
    ("code", TI3D_CODE),
]
