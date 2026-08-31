# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# -*- coding: utf-8 -*-
"""Part II cells, sections 21-23 (2D: Haldane, Kane-Mele, p+ip)."""

HALDANE_MD = r'''---
## 21. The Haldane model — a Chern insulator without Landau levels

Haldane [PRL **61**, 2015 (1988)] showed that the quantum Hall effect needs no
net magnetic field — only broken time-reversal symmetry.  Take graphene, add a
staggered sublattice potential $\pm M$ and complex second-neighbour hoppings
$t_2 e^{\pm i\phi}$ (the sign set by the chirality of the path):

$$H = t_1\!\!\sum_{\langle ij\rangle}\! c_i^\dagger c_j
    + t_2\!\!\sum_{\langle\langle ij\rangle\rangle}\!\! e^{i\nu_{ij}\phi}\, c_i^\dagger c_j
    + M\sum_i \xi_i\, c_i^\dagger c_i .$$

The phase diagram in $(\phi, M/t_2)$ contains lobes with Chern number
$C = \pm 1$ bounded by $|M| = 3\sqrt{3}\, t_2 \sin\phi$.  Consequences, all
verified below:

* $C$ computed by the FHS formula jumps between $0$ and $\pm 1$ exactly at the
  predicted boundary;
* a ribbon carries one **chiral** edge mode per edge crossing the bulk gap;
* the two-terminal conductance is quantized at $C\,e^2/h$ and — because a
  chiral mode has no backward channel to scatter into — *completely immune to
  disorder*.

(See topocondmat.org week 4; PythTB's `haldane_bp` example computes the same
Berry curvature.)'''

HALDANE_CODE1 = r'''# --- Haldane model: Bloch Hamiltonian from kwant + Chern phase diagram --------
import kwant, kwant.wraparound, numpy as np
from matplotlib import pyplot

t1_h, t2_h = 1.0, 0.15
lat = kwant.lattice.honeycomb(norbs=1)
a_sub, b_sub = lat.sublattices
nnn_a = [kwant.builder.HoppingKind(v, a_sub, a_sub)
         for v in [(1, 0), (-1, 1), (0, -1)]]      # one chirality class
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

def bloch_hamiltonian(bulk_builder, prim_vecs):
    """H(theta1, theta2), theta_i = phase across primitive vector i.

    Works for any 2D lattice: wraparound gives H(k) in Cartesian momenta;
    mapping through the reciprocal vectors makes it 2pi-periodic in theta,
    which is what chern_fhs (section 20) expects.
    """
    wrapped = kwant.wraparound.wraparound(bulk_builder).finalized()
    b1, b2 = 2 * np.pi * np.linalg.inv(np.array(prim_vecs)).T
    def hfunc(th1, th2):
        k = (th1 * b1 + th2 * b2) / (2 * np.pi)
        return wrapped.hamiltonian_submatrix(params=dict(k_x=k[0], k_y=k[1]))
    return hfunc

Mc = 3 * np.sqrt(3) * t2_h
for M, phi, label in [(0.0, np.pi / 2, "centre of the C=+1 lobe"),
                      (1.3 * Mc, np.pi / 2, "above the lobe"),
                      (0.0, -np.pi / 2, "opposite chirality")]:
    C = chern_fhs(bloch_hamiltonian(haldane_bulk(M, phi), lat.prim_vecs),
                  n_occ=1, n1=24, n2=24)
    print(f"M={M:5.2f}, phi={phi:+.2f}:  C = {C:+d}   ({label})")

# the celebrated phase diagram, computed pointwise
phis = np.linspace(-np.pi, np.pi, 15)
Ms = np.linspace(-1.5 * Mc, 1.5 * Mc, 13)
Cmap = np.array([[chern_fhs(bloch_hamiltonian(haldane_bulk(M, phi),
                                              lat.prim_vecs),
                            n_occ=1, n1=16, n2=16)
                  for phi in phis] for M in Ms])

pyplot.pcolormesh(phis, Ms / Mc, Cmap, shading='auto', cmap='RdBu_r',
                  vmin=-1.5, vmax=1.5)
pyplot.colorbar(label="Chern number")
ph = np.linspace(-np.pi, np.pi, 200)
pyplot.plot(ph, np.sin(ph) * np.ones_like(ph) * 1.0, 'k--', lw=1,
            label=r"$M = 3\sqrt{3}t_2\sin\phi$")
pyplot.plot(ph, -np.sin(ph), 'k--', lw=1)
pyplot.xlabel(r"$\phi$"); pyplot.ylabel(r"$M / 3\sqrt{3}t_2$")
pyplot.title("Haldane phase diagram from the FHS Chern number")
pyplot.legend(loc='upper right'); pyplot.show()'''

HALDANE_CODE2 = r'''# --- Haldane: chiral edge states and disorder-proof conductance ---------------
import kwant, numpy as np
from matplotlib import pyplot

def haldane_ribbon(M, phi, W=12):
    syst = kwant.Builder(kwant.TranslationalSymmetry(lat.vec((1, 0))))
    syst[lat.shape(lambda p: 0 <= p[1] < W * np.sqrt(3) / 2, (0, 0))] = \
        lambda s: M if s.family == a_sub else -M
    syst[lat.neighbors()] = t1_h
    for kind in nnn_a:
        syst[kind] = t2_h * np.exp(1j * phi)
    for kind in nnn_b:
        syst[kind] = t2_h * np.exp(-1j * phi)
    return syst

frib = haldane_ribbon(0.0, np.pi / 2).finalized()
fig, ax = pyplot.subplots()
kwant.plotter.bands(frib, momenta=np.linspace(-np.pi, np.pi, 201), ax=ax)
ax.set_ylim(-1.5, 1.5)
ax.axhspan(-Mc, Mc, color='y', alpha=.15)
ax.set_xlabel("momentum"); ax.set_ylabel("energy $[t_1]$")
ax.set_title("Haldane ribbon: one chiral edge mode per edge crosses the gap")
pyplot.show()

def haldane_bar(M, phi, W=10, L=16, U0=0.0, salt="a"):
    syst = kwant.Builder()
    shape = lambda p: (0 <= p[0] < L) and (0 <= p[1] < W * np.sqrt(3) / 2)
    def onsite(s):
        m = M if s.family == a_sub else -M
        return m + U0 * (kwant.digest.uniform(repr(s.tag) + s.family.name,
                                              salt) - 0.5)
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

E = 0.15                                        # inside the bulk gap
for U0 in (0.0, 0.3, 0.6):
    T = kwant.smatrix(haldane_bar(0.0, np.pi / 2, U0=U0), E).transmission(1, 0)
    print(f"disorder U0={U0}:  T = {T:.6f}   (chiral edge: no backscattering)")
    assert abs(T - 1.0) < 1e-3'''

KM_MD = r'''---
## 22. The Kane–Mele model — Z₂ and the quantum spin Hall effect

Kane & Mele [PRL **95**, 226801 (2005)] asked what intrinsic spin–orbit
coupling does to graphene.  The answer founded the field of topological
insulators: each spin sector is a Haldane model, with opposite chirality for
opposite spins (so time reversal is preserved),

$$H = t\!\!\sum_{\langle ij\rangle}\! c_i^\dagger c_j
 + i\lambda_{SO}\!\!\sum_{\langle\langle ij\rangle\rangle}\!\! \nu_{ij}\,
   c_i^\dagger \sigma_z c_j .$$

With $S_z$ conserved the spin Chern numbers are $C_\uparrow = -C_\downarrow =
1$: total Chern number zero, but a $\mathbb{Z}_2$ invariant
$\nu = (C_\uparrow - C_\downarrow)/2 \bmod 2 = 1$.  The edges carry a
**helical** Kramers pair (opposite spins move in opposite directions), giving
$G = 2e^2/h$.

The deep point is what survives when $S_z$ conservation is broken (Rashba
term $i\lambda_R (\boldsymbol{\sigma}\times\mathbf{d})_z$ on NN bonds): the
spin Chern numbers lose meaning, but time reversal still forbids
backscattering between Kramers partners — the edge crossing and the quantized
conductance persist.  That robustness *is* the $\mathbb{Z}_2$ classification.
A staggered potential $M > 3\sqrt{3}\lambda_{SO}$ kills the phase.'''

KM_CODE = r'''# --- Kane-Mele: spin Chern numbers, helical edges, quantized G ----------------
import kwant, kwant.wraparound, numpy as np
from matplotlib import pyplot

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])

t1_km, lam_so = 1.0, 0.1
lat = kwant.lattice.honeycomb(norbs=2)              # 2 orbitals = spin
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

def km_system(sym=None, M=0.0, lam_r=0.0, U0=0.0, shape=None, salt="km"):
    syst = kwant.Builder(sym) if sym is not None else kwant.Builder()
    def onsite(s):
        m = M if s.family == a_sub else -M
        dis = U0 * (kwant.digest.uniform(repr(s.tag) + s.family.name, salt) - .5)
        return (m + dis) * s0
    if shape is None:                       # translationally invariant bulk
        syst[a_sub(0, 0)] = M * s0
        syst[b_sub(0, 0)] = -M * s0
    else:
        syst[lat.shape(shape, (0, 0))] = onsite
    syst[lat.neighbors()] = rashba_nn(lam_r)
    for kind in nnn_a:
        syst[kind] = 1j * lam_so * sz       # spin-up: one chirality...
    for kind in nnn_b:
        syst[kind] = -1j * lam_so * sz      # ...spin-down: the opposite one
    return syst

# spin-resolved Chern numbers (basis per cell: A-up, A-dn, B-up, B-dn)
h_full = bloch_hamiltonian(
    km_system(kwant.TranslationalSymmetry(*lat.prim_vecs)), lat.prim_vecs)
spin_idx = {'up': np.array([0, 2]), 'dn': np.array([1, 3])}
spin_block = lambda h, s: (
    lambda t1, t2: h(t1, t2)[np.ix_(spin_idx[s], spin_idx[s])])

C_up = chern_fhs(spin_block(h_full, 'up'), n_occ=1, n1=24, n2=24)
C_dn = chern_fhs(spin_block(h_full, 'dn'), n_occ=1, n1=24, n2=24)
C_tot = chern_fhs(h_full, n_occ=2, n1=24, n2=24)
print(f"C_up = {C_up:+d},  C_dn = {C_dn:+d},  C_total = {C_tot}"
      f"   =>   Z2 = {abs(C_up - C_dn) // 2 % 2}")
assert C_up == -C_dn and C_tot == 0

# helical edge states: the crossing survives a Rashba perturbation
ribbon_shape = lambda p: 0 <= p[1] < 12 * np.sqrt(3) / 2
fig, axes = pyplot.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, lam_r in zip(axes, (0.0, 0.07)):
    frib = km_system(kwant.TranslationalSymmetry(lat.vec((1, 0))),
                     lam_r=lam_r, shape=ribbon_shape).finalized()
    kwant.plotter.bands(frib, momenta=np.linspace(-np.pi, np.pi, 161), ax=ax)
    ax.set_ylim(-1, 1); ax.set_title(f"$\\lambda_R = {lam_r}$")
    ax.set_xlabel("momentum")
axes[0].set_ylabel("energy $[t]$")
fig.suptitle("Kane-Mele ribbon: the helical crossing is protected by TRS")
pyplot.show()

# transport: G = 2 e^2/h, robust to TRS-preserving disorder and Rashba
def km_bar(M=0.0, lam_r=0.0, U0=0.0, W=10, L=16):
    shape = lambda p: (0 <= p[0] < L) and (0 <= p[1] < W * np.sqrt(3) / 2)
    syst = km_system(M=M, lam_r=lam_r, U0=U0, shape=shape)
    syst.eradicate_dangling()
    lead = km_system(kwant.TranslationalSymmetry(lat.vec((1, 0))), M=M,
                     lam_r=lam_r, shape=lambda p: 0 <= p[1] < W * np.sqrt(3) / 2)
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

E = 0.1
for kwargs, label in [(dict(), "clean"),
                      (dict(U0=0.4), "disorder U0=0.4"),
                      (dict(U0=0.4, lam_r=0.05), "disorder + Rashba"),
                      (dict(M=1.5 * 3 * np.sqrt(3) * lam_so), "M > Mc (trivial)")]:
    T = kwant.smatrix(km_bar(**kwargs), E).transmission(1, 0)
    print(f"{label:22s}:  T = {T:.5f}")'''

PIP_MD = r'''---
## 23. The p+ip superconductor — chiral Majorana edges

Read & Green [PRB **61**, 10267 (2000)]: a 2D spinless superconductor with
$p_x + ip_y$ pairing,

$$H(\mathbf{k}) = \left[-2t(\cos k_x + \cos k_y) - \mu\right]\tau_z
 + \Delta\left(\sin k_x\, \tau_x + \sin k_y\, \tau_y\right),$$

is the 2D relative of the Kitaev chain: same symmetry class (D), but in 2D the
invariant is the **Chern number of the BdG bands**.  The weak-pairing phases
$-4t < \mu < 0$ and $0 < \mu < 4t$ carry $C = \pm 1$; strong pairing
($|\mu| > 4t$) is trivial.

Bulk–boundary correspondence here produces something strictly stranger than in
a Chern insulator: the edge carries a single **chiral Majorana mode** — "half"
a chiral fermion, $\gamma(-E)=\gamma^\dagger(E)$ — and a vortex in the order
parameter binds a Majorana zero mode, which is the original proposal for
topological quantum computation.  Below: the BdG Chern number through both
transitions, the chiral Majorana dispersion on a strip, and its localization
on the boundary of a finite sample.'''

PIP_CODE = r'''# --- p+ip: BdG Chern number, chiral Majorana edge mode ------------------------
import kwant, kwant.wraparound, numpy as np
import scipy.sparse.linalg as sla
from matplotlib import pyplot

tau_x = np.array([[0, 1], [1, 0]])
tau_y = np.array([[0, -1j], [1j, 0]])
tau_z = np.array([[1, 0], [0, -1]])
t, Delta = 1.0, 0.5
lat = kwant.lattice.square(norbs=2)             # Nambu (particle, hole)

hop_x = -t * tau_z - 0.5j * Delta * tau_x
hop_y = -t * tau_z - 0.5j * Delta * tau_y

def pip_bulk(mu):
    syst = kwant.Builder(kwant.TranslationalSymmetry(*lat.prim_vecs))
    syst[lat(0, 0)] = -mu * tau_z
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = hop_x
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = hop_y
    return syst

# BdG Chern number vs mu: transitions at mu = -4t, 0, +4t
mus = np.linspace(-6, 6, 25)
Cs = [chern_fhs(bloch_hamiltonian(pip_bulk(m), lat.prim_vecs),
                n_occ=1, n1=20, n2=20) for m in mus]
pyplot.step(mus, Cs, where='mid', lw=2)
for m in (-4, 0, 4):
    pyplot.axvline(m, color='r', ls=':', alpha=.6)
pyplot.xlabel(r"$\mu\ [t]$"); pyplot.ylabel("BdG Chern number")
pyplot.title(r"p+ip phase diagram: $C=\pm1$ in the weak-pairing phases")
pyplot.grid(alpha=.3); pyplot.show()

# strip: the chiral Majorana branch crosses E = 0
def pip_strip(mu, W=25):
    syst = kwant.Builder(kwant.TranslationalSymmetry((-1, 0)))
    syst[(lat(0, y) for y in range(W))] = -mu * tau_z
    syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = hop_x
    syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = hop_y
    return syst.finalized()

fig, axes = pyplot.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, mu, label in zip(axes, (-2.0, -5.0), ("topological", "trivial")):
    kwant.plotter.bands(pip_strip(mu), momenta=np.linspace(-np.pi, np.pi, 161),
                        ax=ax)
    ax.set_ylim(-2, 2); ax.set_title(f"$\\mu = {mu}$ ({label})")
    ax.set_xlabel("momentum")
axes[0].set_ylabel("BdG energy $[t]$")
fig.suptitle("Chiral Majorana edge mode in the strip spectrum")
pyplot.show()

# the near-zero mode of a finite sample lives on the boundary
W = L = 25
syst = kwant.Builder()
syst[(lat(x, y) for x in range(L) for y in range(W))] = 2.0 * tau_z  # mu = -2
syst[kwant.builder.HoppingKind((1, 0), lat, lat)] = hop_x
syst[kwant.builder.HoppingKind((0, 1), lat, lat)] = hop_y
fsyst = syst.finalized()
ham = fsyst.hamiltonian_submatrix(sparse=True).tocsc()
ev, vec = sla.eigsh(ham, k=8, sigma=0)
i0 = np.argmin(np.abs(ev))
dens = (np.abs(vec[:, i0]) ** 2).reshape(-1, 2).sum(axis=1)
kwant.plotter.density(fsyst, dens, cmap='inferno')
print(f"lowest BdG level E = {ev[i0]:+.4f}; the density map shows the "
      "chiral Majorana circulating the boundary")'''

CELLS = [
    ("markdown", HALDANE_MD),
    ("code", HALDANE_CODE1),
    ("code", HALDANE_CODE2),
    ("markdown", KM_MD),
    ("code", KM_CODE),
    ("markdown", PIP_MD),
    ("code", PIP_CODE),
]
