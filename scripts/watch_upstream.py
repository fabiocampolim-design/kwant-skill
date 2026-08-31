# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Weekly upstream watch for Kwant (publishing playbook rule 23 / S8).

--snapshot   dump tags / issues / merge requests of gitlab.kwant-project.org
             (GitLab REST v4, anonymous) to --state-dir
--weekly     compare with the previous snapshot, write <outdir>/YYYY-WW.md, then snapshot
--fetch      git fetch the local clone under --upstream-dir and log how far origin/main moved

Usage:
    python scripts/watch_upstream.py --weekly --fetch
    python scripts/watch_upstream.py --snapshot --state-dir upstream/watch-state

Requests are anonymous, one page per second, with a descriptive User-Agent.
Only tag names and dates, issue/MR numbers, titles, states and URLs are
recorded -- never message bodies or author identities. The kwant-discuss
list (mail.python.org) has no stable anonymous API; the report links its
archive for a manual look.

Exit 0 ok, 1 upstream unreachable, 2 usage error.
"""
import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
API = "https://gitlab.kwant-project.org/api/v4/projects/kwant%2Fkwant"
ENDPOINTS = {"tags": "/repository/tags",
             "issues": "/issues?state=all&order_by=updated_at",
             "merge_requests": "/merge_requests?state=all&order_by=updated_at"}
LIST_ARCHIVE = "https://mail.python.org/archives/list/kwant-discuss@python.org/"
KEEP = {"tags": ("name", "created_at"),
        "issues": ("iid", "title", "state", "updated_at", "web_url"),
        "merge_requests": ("iid", "title", "state", "updated_at", "web_url")}


def _version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def fetch_all(url, max_pages=200, pause=1.0):
    """Follow X-Next-Page through a paginated GitLab endpoint; return the list of items."""
    items, page = [], 1
    while page <= max_pages:
        sep = "&" if "?" in url else "?"
        req = urllib.request.Request(f"{url}{sep}per_page=100&page={page}",
                                     headers={"User-Agent": "kwant-theory-and-practice watch (study project)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            batch = json.loads(r.read().decode("utf-8"))
            nxt = r.headers.get("X-Next-Page", "")
        items.extend(batch)
        if not batch or not nxt:
            break
        page = int(nxt)
        time.sleep(pause)
    return items


def _slim(name, items):
    """Keep only the fields the report needs (no bodies, no identities)."""
    keys = KEEP[name]
    return [{k: x.get(k) for k in keys} for x in items]


def _key(x):
    return x.get("iid", x.get("name"))


def delta(old, new):
    """Split `new` into new / updated / closed relative to `old` (by iid or tag name)."""
    o = {_key(x): x for x in old}
    out = {"new": [], "updated": [], "closed": []}
    for x in new:
        k = _key(x)
        if k not in o:
            out["new"].append(x)
        elif x.get("state") == "closed" and o[k].get("state") != "closed":
            out["closed"].append(x)
        elif x.get("updated_at", x.get("created_at")) != o[k].get("updated_at", o[k].get("created_at")):
            out["updated"].append(x)
    return out


def render_weekly(deltas, week, counts, clone=None, first=False):
    lines = [f"# Upstream watch {week}", "",
             f"Kwant at gitlab.kwant-project.org, checked {_dt.date.today().isoformat()}"
             + (" — first snapshot, every item counts as new" if first else "") + ".", ""]
    for name, d in deltas.items():
        lines.append(f"## {name}: {counts[name]} total; {len(d['new'])} new, "
                     f"{len(d['updated'])} updated, {len(d['closed'])} closed")
        for bucket in ("new", "updated", "closed"):
            shown = d[bucket] if not first else d[bucket][:15]
            for x in shown:
                if name == "tags":
                    lines.append(f"- [{bucket}] {x['name']} ({(x.get('created_at') or '')[:10]})")
                else:
                    prefix = "!" if name == "merge_requests" else "#"
                    lines.append(f"- [{bucket}] {prefix}{x['iid']} {x.get('title', '')} ({x.get('state')}) — {x.get('web_url', '')}")
            if first and len(d[bucket]) > 15:
                lines.append(f"- … {len(d[bucket]) - 15} more (see the snapshot)")
        lines.append("")
    if clone is not None:
        lines.append("## local clone")
        lines.append(f"- upstream/kwant origin/main: {clone[0]} → {clone[1]}"
                     + (" (unchanged)" if clone[0] == clone[1] else f" ({clone[2]} new commit(s))"))
        lines.append("")
    lines.append("## kwant-discuss")
    lines.append(f"- no anonymous API; look at {LIST_ARCHIVE} (latest threads) by hand.")
    lines.append("")
    lines.append("## Our open items against upstream")
    lines.append("- K1 magnetic_gauge on numpy >= 2.5 (docs/02) — check whether a release or pin appeared above.")
    lines.append("- K2 MUMPS thread safety, patch 0001 — check for MRs touching solvers/mumps.")
    lines.append("- K6 plotter resets warning filters, patch 0004 — check for MRs touching plotter.py.")
    lines.append("")
    return "\n".join(lines)


def snapshot(state_dir):
    os.makedirs(state_dir, exist_ok=True)
    data = {}
    for name, ep in ENDPOINTS.items():
        data[name] = _slim(name, fetch_all(API + ep))
        with open(os.path.join(state_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data[name], f, indent=0)
    return data


def load_previous(state_dir):
    prev = {}
    for name in ENDPOINTS:
        p = os.path.join(state_dir, f"{name}.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                prev[name] = json.load(f)
        else:
            prev[name] = None
    return prev


def fetch_clone(upstream_dir):
    """git fetch in the clone; return (before, after, n_new) for origin/main or None."""
    p = os.path.join(upstream_dir, "kwant")
    if not os.path.isdir(os.path.join(p, ".git")):
        return None

    def rev():
        return subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=p,
                              capture_output=True, text=True).stdout.strip()
    before = rev()
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=p, capture_output=True, text=True, timeout=600)
    after = rev()
    n = subprocess.run(["git", "rev-list", "--count", f"{before}..{after}"], cwd=p,
                       capture_output=True, text=True).stdout.strip() if before and after else "?"
    return (before, after, n)


def build_parser():
    ap = argparse.ArgumentParser(prog="watch_upstream", description=__doc__.splitlines()[0],
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--snapshot", action="store_true", help="dump the current GitLab state")
    ap.add_argument("--weekly", action="store_true", help="delta vs previous snapshot, then snapshot")
    ap.add_argument("--fetch", action="store_true", help="git fetch the clone under --upstream-dir")
    ap.add_argument("--state-dir", default=os.path.join(ROOT, "upstream", "watch-state"),
                    help="where snapshots and the audit log live (gitignored)")
    ap.add_argument("--upstream-dir", default=os.path.join(ROOT, "upstream"),
                    help="directory holding the kwant clone")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "docs", "watch"),
                    help="where weekly reports go")
    ap.add_argument("--log-dir", default=None, help="audit-log directory (default <state-dir>/logs)")
    ap.add_argument("-q", "--quiet", action="store_true", help="no console output")
    ap.add_argument("--version", action="version", version=f"watch_upstream {_version()}")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not (args.weekly or args.snapshot or args.fetch):
        build_parser().print_help()
        return 2
    week = _dt.date.today().strftime("%G-W%V")
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    extra = {"week": week}
    rc = 0
    try:
        clone = fetch_clone(args.upstream_dir) if args.fetch else None
        if clone is not None:
            extra["clone"] = clone
        if args.weekly:
            prev = load_previous(args.state_dir)
            first = any(v is None for v in prev.values())
            new = snapshot(args.state_dir)
            deltas = {n: delta(prev[n] or [], new[n]) for n in ENDPOINTS}
            counts = {n: len(new[n]) for n in ENDPOINTS}
            os.makedirs(args.outdir, exist_ok=True)
            report = os.path.join(args.outdir, f"{week}.md")
            with open(report, "w", encoding="utf-8", newline="\n") as f:
                f.write(render_weekly(deltas, week, counts, clone, first))
            extra["written"] = report
            extra["counts"] = counts
            extra["delta"] = {n: {b: len(deltas[n][b]) for b in deltas[n]} for n in ENDPOINTS}
        elif args.snapshot:
            data = snapshot(args.state_dir)
            extra["snapshot"] = args.state_dir
            extra["counts"] = {n: len(data[n]) for n in ENDPOINTS}
    except (urllib.error.URLError, OSError, subprocess.SubprocessError) as e:
        extra["error"] = f"{type(e).__name__}: {e}"
        rc = 1
    log_dir = args.log_dir or os.path.join(args.state_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"watch_upstream_{stamp}.log"), "w", encoding="utf-8") as f:
        f.write(f"# watch_upstream {_version()}\n# command: {' '.join(sys.argv)}\n"
                f"# python: {sys.version.split()[0]}\n{json.dumps(extra, default=str, indent=1)}\n")
    if not args.quiet:
        print("watch_upstream:", json.dumps(extra, default=str))
    return rc


if __name__ == "__main__":
    sys.exit(main())
