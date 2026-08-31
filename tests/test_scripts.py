# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""CLI contract of the two support scripts (playbook rules 11 and 12).

Every input and output is reachable from the command line, --help lists each
option with its default, and every run leaves an audit log under
<outdir>/logs/ plus a machine-readable summary.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "verify_kwant.py"
THREADS = ROOT / "test_thread_safety.py"


def run(script, *args, timeout=600):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, timeout=timeout,
                          cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})


@pytest.mark.parametrize("script", [VERIFY, THREADS], ids=["verify", "threads"])
def test_help_lists_every_option_with_default(script):
    r = run(script, "--help")
    assert r.returncode == 0, r.stderr
    for opt in ("--outdir", "--log-dir", "--json", "--verbose", "--quiet"):
        assert opt in r.stdout, f"{script.name}: {opt} missing from --help"
    assert "default" in r.stdout.lower()


def test_verify_writes_log_and_json_summary(tmp_path):
    r = run(VERIFY, "--outdir", str(tmp_path), "--quiet")
    assert r.returncode == 0, r.stdout + r.stderr
    logs = list((tmp_path / "logs").glob("verify_kwant_*.log"))
    assert len(logs) == 1, "exactly one audit log per invocation"
    text = logs[0].read_text(encoding="utf-8")
    assert "verify_kwant.py" in text and "kwant" in text      # command line + versions
    summary = json.loads((tmp_path / "verify_kwant_summary.json").read_text(encoding="utf-8"))
    assert summary["failures"] == []
    assert summary["kwant"] and summary["numpy"]
    assert isinstance(summary["warnings"], list)
    # --quiet: only the one-line result on stdout
    assert len(r.stdout.strip().splitlines()) <= 2


def test_verify_log_dir_overrides_outdir(tmp_path):
    out, logdir = tmp_path / "out", tmp_path / "elsewhere"
    r = run(VERIFY, "--outdir", str(out), "--log-dir", str(logdir), "--quiet")
    assert r.returncode == 0, r.stdout + r.stderr
    assert list(logdir.glob("verify_kwant_*.log"))
    assert not (out / "logs").exists()


def test_threads_safe_path_runs_and_logs(tmp_path):
    r = run(THREADS, "--outdir", str(tmp_path), "--no-canary", "--workers", "2",
            "--energies", "8", "--quiet")
    assert r.returncode == 0, r.stdout + r.stderr
    assert list((tmp_path / "logs").glob("test_thread_safety_*.log"))
    summary = json.loads((tmp_path / "test_thread_safety_summary.json").read_text(encoding="utf-8"))
    assert summary["safe_path_maxdiff"] < 1e-12
    assert summary["canary"] == "skipped"
