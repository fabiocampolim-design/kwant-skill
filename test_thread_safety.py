#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""
test_thread_safety.py -- regression test for the MUMPS thread crash of 2026-08-20.

The bug: calling `kwant.smatrix` from several threads at once segfaults the whole
process whenever the MUMPS solver is installed, because MUMPS is not re-entrant.
In a notebook this surfaces as "The Kernel crashed..." with no traceback, and it
took down the "Parallel parameter sweep" cell.  Giving each thread its own
`mumps.Solver()` does NOT help -- the shared state is inside the MUMPS library
itself.  The notebook was fixed to use `kwant.solvers.sparse` (SuperLU,
re-entrant) in its thread pool.

What this script checks:

  1. SAFE PATH   (in-process):  threads + SciPy/SuperLU produce results identical
     to a serial sweep.  This is the approach the notebook uses; if this fails,
     the notebook's parallel cell is broken.

  2. MUMPS CANARY (subprocess): threads + kwant.smatrix/MUMPS.  Run in a child
     process because the expected outcome is a segfault, which no try/except can
     catch.  While the canary still crashes, the notebook must keep avoiding
     threaded MUMPS.  If some future Kwant/python-mumps release makes it survive,
     this script says so -- the notebook could then go back to MUMPS threads.

Usage:
    python test_thread_safety.py                       # both checks, log under ./logs/
    python test_thread_safety.py --no-canary           # safe path only (fast, no crash)
    python test_thread_safety.py --outdir out --json

Exit code 0 means the safe path works (whatever the canary shows); 1 otherwise.
"""
import argparse
import datetime as _dt
import json
import os
import platform
import subprocess
import sys
import textwrap

__version__ = "1.1.0"      # fallback; the product version is the VERSION file
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"), encoding="utf-8") as _f:
        __version__ = _f.read().strip() or __version__
except OSError:
    pass

# The same clean quantum wire the notebook sweeps (section 3).
BUILD_WIRE = """
import kwant

def build_wire(t=1.0, W=10, L=30):
    lat = kwant.lattice.square(1.0, norbs=1)
    syst = kwant.Builder()
    syst[(lat(x, y) for x in range(L) for y in range(W))] = 4 * t
    syst[lat.neighbors()] = -t
    lead = kwant.Builder(kwant.TranslationalSymmetry((-1.0, 0)))
    lead[(lat(0, j) for j in range(W))] = 4 * t
    lead[lat.neighbors()] = -t
    syst.attach_lead(lead)
    syst.attach_lead(lead.reversed())
    return syst.finalized()
"""


def check_safe_path(workers, n_energies, tol):
    """Threads + SciPy/SuperLU must match a serial sweep exactly.  Returns max diff."""
    from concurrent.futures import ThreadPoolExecutor

    import numpy as np
    import kwant.solvers.sparse as scipy_solver

    ns = {}
    exec(BUILD_WIRE, ns)
    fsyst = ns["build_wire"]()
    energies = np.linspace(0.01, 1.0, n_energies)

    def transmission(e):
        return scipy_solver.smatrix(fsyst, e).transmission(1, 0)

    serial = np.array([transmission(e) for e in energies])
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parallel = np.array(list(pool.map(transmission, energies)))
    dev = float(np.abs(parallel - serial).max())
    if dev >= tol:
        raise AssertionError(f"threaded SciPy sweep diverged from serial: maxdiff={dev:.2e}")
    return dev


def run_mumps_canary(workers, n_energies, timeout):
    """Run the crashing pattern in a child process; return (exit code, survived, stderr)."""
    child = textwrap.dedent(BUILD_WIRE) + textwrap.dedent(f"""
        from concurrent.futures import ThreadPoolExecutor
        import numpy as np
        import kwant.solvers.mumps  # noqa: F401  -- die with ImportError if absent

        fsyst = build_wire()
        energies = np.linspace(0.01, 1.0, {n_energies})

        def transmission(e):
            # kwant.smatrix dispatches to MUMPS since MUMPS is importable
            return kwant.smatrix(fsyst, e).transmission(1, 0)

        with ThreadPoolExecutor(max_workers={workers}) as pool:
            data = list(pool.map(transmission, energies))
        print("CANARY-SURVIVED")
        """)
    try:
        proc = subprocess.run([sys.executable, "-c", child],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        # A deadlock is as plausible an outcome of a re-entrancy bug as a
        # segfault; it is a result to record, not a traceback (1.3.5).
        return None, False, f"timed out after {timeout} s (child killed)"
    survived = "CANARY-SURVIVED" in proc.stdout
    return proc.returncode, survived, proc.stderr.strip()


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Regression test: threaded Kwant sweeps and the MUMPS re-entrancy crash.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--workers", type=int, default=4, help="threads in the pool")
    p.add_argument("--energies", type=int, default=64, help="energy points in the sweep")
    p.add_argument("--tol", type=float, default=1e-12,
                   help="max allowed |threaded - serial| for the safe path")
    p.add_argument("--no-canary", action="store_true",
                   help="skip the MUMPS crash canary (safe path only)")
    p.add_argument("--canary-timeout", type=float, default=300,
                   help="seconds before the canary child is killed")
    p.add_argument("--outdir", default=".",
                   help="directory for the summary JSON and (unless --log-dir) the logs/ folder")
    p.add_argument("--log-dir", default=None,
                   help="where to write the audit log (default: <outdir>/logs)")
    p.add_argument("--json", action="store_true", help="also print the summary as JSON")
    v = p.add_mutually_exclusive_group()
    v.add_argument("--verbose", action="store_true", help="show the canary's stderr")
    v.add_argument("--quiet", action="store_true", help="print only the one-line result")
    p.add_argument("--version", action="version", version=f"test_thread_safety {__version__}")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    outdir = os.path.abspath(args.outdir)
    log_dir = os.path.abspath(args.log_dir) if args.log_dir else os.path.join(outdir, "logs")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"test_thread_safety_{stamp}.log")
    log = open(log_path, "w", encoding="utf-8")

    def say(line, level=1):
        log.write(line + "\n")
        if (0 if args.quiet else (2 if args.verbose else 1)) >= level:
            print(line)

    import kwant
    log.write(f"# test_thread_safety {__version__}\n# command: {' '.join(sys.argv)}\n"
              f"# started: {_dt.datetime.now().isoformat(timespec='seconds')}\n"
              f"# python {platform.python_version()} on {platform.platform()}; "
              f"kwant {kwant.__version__}\n")
    summary = {"tool": "test_thread_safety", "version": __version__, "started": stamp,
               "kwant": kwant.__version__, "workers": args.workers, "energies": args.energies,
               "safe_path_maxdiff": None, "canary": "not run", "log": log_path}
    code = 0

    say(f"1. safe path: {args.workers} threads + kwant.solvers.sparse (SuperLU)")
    try:
        dev = check_safe_path(args.workers, args.energies, args.tol)
        summary["safe_path_maxdiff"] = dev
        say(f"   [ ok ] parallel == serial  (maxdiff = {dev:.2e})")
    except Exception as exc:
        summary["safe_path_error"] = str(exc)
        say(f"   [FAIL] {exc}", level=0)
        code = 1

    if args.no_canary:
        summary["canary"] = "skipped"
        say("2. canary: skipped (--no-canary)")
    else:
        say(f"2. canary: {args.workers} threads + kwant.smatrix (MUMPS), in a subprocess")
        try:
            import kwant.solvers.mumps  # noqa: F401
        except ImportError:
            summary["canary"] = "skipped: MUMPS not installed"
            say("   [skip] MUMPS not installed; the crash cannot occur here")
        else:
            rc, survived, err = run_mumps_canary(args.workers, args.energies,
                                                args.canary_timeout)
            summary["canary_exit_code"] = rc
            if rc is None:
                summary["canary"] = "hung (timeout)"
                say(f"   [ ok ] child hung and was killed ({err})")
                say("          -> a deadlock, not a crash; keep using kwant.solvers.sparse")
                say("             in threaded sweeps.")
            elif survived and rc == 0:
                summary["canary"] = "survived"
                say("   [note] threaded MUMPS SURVIVED -- Kwant or python-mumps may have become")
                say("          thread-safe; the notebook could switch its parallel cell back to")
                say("          kwant.smatrix.  Re-run a few times: this is a race, so one clean")
                say("          run proves little.")
            else:
                summary["canary"] = "crashed"
                say(f"   [ ok ] child crashed as expected (exit code {rc})")
                say("          -> keep using kwant.solvers.sparse in threaded sweeps.")
                if err:
                    say(f"          stderr: {err[:400]}", level=2)

    say(("RESULT: safe path OK" if code == 0 else "RESULT: SAFE PATH FAILED")
        + f"; canary: {summary['canary']}", level=0)
    log.write(f"# exit code: {code}\n")
    log.close()
    summary["exit_code"] = code
    with open(os.path.join(outdir, "test_thread_safety_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    if args.json:
        print(json.dumps(summary, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
