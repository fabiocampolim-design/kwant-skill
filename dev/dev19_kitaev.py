# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 19 dev: Kitaev chain — Majorana zero modes, Z2 invariant, NS zero-bias peak."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np, tinyarray as ta

tau_x = ta.array([[0, 1], [1, 0]])
tau_y = ta.array([[0, -1j], [1j, 0]])
tau_z = ta.array([[1, 0], [0, -1]])

t, Delta = 1.0, 0.4
lat = kwant.lattice.chain(norbs=2)          # 2 orbitals = particle, hole

def kitaev_chain(mu, L):
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = -mu * np.array(tau_z)
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        -t * np.array(tau_z) - 1j * Delta * np.array(tau_y)
    return syst

# --- check the bulk spectrum against the analytic BdG bands ------------------
def analytic_bands(k, mu):
    h = -mu - 2 * t * np.cos(k)
    d = 2 * Delta * np.sin(k)
    return np.sqrt(h**2 + d**2)

bulk = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
bulk[lat(0)] = -0.5 * np.array(tau_z)
bulk[kwant.builder.HoppingKind((1,), lat, lat)] = \
    -t * np.array(tau_z) - 1j * Delta * np.array(tau_y)
bands = kwant.physics.Bands(bulk.finalized())
for k in (0.3, 1.2, 2.5):
    e_num = max(bands(k))
    e_ana = analytic_bands(k, 0.5)
    assert abs(e_num - e_ana) < 1e-10, (k, e_num, e_ana)
print("bulk BdG bands match analytic E(k) = sqrt(h^2 + d^2)  OK")

# --- Z2 invariant:  Q = sign[h(0) h(pi)]  ------------------------------------
def z2_invariant(mu):
    return int(np.sign((-mu - 2 * t) * (-mu + 2 * t)))

assert z2_invariant(0.5) == -1     # topological (|mu| < 2t)
assert z2_invariant(3.0) == +1     # trivial
print("Z2: Q(mu=0.5) = -1 (topological), Q(mu=3) = +1 (trivial)  OK")

# --- Majorana zero modes and their splitting vs L ---------------------------
evs = {}
for L in (10, 20, 40):
    h = kitaev_chain(0.5, L).finalized().hamiltonian_submatrix()
    ev = np.linalg.eigvalsh(h)
    evs[L] = np.min(np.abs(ev))
assert evs[40] < evs[20] < evs[10], evs
assert evs[40] < 1e-6, evs[40]
print("MZM splitting:", {L: f"{e:.2e}" for L, e in evs.items()}, " (exponential)  OK")

# Majorana wavefunction localization
h = kitaev_chain(0.5, 40).finalized().hamiltonian_submatrix()
ev, vec = np.linalg.eigh(h)
izero = np.argsort(np.abs(ev))[:2]
dens = (np.abs(vec[:, izero])**2).reshape(40, 2, 2).sum(axis=(1, 2))
assert dens[:6].sum() + dens[-6:].sum() > 0.9
print(f"zero-mode weight on 6 end sites: {dens[:6].sum() + dens[-6:].sum():.3f}  OK")

# --- transport: quantized zero-bias Andreev conductance ----------------------
def ns_kitaev(mu_wire, L=25, mu_lead=1.0, barrier=1.6):
    """Normal lead | barrier | Kitaev chain (other end terminated)."""
    syst = kitaev_chain(mu_wire, L)
    syst[lat(0)] = (-mu_wire + barrier) * np.array(tau_z)     # tunnel barrier
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)),
                         conservation_law=-np.array(tau_z),
                         particle_hole=np.array(tau_x))
    lead[lat(0)] = -mu_lead * np.array(tau_z)                 # normal metal
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = -t * np.array(tau_z)
    syst.attach_lead(lead)
    return syst.finalized()

def andreev_G(fsyst, e):
    s = kwant.smatrix(fsyst, e)
    N = s.submatrix((0, 0), (0, 0)).shape[0]        # electron modes
    r_ee = s.transmission((0, 0), (0, 0))
    r_he = s.transmission((0, 1), (0, 0))
    return N - r_ee + r_he

f_top = ns_kitaev(0.5)
f_tri = ns_kitaev(3.0)
# NB: at exactly E=0 the electron and hole modes of a PH-symmetric lead are
# degenerate and kwant's block labelling is singular -- evaluate at a tiny
# finite bias instead.
V = 1e-4
G_top0 = andreev_G(f_top, V)
G_tri0 = andreev_G(f_tri, V)
print(f"G(V=0): topological={G_top0:.6f} (expect 2)  trivial={G_tri0:.2e} (expect 0)")
assert abs(G_top0 - 2.0) < 1e-3, G_top0
assert G_tri0 < 1e-3, G_tri0

# peak survives changing the barrier (topological protection)
for barrier in (1.0, 2.5):
    G = andreev_G(ns_kitaev(0.5, barrier=barrier), V)
    assert abs(G - 2.0) < 1e-3, (barrier, G)
print("ZBP pinned to 2 e^2/h for barriers 1.0-2.5  OK")
print("PASS section 19 (Kitaev)")
