---
title: "Quantum Transport with Kwant — companion handout"
subtitle: "For the undergraduate course built on *Kwant — Theory and Practice*"
---

# 1. What the course is

An undergraduate course on quantum transport in ten stops, taught from twelve
executed Jupyter chapter notebooks (`chapters/01_…` to `12_…`, Kwant 1.5). Every
figure on the slides is a numbered figure of the course (the numbering runs
continuously through the chapters); every equation on the slides is computed
in them; the exercises at the end of each part are solved and asserted in
`chapters/S1_Solutions_Part_I.ipynb` and `S2_Solutions_Part_II.ipynb`. The deck
is one linear sequence — inside each section plain language first, then the
Kwant code, the mathematics last — so a lecturer can stop each section at the
audience's level.

| Stop | Physics | Kwant | Notebook sections |
|---|---|---|---|
| 1 Lattice | Schrödinger → tight binding | `Builder`, lattices, hoppings | 1–2 |
| 2 Leads | Landauer–Büttiker, Fisher–Lee | `attach_lead`, `smatrix` | 3–4, 7 |
| 3 Shapes | resonances, billiards, parameters | shape and value functions | 5 |
| 4 Spin · graphene · SC | Rashba, Dirac cones, Andreev | matrix values, honeycomb, BdG | 6, 8–10 |
| 5 Magnetic fields | Peierls, Landau levels, Hofstadter | phase hoppings, `wraparound` | 14 |
| 6 Toolbox | KPM, continuum, solvers, pitfalls | `kpm`, `continuum`, MUMPS | 11–13, 15–16 |
| 7 Topology in 1D | SSH, Kitaev, Majorana wire, pump | invariants from the system | 17–20 |
| 8 Topology in 2D/3D | Haldane, Kane–Mele, p+ip, BBH, Weyl, 3D TI | Berry curvature on a torus | 21–26 |
| 9 Close | run it, exercises, reading | Run All | 27 |

# 2. The reference card

| Object | What it is | Typical line |
|---|---|---|
| `Lattice` | geometry: unit vectors + basis | `kwant.lattice.square(a=1, norbs=1)` |
| `Site` | a lattice plus integer coordinates | `lat(3, 4)` |
| `Builder` | the Hamiltonian as a mapping | `syst[lat(0, 0)] = 4*t`; `syst[lat.neighbors()] = -t` |
| `HoppingKind` | a family of bonds by displacement | `kwant.builder.HoppingKind((1, 0), lat)` |
| lead | a Builder with a `TranslationalSymmetry` | `syst.attach_lead(lead)` |
| finalized system | immutable, solvable | `fsyst = syst.finalized()` |
| scattering matrix | `S` at one energy | `sm = kwant.smatrix(fsyst, E, params=...)` |
| conductance | transmission 0 → 1 | `sm.transmission(1, 0)` (units of e²/h) |
| wavefunction | scattering states from lead 0 | `kwant.wave_function(fsyst, E)(0)` |
| observables | density / current operators | `kwant.operator.Density(fsyst, σ)` |
| bands | lead dispersion | `kwant.physics.Bands(fsyst.leads[0])` |
| spectral density | KPM | `kwant.kpm.SpectralDensity(fsyst)` |
| continuum model | symbolic → lattice | `kwant.continuum.discretize(hamiltonian, grid=a)` |
| periodic system | symmetry → momentum parameter | `kwant.wraparound.wraparound(syst)` |

Value rule: a value on a site or bond is a number, a matrix (spin, BdG), or a
function whose first argument(s) are the site(s) and whose other named
arguments are passed at solve time through `params=`.

# 3. Key equations

**Discretisation (2D, spacing a).** Hopping $t = \hbar^2/(2ma^2)$, on-site
$\varepsilon_i = 4t + V(\mathbf r_i)$;
$E(\mathbf k) = 4t - 2t(\cos k_x a + \cos k_y a) \approx \hbar^2 k^2/2m$.

**Landauer–Büttiker.** $G = \dfrac{e^2}{h}\sum_n T_n = \dfrac{e^2}{h}\,\mathrm{Tr}\,(t^\dagger t)$;
unitarity $S^\dagger S = 1$; sum rule $\sum_n (T_n + R_n) = N$.

**Fisher–Lee.** $S = -1 + i\,\Gamma^{1/2} G^r(E)\, \Gamma^{1/2}$, with
$G^r = (E - H - \Sigma)^{-1}$, $\Sigma = \sum_{\text{leads}} V^\dagger g\, V$,
$\Gamma = i(\Sigma - \Sigma^\dagger)$.

**Bogoliubov–de Gennes.**
$H_{\mathrm{BdG}} = \begin{pmatrix} H-\mu & \Delta \\ \Delta^* & -(H-\mu)^* \end{pmatrix}$,
$P H_{\mathrm{BdG}} P^{-1} = -H_{\mathrm{BdG}}$;
sub-gap conductance $G = \frac{e^2}{h}\,[N - R_{ee} + R_{he}]$, perfect Andreev
reflection $G = 2Ne^2/h$.

**Peierls substitution.** $t_{ij} \to t_{ij}\exp\!\big(\tfrac{ie}{\hbar}\int_j^i \mathbf A\cdot d\mathbf l\big)$;
the product of the phases around a plaquette is $e^{2\pi i\Phi/\Phi_0}$, $\Phi_0 = h/e$.
Harper: $-t[\psi_{y+1} + \psi_{y-1}] - 2t\cos(k_x a - 2\pi\alpha y)\psi_y = E\psi_y$.

**KPM.** $\rho(E) = \dfrac{1}{\pi\sqrt{1-E^2}}\Big[g_0\mu_0 + 2\sum_{n\ge1} g_n \mu_n T_n(E)\Big]$,
$\mu_n = \mathrm{Tr}\,T_n(H)$ (stochastic trace, Jackson kernel $g_n$).

**SSH.** $H(k) = \mathbf d(k)\cdot\boldsymbol\sigma$, $\mathbf d = (t_1 + t_2\cos k,\ t_2 \sin k,\ 0)$;
winding $\nu = \frac{1}{2\pi i}\oint dk\, \partial_k \log(d_x + i d_y)$; Zak phase $\gamma = \pi\nu$;
zero modes at the ends iff $t_1 < t_2$.

**Kitaev.** $c_j = (\gamma_{j,1} + i\gamma_{j,2})/2$;
$(-1)^\nu = \mathrm{sgn}\,\mathrm{Pf}[A(0)]\cdot \mathrm{sgn}\,\mathrm{Pf}[A(\pi)]$; topological iff $|\mu| < 2t$.
Majorana nanowire: gap closes at $B_c = \sqrt{\Delta^2 + \mu^2}$; zero-bias peak $2e^2/h$.

**Chern number (Fukui–Hatsugai–Suzuki).**
$U_i(\mathbf k) = \langle u_{\mathbf k} | u_{\mathbf k + \delta_i}\rangle / |\cdot|$,
$F(\mathbf k) = \arg\big[U_x(\mathbf k)\,U_y(\mathbf k+\delta_x)\,U_x(\mathbf k+\delta_y)^{-1}\,U_y(\mathbf k)^{-1}\big]$,
$C = \frac{1}{2\pi}\sum_{\mathbf k} F(\mathbf k) \in \mathbb Z$; $\sigma_{xy} = (e^2/h)\sum_{\text{occ}} C_n$.

**Fu–Kane.** $(-1)^{\nu_0} = \prod_{\text{TRIM}}\prod_{\text{occ}} \xi$ (parity eigenvalues at the
time-reversal-invariant momenta).

# 4. The models of Part II

| Model | Lattice | Invariant | Boundary state | Phase condition (notebook) |
|---|---|---|---|---|
| SSH | chain, 2 sites/cell | winding number ℤ (chiral) | end zero modes | $t_1 < t_2$ |
| Kitaev chain | chain, p-wave BdG | ℤ₂ (Pfaffian) | Majorana end modes, ZBP 2e²/h | $\lvert\mu\rvert < 2t$ |
| Majorana nanowire | chain, Rashba + Zeeman + s-wave | ℤ₂ | Majorana end modes | $B > \sqrt{\Delta^2+\mu^2}$ |
| Rice–Mele pump | chain in (k, t) | Chern number ℤ | edge-state ladder, one charge per cycle | cycle encloses (0, 0) |
| Haldane | honeycomb, complex NNN | Chern number ℤ | chiral edge mode, G = e²/h | $\lvert M\rvert < 3\sqrt3\, t_2 \sin\phi$ |
| Kane–Mele | honeycomb, spinful | ℤ₂ (spin Chern mod 2) | helical edge pair, G = 2e²/h | $\lvert M\rvert < M_c$ |
| p+ip | square, spinless BdG | BdG Chern ℤ | chiral Majorana edge | $\mu \in (-4t, 0) \cup (0, 4t)$ |
| BBH quadrupole | square, 4 sites/cell, π flux | nested Wilson loop, q = ½ | four corner zero modes | $\gamma < \lambda$ |
| Weyl semimetal | cubic, 2 bands | sliced Chern numbers | Fermi arcs | between the nodes |
| 3D TI | cubic, 4 bands | Fu–Kane ℤ₂ | single surface Dirac cone, G = 2e²/h | $\nu_0 = 1$ (m₀ = 2) |

# 5. Pitfalls (each is checked in the notebook)

- **MUMPS is not re-entrant**: never call `kwant.smatrix` from threads with
  MUMPS installed — the kernel dies without a traceback. Use processes, a
  serial loop, or `kwant.solvers.sparse` (SuperLU) in threads.
- **numpy ≥ 2.5** breaks `kwant.physics.magnetic_gauge` in Kwant 1.5.0; pin
  `numpy<2.5` (the installer does) or avoid the helper.
- **Energies inside a gap**: `num_propagating` is zero, `S` is empty.
- **Degenerate BdG pairs** come with run-dependent signs; compare $|E|$.
- **`site_color` callables** receive a `Site` for a Builder but an index for a
  finalized system.
- **Always assert an identity**: unitarity, the sum rule, particle–hole
  symmetry, current conservation, an integer invariant.

# 6. Running it

Windows: `.\install_kwant_windows.ps1`, then `python verify_kwant.py` (ends
"physically correct"). Elsewhere:
`conda create -n kwant -c conda-forge kwant "numpy<2.5" scipy matplotlib sympy python-mumps ipykernel jupyterlab`,
then register the kernel `kwant`. Open `chapters/00_Contents.ipynb`, then a
chapter, with the kernel *Python (kwant)* and **Run All** (all twelve chapters
take about 5 minutes with MUMPS; the two solutions notebooks about 2).
`python -m pytest tests` checks counts, licence texts and documentation;
`python course/build_course.py` rebuilds this handout, the deck and the
lecturer notes from the executed chapters.

# 7. Reading

Groth, Wimmer, Akhmerov, Waintal, *New J. Phys.* **16**, 063065 (2014) —
Kwant. Datta, *Electronic Transport in Mesoscopic Systems* (1995). Nazarov &
Blanter, *Quantum Transport* (2009). Asbóth, Oroszlány, Pályi, *A Short Course
on Topological Insulators* (Springer 2016; arXiv:1509.02295). topocondmat.org
(TU Delft). Bernevig & Hughes, *Topological Insulators and Topological
Superconductors* (2013). Section 27 (chapter 12) lists the paper behind
every model.

*Apache License 2.0 — see `LICENSE` and `NOTICE` in the repository. This
course is independent of, and not endorsed by, the Kwant authors, TU Delft or
the authors of the works cited.*
