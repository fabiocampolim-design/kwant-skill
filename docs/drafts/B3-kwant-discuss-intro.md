# DRAFT — B2/B3: introduction post to kwant-discuss

> Status: **drafted 2026-08-28 — not sent.** Per playbook S9: introduce
> the work before large contributions, start small, all contact under
> the owner's identity. Suggested timing: send *after* K1 and K2 are filed on
> GitLab, so the post can point at them (replace the `<issue #>`
> placeholders). Subscribe first: mail kwant-discuss-join@python.org.
> The August 2025 thread "Your input for a Kwant AI system" is the closest
> existing conversation; replying there instead of a fresh thread is an
> option if the owner prefers.

---

**To:** kwant-discuss@python.org
**Subject:** A Kwant teaching notebook, a Windows installer, and two bugs found on the way

Hello,

I am a condensed-matter physics PhD student and have spent the last weeks
building a self-contained "Kwant — theory and practice" course as a single
executed Jupyter notebook against Kwant 1.5: Part I covers the core API
alongside the scattering theory it implements, Part II reproduces ten
topological models with Kwant (SSH, Kitaev chain, Majorana nanowire,
Thouless pump, Haldane, Kane–Mele, p+ip, BBH quadrupole, Weyl semimetal, 3D
TI). Every figure is generated live, and a companion notebook works
through 25 exercises with asserted solutions. The notebooks were written
with substantial help from an AI coding assistant, and every result was
checked against the literature or an independent calculation before it was
kept; I mention this openly because the "Kwant AI system" thread from last
August asked exactly what such tools are good and bad at, and I am happy to
share what I learned.

Three things from that work may be useful to the project:

1. **Two bugs, now on GitLab.** With numpy ≥ 2.5 the released 1.5.0
   `magnetic_gauge` fails for every 2-D system (the fix is already on
   `main`, but unreleased — issue <#K1>). And calling `kwant.smatrix` from
   several threads segfaults the process when MUMPS is installed, because
   MUMPS is not re-entrant — issue <#K2>, with a small merge request that
   serializes the MUMPS calls, adds a test and documents the constraint.
   Two documentation clarifications (what a `site_color` callable receives
   for a finalized system; what the wraparound momenta are and why they are
   periodic) are attached to the same MR series.

2. **A Windows installer script** (PowerShell, conda-forge based: finds or
   installs Miniforge, creates the environment with kwant + python-mumps,
   registers a Jupyter kernel, runs a real transport calculation to verify).
   `README_WINDOWS.txt` in the repository is rather brief; if a
   Windows-install section on the website would be welcome I can contribute
   it there.

3. **The notebooks themselves**, if there is interest in linking them from
   the "tutorial" or "community" pages once they are public. I would value
   a critical read from anyone here before that.

Thanks for Kwant — it made all of the above possible in weeks rather than
months.

Best regards,
[name]
[institution / link to public repo once published]
