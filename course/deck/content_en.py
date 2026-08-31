# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Quantum transport with Kwant -- undergraduate course, English content.

One dict, DECK: the sections follow each other in one linear sequence (the deck
has previous/next navigation only). Inside each section the slides go from
plain language to Kwant code to the mathematics — the order of understanding.
Every `figure` number is a figure of Kwant_Theory_and_Practice.ipynb (the
notebook's own numbering); build_course.py extracts them from the executed
notebook, so no picture here exists without the cell that made it.  PLACEMENT
(at the end of this file) gives every notebook figure that is not already on
an authored slide its own full-width figure page, inserted after the named
slide — together they put all of the notebook's figures in the deck and in
the slides PDF, each with its full caption.

Layouts: hero | text | figure (bullets left, figures right) | figure-wide
(figures above, bullets below) | code | math (equations, then bullets) | table.
Math is set by hand in HTML (<sup>, <sub>, Unicode Greek) so the deck runs
offline. `notes` are the lecturer notes (shown with S in the deck, exported to
lecturer_notes.md) and always end with one anticipated audience question.
"""

M = '<span class="math">'   # inline math opener; close with </span>
E = "</span>"

DECK = {
    "title": "Quantum Transport with Kwant",
    "sections": [
        # ------------------------------------------------------------------ 0
        {"id": "opening", "name": "Opening",
         "goal": "Say what quantum transport is, why a lattice code is the right tool, and where the course goes.",
         "slides": [
            {"id": "cold-open", "layout": "hero",
             "kicker": "An undergraduate course · one executed notebook",
             "title": "Quantum Transport with Kwant",
             "sub": "From the Schrödinger equation to topological matter, with the code that computes it",
             "notes": "Open with the object on the table: a wire a few hundred nanometres wide, colder than deep space, "
                      "and a current that comes in exact steps. Nothing about it is classical. The promise of the course: every "
                      "picture on these slides was computed by a notebook you can run yourself in a few minutes, and every "
                      "equation is one you will be able to type into Kwant by the end. No result is shown that the notebook "
                      "does not check. Q: \"Do I need to know Python?\" A: you need to read it; the notebook is the textbook."},
            {"id": "what-is-transport", "layout": "text",
             "title": "What quantum transport asks",
             "lead": "Attach wires to a small quantum object and push a current through it. How much gets through, and why?",
             "bullets": [
                 "<strong>Classical wire:</strong> resistance grows with length, current is a smooth function of voltage.",
                 "<strong>Quantum wire:</strong> the conductance comes in <em>steps</em> of "
                 + M + "e<sup>2</sup>/h" + E + " and can be <em>higher</em> with a barrier than without — interference decides.",
                 "The question turns into a scattering problem: an electron wave comes in through a lead, the device scatters it, "
                 "and the current is the probability of getting through.",
                 "A computer is needed because devices have thousands of atoms, disorder, spin, magnetic fields — but the "
                 "physics is one equation, and one lattice code solves it exactly."],
             "notes": "Set the two contrasts: length dependence (Ohm) versus steps; and the surprise that a barrier can raise "
                      "conductance through resonance. Then reframe as scattering: leads are waveguides, the device is the "
                      "scatterer, transmission is conductance. That is the whole Landauer picture in one sentence; the "
                      "mathematics comes in section 2. Q: \"Why not solve the Schrödinger equation directly?\" A: you do — on "
                      "a lattice, where it is a sparse matrix; that is what Kwant does."},
            {"id": "course-map", "layout": "table",
             "title": "The course in ten stops",
             "lead": "The stops follow each other in order; inside each one the slides go from words to code to equations.",
             "header": ["Stop", "Physics", "Kwant"],
             "rows": [
                 ["1 Lattice", "Schrödinger → tight binding", "Builder, lattices, hoppings"],
                 ["2 Leads", "Landauer–Büttiker, Fisher–Lee", "attach_lead, smatrix"],
                 ["3 Shapes", "resonances, billiards, parameters", "shape functions, value functions"],
                 ["4 Spin · graphene · SC", "Rashba, Dirac cones, Andreev", "matrix values, honeycomb, BdG"],
                 ["5 Magnetic fields", "Peierls phase, Landau levels, Hofstadter", "phase hoppings, wraparound"],
                 ["6 Toolbox", "KPM, continuum models, solvers, pitfalls", "kpm, continuum, MUMPS vs SuperLU"],
                 ["7 Topology in 1D", "SSH, Kitaev, Majoranas, pumps", "invariants from the system"],
                 ["8 Topology in 2D/3D", "Chern, Z<sub>2</sub>, chiral Majoranas, corners, Weyl, 3D TI", "Berry curvature on a torus"],
                 ["9 Close", "how to run it, exercises, reading", "Run All"]],
             "notes": "Read the map once, quickly. Tell the audience which stops you will take at depth today and which you "
                      "will pass through — the maths and the extra figure pages of a stop can be skipped forward without "
                      "losing the thread. Stops 7 and 8 are the second half of the notebook (Part II) and can be a separate "
                      "lecture. Q: \"Which stops need the most maths?\" A: 2, 5 and 7–8; each has its maths near the end of "
                      "the section."},
         ]},
        # ------------------------------------------------------------------ 1
        {"id": "lattice", "name": "From Schrödinger to a lattice",
         "goal": "Show that discretising the Schrödinger equation gives a hopping model, and that Kwant's Builder is exactly that model written down.",
         "slides": [
            {"id": "why-lattice", "layout": "figure",
             "title": "Put the wavefunction on a grid",
             "lead": "Replace space by a lattice of sites. The kinetic energy becomes a rule: an electron hops to its neighbours.",
             "figure": 2,
             "bullets": [
                 "Each site carries an <strong>on-site energy</strong>; each bond carries a <strong>hopping</strong> amplitude "
                 + M + "t" + E + ".",
                 "A finer grid means a better approximation to the continuum — and more sites to solve for.",
                 "Real crystals <em>are</em> lattices: for graphene or a chain of atoms the model is not an approximation at all.",
                 "Everything else in the course — leads, spin, magnetic fields, superconductivity — is a choice of what sits on the "
                 "sites and the bonds."],
             "notes": "The figure is the notebook's 5×5 square lattice with every nearest-neighbour bond drawn. Make the two "
                      "readings explicit: (1) the grid is a numerical discretisation of a continuum; (2) the grid is a real "
                      "crystal. Kwant does not care which. The bond picture is the mental model for the whole course: numbers on "
                      "dots, numbers on lines. Q: \"How fine must the grid be?\" A: fine enough that the wavelength spans many "
                      "sites — the next slide gives the number."},
            {"id": "discretise", "layout": "math",
             "title": "The discretisation, done honestly",
             "lead": "Finite differences on a grid of spacing a turn the Laplacian into hopping.",
             "equations": [
                 ("Continuum", M + "H = −(ħ<sup>2</sup>/2m) ∇<sup>2</sup> + V(<b>r</b>)" + E),
                 ("Second derivative on a grid", M + "ψ″(x) ≈ [ψ(x+a) − 2ψ(x) + ψ(x−a)] / a<sup>2</sup>" + E),
                 ("Hopping and on-site energy (2D)", M + "t = ħ<sup>2</sup>/(2ma<sup>2</sup>),   ε<sub>i</sub> = 4t + V(<b>r</b><sub>i</sub>)" + E),
                 ("Tight-binding Hamiltonian", M + "H = Σ<sub>i</sub> ε<sub>i</sub> |i⟩⟨i| − t Σ<sub>⟨ij⟩</sub> (|i⟩⟨j| + h.c.)" + E),
                 ("Band of the empty lattice", M + "E(<b>k</b>) = 4t − 2t(cos k<sub>x</sub>a + cos k<sub>y</sub>a) ≈ ħ<sup>2</sup>k<sup>2</sup>/2m" + E)],
             "bullets": ["The lattice reproduces the free particle for " + M + "ka ≪ 1" + E
                         + "; at the band edge it is a different (but perfectly legitimate) crystal.",
                         "Sign convention: hoppings are " + M + "−t" + E + "; the on-site " + M + "4t" + E
                         + " puts the band bottom at zero. Kwant lets you choose; the notebook keeps this one."],
             "notes": "Derive the second-difference formula on the board in one line; the rest follows. The key numbers: t sets the "
                      "energy scale, 4t (in 2D; 2t in 1D, 6t in 3D) is the band width divided by two. The dispersion at the bottom "
                      "of the band is quadratic with the right mass — that is the check that the lattice is the continuum. "
                      "Q: \"Where did ħ and m go in the notebook?\" A: into t = 1; every energy is in units of t and every length "
                      "in units of a."},
            {"id": "builder", "layout": "code",
             "title": "Kwant's Builder is the Hamiltonian, written as a dictionary",
             "lead": "Sites and hoppings are keys; the numbers (or functions) on them are the values.",
             "code": ("import kwant\n"
                      "lat = kwant.lattice.square(a=1, norbs=1)\n"
                      "syst = kwant.Builder()\n"
                      "for x in range(30):\n"
                      "    for y in range(10):\n"
                      "        syst[lat(x, y)] = 4 * t          # on-site energy\n"
                      "syst[lat.neighbors()] = -t           # every nearest-neighbour bond\n"
                      "fsyst = syst.finalized()             # freeze -> sparse matrices\n"),
             "bullets": ["<code>lat(x, y)</code> is a <strong>Site</strong>: a lattice plus integer coordinates.",
                         "<code>lat.neighbors()</code> is a <strong>HoppingKind</strong>: 'all bonds of this shape'; "
                         "<code>lat.neighbors(2)</code> adds the diagonals.",
                         "Values may be numbers, matrices (spin!) or <em>functions</em> of the site and of runtime parameters.",
                         "<code>finalized()</code> turns the dictionary into the matrices the solvers use. Nothing is computed before."],
             "notes": "Type it live if you can. The Builder is literally a mapping: site → on-site value, (site, site) → hopping. "
                      "Stress the three kinds of value (number, matrix, function) — each later section is one of them. "
                      "Finalisation is the moment the lazy description becomes numbers; leads get attached before it. "
                      "Q: \"What does norbs do?\" A: the number of orbitals per site — 1 here, 2 for spin, 4 for spinful "
                      "superconductors; Kwant needs it to interpret matrix values and to compute densities."},
            {"id": "object-model", "layout": "table",
             "title": "The vocabulary you will use every day",
             "lead": "Six objects; everything in the course is built from them.",
             "header": ["Object", "What it is", "Typical line"],
             "rows": [
                 ["<code>Lattice</code>", "the geometry: unit vectors + basis", "<code>kwant.lattice.honeycomb()</code>"],
                 ["<code>Site</code>", "a lattice plus a tag (integer coordinates)", "<code>lat(3, 4)</code>"],
                 ["<code>Builder</code>", "the mutable Hamiltonian: sites → values, bonds → values", "<code>syst[lat(0, 0)] = 4*t</code>"],
                 ["<code>HoppingKind</code>", "a family of bonds by displacement", "<code>kwant.builder.HoppingKind((1, 0), lat)</code>"],
                 ["lead", "a Builder with a translational symmetry, repeated to infinity", "<code>syst.attach_lead(lead)</code>"],
                 ["finalized system", "immutable, indexable, solvable", "<code>kwant.smatrix(fsyst, energy)</code>"]],
             "notes": "This table is the reference card; the handout repeats it. Two things people mix up: a Site is a "
                      "key, not a number; a lead is not a wire of finite length but an infinite repetition of one unit cell "
                      "along its symmetry. Q: \"Can a lead have a different lattice from the device?\" A: yes, as long as the "
                      "sites at the interface match up — the graphene example does exactly that."},
         ]},
        # ------------------------------------------------------------------ 2
        {"id": "leads", "name": "Leads and conductance",
         "goal": "Compute a first conductance, see it quantised, and derive why: Landauer–Büttiker and the Fisher–Lee relation.",
         "slides": [
            {"id": "two-terminal", "layout": "figure",
             "title": "The canonical experiment: a wire between two reservoirs",
             "lead": "A finite scattering region (blue) with two semi-infinite leads (red). Electrons come in from one side and leave through either.",
             "figure": 4,
             "bullets": ["Leads are perfect waveguides: translationally invariant, so their states are Bloch waves with a "
                         "band structure " + M + "E<sub>n</sub>(k)" + E + ".",
                         "At a given energy each lead carries a finite number " + M + "N" + E + " of <strong>propagating modes</strong>.",
                         "The device mixes them; the scattering matrix records the outcome."],
             "notes": "The figure is the notebook's W=10, L=30 wire, drawn by kwant.plot. Point at the lead unit cell being "
                      "repeated. Introduce 'mode' as 'a transverse standing wave that also travels along the lead'. "
                      "Q: \"Where is the voltage?\" A: in the reservoirs the leads end in — they fix the occupation of incoming "
                      "modes; the leads themselves are ideal."},
            {"id": "quantised", "layout": "figure",
             "title": "Conductance comes in steps",
             "lead": "Sweep the energy: every time a new subband opens in the lead, the conductance rises by exactly one unit.",
             "figure": 5,
             "bullets": ["Step height " + M + "e<sup>2</sup>/h" + E + " for spinless electrons (" + M + "2e<sup>2</sup>/h" + E
                         + " with spin) — a universal constant, no material parameter in it.",
                         "A clean wire transmits every open mode perfectly: " + M + "G = (e<sup>2</sup>/h) · N(E)" + E + ".",
                         "First seen in a quantum point contact in 1988 (van Wees; Wharam); this figure is that experiment computed."],
             "notes": "This is the first result the audience should be able to reproduce from the notebook. Ask them to count "
                      "the steps and compare with the subband minima on the band-structure slide two slides ahead. Emphasise "
                      "the universality: the step is a ratio of fundamental constants. Q: \"Why is it not infinite for a perfect "
                      "conductor?\" A: the contact resistance — connecting a lead with finitely many modes to a reservoir costs "
                      "h/e² per mode, however perfect the wire."},
            {"id": "landauer", "layout": "math",
             "title": "The Landauer–Büttiker formula and where Kwant gets it",
             "lead": "Conductance is transmission. The transmission comes from the Green's function of the device.",
             "equations": [
                 ("Landauer", M + "G = (e<sup>2</sup>/h) Σ<sub>n</sub> T<sub>n</sub> = (e<sup>2</sup>/h) Tr(t<sup>†</sup>t)" + E),
                 ("Scattering matrix", M + "S = " + E + "[[r, t′], [t, r′]]" + M + ",   S<sup>†</sup>S = 1" + E),
                 ("Fisher–Lee", M + "S = −1 + i Γ<sup>1/2</sup> G<sup>r</sup>(E) Γ<sup>1/2</sup>,   G<sup>r</sup> = (E − H − Σ)<sup>−1</sup>" + E),
                 ("Lead self-energy", M + "Σ(E) = Σ<sub>leads</sub> V<sup>†</sup> g<sub>lead</sub>(E) V,   Γ = i(Σ − Σ<sup>†</sup>)" + E),
                 ("Sum rule", M + "Σ<sub>n</sub> (T<sub>n</sub> + R<sub>n</sub>) = N" + E + " — current conservation")],
             "bullets": ["Kwant solves a sparse linear system of the size of the device once per energy; the leads enter only "
                         "through their self-energy, computed from their unit cell.",
                         "Unitarity and the sum rule are exact identities — the notebook asserts them after every calculation, and "
                         "so should you."],
             "notes": "Derivation sketch on the board: incoming flux in mode n is e/h per unit energy; the fraction T_n gets "
                      "through; sum and multiply by e for the current. Then say what Kwant does: it never builds the infinite "
                      "leads, it folds them into a boundary condition (the self-energy) and solves a finite sparse problem. "
                      "Q: \"Is this only linear response?\" A: yes — G at fixed E; a finite bias is an integral of T(E) between "
                      "the two chemical potentials."},
            {"id": "modes", "layout": "figure",
             "title": "See the modes: lead bands and a scattering state",
             "lead": "The staircase is the lead's subband structure; a scattering state is one incoming mode plus everything it becomes.",
             "figures": [12, 6],
             "bullets": ["Each subband minimum " + M + "E<sub>n</sub>" + E + " opens one channel: transverse quantisation in a strip of width "
                         + M + "W" + E + " gives " + M + "E<sub>n</sub> ≈ 2t[1 − cos(nπ/(W+1))]" + E + ".",
                         "The scattering state is a standing wave across the wire and a travelling wave along it — with the density "
                         "pattern of the mode it came from."],
             "notes": "Left: kwant.physics.Bands of the lead — compare each minimum with a step of the staircase. Right: "
                      "kwant.wave_function at E = 0.6 for the lowest mode from the left; the density shows the transverse node "
                      "structure. Q: \"What happens at a band maximum?\" A: modes close again — the staircase comes back down at "
                      "the top of the band; on a lattice the band is finite."},
            {"id": "code-smatrix", "layout": "code",
             "title": "Ten lines from geometry to conductance",
             "lead": "Attach leads, finalise, ask for the scattering matrix.",
             "code": ("lead = kwant.Builder(kwant.TranslationalSymmetry((-1, 0)))\n"
                      "lead[(lat(0, y) for y in range(W))] = 4 * t\n"
                      "lead[lat.neighbors()] = -t\n"
                      "syst.attach_lead(lead)                 # left\n"
                      "syst.attach_lead(lead.reversed())      # right\n"
                      "fsyst = syst.finalized()\n"
                      "\n"
                      "sm = kwant.smatrix(fsyst, energy=0.5)\n"
                      "G = sm.transmission(1, 0)              # e^2/h units\n"
                      "assert abs(sm.transmission(0, 0) + G - sm.num_propagating(0)) < 1e-10\n"),
             "bullets": ["The lead is a Builder with a <code>TranslationalSymmetry</code>; <code>attach_lead</code> finds the interface sites.",
                         "<code>smatrix</code> returns the full " + M + "S" + E + "; <code>transmission(1, 0)</code> sums "
                         + M + "T<sub>n</sub>" + E + " from lead 0 into lead 1.",
                         "The last line is the sum rule as an <code>assert</code>: the notebook's habit of checking every result."],
             "notes": "Walk the code top to bottom. lead.reversed() flips the symmetry direction for the right lead. Point out "
                      "that the assert is not decoration: it catches a wrong lead, a wrong energy inside a gap, a broken "
                      "build. Q: \"How long does this take?\" A: milliseconds for 300 sites; the solver section shows the "
                      "scaling."},
         ]},
        # ------------------------------------------------------------------ 3
        {"id": "shapes", "name": "Shapes, potentials, parameters",
         "goal": "Make the device interesting: potentials that vary in space, arbitrary shapes, and parameters changed at solve time.",
         "slides": [
            {"id": "well", "layout": "figure",
             "title": "A potential well makes resonances",
             "lead": "Lower the on-site energy in a stretch of the wire and the transmission acquires sharp peaks: quasi-bound states.",
             "figure": 7,
             "bullets": ["The well is a cavity; an electron bounces between its ends like light in a Fabry–Pérot etalon.",
                         "Constructive interference at the quasi-bound energies gives " + M + "T → 1" + E + " peaks; in between, "
                         "reflection.",
                         "In Kwant the potential is just a <em>function of the site</em> assigned as the on-site value."],
             "notes": "Connect to optics explicitly; students know Fabry–Pérot. The peak positions move with the well depth "
                      "and length — a good exercise (the notebook has one). Q: \"Why are the peaks not delta functions?\" "
                      "A: the states leak into the leads; the width is the inverse lifetime, ħ/τ."},
            {"id": "stadium", "layout": "figure",
             "title": "Any shape you can write as a function",
             "lead": "A shape is a predicate on coordinates. The stadium is the classic chaotic billiard; its eigenstates are 'scars' on classical orbits.",
             "figures": [8, 9],
             "bullets": ["<code>lat.shape(stadium, start)</code> floods the lattice from a start site, keeping every site where the "
                         "predicate is true.",
                         "Closed systems have no leads: diagonalise <code>fsyst.hamiltonian_submatrix(sparse=True)</code> with "
                         "<code>scipy.sparse.linalg.eigsh</code>.",
                         "Chaotic billiards are the playground of random-matrix theory: level statistics, scarring, weak localisation."],
             "notes": "The stadium is two half-discs joined by a rectangle; the function is three lines. Show the eigenstate "
                      "and ask what a classical billiard ball would do — the 'scar' is a quantum memory of an unstable periodic "
                      "orbit. Q: \"Why sparse?\" A: the Hamiltonian has ~5 non-zeros per row; a dense matrix for 10⁴ sites "
                      "would be 800 MB, the sparse one is a few MB."},
            {"id": "params", "layout": "code",
             "title": "Parameters at solve time, not at build time",
             "lead": "Values can be functions whose extra arguments are supplied when you solve — sweep a field without rebuilding.",
             "code": ("def onsite(site, V0, x0):\n"
                      "    x, y = site.pos\n"
                      "    return 4 * t + (V0 if abs(x - x0) < 5 else 0)\n"
                      "\n"
                      "syst[(lat(x, y) for x in range(L) for y in range(W))] = onsite\n"
                      "fsyst = syst.finalized()\n"
                      "\n"
                      "for V0 in np.linspace(-1, 1, 41):\n"
                      "    sm = kwant.smatrix(fsyst, energy=0.5, params=dict(V0=V0, x0=15))\n"),
             "bullets": ["The function's first argument is the site (or two sites for a hopping); the rest are named parameters.",
                         "<code>params=</code> passes them at solve time; the finalized system is built once.",
                         "This is how every sweep in the course works: energy, field, chemical potential, pairing, dimerisation."],
             "notes": "Emphasise the separation: geometry once, physics per call. Names matter — Kwant inspects the function "
                      "signature to know which parameters it needs, so a typo shows up as a clear error. Q: \"Can I pass "
                      "arrays?\" A: anything hashable-or-not; Kwant only forwards it. The magnetic-field section passes a "
                      "float, the KPM section passes a callable."},
         ]},
        # ------------------------------------------------------------------ 4
        {"id": "spin-graphene-sc", "name": "Spin, graphene, superconductors",
         "goal": "Show the three ways to enrich a site: matrix values (spin), other lattices (graphene), particle-hole doubling (BdG).",
         "slides": [
            {"id": "rashba", "layout": "figure",
             "title": "Spin: matrix values on sites and bonds",
             "lead": "Two orbitals per site. Rashba spin–orbit coupling is a spin-dependent hopping; a Zeeman field is a spin-dependent on-site term.",
             "figures": [10, 11],
             "bullets": [M + "H = −t Σ (c<sup>†</sup><sub>i</sub>c<sub>j</sub>) − iα Σ c<sup>†</sup><sub>i</sub>(<b>σ</b>×<b>d</b><sub>ij</sub>)<sub>z</sub> c<sub>j</sub> + B Σ c<sup>†</sup><sub>i</sub>σ<sub>z</sub>c<sub>i</sub>" + E,
                         "Rashba splits the subbands in " + M + "k" + E + "; Zeeman opens a <strong>helical gap</strong> at "
                         + M + "k = 0" + E + " where only one spin direction propagates each way.",
                         "The conductance staircase becomes non-monotonic: a plateau at an odd number of modes signals the helical gap."],
             "notes": "The hopping is a 2×2 matrix that depends on the bond direction — Kwant's HoppingKind gives you (1,0) "
                      "and (0,1) separately, so the σ×d term is two lines. The helical gap is the ingredient of the Majorana "
                      "nanowire in section 7; plant that now. Q: \"Why does the plateau go down?\" A: inside the helical gap "
                      "one subband is missing at k = 0 — fewer modes at that energy than just above or below."},
            {"id": "graphene", "layout": "figure",
             "title": "Graphene: a honeycomb lattice and a p–n junction",
             "lead": "Two sublattices, a linear 'Dirac' dispersion, and Klein tunnelling: at normal incidence a p–n junction is transparent.",
             "figures": [14, 16],
             "bullets": ["<code>kwant.lattice.honeycomb()</code> has a two-site basis; <code>lat.sublattices</code> gives A and B.",
                         "A smooth potential step " + M + "V(x)" + E + " puts the Fermi level in the conduction band on one side "
                         "and the valence band on the other.",
                         "Transmission is suppressed near the Dirac point and revives above it — the notebook's ribbon leads "
                         "show the folded Dirac cones (fig. 15)."],
             "notes": "The figure on the left is a circular flake with two leads attached at 120°, sites coloured by "
                      "sublattice — a good demonstration that leads may point in any lattice direction. Klein tunnelling is "
                      "the headline: the chirality of the Dirac electron forbids backscattering at normal incidence. "
                      "Q: \"Is graphene special for Kwant?\" A: no — it is one more lattice; the physics is in the geometry."},
            {"id": "bdg", "layout": "figure",
             "title": "Superconductors: double the space, get Andreev reflection",
             "lead": "Bogoliubov–de Gennes doubles every site into electron and hole. An electron hitting a superconductor can bounce back as a hole.",
             "figures": [17, 18],
             "bullets": ["Below the gap " + M + "Δ" + E + " no quasiparticle can enter the superconductor: the only channels are "
                         "normal reflection and <strong>Andreev reflection</strong> (electron → hole, a Cooper pair enters).",
                         "Perfect Andreev reflection doubles the conductance: " + M + "G = 2e<sup>2</sup>/h" + E + " per mode with no barrier.",
                         "A tunnel barrier crosses over to the normal-state result — the Blonder–Tinkham–Klapwijk curves."],
             "notes": "The N–S junction figure shows normal region, barrier and superconductor; the conductance panel is BTK "
                      "for several barrier strengths. The doubling is the key surprise: charge 2e crosses per event. "
                      "Q: \"What is a hole here?\" A: the time-reversed electron state at −E; BdG treats it as a second particle "
                      "type so that pairing becomes a hopping between the two."},
            {"id": "bdg-math", "layout": "math",
             "title": "The BdG construction and the conductance of an N–S junction",
             "lead": "Particle–hole symmetry is built in; the scattering matrix gets electron and hole blocks.",
             "equations": [
                 ("BdG Hamiltonian", M + "H<sub>BdG</sub> = " + E + "[[H − μ, Δ], [Δ<sup>*</sup>, −(H − μ)<sup>*</sup>]]"),
                 ("Particle–hole symmetry", M + "P H<sub>BdG</sub> P<sup>−1</sup> = −H<sub>BdG</sub>,   P = τ<sub>x</sub> K" + E
                  + "  ⇒ spectrum symmetric about zero"),
                 ("Sub-gap conductance", M + "G = (e<sup>2</sup>/h) [N − R<sub>ee</sub> + R<sub>he</sub>]" + E),
                 ("Perfect Andreev", M + "R<sub>he</sub> = N, R<sub>ee</sub> = 0 ⇒ G = 2Ne<sup>2</sup>/h" + E)],
             "bullets": ["In Kwant: <code>norbs=2</code> (or 4 with spin), on-site " + M + "τ<sub>z</sub>(ε − μ) + τ<sub>x</sub>Δ" + E
                         + ", and <code>conservation_law=-τ<sub>z</sub></code> so <code>smatrix</code> can separate electron and hole blocks.",
                         "The notebook checks particle–hole symmetry of the spectrum and the N–S sum rule explicitly."],
             "notes": "Write the 2×2 block form and point out the minus sign and complex conjugate — that is where particle–hole "
                      "symmetry comes from. The conductance formula is the Landauer formula with Andreev counted with a plus "
                      "sign because a hole carries current the other way. Q: \"Why does Kwant need conservation_law?\" A: to "
                      "label the lead modes as electron or hole so that transmission(1, 0) can be resolved into R_ee and R_he."},
            {"id": "observables", "layout": "figure-wide",
             "title": "Local observables: where the current flows",
             "lead": "Densities and currents of a scattering state, as operators applied to the wavefunction.",
             "figure": 19,
             "bullets": ["<code>kwant.operator.Density(fsyst, σ)</code> and <code>kwant.operator.Current(fsyst, σ)</code> — with a matrix "
                         + M + "σ" + E + " to resolve spin.",
                         "The four panels are charge density, spin density, charge current and spin current of one scattering "
                         "state in the Rashba wire.",
                         "Current conservation on every site is another identity the notebook asserts."],
             "notes": "This is the bridge to experiments that image current (scanning gate, SQUID microscopy). Point at the "
                      "spin current being non-zero where the charge current is smooth — spin–orbit coupling at work. "
                      "Q: \"Is the current operator unique on a lattice?\" A: the bond current is; Kwant computes the current "
                      "through each bond from the hopping matrix element."},
         ]},
        # ------------------------------------------------------------------ 5
        {"id": "magnetic", "name": "Magnetic fields",
         "goal": "Put a magnetic field on the lattice with Peierls phases; see Landau levels, the Hofstadter butterfly and a topological phase transition.",
         "slides": [
            {"id": "peierls", "layout": "figure",
             "title": "A magnetic field is a phase on every bond",
             "lead": "Minimal coupling on a lattice: multiply each hopping by the phase of the vector potential integrated along the bond.",
             "figure": 29,
             "bullets": ["Landau gauge " + M + "<b>A</b> = (−By, 0)" + E + ": horizontal bonds pick up " + M + "exp(−2πi Φ y/Φ<sub>0</sub>)" + E + ".",
                         "The wire bands develop flat pieces: <strong>Landau levels</strong> in the bulk, dispersive <strong>edge states</strong> "
                         "at the boundaries.",
                         "The dashed lines are the exact continuum Landau levels " + M + "ħω<sub>c</sub>(n + ½)" + E + " — the lattice hits them "
                         "at low field."],
             "notes": "Peierls substitution is the whole story: the phase around a plaquette is 2π times the flux through it in "
                      "units of the flux quantum. The figure compares the lattice with the continuum — a validation the "
                      "notebook performs numerically. Q: \"Which gauge should I use?\" A: any; only the flux per plaquette is "
                      "physical. But a lead must be translationally invariant, so the gauge must respect its symmetry — the "
                      "Landau gauge with the lead along x does."},
            {"id": "peierls-math", "layout": "math",
             "title": "Peierls, Harper, and the flux quantum",
             "lead": "The phase per bond, the phase per plaquette, and the 1D equation that hides the butterfly.",
             "equations": [
                 ("Peierls phase", M + "t<sub>ij</sub> → t<sub>ij</sub> exp(i(e/ħ)∫<sub>j</sub><sup>i</sup> <b>A</b>·d<b>l</b>)" + E),
                 ("Flux per plaquette", M + "∏<sub>plaquette</sub> phases = exp(2πi Φ/Φ<sub>0</sub>),   Φ<sub>0</sub> = h/e" + E),
                 ("Harper equation (Landau gauge, " + M + "k<sub>x</sub>" + E + " conserved)",
                  M + "−t[ψ<sub>y+1</sub> + ψ<sub>y−1</sub>] − 2t cos(k<sub>x</sub>a − 2πα y) ψ<sub>y</sub> = E ψ<sub>y</sub>,   α = Φ/Φ<sub>0</sub>" + E),
                 ("Rational flux", M + "α = p/q" + E + " ⇒ the magnetic unit cell is " + M + "q" + E + " sites and the band splits into "
                  + M + "q" + E + " subbands")],
             "bullets": ["Every one of Kwant's magnetic-field examples is this substitution with a different " + M + "<b>A</b>" + E + ".",
                         "For a periodic system use <code>kwant.wraparound</code> to turn a symmetry into a momentum parameter."],
             "notes": "The Harper equation is worth the board: a 1D chain with a cosine potential whose period is 1/α lattice "
                      "spacings — commensurate for rational α. That is why the spectrum vs α is so intricate. Q: \"How does "
                      "the notebook get a magnetic field into a lead?\" A: Landau gauge with A along the lead; the phases then "
                      "depend on y only and the lead stays periodic in x."},
            {"id": "hofstadter", "layout": "figure",
             "title": "The Hofstadter butterfly",
             "lead": "Spectrum of the square lattice against flux per plaquette: at every rational flux the band splits, and the gap structure recurs at every scale.",
             "figures": [30, 32],
             "bullets": ["Computed with <code>kwant.wraparound</code> at fixed denominator " + M + "q" + E + ": " + M + "q" + E
                         + " magnetic subbands per flux value.",
                         "Every gap carries an integer — its Hall conductance (TKNN, 1982) — the colour in the 3D view; the "
                         "Landau fan of the previous slide is the sliver near " + M + "Φ = 0" + E + ".",
                         "The first experiments to resolve it used moiré superlattices in graphene (2013), where the magnetic "
                         "unit cell fits in a laboratory field."],
             "notes": "Spend a moment on the beauty; then on the content: every gap is a quantum Hall phase with its own "
                      "integer, and the integers satisfy a Diophantine equation. The 3D coloured view is the notebook's own "
                      "figure with Chern numbers from the same code used in section 8 — the deck's first topological invariant, "
                      "planted early. Q: \"Why do we need moiré lattices to see it?\" A: one flux quantum per atomic plaquette "
                      "would need ~10⁴ T; a superlattice of 10 nm needs a few tesla."},
            {"id": "landau-fan-bhz", "layout": "figure",
             "title": "A field can switch a topological phase off",
             "lead": "The BHZ quantum spin Hall model in a magnetic field: the Landau fan, and the level crossing where quantum spin Hall becomes quantum Hall.",
             "figure": 33,
             "bullets": ["The BHZ model (section 6 builds it from a continuum Hamiltonian) has helical edge states protected by "
                         "time reversal.",
                         "A magnetic field breaks time reversal; the two lowest Landau levels cross at a critical field and the edge "
                         "states are gone.",
                         "Same code path: Peierls phases on the BHZ hoppings, spectrum vs " + M + "B" + E + "."],
             "notes": "This slide is a preview of section 8 and a demonstration that magnetic fields are a probe of topology: "
                      "the crossing is the transition. Q: \"What does the crossing look like in transport?\" A: the quantised "
                      "2e²/h edge conductance of the QSH phase collapses beyond the crossing."},
         ]},
        # ------------------------------------------------------------------ 6
        {"id": "toolbox", "name": "Toolbox",
         "goal": "The parts of Kwant that make large or unusual problems tractable, and the pitfalls the notebook fell into so you need not.",
         "slides": [
            {"id": "plotting", "layout": "figure",
             "title": "Seeing the system: kwant.plot and kwant.plotter.map",
             "lead": "Styling by callables: colour by sublattice, size by wavefunction weight, or interpolate onto a heat map.",
             "figures": [21, 22],
             "bullets": ["<code>kwant.plot(syst, site_color=f, site_size=g, hop_lw=h)</code> — each argument may be a function of the site "
                         "(Builder) or of the site index (finalized system).",
                         "<code>kwant.plotter.map(fsyst, density)</code> interpolates a per-site quantity onto a continuous image.",
                         "3D lattices render the same way (the zincblende example in the notebook, fig. 23)."],
             "notes": "One trap the notebook documents and reported upstream: a site_color callable receives a Site for a "
                      "Builder but an integer index for a finalized system. Mention it — it costs everyone an hour once. "
                      "Q: \"Can I plot with something other than matplotlib?\" A: Kwant 1.5 has a plotly backend for interactive "
                      "3D; the notebook keeps matplotlib so it runs everywhere."},
            {"id": "kpm", "layout": "figure",
             "title": "Spectra without diagonalisation: the kernel polynomial method",
             "lead": "Expand the density of states in Chebyshev polynomials of H; each moment costs one sparse matrix–vector product.",
             "figures": [24, 25],
             "bullets": [M + "ρ(E) = (1/π√(1−E<sup>2</sup>)) [g<sub>0</sub>μ<sub>0</sub> + 2Σ<sub>n≥1</sub> g<sub>n</sub>μ<sub>n</sub>T<sub>n</sub>(E)],   μ<sub>n</sub> = Tr T<sub>n</sub>(H)" + E,
                         "The trace is estimated with random vectors; the Jackson kernel " + M + "g<sub>n</sub>" + E + " damps the Gibbs ringing.",
                         "<code>kwant.kpm.SpectralDensity(fsyst)</code>: graphene's van Hove peaks at " + M + "|E| = t" + E
                         + " and the linear pseudogap at the Dirac point, for 10<sup>4</sup>–10<sup>6</sup> sites."],
             "notes": "KPM is how you get a density of states for a million sites in a minute. The resolution is set by the "
                      "number of moments; the noise by the number of random vectors. The second figure is the sublattice-"
                      "resolved local DOS with a staggered potential — the A and B sublattices become spectrally different. "
                      "Q: \"Does KPM give eigenvectors?\" A: no — densities, local densities, and (with kwant.kpm.Correlator) "
                      "conductivities; for eigenvectors you diagonalise."},
            {"id": "continuum", "layout": "code",
             "title": "From a continuum Hamiltonian to a lattice in one call",
             "lead": "Write the k·p model as a string; kwant.continuum discretises it symbolically.",
             "code": ("import kwant.continuum\n"
                      "hamiltonian = \"\"\"\n"
                      "    + C * identity(4) + M * kron(sigma_0, sigma_z)\n"
                      "    - B * (k_x**2 + k_y**2) * kron(sigma_0, sigma_z)\n"
                      "    - D * (k_x**2 + k_y**2) * kron(sigma_0, sigma_0)\n"
                      "    + A * k_x * kron(sigma_z, sigma_x)\n"
                      "    - A * k_y * kron(sigma_0, sigma_y)\n"
                      "\"\"\"\n"
                      "a = 20                                   # lattice constant in nm\n"
                      "template = kwant.continuum.discretize(hamiltonian, grid=a)\n"
                      "syst.fill(template, shape, start)\n"),
             "bullets": ["This is the BHZ model of HgTe quantum wells; <code>discretize</code> applies the finite-difference rules of "
                         "section 1 to every " + M + "k" + E + " automatically.",
                         "The ribbon spectrum shows a Kramers pair of helical edge states crossing the inverted gap (fig. 26); the "
                         "edge states are spin-polarised and counter-propagating (fig. 27).",
                         "<code>kwant.continuum.lambdify</code> evaluates the continuum dispersion to check the lattice against it (fig. 28)."],
             "notes": "This is the fastest route from a paper to a simulation: copy the Hamiltonian, discretise, fill a shape. "
                      "Say what can go wrong: a too-coarse grid changes the physics (fermion doubling for linear terms is "
                      "handled by the symmetric difference, but the band structure is only right for ka ≪ 1). "
                      "Q: \"What is k_x in the string?\" A: a symbol; discretize replaces k_x by −i∂_x and then by its finite-"
                      "difference stencil, keeping matrices and constants where they are."},
            {"id": "solvers", "layout": "figure",
             "title": "What actually costs time",
             "lead": "One sparse solve per energy; the solver choice matters more than anything else you can tune.",
             "figure": 34,
             "bullets": ["MUMPS (via <code>python-mumps</code>) is the fast default when installed: close to linear scaling with the "
                         "number of sites for quasi-1D systems.",
                         "SciPy's SuperLU is the fallback: the same answers, several times slower.",
                         "Lead self-energies are computed once per energy per lead and cached — many leads are cheap, many energies are not."],
             "notes": "The figure is the notebook's timing of a scattering solve versus system size. Give the rule of thumb: "
                      "width matters more than length (bandwidth of the sparse matrix). Q: \"Can I parallelise over energies?\" "
                      "A: yes, with processes — and this is exactly where the next slide's pitfall lives."},
            {"id": "pitfalls", "layout": "text",
             "title": "Pitfalls the notebook hit so you do not have to",
             "lead": "Five things that went wrong while building this course, each with its check.",
             "bullets": ["<strong>MUMPS is not re-entrant.</strong> Calling <code>kwant.smatrix</code> from several threads with MUMPS "
                         "installed crashes the interpreter with no traceback. Use processes, a serial loop, or the SuperLU "
                         "solver in threads. (Reported upstream with a patch; <code>test_thread_safety.py</code> guards it.)",
                         "<strong>numpy ≥ 2.5 breaks <code>kwant.physics.magnetic_gauge</code></strong> in Kwant 1.5.0 (fixed upstream, "
                         "unreleased): pin <code>numpy&lt;2.5</code> or avoid the gauge helper.",
                         "<strong>Energies inside a gap</strong> give zero propagating modes and a scattering matrix of size 0 — "
                         "check <code>num_propagating</code> before dividing.",
                         "<strong>Degenerate BdG pairs</strong> come out with run-dependent signs; compare " + M + "|E|" + E + ".",
                         "<strong>Every result gets an identity check:</strong> unitarity, sum rule, particle–hole symmetry, "
                         "current conservation, an invariant's quantisation — <code>assert</code> them."],
             "notes": "This is the slide people photograph. Tell the MUMPS story in two sentences: a parallel sweep cell "
                      "killed the kernel with no message; the diagnosis took an afternoon and became a regression test and an "
                      "upstream patch. The lesson generalises: in numerical physics, the assertion is the experiment's error "
                      "bar. Q: \"How do I know MUMPS is being used?\" A: kwant.solvers.default reports it; the notebook's first "
                      "cell prints the active solver."},
         ]},
        # ------------------------------------------------------------------ 7
        {"id": "topo1d", "name": "Topology in one dimension",
         "goal": "Four one-dimensional models where an integer, computed from the bulk, predicts a state at the edge.",
         "slides": [
            {"id": "ssh", "layout": "figure",
             "title": "The SSH chain: the simplest topological insulator",
             "lead": "Two sites per cell, alternating hoppings. Whether the weak bond is inside or between cells decides if the ends carry zero-energy states.",
             "figures": [35, 36],
             "bullets": ["For " + M + "t<sub>1</sub> &lt; t<sub>2</sub>" + E + " a doublet is pinned to zero energy for any chain length; for "
                         + M + "t<sub>1</sub> &gt; t<sub>2</sub>" + E + " there is none.",
                         "The two zero modes live at opposite ends, each on a single sublattice (fig. 37); in-gap transport with weak "
                         "leads happens only in the topological phase (fig. 38).",
                         "Nothing local distinguishes the two phases — only a winding number of the bulk does."],
             "notes": "Start with the bond picture: a chain of dimers; cut it between strong bonds and you leave an unpaired site "
                      "at each end. That is the whole intuition, and it is exact in the fully dimerised limit. The spectrum "
                      "figure shows the zero-energy doublet appearing precisely at t1 = t2. Q: \"Are the zero modes protected?\" "
                      "A: by chiral (sublattice) symmetry — a perturbation that respects it cannot move them from zero; the maths "
                      "slide says why."},
            {"id": "ssh-math", "layout": "math",
             "title": "Winding number and Zak phase",
             "lead": "The bulk Hamiltonian is a vector in the plane; count how many times it winds around the origin.",
             "equations": [
                 ("Bloch Hamiltonian", M + "H(k) = <b>d</b>(k)·<b>σ</b>,   <b>d</b> = (t<sub>1</sub> + t<sub>2</sub>cos k,  t<sub>2</sub>sin k,  0)" + E),
                 ("Winding number", M + "ν = (1/2πi) ∮ dk  d<sub>k</sub> log(d<sub>x</sub> + i d<sub>y</sub>)  ∈ ℤ" + E),
                 ("Zak phase", M + "γ = i ∮ dk ⟨u<sub>k</sub>|∂<sub>k</sub>u<sub>k</sub>⟩ = πν  (mod 2π)" + E),
                 ("Bulk–boundary", M + "ν = 1" + E + " ⇒ one zero mode per end, protected by " + M + "σ<sub>z</sub>Hσ<sub>z</sub> = −H" + E)],
             "bullets": ["The notebook computes " + M + "ν" + E + " from " + M + "<b>d</b>(k)" + E + " and the Zak phase from the "
                         "Bloch eigenvectors, and asserts they agree with the count of zero modes.",
                         "Chiral symmetry keeps " + M + "d<sub>z</sub> = 0" + E + ": the loop cannot leave the plane, so the winding cannot change without "
                         "closing the gap."],
             "notes": "Draw the d(k) circle: centre t1, radius t2 — it encloses the origin exactly when t2 > t1. That picture is "
                      "the invariant. The Zak phase is its Berry-phase form and is what generalises to 2D. Q: \"What if the "
                      "chiral symmetry is broken?\" A: the zero modes move off zero but stay at the ends as long as the gap is "
                      "open; the topological classification changes (no integer, just a Berry phase)."},
            {"id": "kitaev", "layout": "figure",
             "title": "The Kitaev chain: split an electron in two",
             "lead": "A p-wave superconducting chain. Each fermion is two Majorana operators; in the topological phase the unpaired Majoranas sit at the two ends.",
             "figures": [39, 40],
             "bullets": ["Topological for " + M + "|μ| &lt; 2t" + E + " with " + M + "Δ ≠ 0" + E + ": a zero-energy BdG state spans the whole window "
                         "(fig. 40), its density split between the ends (fig. 41).",
                         "The Majorana end mode pins the Andreev conductance at exactly " + M + "2e<sup>2</sup>/h" + E + " at zero bias, for any "
                         "barrier (fig. 42).",
                         "Two Majoranas far apart make one fermion whose occupation costs no energy — the qubit idea."],
             "notes": "The Majorana-language figure is the intuition: write c = (γ1 + iγ2)/2, choose parameters so the "
                      "Hamiltonian couples γ2 of one site to γ1 of the next, and the first and last operators are left out. "
                      "The zero-bias peak quantised at 2e²/h is the experimental signature everybody looks for. Q: \"How is this "
                      "different from the SSH zero modes?\" A: these are their own antiparticles — a Majorana mode is half a "
                      "fermion; SSH zero modes are ordinary electron states."},
            {"id": "kitaev-math", "layout": "math",
             "title": "Majorana operators and the Z<sub>2</sub> invariant",
             "lead": "The invariant of a particle–hole symmetric chain is a sign: the Pfaffian of the Hamiltonian at the two time-reversal-invariant momenta.",
             "equations": [
                 ("Kitaev Hamiltonian", M + "H = Σ<sub>j</sub> [−μ c<sup>†</sup><sub>j</sub>c<sub>j</sub> − t(c<sup>†</sup><sub>j</sub>c<sub>j+1</sub> + h.c.) + Δ(c<sub>j</sub>c<sub>j+1</sub> + h.c.)]" + E),
                 ("Majorana operators", M + "c<sub>j</sub> = (γ<sub>j,1</sub> + iγ<sub>j,2</sub>)/2,   γ<sup>†</sup> = γ,   {γ<sub>a</sub>, γ<sub>b</sub>} = 2δ<sub>ab</sub>" + E),
                 ("Z<sub>2</sub> invariant", M + "(−1)<sup>ν</sup> = sgn Pf[A(0)] · sgn Pf[A(π)],   A(k) = i H<sub>BdG</sub>(k) " + E + " in the Majorana basis"),
                 ("Result", M + "ν = 1 ⇔ |μ| &lt; 2t" + E)],
             "bullets": ["The notebook computes the Pfaffians and asserts the phase boundary at " + M + "μ = ±2t" + E + ".",
                         "A Z<sub>2</sub> invariant can only be 0 or 1: two Majorana pairs at one end can gap each other out."],
             "notes": "The Pfaffian is the square root of the determinant with a sign; that sign is the invariant. Point at "
                      "the two momenta 0 and π — the only ones where a 1D BdG Hamiltonian is its own particle–hole partner. "
                      "Q: \"Why Z2 and not Z?\" A: particle–hole symmetry alone (class D) only protects the parity of the number "
                      "of Majoranas per end."},
            {"id": "nanowire", "layout": "figure",
             "title": "The Majorana nanowire: Kitaev physics in a real device",
             "lead": "A semiconductor wire with spin–orbit coupling on a superconductor, in a magnetic field. Three ingredients, one Kitaev chain.",
             "figures": [44, 45],
             "bullets": ["The bulk gap closes exactly at " + M + "B<sub>c</sub> = √(Δ<sup>2</sup> + μ<sup>2</sup>)" + E + " and reopens topological (fig. 44).",
                         "A tunnelling map " + M + "G(V, B)" + E + " shows the zero-bias peak emerging beyond " + M + "B<sub>c</sub>" + E + " (fig. 45); "
                         "the Majorana pair is visible in real space (fig. 46).",
                         "Rashba + Zeeman make the helical gap of section 4; proximity pairing inside it is effectively p-wave."],
             "notes": "This is the Oreg–Lutchyn / Lutchyn–Sau–Das Sarma proposal of 2010 and the device of the 2012 experiments. "
                      "Say clearly what the notebook shows: the phase boundary formula reproduced numerically, and the zero-bias "
                      "peak. Then say what it does not: disorder, soft gaps, Andreev bound states that mimic the peak — the "
                      "reason the experiments are still debated. Q: \"Why do we need the magnetic field?\" A: to remove one "
                      "spin species from the Fermi level so that the induced pairing is effectively spinless — the Kitaev "
                      "condition."},
            {"id": "pump", "layout": "figure",
             "title": "The Thouless pump: a Chern number in (k, t)",
             "lead": "Cycle the SSH parameters slowly around the gapless point and exactly one electron per cell is transported per cycle.",
             "figures": [47, 48],
             "bullets": ["The Rice–Mele model adds a staggered potential to SSH; the cycle encircles the only gapless point " + M + "(δ, Δ) = (0, 0)" + E + ".",
                         "Edge states ladder across the bulk gap while the bulk polarisation winds by one unit cell (fig. 48).",
                         "The pumped charge is the Chern number of the band over the " + M + "(k, t)" + E + " torus — the same integer as in 2D."],
             "notes": "This is the bridge to section 8: replace time by a second momentum and the pump becomes a Chern insulator. "
                      "The notebook computes the Chern number with the same function it later uses for Haldane. Q: \"Has this "
                      "been measured?\" A: yes — in cold-atom optical superlattices (2016) and in photonic waveguides."},
         ]},
        # ------------------------------------------------------------------ 8
        {"id": "topo2d3d", "name": "Topology in two and three dimensions",
         "goal": "Six models, one method: compute a Berry-curvature invariant from the bulk Bloch Hamiltonian, then find the promised boundary state in a finite system.",
         "slides": [
            {"id": "haldane", "layout": "figure",
             "title": "The Haldane model: a Chern insulator without Landau levels",
             "lead": "Honeycomb lattice, real nearest-neighbour hopping, complex second-neighbour hopping. A quantum Hall effect with zero net field.",
             "figures": [50, 52],
             "bullets": ["Phase diagram from the Chern number: lobes with " + M + "C = ±1" + E + " bounded by "
                         + M + "|M| = 3√3 t<sub>2</sub> sin φ" + E + " (fig. 50).",
                         "One chiral edge mode per edge crosses the bulk gap of a zigzag ribbon (fig. 52); the two-terminal conductance is "
                         + M + "e<sup>2</sup>/h" + E + ".",
                         "Realised in cold atoms (2014) and, as the quantum anomalous Hall effect, in magnetic topological insulators (2013)."],
             "notes": "Haldane's 1988 paper is the origin of everything in this section. The figure of the lattice (fig. 49) shows "
                      "the second-neighbour bonds with their phases; the phase diagram is computed by the notebook with the "
                      "Fukui–Hatsugai–Suzuki method on a 30×30 grid. Q: \"Why does the net flux have to be zero?\" A: it need "
                      "not — but with zero net flux the model keeps the lattice translation symmetry, which is the point: no "
                      "Landau levels, still a Chern number."},
            {"id": "chern-math", "layout": "math",
             "title": "Berry curvature and the Chern number on a lattice",
             "lead": "The invariant is the integral of the Berry curvature over the Brillouin-zone torus; on a grid it is a sum of plaquette phases.",
             "equations": [
                 ("Berry connection and curvature", M + "A<sub>i</sub>(<b>k</b>) = i⟨u|∂<sub>i</sub>u⟩,   Ω = ∂<sub>x</sub>A<sub>y</sub> − ∂<sub>y</sub>A<sub>x</sub>" + E),
                 ("Chern number", M + "C = (1/2π) ∫<sub>BZ</sub> Ω d<sup>2</sup>k  ∈ ℤ" + E),
                 ("Fukui–Hatsugai–Suzuki", M + "U<sub>i</sub>(<b>k</b>) = ⟨u<sub><b>k</b></sub>|u<sub><b>k</b>+δ<sub>i</sub></sub>⟩/|…|,   "
                  "F = arg[U<sub>x</sub>(<b>k</b>) U<sub>y</sub>(<b>k</b>+δ<sub>x</sub>) U<sub>x</sub>(<b>k</b>+δ<sub>y</sub>)<sup>−1</sup> U<sub>y</sub>(<b>k</b>)<sup>−1</sup>],   C = (1/2π)Σ F" + E),
                 ("TKNN", M + "σ<sub>xy</sub> = (e<sup>2</sup>/h) Σ<sub>occupied</sub> C<sub>n</sub>" + E)],
             "bullets": ["The lattice formula is gauge invariant plaquette by plaquette and exactly integer for any grid fine enough "
                         "to resolve the gap — the notebook's <code>chern_fhs</code> (section 20) serves every 2D model.",
                         "The Berry curvature of the lower Haldane band over the torus (fig. 51) integrates to " + M + "C = 1" + E + "."],
             "notes": "Derive the FHS link variable on the board: it is the discrete version of the Berry phase around one "
                      "plaquette; the sum of all plaquettes is the Chern number because the phases of interior links cancel. "
                      "Stress 'from the system': the notebook takes H(k) from the Kwant Builder via wraparound, so any model "
                      "you build can be tested. Q: \"How fine a grid?\" A: the notebook's chern_fhs defaults to 40×40 and the "
                      "result is exactly integer on any grid that resolves the gap; near a phase transition the curvature "
                      "spikes and you need more."},
            {"id": "kane-mele", "layout": "figure",
             "title": "Kane–Mele: two copies of Haldane, one Z<sub>2</sub>",
             "lead": "Spin-up and spin-down electrons see opposite Haldane phases. Time reversal is restored; the edge carries a helical pair.",
             "figures": [53, 54],
             "bullets": ["The helical crossing survives Rashba coupling because Kramers' theorem forbids the two partners from mixing "
                         "(fig. 53, right).",
                         "All current injected inside the gap flows along the edges (fig. 54); the two-terminal conductance is "
                         + M + "2e<sup>2</sup>/h" + E + ".",
                         "The invariant is Z<sub>2</sub>: the spin Chern number mod 2, or the Fu–Kane Pfaffian."],
             "notes": "The quantum spin Hall effect: HgTe wells (2007) are the BHZ version of this; Kane–Mele is the graphene "
                      "version with a spin–orbit gap too small to see. The key protection statement is Kramers: at time-reversal-"
                      "invariant momenta the two edge states are a Kramers pair and cannot split. Q: \"What is a Z2 invariant "
                      "physically?\" A: whether the number of Kramers pairs of edge states is odd (protected) or even (can be "
                      "gapped out)."},
            {"id": "pip", "layout": "figure",
             "title": "The p+ip superconductor: a chiral Majorana edge",
             "lead": "Spinless pairing with a phase that winds around the Fermi surface. The topological phase has a single Majorana mode running around the boundary.",
             "figures": [56, 58],
             "bullets": ["BdG Chern number " + M + "C = ±1" + E + " in the weak-pairing phases, transitions at " + M + "μ = 0, ±4t" + E + " (fig. 56).",
                         "A strip has one chiral Majorana branch crossing the gap in the topological phase (fig. 57); a finite sample's lowest "
                         "state circulates the whole boundary (fig. 58).",
                         "A vortex in the pairing binds a Majorana zero mode — the 2D route to non-Abelian statistics."],
             "notes": "This is the 2D Kitaev chain and the effective model of the ν = 5/2 quantum Hall state and of Sr₂RuO₄ "
                      "(disputed). The pairing is real on horizontal bonds and imaginary on vertical ones (fig. 55) — that is the "
                      "phase winding on the lattice. Q: \"Chiral Majorana — half a chiral fermion?\" A: yes: it carries half the "
                      "thermal Hall conductance of an electron edge mode, κ = ½ × (π²k_B²T/3h)."},
            {"id": "bbh", "layout": "figure",
             "title": "Higher-order topology: the BBH quadrupole",
             "lead": "Four sites per cell on a square lattice with π flux. The bulk and the edges are gapped; the corners carry the zero modes.",
             "figures": [60, 61],
             "bullets": ["Wannier bands " + M + "ν<sub>±</sub>(k<sub>x</sub>)" + E + " are gapped in the topological phase and collapse in the trivial one (fig. 60).",
                         "A finite flake has four zero-energy states whose density sits on the four corners (fig. 61); each carries charge "
                         + M + "e/2" + E + ".",
                         "The invariant is a nested Wilson loop — a Berry phase of a Berry phase — the quadrupole moment quantised to ½."],
             "notes": "Benalcazar–Bernevig–Hughes 2017; realised in microwave, acoustic and electrical-circuit metamaterials within a "
                      "year. The point for the course: the boundary of the boundary carries the state — a second-order insulator. "
                      "Q: \"Why π flux?\" A: it makes the model have the mirror and C4 symmetries with the right algebra to "
                      "quantise the quadrupole; the notebook implements it as a sign on one bond per plaquette."},
            {"id": "weyl", "layout": "figure",
             "title": "Weyl semimetals: Fermi arcs from sliced Chern numbers",
             "lead": "A 3D band touching that is a monopole of Berry curvature. Slice the Brillouin zone: the Chern number jumps at each node, and the surface shows an arc.",
             "figures": [62, 63],
             "bullets": ["Chern number of the 2D slices " + M + "H(k<sub>x</sub>, k<sub>y</sub>; k<sub>z</sub>)" + E + " jumps by the chirality "
                         + M + "±1" + E + " at each Weyl node (fig. 62).",
                         "Between the nodes every slice is a Chern insulator with an edge state — stacked, they form the <strong>Fermi arc</strong> "
                         "on the surface (fig. 63).",
                         "Transport through a Weyl bar (fig. 65) shows the arc contribution; the 3D dispersion (fig. 64) shows the "
                         "two sheets touching at the nodes."],
             "notes": "The slicing argument is the whole physics: a 3D semimetal is a family of 2D insulators parametrised by "
                      "k_z, and the Chern number can only change where the gap closes — at a Weyl node. Discovered in TaAs in "
                      "2015. Q: \"Can Weyl nodes be removed?\" A: only by annihilating two of opposite chirality — the monopole "
                      "charge is conserved."},
            {"id": "ti3d", "layout": "figure",
             "title": "The 3D topological insulator: a Dirac cone on every surface",
             "lead": "A band-inverted 3D insulator with time reversal. Its Z<sub>2</sub> index is a product of parities; its surface is a single, unremovable Dirac cone.",
             "figures": [66, 68],
             "bullets": ["Slab spectrum coloured by surface weight: one surface Dirac cone spans the inverted gap (fig. 66); as a 3D "
                         "dispersion it is a single cone (fig. 67).",
                         "Fu–Kane: " + M + "(−1)<sup>ν<sub>0</sub></sup> = ∏<sub>TRIM</sub> ξ<sub>occupied</sub>" + E + " — the product of parity "
                         "eigenvalues at the eight time-reversal-invariant momenta.",
                         "Transport through a TI bar (fig. 68): in the topological phase the surface conducts while the bulk is insulating."],
             "notes": "Bi₂Se₃ is the textbook material; the notebook's model is the four-band k·p lattice model. The single Dirac cone "
                      "is the odd number that Z2 protects — a normal surface state comes in pairs. Q: \"Why can a single Dirac "
                      "cone not exist in a 2D lattice by itself?\" A: fermion doubling — on a 2D lattice cones come in pairs; a "
                      "single one needs the 3D bulk as its 'other half'. That is why a TI surface is different from graphene."},
         ]},
        # ------------------------------------------------------------------ 9
        {"id": "close", "name": "Close",
         "goal": "Send them to the notebook: how to run it, what the exercises ask, where to read next.",
         "slides": [
            {"id": "run-it", "layout": "code",
             "title": "Run it yourself",
             "lead": "One command on Windows; three lines of conda elsewhere. Then Run All.",
             "code": ("# Windows (PowerShell, from the repository):\n"
                      ".\\install_kwant_windows.ps1        # Miniforge + kwant + MUMPS + kernel 'kwant'\n"
                      "python verify_kwant.py             # ends with 'physically correct'\n"
                      "\n"
                      "# Linux / macOS / existing conda:\n"
                      "conda create -n kwant -c conda-forge kwant \"numpy<2.5\" scipy matplotlib sympy python-mumps ipykernel jupyterlab\n"
                      "conda activate kwant\n"
                      "python -m ipykernel install --user --name kwant --display-name \"Python (kwant)\"\n"),
             "bullets": ["Open <code>Kwant_Theory_and_Practice.ipynb</code> with the kernel <strong>Python (kwant)</strong> and Run All: "
                         "about four minutes with MUMPS.",
                         "Every figure of this deck is a numbered figure of that notebook (<code>course/figures/figures.json</code> maps them).",
                         "<code>python -m pytest tests</code> checks the notebook's counts, the licence texts and the documentation."],
             "notes": "Do the install before the lecture, not during. The verify script runs real physics checks — quantised "
                      "conductance, unitarity, the sum rule — so 'it imports' is not the bar. Q: \"pip install kwant?\" "
                      "A: on Linux it works; on Windows the conda-forge build is the one with MUMPS and is the one this course "
                      "was tested with."},
            {"id": "exercises", "layout": "text",
             "title": "The exercises",
             "lead": "Twenty-five, at the end of each part, each with an origin flag and a difficulty mark; every one is solved and asserted in the companion notebook.",
             "bullets": ["◦ direct — one call or one parameter change: thread a wire (E1.1), sweep the potential well (E1.4), "
                         "reverse the Rice–Mele pump cycle (E2.5), recompute the Haldane phase diagram (E2.6).",
                         "• requires thought — a new observable or geometry: the Landauer formula at finite bias (E1.3), universal "
                         "conductance fluctuations (E1.5), the graphene p–n sweep (E1.6), a Kane–Mele Rashba sweep (E2.8), tracking the Weyl nodes (E2.11).",
                         "★ mini-project — Andreev bound states and the Josephson effect (E1.8), a next-nearest-neighbour SSH chain (E2.3), "
                         "a vortex in the p+ip superconductor (E2.9), the Fu–Kane parity invariant (E2.12).",
                         "Two are pencil-and-paper: the FHS plaquette flux (E1.11) and what particle–hole symmetry alone implies (E2.14).",
                         "Origins are marked: some are re-posed Kwant tutorial problems, some paraphrase topocondmat.org or Asbóth <em>et al.</em>, "
                         "most are original. The solutions notebook is the marking key: its <code>assert</code>s are the rubric."],
             "notes": "Assign by mark: ◦ for everyone, • for a problem set, ★ for a term project. The assert-based solutions "
                      "mean students can self-check without seeing the code first — hide the solutions notebook until the "
                      "deadline. Q: \"Can I use the solutions in my own course?\" A: yes — Apache-2.0; keep the notice and the "
                      "attribution cell."},
            {"id": "reading", "layout": "text",
             "title": "Where to read next",
             "lead": "The three sources this course was modelled on, and the papers behind each model.",
             "bullets": ["<strong>Kwant</strong>: Groth, Wimmer, Akhmerov, Waintal, <em>New J. Phys.</em> 16, 063065 (2014); the tutorial at kwant-project.org.",
                         "<strong>Transport</strong>: Datta, <em>Electronic Transport in Mesoscopic Systems</em>; Nazarov & Blanter, <em>Quantum Transport</em>.",
                         "<strong>Topology</strong>: Asbóth, Oroszlány, Pályi, <em>A Short Course on Topological Insulators</em> (arXiv:1509.02295); "
                         "topocondmat.org (TU Delft); Bernevig & Hughes, <em>Topological Insulators and Topological Superconductors</em>.",
                         "<strong>The models</strong>: SSH 1979 · Haldane 1988 · Kane–Mele 2005 · Fu–Kane 2007 · Kitaev 2001 · Lutchyn/Oreg 2010 · "
                         "BBH 2017 · Weyl in TaAs 2015 — every one cited in the notebook's reference shelf (section 27).",
                         "<strong>Upstream</strong>: the Kwant findings of this project (MUMPS re-entrancy, numpy 2.5, plotter warning filters) "
                         "are documented in <code>docs/02-findings-backlog.md</code> with patches."],
             "notes": "Point students at the notebook's section 27, which has ~70 references with one-line descriptions, "
                      "rather than at this slide. Q: \"Is there a textbook that uses Kwant throughout?\" A: topocondmat.org is "
                      "the closest; this notebook was written to be that for a transport course."},
            {"id": "thanks", "layout": "hero",
             "kicker": "Quantum Transport with Kwant",
             "title": "Thank you",
             "sub": "Slides, handout, lecturer notes and the notebook that made every figure: kwant-theory-and-practice · Apache-2.0",
             "notes": "Close by returning to the object on the table: the steps in the current are e²/h, the Majorana peak is "
                      "2e²/h, the Chern number is an integer — and the notebook checks all three. The handout has the "
                      "reference card, the key equations and the models table. Q: \"Where do I report a problem?\" A: the "
                      "repository's issue tracker; the notebook's counts and figures are tested, so a failing test is a real "
                      "finding."},
         ]},
    ],
}

# Every notebook figure that is not already on an authored slide gets its own
# figure page (full caption, full width), inserted after the slide named here.
# build_course.py checks that authored figures and PLACEMENT together cover the
# notebook's figures exactly once each.
PLACEMENT = {
    1: "builder", 3: "builder",                 # HoppingKind / neighbors(2) examples
    13: "peierls",                              # closed disc vs B: Landau condensation
    15: "graphene",                             # ribbon lead subbands: folded Dirac cones
    20: "plotting", 23: "plotting",             # styling callables; 3D zincblende
    26: "continuum", 27: "continuum", 28: "continuum",  # BHZ ribbon, edge states, lambdify check
    31: "hofstadter",                           # butterfly as 3D DOS landscape
    37: "ssh", 38: "ssh",                       # zero-mode density; in-gap transmission
    41: "kitaev", 42: "kitaev",                 # Majorana halves; zero-bias peak
    43: "nanowire", 46: "nanowire",             # device sketch; Majorana pair in real space
    49: "haldane",                              # the Haldane lattice with its phases
    51: "chern-math",                           # Berry curvature over the torus
    55: "pip", 57: "pip",                       # p+ip pairing pattern; strip spectra
    59: "bbh",                                  # the BBH lattice
    64: "weyl", 65: "weyl",                     # slab dispersion; transport bar geometry
    67: "ti3d",                                 # surface Dirac cone in 3D
}
