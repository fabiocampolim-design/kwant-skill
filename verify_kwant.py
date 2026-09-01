#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""
verify_kwant.py -- prove that a Kwant installation actually works.

This does not just import kwant. It runs a real quantum transport calculation
and checks the results against physics that must hold exactly:

  * conductance of a clean wire is quantised in integer units of e^2/h
  * the scattering matrix is unitary  (== current conservation)
  * T + R equals the number of propagating modes  (sum rule)
  * a closed-system diagonalisation runs
  * kwant.continuum can discretise a symbolic Hamiltonian, if sympy is present
  * kwant.physics.magnetic_gauge works (it is broken on kwant 1.5.0 + numpy >= 2.5;
    reported as a warning because the notebooks do not depend on it)

Usage:
    python verify_kwant.py                     # console report, log under ./logs/
    python verify_kwant.py --outdir out --json # summary JSON + log under out/
    python verify_kwant.py --quiet             # one-line result only

Exit code 0 means everything that is installed works; 1 means at least one
check failed; 2 means kwant itself could not be imported.
"""
import argparse
import datetime as _dt
import json
import os
import platform
import sys
import traceback

__version__ = "1.1.0"      # fallback; the product version is the VERSION file
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"), encoding="utf-8") as _f:
        __version__ = _f.read().strip() or __version__
except OSError:
    pass

# --------------------------------------------------------------------------- reporting


class Report:
    """Collects results, prints to the console at the chosen verbosity and to a log."""

    def __init__(self, log_path, verbosity):
        self.failures, self.warnings, self.oks = [], [], []
        self.verbosity = verbosity          # 0 quiet, 1 normal, 2 verbose
        self.log = open(log_path, "w", encoding="utf-8")
        self.log_path = log_path

    def _emit(self, line, level=1):
        self.log.write(line + "\n")
        if self.verbosity >= level:
            print(line)

    def ok(self, msg):
        self.oks.append(msg)
        self._emit(f"  [ ok ] {msg}")

    def warn(self, msg):
        self.warnings.append(msg)
        self._emit(f"  [warn] {msg}")

    def fail(self, msg):
        self.failures.append(msg)
        self._emit(f"  [FAIL] {msg}")

    def section(self, title):
        self._emit("")
        self._emit(title)
        self._emit("-" * 70)

    def detail(self, msg):
        self._emit(f"         {msg}", level=2)

    def close(self):
        self.log.close()


# --------------------------------------------------------------------------- checks


def check_imports(rep):
    rep.section("1. Core imports")
    try:
        import kwant
        rep.ok(f"kwant       {kwant.__version__}")
    except Exception as exc:
        rep.fail(f"cannot import kwant: {exc}")
        rep.detail(traceback.format_exc())
        return None
    import numpy as np
    rep.ok(f"numpy       {np.__version__}")
    import scipy
    rep.ok(f"scipy       {scipy.__version__}")
    try:
        import tinyarray
        rep.ok(f"tinyarray   {getattr(tinyarray, '__version__', 'present')}")
    except ImportError:
        rep.fail("tinyarray missing -- kwant cannot work properly without it")
    try:
        import matplotlib
        rep.ok(f"matplotlib  {matplotlib.__version__}")
        matplotlib.use("Agg")          # headless, so this script never blocks on a window
    except ImportError:
        rep.warn("matplotlib missing -- plotting sections of the notebook will not run")
    return kwant


def check_optional(rep, kwant):
    rep.section("2. Optional components")
    have = {}
    try:
        import kwant.solvers.mumps          # noqa: F401
        rep.ok("MUMPS solver available  <-- large systems will be much faster")
        have["mumps"] = True
    except ImportError:
        rep.warn("MUMPS not available; falling back to scipy sparse (slower). "
                 "Install with: conda install -c conda-forge python-mumps")
        have["mumps"] = False
    try:
        import sympy                        # noqa: F401
        import kwant.continuum              # noqa: F401
        rep.ok(f"kwant.continuum available (sympy {sympy.__version__})")
        have["continuum"] = True
    except ImportError as exc:
        rep.warn(f"kwant.continuum unavailable ({exc}); notebook sections 13/14 will not "
                 "run. Install with: conda install -c conda-forge sympy")
        have["continuum"] = False
    try:
        import qsymm
        import kwant.qsymm                  # noqa: F401
        rep.ok(f"kwant.qsymm available (qsymm {qsymm.__version__})")
    except ImportError:
        rep.warn("kwant.qsymm unavailable (optional)")
    try:
        import plotly                       # noqa: F401
        rep.ok(f"plotly {plotly.__version__} -- interactive backend usable via "
               "kwant.plotter.set_engine('plotly')")
    except ImportError:
        rep.warn("plotly not installed (optional; matplotlib is the default backend)")
    import kwant.solvers.default
    rep.detail(f"default solver: {kwant.solvers.default.__name__}")
    have["default_solver"] = kwant.solvers.default.__name__
    return have


def build_wire(kwant, t=1.0, W=10, L=30):
    lat = kwant.lattice.square(1, norbs=1)
    syst = kwant.Builder()
    syst[(lat(x, y) for x in range(L) for y in range(W))] = 4 * t
    syst[lat.neighbors()] = -t
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1, 0)))
    lead[(lat(0, j) for j in range(W))] = 4 * t
    lead[lat.neighbors()] = -t
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return lat, lead, syst.finalized()


def check_transport(rep, kwant, fsyst):
    rep.section("3. Transport calculation: conductance quantisation")
    rep.ok(f"built and finalised a {len(fsyst.sites)}-site system with {len(fsyst.leads)} leads")
    # In a clean wire every open mode transmits perfectly, so T must be an integer
    # equal to the number of propagating modes.
    for energy in (0.05, 0.25, 0.55, 0.95):
        sm = kwant.smatrix(fsyst, energy)
        T, N = sm.transmission(1, 0), sm.num_propagating(0)
        if abs(T - N) < 1e-6:
            rep.ok(f"E={energy:4.2f}:  T = {T:.9f}  == N = {N}  (perfect transmission)")
        else:
            rep.fail(f"E={energy:4.2f}:  T = {T:.9f} but N = {N} -- not quantised!")


def check_identities(rep, kwant, fsyst):
    import numpy as np
    rep.section("4. Exact identities")
    sm = kwant.smatrix(fsyst, 0.6)
    S = sm.data
    dev = np.max(np.abs(S.conj().T @ S - np.eye(S.shape[0])))
    if dev < 1e-9:
        rep.ok(f"S-matrix unitary:  max|S^dag S - 1| = {dev:.2e}")
    else:
        rep.fail(f"S-matrix NOT unitary:  max|S^dag S - 1| = {dev:.2e}")
    T, R, N = sm.transmission(1, 0), sm.transmission(0, 0), sm.num_propagating(0)
    if abs(T + R - N) < 1e-9:
        rep.ok(f"sum rule:  T + R = {T + R:.9f} == N = {N}")
    else:
        rep.fail(f"sum rule violated:  T + R = {T + R:.9f}, N = {N}")
    psi = kwant.wave_function(fsyst, 0.6)(0)
    if psi.shape[0] == N:
        rep.ok(f"wave_function returned {psi.shape[0]} states, matching N = {N}")
    else:
        rep.fail(f"wave_function returned {psi.shape[0]} states but N = {N}")
    try:
        dens = kwant.operator.Density(fsyst)(psi[0])
        if dens.shape[0] == len(fsyst.sites):
            rep.ok(f"kwant.operator.Density works ({dens.shape[0]} sites)")
        else:
            rep.fail("Density returned the wrong number of values")
        kwant.operator.Current(fsyst)(psi[0])
        rep.ok("kwant.operator.Current works")
    except Exception as exc:
        rep.fail(f"kwant.operator failed: {exc}")
    # kwant 1.5.0 + numpy >= 2.5 breaks magnetic_gauge for 2-D systems (np.cross on
    # 2-vectors was removed in numpy 2.5.0).  The notebooks do not depend on it, so
    # this is a warning, not a failure -- but it must be visible.
    try:
        gauge = kwant.physics.magnetic_gauge(fsyst)
        gauge(0.05, *([0.0] * len(fsyst.leads)))   # one field per lead, zero there
        rep.ok("kwant.physics.magnetic_gauge works on a 2-D system")
    except ValueError as exc:
        if "3-dimensional vectors" in str(exc):
            rep.warn(f"magnetic_gauge is broken on this numpy ({np.__version__}): kwant "
                     "1.5.0 uses np.cross on 2-vectors. Pin numpy<2.5 if you need it; "
                     "the notebooks do not.")
        else:
            rep.fail(f"magnetic_gauge raised: {exc}")
    except Exception as exc:
        rep.fail(f"magnetic_gauge raised: {exc}")


def check_closed_system(rep, kwant, lat, t=1.0):
    import numpy as np
    import scipy.sparse.linalg as sla
    rep.section("5. Closed system: sparse diagonalisation")
    try:
        dot = kwant.Builder()
        dot[lat.shape(lambda p: p[0] ** 2 + p[1] ** 2 < 10 ** 2, (0, 0))] = 4 * t
        dot[lat.neighbors()] = -t
        fdot = dot.finalized()
        ham = fdot.hamiltonian_submatrix(sparse=True)
        ev = sla.eigsh(ham.tocsc(), k=6, sigma=0, return_eigenvectors=False)
        rep.ok(f"diagonalised a {len(fdot.sites)}-site dot; lowest levels = "
               f"{np.round(np.sort(ev)[:3], 5)}")
    except Exception as exc:
        rep.fail(f"closed-system diagonalisation failed: {exc}")


def check_bands(rep, kwant, lead):
    rep.section("6. Band structure")
    try:
        e0 = kwant.physics.Bands(lead.finalized())(0.0)
        rep.ok(f"lead band structure at k=0: {len(e0)} bands, lowest = {min(e0):.5f}")
    except Exception as exc:
        rep.fail(f"band structure failed: {exc}")


def check_continuum(rep, kwant):
    import numpy as np
    rep.section("7. Symbolic discretisation (kwant.continuum)")
    try:
        import kwant.continuum
        kwant.continuum.discretize("k_x**2 + k_y**2 + V(x, y)")
        rep.ok("discretized 'k_x**2 + k_y**2 + V(x, y)' into a Builder template")
        val = kwant.continuum.lambdify("k_x**2 + k_y**2")(k_x=1.0, k_y=2.0)
        if abs(float(np.real(val)) - 5.0) < 1e-12:
            rep.ok("lambdify evaluates correctly (1^2 + 2^2 = 5)")
        else:
            rep.fail(f"lambdify gave {val}, expected 5")
    except Exception as exc:
        rep.fail(f"kwant.continuum failed: {exc}")


# --------------------------------------------------------------------------- main


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Verify a Kwant installation with real physics checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--outdir", default=".",
                   help="directory for the summary JSON and (unless --log-dir) the logs/ folder")
    p.add_argument("--log-dir", default=None,
                   help="where to write the audit log (default: <outdir>/logs)")
    p.add_argument("--json", action="store_true",
                   help="also print the summary as JSON on stdout")
    v = p.add_mutually_exclusive_group()
    v.add_argument("--verbose", action="store_true", help="show extra details")
    v.add_argument("--quiet", action="store_true", help="print only the one-line result")
    p.add_argument("--version", action="version", version=f"verify_kwant {__version__}")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    outdir = os.path.abspath(args.outdir)
    log_dir = os.path.abspath(args.log_dir) if args.log_dir else os.path.join(outdir, "logs")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"verify_kwant_{stamp}.log")
    verbosity = 0 if args.quiet else (2 if args.verbose else 1)
    rep = Report(log_path, verbosity)
    rep.log.write(f"# verify_kwant {__version__}\n# command: {' '.join(sys.argv)}\n"
                  f"# started: {_dt.datetime.now().isoformat(timespec='seconds')}\n"
                  f"# python {platform.python_version()} on {platform.platform()}\n")

    kwant = check_imports(rep)
    summary = {"tool": "verify_kwant", "version": __version__, "started": stamp,
               "python": platform.python_version(), "platform": platform.platform(),
               "kwant": None, "numpy": None, "scipy": None,
               "optional": {}, "ok": [], "warnings": [], "failures": [], "log": log_path}
    if kwant is None:
        summary["failures"] = rep.failures
        _finish(rep, summary, args, outdir, exit_code=2)
        return 2

    import numpy as np
    import scipy
    summary.update(kwant=kwant.__version__, numpy=np.__version__, scipy=scipy.__version__)
    summary["optional"] = check_optional(rep, kwant)
    lat, lead, fsyst = build_wire(kwant)
    check_transport(rep, kwant, fsyst)
    check_identities(rep, kwant, fsyst)
    check_closed_system(rep, kwant, lat)
    check_bands(rep, kwant, lead)
    if summary["optional"].get("continuum"):
        check_continuum(rep, kwant)

    summary.update(ok=rep.oks, warnings=rep.warnings, failures=rep.failures)
    code = 1 if rep.failures else 0
    _finish(rep, summary, args, outdir, exit_code=code)
    return code


def _finish(rep, summary, args, outdir, exit_code):
    rep._emit("")
    rep._emit("=" * 70)
    if summary["failures"]:
        rep._emit(f"  RESULT: {len(summary['failures'])} FAILURE(S)", level=0)
        for f_ in summary["failures"]:
            rep._emit(f"    - {f_}", level=0)
    else:
        rep._emit("  RESULT: Kwant is installed and physically correct.", level=0)
        if summary["warnings"]:
            rep._emit(f"          ({len(summary['warnings'])} warning(s); see log)", level=1)
    rep._emit("=" * 70)
    if not summary["failures"]:
        rep._emit("")
        rep._emit("  Next:  jupyter lab chapters/00_Contents.ipynb")
        rep._emit(f"  or open that notebook in VS Code and pick the kernel for THIS Python:\n"
                  f"         {sys.executable}")
    rep.log.write(f"# exit code: {exit_code}\n")
    rep.close()
    summary["exit_code"] = exit_code
    with open(os.path.join(outdir, "verify_kwant_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    if args.json:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    sys.exit(main())
