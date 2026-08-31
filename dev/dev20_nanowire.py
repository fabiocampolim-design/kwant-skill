# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 20 dev: Oreg-Lutchyn Majorana nanowire — phase boundary, ZBP map."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np

s0 = np.eye(2)
sx = np.array([[0, 1], [1, 0]])
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]])

def k4(a, b):
    return np.kron(a, b)

# Basis (psi_up, psi_dn, psi_dn^dag, -psi_up^dag): tau act on Nambu, sigma on spin.
# H = (k^2/2m - mu + alpha k sigma_y) tau_z + B sigma_x + Delta tau_x
t, alpha, Delta = 1.0, 0.4, 0.25
lat = kwant.lattice.chain(norbs=4)

def onsite(mu, B):
    return (2 * t - mu) * k4(sz, s0) + B * k4(np.eye(2), sx) + Delta * k4(sx, s0)

def hopping():
    return -t * k4(sz, s0) + 0.5j * alpha * k4(sz, sy)

def wire_lead(mu, B):
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
    lead[lat(0)] = onsite(mu, B)
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = hopping()
    return lead

def bulk_gap(mu, B, nk=400):
    bands = kwant.physics.Bands(wire_lead(mu, B).finalized())
    ks = np.linspace(0, np.pi, nk)
    return min(np.min(np.abs(bands(k))) for k in ks)

# --- phase boundary: gap closes at B_c = sqrt(Delta^2 + mu^2) ----------------
mu = 0.2
Bc = np.hypot(Delta, mu)
gaps = {B: bulk_gap(mu, B) for B in (0.5 * Bc, Bc, 1.6 * Bc)}
print("gaps:", {f"{B:.3f}": f"{g:.5f}" for B, g in gaps.items()}, f"(Bc={Bc:.3f})")
assert gaps[Bc] < 0.01, gaps[Bc]
assert gaps[0.5 * Bc] > 5 * gaps[Bc]
assert gaps[1.6 * Bc] > 5 * gaps[Bc]
print(f"bulk gap closes at B_c = sqrt(Delta^2+mu^2) = {Bc:.3f}  OK")

# --- NS junction: zero-bias peak only above B_c ------------------------------
def ns_wire(mu, B, L=70, barrier=1.2, mu_lead=1.5):
    syst = kwant.Builder()
    syst[(lat(x) for x in range(L))] = onsite(mu, B)
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = hopping()
    syst[lat(0)] = onsite(mu, B) + barrier * k4(sz, s0)      # tunnel barrier
    # normal lead: no pairing; electron/hole blocks decouple -> conservation law
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

V = 1e-4
G_below = andreev_G(ns_wire(mu, 0.5 * Bc), V)
G_above = andreev_G(ns_wire(mu, 1.8 * Bc), V)
print(f"G(V~0): B=0.5Bc -> {G_below:.4f}   B=1.8Bc -> {G_above:.4f} (expect ~2)")
assert abs(G_above - 2.0) < 0.05, G_above
assert G_below < 0.5, G_below
print("PASS section 20 (nanowire)")
