# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""scripts/watch_upstream.py: CLI contract (rules 11/12) and the offline logic of
the weekly delta and report (no network in the suite)."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "watch_upstream.py"
sys.path.insert(0, str(SCRIPT.parent))
import watch_upstream as w  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          cwd=ROOT, timeout=120)


def test_help_and_version():
    r = run("--help")
    assert r.returncode == 0
    for opt in ("--snapshot", "--weekly", "--fetch", "--state-dir", "--upstream-dir", "--outdir",
                "--log-dir", "--quiet", "--version"):
        assert opt in r.stdout, opt
    assert "default" in r.stdout.lower()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert run("--version").stdout.strip() == f"watch_upstream {version}"


def test_no_action_is_a_usage_error():
    assert run().returncode == 2


def test_delta_classifies_new_updated_closed():
    old = [{"iid": 1, "title": "a", "state": "opened", "updated_at": "t1"},
           {"iid": 2, "title": "b", "state": "opened", "updated_at": "t1"},
           {"iid": 3, "title": "c", "state": "opened", "updated_at": "t1"}]
    new = [{"iid": 1, "title": "a", "state": "opened", "updated_at": "t1"},      # untouched
           {"iid": 2, "title": "b", "state": "opened", "updated_at": "t2"},      # updated
           {"iid": 3, "title": "c", "state": "closed", "updated_at": "t2"},      # closed
           {"iid": 4, "title": "d", "state": "opened", "updated_at": "t2"}]      # new
    d = w.delta(old, new)
    assert [x["iid"] for x in d["new"]] == [4]
    assert [x["iid"] for x in d["updated"]] == [2]
    assert [x["iid"] for x in d["closed"]] == [3]
    tags = w.delta([{"name": "v1.5.0", "created_at": "2025"}],
                   [{"name": "v1.5.0", "created_at": "2025"}, {"name": "v1.6.0", "created_at": "2026"}])
    assert [x["name"] for x in tags["new"]] == ["v1.6.0"]


def test_slim_drops_bodies_and_identities():
    items = [{"iid": 7, "title": "t", "state": "opened", "updated_at": "u", "web_url": "w",
              "description": "long body", "author": {"name": "someone", "email": "x@y"}}]
    out = w._slim("issues", items)
    assert out == [{"iid": 7, "title": "t", "state": "opened", "updated_at": "u", "web_url": "w"}]
    tag = w._slim("tags", [{"name": "v1", "created_at": "c", "message": "signed by someone"}])
    assert "message" not in tag[0]


def test_render_weekly_reads_like_a_report():
    deltas = {"tags": {"new": [{"name": "v1.6.0", "created_at": "2026-09-01T00:00:00Z"}], "updated": [], "closed": []},
              "issues": {"new": [], "updated": [], "closed": [{"iid": 5, "title": "x", "state": "closed", "web_url": "u"}]},
              "merge_requests": {"new": [], "updated": [], "closed": []}}
    md = w.render_weekly(deltas, "2026-W36", {"tags": 9, "issues": 100, "merge_requests": 50}, ("abc", "def", "3"))
    assert md.startswith("# Upstream watch 2026-W36")
    assert "v1.6.0 (2026-09-01)" in md and "#5 x (closed)" in md
    assert "abc → def (3 new commit(s))" in md
    assert "kwant-discuss" in md and "K1" in md and "K2" in md and "K6" in md


def test_weekly_offline_writes_report_and_log(tmp_path, monkeypatch):
    """--weekly against a stubbed GitLab: a first run marks everything new, a
    second run with the same data reports zero deltas; both leave an audit log."""
    fake = {"tags": [{"name": "v1.5.0", "created_at": "2024"}],
            "issues": [{"iid": 1, "title": "one", "state": "opened", "updated_at": "t", "web_url": "u"}],
            "merge_requests": []}
    monkeypatch.setattr(w, "fetch_all", lambda url, **k: fake[[n for n, ep in w.ENDPOINTS.items() if ep in url][0]])
    state, out = tmp_path / "state", tmp_path / "watch"
    rc = w.main(["--weekly", "--state-dir", str(state), "--outdir", str(out), "-q",
                 "--upstream-dir", str(tmp_path / "nowhere")])
    assert rc == 0
    reports = list(out.glob("*-W*.md"))
    assert len(reports) == 1
    text = reports[0].read_text(encoding="utf-8")
    assert "first snapshot" in text and "[new] v1.5.0" in text and "[new] #1 one" in text
    assert list((state / "logs").glob("watch_upstream_*.log"))
    rc = w.main(["--weekly", "--state-dir", str(state), "--outdir", str(out), "-q"])
    assert rc == 0
    text = reports[0].read_text(encoding="utf-8")
    assert "0 new, 0 updated, 0 closed" in text and "first snapshot" not in text


def test_unreachable_upstream_exits_1_and_still_logs(tmp_path, monkeypatch):
    import urllib.error

    def boom(url, **k):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(w, "fetch_all", boom)
    state = tmp_path / "state"
    assert w.main(["--snapshot", "--state-dir", str(state), "-q"]) == 1
    log = next((state / "logs").glob("watch_upstream_*.log")).read_text(encoding="utf-8")
    assert "URLError" in log


def test_non_json_reply_from_upstream_exits_1_and_still_logs(tmp_path, monkeypatch):
    """1.3.5: a GitLab maintenance page (HTML, status 200) is upstream being
    unreachable, not a traceback."""
    class _Reply:
        headers = {}

        def read(self):
            return b"<html>maintenance</html>"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(w.urllib.request, "urlopen", lambda req, timeout=60: _Reply())
    state = tmp_path / "state"
    assert w.main(["--snapshot", "--state-dir", str(state), "-q"]) == 1
    log = next((state / "logs").glob("watch_upstream_*.log")).read_text(encoding="utf-8")
    assert "JSONDecodeError" in log


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Task Scheduler wrapper")
def test_register_task_dry_run_and_version():
    ps1 = ROOT / "scripts" / "register_watch_task.ps1"
    base = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)]
    r = subprocess.run(base + ["-DryRun"], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and r.stdout.startswith("DRY-RUN: Register-ScheduledTask"), r.stdout + r.stderr
    assert "--weekly --fetch" in r.stdout
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    r = subprocess.run(base + ["-Version"], capture_output=True, text=True, timeout=120)
    assert r.stdout.strip().endswith(version)
