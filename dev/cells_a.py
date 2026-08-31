# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# -*- coding: utf-8 -*-
"""Part II cells, sections 17-20 (intro + 1D models)."""

INTRO_MD = r'''---
# Part II — Topological matter

Everything below applies the machinery of Part I to the flagship models of
topological condensed matter, in one, two and three dimensions.  Each section
follows the same arc: *theory → a numerical topological invariant → edge or
surface states → a transport signature* (where transport is meaningful).

Two computational ideas do most of the work:

* **Berry phases on a discretized Brillouin zone.**  Wilson loops (products of
  overlap matrices of occupied states) give polarizations, Wannier centers and,
  via the Fukui–Hatsugai–Suzuki plaquette formula, Chern numbers that are
  *exactly* integer even on coarse grids.
* **Bulk–boundary correspondence in transport.**  A nonzero bulk invariant
  forces gapless edge/surface states, which Kwant sees directly as quantized,
  disorder-immune conductance.

Sources this part draws on: the Delft course
[topocondmat.org](https://topocondmat.org) (Kwant-based notebooks),
the [PythTB examples](https://www.physics.rutgers.edu/pythtb/examples.html)
(Berry-phase computations), Asbóth, Oroszlány & Pályi,
*A Short Course on Topological Insulators* (Springer 2016), and the original
papers cited in each section.'''

SSH_MD = r'''---
## 17. The SSH chain — the simplest topological insulator

The Su–Schrieffer–Heeger model [PRL **42**, 1698 (1979)] is a dimerized chain:
two sites per cell, alternating hoppings $t_1$ (intra-cell) and $t_2$
(inter-cell),

$$H(k) = \begin{pmatrix} 0 & q(k) \\ q^*(k) & 0 \end{pmatrix},
\qquad q(k) = t_1 + t_2 e^{ik}.$$

Chiral (sublattice) symmetry $\sigma_z H \sigma_z = -H$ makes the *winding
number* of $q(k)$ around the origin a quantized invariant:

$$\nu = \frac{1}{2\pi i}\oint dk\, \frac{d}{dk}\log q(k) =
\begin{cases} 0 & t_1 > t_2 \text{ (trivial)}\\ 1 & t_1 < t_2 \text{ (topological)}\end{cases}$$

Equivalently the Zak phase (Berry phase of the filled band across the BZ) is
$0$ or $\pi$.  Bulk–boundary correspondence: $\nu = 1$ forces one zero-energy
state per end, exponentially localized, living on a single sublattice.

**Transport subtlety worth internalizing:** the two end states only talk to
each other through their overlap $\delta \sim (t_1/t_2)^{L}$.  A long chain
therefore transmits *nothing* even on resonance — to see the edge doublet in a
conductance trace you need a short chain and weakly coupled leads, so that the
level broadening $\Gamma$ matches $\delta$.'''

SSH_CODE1 = r'''# --- SSH chain: winding number, Zak phase, and the edge-state doublet --------
import kwant, numpy as np
from matplotlib import pyplot

sigma_x = np.array([[0, 1], [1, 0]])
lat = kwant.lattice.chain(norbs=2)              # 2 orbitals = A/B sublattice
hop_inter = np.array([[0.0, 1.0], [0.0, 0.0]])  # B(x) -> A(x+1)

def ssh_chain(t1, t2, L):
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = t1 * sigma_x
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = t2 * hop_inter
    return syst

def winding_number(t1, t2, nk=201):
    ks = np.linspace(0, 2 * np.pi, nk)
    q = t1 + t2 * np.exp(1j * ks)                       # det block of H(k)
    return int(round(np.diff(np.unwrap(np.angle(q))).sum() / (2 * np.pi)))

def zak_phase(t1, t2, nk=200):
    """Berry phase of the filled band: a discrete Wilson loop over the BZ."""
    ks = np.linspace(0, 2 * np.pi, nk, endpoint=False)
    us = []
    for k in ks:
        q = t1 + t2 * np.exp(1j * k)
        h = np.array([[0, q], [np.conj(q), 0]])
        us.append(np.linalg.eigh(h)[1][:, 0])
    prod = 1.0 + 0j
    for i in range(nk):
        prod *= np.vdot(us[i], us[(i + 1) % nk])
    return (-np.angle(prod)) % (2 * np.pi)

for (t1, t2), label in [((1.0, 0.5), "trivial"), ((0.5, 1.0), "topological")]:
    print(f"{label:12s} t1={t1} t2={t2}:  winding = {winding_number(t1, t2)},  "
          f"Zak phase = {zak_phase(t1, t2) / np.pi:.4f} pi")

# spectrum of a finite chain across the transition: watch the zero modes appear
L = 40
ratios = np.linspace(0.2, 2.0, 61)
spectra = []
for r in ratios:                                   # t1/t2 = r at fixed bandwidth
    h = ssh_chain(r, 1.0, L).finalized().hamiltonian_submatrix()
    spectra.append(np.linalg.eigvalsh(h))
spectra = np.array(spectra)

pyplot.plot(ratios, spectra, 'k-', lw=.4)
pyplot.axvline(1.0, color='r', ls='--', alpha=.7, label=r'$t_1 = t_2$')
pyplot.xlabel(r"$t_1 / t_2$"); pyplot.ylabel("energy $[t_2]$")
pyplot.title("SSH finite chain: zero modes exist exactly for $t_1 < t_2$")
pyplot.legend(); pyplot.grid(alpha=.3); pyplot.show()

# the zero modes live on the ends, one sublattice each
h = ssh_chain(0.5, 1.0, L).finalized().hamiltonian_submatrix()
ev, vec = np.linalg.eigh(h)
izero = np.argsort(np.abs(ev))[:2]
dens = (np.abs(vec[:, izero]) ** 2).sum(axis=1).reshape(L, 2).sum(axis=1)
pyplot.bar(range(L), dens, color='C0')
pyplot.xlabel("unit cell"); pyplot.ylabel(r"$|\psi|^2$ (both zero modes)")
pyplot.title("Edge localization of the SSH zero modes")
pyplot.grid(alpha=.3); pyplot.show()'''

SSH_CODE2 = r'''# --- SSH transport: resonant tunnelling through the edge doublet -------------
import kwant, numpy as np
from matplotlib import pyplot

sigma_x = np.array([[0, 1], [1, 0]])
lat = kwant.lattice.chain(norbs=2)
hop_inter = np.array([[0.0, 1.0], [0.0, 0.0]])

def ssh_transport(t1, t2, L=8, t_c=0.15):
    """Short SSH chain, weak links t_c to metallic contacts, uniform-chain leads."""
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = t1 * sigma_x
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = t2 * hop_inter
    syst[lat(-1)] = 1.0 * sigma_x                 # metallic contact cells
    syst[lat(L)] = 1.0 * sigma_x
    syst[lat(0), lat(-1)] = t_c * hop_inter       # the weak links
    syst[lat(L), lat(L - 1)] = t_c * hop_inter
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
    lead[lat(0)] = 1.0 * sigma_x                  # t1 = t2: gapless = metallic
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = hop_inter
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()

energies = np.linspace(-0.6, 0.6, 601)
T_top = [kwant.smatrix(ssh_transport(0.5, 1.0), e).transmission(1, 0)
         for e in energies]
T_tri = [kwant.smatrix(ssh_transport(1.0, 0.5), e).transmission(1, 0)
         for e in energies]

pyplot.semilogy(energies, T_top, lw=2, label=r"topological ($t_1 < t_2$)")
pyplot.semilogy(energies, T_tri, lw=2, label=r"trivial ($t_1 > t_2$)")
pyplot.xlabel("energy $[t_2]$"); pyplot.ylabel(r"$T$")
pyplot.title("Midgap transmission exists only through the edge doublet")
pyplot.legend(); pyplot.grid(alpha=.3, which='both'); pyplot.show()

print(f"in-gap max T:  topological = {max(T_top):.4f},  trivial = {max(T_tri):.2e}")
assert max(T_top) > 30 * max(T_tri)'''

KITAEV_MD = r'''---
## 18. The Kitaev chain — Majorana zero modes

Kitaev's model [Phys.-Usp. **44**, 131 (2001)] is a spinless 1D $p$-wave
superconductor.  In the BdG basis $(c, c^\dagger)$,

$$H(k) = \underbrace{(-\mu - 2t\cos k)}_{h(k)}\,\tau_z +
         \underbrace{2\Delta \sin k}_{d(k)}\,\tau_y ,$$

with spectrum $E(k) = \pm\sqrt{h^2 + d^2}$.  Particle–hole symmetry
($P = \tau_x K$, $P H(k) P^{-1} = -H(-k)$) protects a $\mathbb{Z}_2$
invariant that only depends on the signs of $h$ at the PH-symmetric momenta:

$$Q = \operatorname{sign}\left[h(0)\,h(\pi)\right] =
\operatorname{sign}\left[\mu^2 - 4t^2\right],$$

so the chain is **topological for $|\mu| < 2t$**.  There it hosts one Majorana
zero mode per end ($\gamma = \gamma^\dagger$), split only by an exponentially
small overlap.

The experimental smoking gun is transport: an electron incident from a normal
lead *must* Andreev-reflect resonantly through the Majorana, pinning the
zero-bias conductance to exactly $2e^2/h$ — independent of the barrier
strength.  This is the cleanest quantization in this notebook after the
conductance staircase of Part I.  (See topocondmat.org, week 1–2.)'''

KITAEV_CODE1 = r'''# --- Kitaev chain: phase diagram and Majorana modes ---------------------------
import kwant, numpy as np
from matplotlib import pyplot

tau_y = np.array([[0, -1j], [1j, 0]])
tau_z = np.array([[1, 0], [0, -1]])

t, Delta = 1.0, 0.4
lat = kwant.lattice.chain(norbs=2)          # 2 orbitals = particle, hole

def kitaev_chain(mu, L):
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = -mu * tau_z
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        -t * tau_z - 1j * Delta * tau_y
    return syst

# spectrum of a finite chain vs mu: Majoranas exist exactly for |mu| < 2t
L = 40
mus = np.linspace(-3, 3, 81)
spectra = np.array([np.linalg.eigvalsh(
    kitaev_chain(m, L).finalized().hamiltonian_submatrix()) for m in mus])

pyplot.plot(mus, spectra, 'k-', lw=.4)
pyplot.axvline(-2, color='r', ls='--', alpha=.7)
pyplot.axvline(2, color='r', ls='--', alpha=.7, label=r'$|\mu| = 2t$')
pyplot.ylim(-1.5, 1.5)
pyplot.xlabel(r"$\mu\ [t]$"); pyplot.ylabel("BdG energy $[t]$")
pyplot.title("Kitaev chain: Majorana zero modes for $|\\mu| < 2t$")
pyplot.legend(); pyplot.grid(alpha=.3); pyplot.show()

# the Z2 invariant needs only the signs of h(k) at k = 0 and pi
Q = lambda mu: int(np.sign((-mu - 2 * t) * (-mu + 2 * t)))
print("Q(mu=0.5) =", Q(0.5), " (topological);  Q(mu=3.0) =", Q(3.0), " (trivial)")

# exponential protection: the zero-mode splitting vs chain length
for L_ in (10, 20, 40):
    ev = np.linalg.eigvalsh(kitaev_chain(0.5, L_).finalized()
                            .hamiltonian_submatrix())
    print(f"L={L_:3d}:  |E_0| = {np.abs(ev).min():.2e}")

# Majorana wavefunction: half a fermion on each end
h = kitaev_chain(0.5, L).finalized().hamiltonian_submatrix()
ev, vec = np.linalg.eigh(h)
izero = np.argsort(np.abs(ev))[:2]
dens = (np.abs(vec[:, izero]) ** 2).sum(axis=1).reshape(L, 2).sum(axis=1)
pyplot.bar(range(L), dens, color='C3')
pyplot.xlabel("site"); pyplot.ylabel(r"$|\psi|^2$")
pyplot.title("The Majorana pair: one zero mode split across both ends")
pyplot.grid(alpha=.3); pyplot.show()'''

KITAEV_CODE2 = r'''# --- NS junction: the quantized zero-bias peak --------------------------------
import kwant, numpy as np
from matplotlib import pyplot

tau_x = np.array([[0, 1], [1, 0]])
tau_y = np.array([[0, -1j], [1j, 0]])
tau_z = np.array([[1, 0], [0, -1]])
t, Delta = 1.0, 0.4
lat = kwant.lattice.chain(norbs=2)

def ns_kitaev(mu_wire, L=25, mu_lead=1.0, barrier=1.6):
    """normal lead | tunnel barrier | Kitaev chain (far end terminated)."""
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = -mu_wire * tau_z
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        -t * tau_z - 1j * Delta * tau_y
    syst[lat(0)] = (-mu_wire + barrier) * tau_z
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)),
                         conservation_law=-tau_z, particle_hole=tau_x)
    lead[lat(0)] = -mu_lead * tau_z
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = -t * tau_z
    syst.attach_lead(lead)
    return syst.finalized()

def andreev_G(fsyst, e):
    """G = N - R_ee + R_he, in units e^2/h (one lead: reflection only)."""
    s = kwant.smatrix(fsyst, e)
    N = s.submatrix((0, 0), (0, 0)).shape[0]
    return N - s.transmission((0, 0), (0, 0)) + s.transmission((0, 1), (0, 0))

# NB: at exactly E = 0 the electron and hole modes of a PH-symmetric lead are
# degenerate and the block labelling is singular -- never evaluate there.
energies = np.linspace(-0.35, 0.35, 281) + 5e-4
G_top = [andreev_G(ns_kitaev(0.5), e) for e in energies]
G_tri = [andreev_G(ns_kitaev(3.0), e) for e in energies]

pyplot.plot(energies, G_top, lw=2, label=r"$\mu = 0.5\,t$ (topological)")
pyplot.plot(energies, G_tri, lw=2, label=r"$\mu = 3\,t$ (trivial)")
pyplot.axhline(2, color='gray', ls=':', label=r'$2e^2/h$')
pyplot.xlabel("bias $[t]$"); pyplot.ylabel(r"$G\ [e^2/h]$")
pyplot.title("Majorana zero-bias peak, quantized at $2e^2/h$")
pyplot.legend(); pyplot.grid(alpha=.3); pyplot.show()

for barrier in (1.0, 1.6, 2.5):
    G0 = andreev_G(ns_kitaev(0.5, barrier=barrier), 1e-4)
    print(f"barrier={barrier}:  G(V~0) = {G0:.6f}  (pinned to 2 by the Majorana)")
    assert abs(G0 - 2.0) < 1e-3'''

NANOWIRE_MD = r'''---
## 19. The Majorana nanowire — Kitaev physics in a real device

No spinless $p$-wave superconductors exist in nature.  Oreg *et al.* [PRL
**105**, 177002 (2010)] and Lutchyn *et al.* [PRL **105**, 077001 (2010)]
showed how to engineer one: a semiconductor wire with Rashba spin–orbit
coupling $\alpha$, proximitized by an $s$-wave superconductor $\Delta$, in a
magnetic field $B$ along the wire.  In the Nambu basis
$(\psi_\uparrow, \psi_\downarrow, \psi_\downarrow^\dagger, -\psi_\uparrow^\dagger)$:

$$H = \left(\frac{k^2}{2m} - \mu + \alpha k \sigma_y\right)\tau_z
      + B\,\sigma_x + \Delta\,\tau_x .$$

The Zeeman term opens a helical gap; pairing then drives the wire into an
effective Kitaev phase when

$$B > B_c = \sqrt{\Delta^2 + \mu^2},$$

with the bulk gap closing and reopening exactly at $B_c$.  The signature is
the same as for the Kitaev chain — a zero-bias conductance peak at $2e^2/h$ —
but now it *emerges as the field is tuned through* $B_c$, which is what the
2012 Delft experiment [Mourik *et al.*, Science **336**, 1003] looked for.
(See topocondmat.org, week 2.)'''

NANOWIRE_CODE = r'''# --- Majorana nanowire: gap closing at B_c and the emerging ZBP ---------------
import kwant, numpy as np
from matplotlib import pyplot

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])
k4 = np.kron

t, alpha, Delta, mu = 1.0, 0.4, 0.25, 0.2
Bc = np.hypot(Delta, mu)
lat = kwant.lattice.chain(norbs=4)          # (up, dn) x (particle, hole)

def onsite(B):
    return (2 * t - mu) * k4(sz, s0) + B * k4(np.eye(2), sx) + Delta * k4(sx, s0)

hopping = -t * k4(sz, s0) + 0.5j * alpha * k4(sz, sy)

def wire_lead(B):
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
    lead[lat(0)] = onsite(B)
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = hopping
    return lead

# (a) bulk gap vs B: closes exactly at B_c = sqrt(Delta^2 + mu^2)
Bs = np.linspace(0, 2.5 * Bc, 41)
ks = np.linspace(0, np.pi, 201)
gaps = []
for B in Bs:
    bands = kwant.physics.Bands(wire_lead(B).finalized())
    gaps.append(min(np.abs(bands(k)).min() for k in ks))

pyplot.plot(Bs / Bc, gaps, 'o-', ms=3)
pyplot.axvline(1, color='r', ls='--', alpha=.7, label=r'$B = B_c$')
pyplot.xlabel(r"$B / B_c$"); pyplot.ylabel("bulk gap $[t]$")
pyplot.title(r"Topological transition at $B_c=\sqrt{\Delta^2+\mu^2}$")
pyplot.legend(); pyplot.grid(alpha=.3); pyplot.show()

# (b) tunneling conductance map G(V, B): the ZBP appears only above B_c
def ns_wire(B, L=70, barrier=1.2, mu_lead=1.5):
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = onsite(B)
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = hopping
    syst[lat(0)] = onsite(B) + barrier * k4(sz, s0)
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)),
                         conservation_law=-k4(sz, s0))
    lead[lat(0)] = (2 * t - mu_lead) * k4(sz, s0) + B * k4(np.eye(2), sx)
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = -t * k4(sz, s0)
    syst.attach_lead(lead)
    return syst.finalized()

def andreev_G(fsyst, e):
    s = kwant.smatrix(fsyst, e)
    N = s.submatrix((0, 0), (0, 0)).shape[0]
    return N - s.transmission((0, 0), (0, 0)) + s.transmission((0, 1), (0, 0))

Bs_map = np.linspace(0, 2.2 * Bc, 23)
Vs = np.linspace(-0.12, 0.12, 41) + 2e-4
Gmap = np.array([[andreev_G(ns_wire(B), V) for B in Bs_map] for V in Vs])

pyplot.pcolormesh(Bs_map / Bc, Vs, Gmap, shading='auto', cmap='viridis')
pyplot.colorbar(label=r"$G\ [e^2/h]$")
pyplot.axvline(1, color='w', ls='--', alpha=.7)
pyplot.xlabel(r"$B/B_c$"); pyplot.ylabel("bias $V$ $[t]$")
pyplot.title("Zero-bias peak emerging at the topological transition")
pyplot.show()

G_below = andreev_G(ns_wire(0.5 * Bc), 1e-4)
G_above = andreev_G(ns_wire(1.8 * Bc), 1e-4)
print(f"G(V~0):  B=0.5 B_c -> {G_below:.3f};   B=1.8 B_c -> {G_above:.4f}  (2 = Majorana)")
assert abs(G_above - 2.0) < 0.05'''

PUMP_MD = r'''---
## 20. The Thouless pump — a Chern number in (k, t)

Thouless [PRB **27**, 6083 (1983)]: slide a periodic potential adiabatically
by one period and the charge transported through a filled band is *exactly
quantized* — it is the Chern number of the band over the $(k, \varphi)$ torus,
where $\varphi$ is the pump phase.  Time acts as a second momentum: **a 1D
pump is a 2D Chern insulator in disguise**.

The minimal realization is the Rice–Mele model — an SSH chain whose
dimerization $\delta$ and staggered onsite $\Delta$ trace a loop:

$$t_{1,2} = t_0 \pm \delta_0\cos\varphi, \qquad
\Delta(\varphi) = \Delta_0 \sin\varphi .$$

The loop encircles the gapless point $(\delta, \Delta) = (0, 0)$, so $C = \pm 1$:
one electron pumped per cycle.  Three equivalent diagnostics, all computed
below:

1. the FHS Chern number on the $(k, \varphi)$ torus (this is where the
   `chern_fhs` routine used throughout Part II first appears);
2. the polarization (Zak phase) winding exactly once per cycle;
3. edge states in a finite chain traversing the gap as $\varphi$ advances —
   the real-space picture of the pumped charge.'''

PUMP_CODE = r'''# --- Rice-Mele pump: Chern number, polarization flow, edge-state ladder -------
import kwant, numpy as np
from matplotlib import pyplot

sigma_x = np.array([[0, 1], [1, 0]])
sigma_z = np.array([[1, 0], [0, -1]])
t0, d0, D0 = 1.0, 0.6, 0.6

def h_rice_mele(k, phi):
    t1 = t0 + d0 * np.cos(phi)
    t2 = t0 - d0 * np.cos(phi)
    D = D0 * np.sin(phi)
    q = t1 + t2 * np.exp(1j * k)
    return np.array([[D, q], [np.conj(q), -D]])

def chern_fhs(hfunc, n_occ, n1=40, n2=40):
    """Chern number by the Fukui-Hatsugai-Suzuki plaquette method.

    hfunc(x1, x2): Bloch Hamiltonian, 2pi-periodic in both arguments.  The
    result is exactly integer on any grid fine enough to resolve the gap.
    (Reused by every 2D section below.)
    """
    xs1 = np.linspace(0, 2 * np.pi, n1, endpoint=False)
    xs2 = np.linspace(0, 2 * np.pi, n2, endpoint=False)
    frames = np.empty((n1, n2), dtype=object)
    for i, x1 in enumerate(xs1):
        for j, x2 in enumerate(xs2):
            frames[i, j] = np.linalg.eigh(hfunc(x1, x2))[1][:, :n_occ]
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

C = chern_fhs(h_rice_mele, n_occ=1)
print(f"charge pumped per cycle = C over the (k, phi) torus = {C}")
assert abs(C) == 1

# a cycle that does NOT encircle the gapless point pumps nothing
def h_no_pump(k, phi):
    t1 = t0 + d0 * np.cos(phi)
    t2 = t0 - d0 * np.cos(phi)
    q = t1 + t2 * np.exp(1j * k)
    return np.array([[0, q], [np.conj(q), 0]])
print("cycle without onsite modulation:", chern_fhs(h_no_pump, n_occ=1))

# polarization (Zak phase) winds once per cycle -- same integer
def zak(phi, nk=200):
    ks = np.linspace(0, 2 * np.pi, nk, endpoint=False)
    us = [np.linalg.eigh(h_rice_mele(k, phi))[1][:, 0] for k in ks]
    prod = 1.0 + 0j
    for i in range(nk):
        prod *= np.vdot(us[i], us[(i + 1) % nk])
    return -np.angle(prod) / (2 * np.pi)

phis = np.linspace(0, 2 * np.pi, 61)
pol = np.unwrap([2 * np.pi * zak(p) for p in phis]) / (2 * np.pi)

# finite chain: the edge-state ladder carries the charge across the gap
lat = kwant.lattice.chain(norbs=2)
L = 30
def finite_chain(phi):
    t1 = t0 + d0 * np.cos(phi); t2 = t0 - d0 * np.cos(phi)
    D = D0 * np.sin(phi)
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = D * sigma_z + t1 * sigma_x
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        t2 * np.array([[0, 1], [0, 0]])
    return syst.finalized()

spectra = np.array([np.linalg.eigvalsh(finite_chain(p).hamiltonian_submatrix())
                    for p in phis])

fig, (ax1, ax2) = pyplot.subplots(1, 2, figsize=(11, 4))
ax1.plot(phis, spectra, 'k-', lw=.4)
ax1.set_xlabel(r"pump phase $\varphi$"); ax1.set_ylabel("energy $[t_0]$")
ax1.set_title("Edge states traverse the gap: one charge per cycle")
ax1.grid(alpha=.3)
ax2.plot(phis, pol, lw=2)
ax2.set_xlabel(r"$\varphi$"); ax2.set_ylabel("polarization $[ea]$")
ax2.set_title(f"Polarization winds by {pol[-1] - pol[0]:+.3f}")
ax2.grid(alpha=.3)
pyplot.tight_layout(); pyplot.show()

assert abs(abs(pol[-1] - pol[0]) - 1) < 0.02'''

CELLS = [
    ("markdown", INTRO_MD),
    ("markdown", SSH_MD),
    ("code", SSH_CODE1),
    ("code", SSH_CODE2),
    ("markdown", KITAEV_MD),
    ("code", KITAEV_CODE1),
    ("code", KITAEV_CODE2),
    ("markdown", NANOWIRE_MD),
    ("code", NANOWIRE_CODE),
    ("markdown", PUMP_MD),
    ("code", PUMP_CODE),
]
