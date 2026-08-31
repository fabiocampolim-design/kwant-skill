# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Section 18 dev: SSH chain — winding number, Zak phase, edge states, transport."""
import matplotlib
matplotlib.use("Agg")
import kwant, numpy as np, tinyarray as ta

sigma_x = ta.array([[0, 1], [1, 0]])
sigma_y = ta.array([[0, -1j], [1j, 0]])

lat = kwant.lattice.chain(norbs=2)          # 2 orbitals = A/B sublattice

def ssh_builder(t1, t2, L=None):
    """Finite chain of L unit cells, or the translationally invariant cell."""
    if L is None:
        syst = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
        rng = [0]
    else:
        syst = kwant.Builder()
        rng = range(L)
    for x in rng:
        syst[lat(x)] = t1 * np.array(sigma_x)        # intra-cell hopping A-B
    syst[kwant.builder.HoppingKind((1,), lat, lat)] = \
        t2 * np.array([[0, 1], [0, 0]])              # inter-cell hopping B-A
    return syst

def h_bloch(k, t1, t2):
    q = t1 + t2 * np.exp(1j * k)
    return np.array([[0, q], [q.conj(), 0]])

def winding_number(t1, t2, nk=201):
    ks = np.linspace(0, 2*np.pi, nk)
    q = t1 + t2 * np.exp(1j * ks)
    dtheta = np.diff(np.unwrap(np.angle(q)))
    return int(round(dtheta.sum() / (2*np.pi)))

def zak_phase(t1, t2, nk=200):
    """Berry phase of the lower band across the BZ (discretized Wilson loop)."""
    ks = np.linspace(0, 2*np.pi, nk, endpoint=False)
    us = []
    for k in ks:
        _, v = np.linalg.eigh(h_bloch(k, t1, t2))
        us.append(v[:, 0])
    prod = 1.0 + 0j
    for i in range(nk):
        prod *= np.vdot(us[i], us[(i+1) % nk])
    return -np.angle(prod)

# --- checks -----------------------------------------------------------------
assert winding_number(1.0, 0.5) == 0, "trivial phase must have nu=0"
assert winding_number(0.5, 1.0) == 1, "topological phase must have nu=1"
z_top = zak_phase(0.5, 1.0) % (2*np.pi)
z_tri = zak_phase(1.0, 0.5) % (2*np.pi)
assert abs(z_top - np.pi) < 1e-6, f"Zak phase topological: {z_top}"
assert min(z_tri, 2*np.pi - z_tri) < 1e-6, f"Zak phase trivial: {z_tri}"
print(f"winding: trivial=0 topological=1   Zak: {z_tri:.4f} vs {z_top:.4f} (=pi)  OK")

# --- edge states in a finite chain ------------------------------------------
L = 40
h_top = ssh_builder(0.5, 1.0, L=L).finalized().hamiltonian_submatrix()
h_tri = ssh_builder(1.0, 0.5, L=L).finalized().hamiltonian_submatrix()
ev_top, vec_top = np.linalg.eigh(h_top)
ev_tri = np.linalg.eigvalsh(h_tri)
n_zero_top = int(np.sum(np.abs(ev_top) < 1e-3))
n_zero_tri = int(np.sum(np.abs(ev_tri) < 1e-3))
assert n_zero_top == 2 and n_zero_tri == 0, (n_zero_top, n_zero_tri)
# zero modes localized at the ends
izero = np.argsort(np.abs(ev_top))[:2]
dens = np.abs(vec_top[:, izero])**2
site_dens = dens.reshape(L, 2, -1).sum(axis=(1, 2))
edge_weight = site_dens[:5].sum() + site_dens[-5:].sum()
assert edge_weight > 0.9, edge_weight
print(f"finite chain: 2 zero modes, {edge_weight:.3f} of their weight on 5 end cells  OK")

# --- transport: resonant tunnelling through the edge-state doublet ----------
# The two end modes only talk to each other through their exponentially small
# overlap delta ~ (t1/t2)^L, so a long chain transmits nothing even ON
# resonance (T ~ (delta/Gamma)^2).  To see the edge doublet in transport, use a
# short chain and couple the leads weakly, so that Gamma ~ delta.
def weak_coupling_T(t1, t2, energies, L=8, t_c=0.15):
    """SSH chain with weak links (t_c) to metallic contact cells + leads."""
    hop = np.array([[0.0, 1.0], [0.0, 0.0]])
    syst = ssh_builder(t1, t2, L=L)
    syst[lat(-1)] = 1.0 * np.array(sigma_x)          # metallic contact cells
    syst[lat(L)] = 1.0 * np.array(sigma_x)
    syst[lat(0), lat(-1)] = t_c * hop                # the weak links
    syst[lat(L), lat(L - 1)] = t_c * hop
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1,)))
    lead[lat(0)] = 1.0 * np.array(sigma_x)           # uniform chain: metallic
    lead[kwant.builder.HoppingKind((1,), lat, lat)] = hop
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    fsyst = syst.finalized()
    return [kwant.smatrix(fsyst, e).transmission(1, 0) for e in energies]

energies = np.linspace(-0.35, 0.35, 701)
T_top = weak_coupling_T(0.5, 1.0, energies)
T_tri = weak_coupling_T(1.0, 0.5, energies)
print(f"in-gap max T: topological={max(T_top):.4f}  trivial={max(T_tri):.2e}")
assert max(T_top) > 0.1
assert max(T_tri) < 1e-2
print("PASS section 18 (SSH)")
