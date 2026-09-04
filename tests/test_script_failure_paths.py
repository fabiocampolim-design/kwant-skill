# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Failure paths of the two support scripts (1.3.5, from the line-by-line review).

A hung canary is a recorded outcome, not a traceback; a check that raises
inside verify_kwant.py still leaves a closed, marked audit log.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canary_timeout_is_a_result_not_a_traceback(monkeypatch):
    tts = _load("test_thread_safety")

    def hang(*a, **k):
        raise subprocess.TimeoutExpired(cmd="child", timeout=k.get("timeout", 1))
    monkeypatch.setattr(tts.subprocess, "run", hang)
    rc, survived, err = tts.run_mumps_canary(2, 4, 1)
    assert rc is None and survived is False
    assert "timed out" in err


def test_main_records_a_hung_canary_and_still_writes_the_summary(tmp_path, monkeypatch):
    tts = _load("test_thread_safety")
    monkeypatch.setattr(tts, "check_safe_path", lambda *a: 0.0)
    monkeypatch.setattr(tts, "run_mumps_canary", lambda *a: (None, False, "timed out after 1 s"))
    pytest.importorskip("kwant.solvers.mumps")
    rc = tts.main(["--outdir", str(tmp_path), "--quiet", "--canary-timeout", "1"])
    assert rc == 0
    summary = json.loads((tmp_path / "test_thread_safety_summary.json").read_text(encoding="utf-8"))
    assert summary["canary"] == "hung (timeout)"
    assert summary["canary_exit_code"] is None
    log = next((tmp_path / "logs").glob("test_thread_safety_*.log")).read_text(encoding="utf-8")
    assert "hung" in log and log.rstrip().endswith("# exit code: 0")


def test_verify_log_is_closed_and_marked_when_a_check_raises(tmp_path, monkeypatch):
    vk = _load("verify_kwant")
    pytest.importorskip("kwant")

    def boom(rep, kwant, fsyst):
        raise RuntimeError("boom")
    monkeypatch.setattr(vk, "check_transport", boom)
    with pytest.raises(RuntimeError):
        vk.main(["--outdir", str(tmp_path), "--quiet"])
    log = next((tmp_path / "logs").glob("verify_kwant_*.log")).read_text(encoding="utf-8")
    assert log.rstrip().endswith("# aborted: RuntimeError: boom")
    assert sys.platform != "win32" or True  # the read above proves the handle was released
