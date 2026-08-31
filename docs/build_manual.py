#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""
build_manual.py -- render docs/USER_MANUAL.md to USER_MANUAL.html and USER_MANUAL.pdf.

    python docs/build_manual.py [--src FILE] [--outdir DIR] [--log-dir DIR] [--strict]
                                [--verbose | --quiet] [--version]

The manual's source of truth is the Markdown; the built files are committed so
readers need no tooling. Uses pandoc for the HTML and pandoc + a TeX engine
for the PDF when available; otherwise falls back to a minimal stdlib
Markdown-to-HTML conversion and a plain-text PDF. Every run reads both
artefacts back (every Markdown heading must be in the HTML; the PDF must
parse as a PDF) and writes an audit log under <log-dir>. With --strict a
fallback renderer or a failed readback is an error (exit 1) -- that is what
the committed artefacts are held to (tests/test_manual_readback.py).

Exit codes: 0 ok, 1 readback failed or --strict violated, 2 usage error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import re
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TITLE = "Kwant - Theory and Practice - User Manual"


def _version() -> str:
    try:
        return (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


CSS = """body{font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:860px;
margin:2rem auto;padding:0 1rem;color:#1b1b1b;background:#fff}
h1{font-size:1.6rem;border-bottom:1px solid #999;padding-bottom:.2rem;margin-top:2rem}
h2{font-size:1.25rem;margin-top:1.6rem}table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{border:1px solid #bbb;padding:.3rem .5rem;text-align:left;vertical-align:top}th{background:#f3f3f3}
pre,code{font-family:ui-monospace,Consolas,monospace;font-size:.86rem}pre{background:#f6f6f6;padding:.6rem;overflow-x:auto}
@media(prefers-color-scheme:dark){body{color:#e6e6e6;background:#151515}th{background:#222}pre{background:#222}}"""


def _run(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=str(cwd), capture_output=True, timeout=600).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def md_to_html_min(text: str) -> str:
    """Just enough Markdown for the manual: headings, paragraphs, lists,
    fenced code, pipe tables, inline code/links/bold.  Used only without pandoc."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)   # front matter
    out, lines, i = [], text.splitlines(), 0

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre>" + html.escape("\n".join(lines[i + 1:j])) + "</pre>")
            i = j + 1
        elif ln.startswith("#"):
            lvl = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{lvl}>{inline(ln.lstrip('#').strip())}</h{lvl}>")
            i += 1
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[-| :]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            hdr, body = rows[0], rows[1:]
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                                 for r in body) + "</table>")
        elif re.match(r"^\s*(-|\d+\.)\s", ln):
            items = []
            while i < len(lines) and (re.match(r"^\s*(-|\d+\.)\s", lines[i]) or lines[i].startswith("  ")):
                if re.match(r"^\s*(-|\d+\.)\s", lines[i]):
                    items.append(re.sub(r"^\s*(-|\d+\.)\s", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            tag = "ol" if re.match(r"^\s*\d+\.", ln) else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(it)}</li>" for it in items) + f"</{tag}>")
        elif ln.strip():
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|```|\||\s*-\s|\s*\d+\.\s)", lines[i]):
                para.append(lines[i])
                i += 1
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        else:
            i += 1
    return "\n".join(out)


def pdf_builtin(text: str, path: Path) -> None:
    """A minimal, dependency-free PDF: monospaced plain text, one page per 60 lines."""
    lines = []
    for raw in text.splitlines():
        raw = raw.encode("latin-1", "replace").decode("latin-1")
        while len(raw) > 95:
            lines.append(raw[:95]); raw = raw[95:]
        lines.append(raw)
    pages = [lines[i:i + 60] for i in range(0, max(len(lines), 1), 60)]
    objs = []

    def add(s):
        objs.append(s); return len(objs)
    font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    page_ids = []
    for pg in pages:
        content = "BT /F1 9 Tf 40 800 Td 11 TL " + " ".join(
            "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '" for ln in pg) + " ET"
        data = zlib.compress(content.encode("latin-1"))
        cid = add(f"<< /Length {len(data)} /Filter /FlateDecode >>\nstream\n".encode("latin-1") + data + b"\nendstream")
        page_ids.append(add(f"<< /Type /Page /Parent PAGES /MediaBox [0 0 595 842] /Contents {cid} 0 R /Resources << /Font << /F1 {font} 0 R >> >> >>"))
    pages_id = add("<< /Type /Pages /Kids [" + " ".join(f"{p} 0 R" for p in page_ids) + f"] /Count {len(page_ids)} >>")
    catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, o in enumerate(objs, 1):
        if isinstance(o, str):
            o = o.replace("PAGES", f"{pages_id} 0 R").encode("latin-1")
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root {catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def _wrap(body: str) -> str:
    return (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{TITLE}</title><style>{CSS}</style></head><body>{body}</body></html>")


# ------------------------------------------------------------------ readback
def md_headings(text: str) -> list[str]:
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return [h.replace("`", "").strip() for h in re.findall(r"^#{1,2} (.+)$", text, re.M)]


def readback(src_text: str, out_html: Path, out_pdf: Path) -> list[str]:
    """Return the list of readback problems (empty = both artefacts check out)."""
    problems = []
    page = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", out_html.read_text(encoding="utf-8"))))
    missing = [h for h in md_headings(src_text) if re.sub(r"\s+", " ", h) not in page]
    if missing:
        problems.append(f"html: {len(missing)} heading(s) missing, first {missing[0]!r}")
    raw = out_pdf.read_bytes()
    if not raw.startswith(b"%PDF-"):
        problems.append("pdf: no %PDF header")
    if not raw.rstrip().endswith(b"%%EOF"):
        problems.append("pdf: no %%EOF trailer")
    if len(raw) < 1000:
        problems.append(f"pdf: only {len(raw)} bytes")
    return problems


# ------------------------------------------------------------------ CLI
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render docs/USER_MANUAL.md to HTML and PDF, then read both back.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--src", default=str(HERE / "USER_MANUAL.md"), help="Markdown source")
    p.add_argument("--outdir", default=str(HERE), help="where USER_MANUAL.html and USER_MANUAL.pdf go")
    p.add_argument("--log-dir", default=None, help="where the audit log goes (default: <outdir>/logs)")
    p.add_argument("--strict", action="store_true",
                   help="fail (exit 1) if a fallback renderer had to be used")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--verbose", action="store_true", help="show renderer decisions")
    g.add_argument("--quiet", action="store_true", help="print only the one-line result")
    p.add_argument("--version", action="version", version=f"build_manual {_version()}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    src = Path(args.src).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out_html, out_pdf = outdir / "USER_MANUAL.html", outdir / "USER_MANUAL.pdf"
    log_dir = Path(args.log_dir).resolve() if args.log_dir else outdir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"build_manual_{stamp}.log"
    lines = [f"# build_manual {_version()}", f"# command: {' '.join(sys.argv)}",
             f"# python: {sys.version.split()[0]}  pandoc: {shutil.which('pandoc') or 'none'}",
             f"# src: {src}", f"# outdir: {outdir}"]

    def say(msg, detail=False):
        lines.append(msg)
        if not args.quiet and (not detail or args.verbose):
            print(msg)

    text = src.read_text(encoding="utf-8")
    fallback = []
    if shutil.which("pandoc"):
        css = outdir / "_manual.css"
        css.write_text(CSS, encoding="utf-8")
        ok = _run(["pandoc", str(src), "-s", "--toc", "--toc-depth=2", "-c", css.name,
                   "--embed-resources", "--metadata", f"title={TITLE}", "-o", str(out_html)], outdir)
        css.unlink()
        say(f"html via {'pandoc' if ok else 'pandoc FAILED -> builtin'}", detail=True)
        if not ok:
            out_html.write_text(_wrap(md_to_html_min(text)), encoding="utf-8")
            fallback.append("html")
    else:
        out_html.write_text(_wrap(md_to_html_min(text)), encoding="utf-8")
        say("html via builtin converter (install pandoc for a nicer one)", detail=True)
        fallback.append("html")
    engine = next((e for e in ("xelatex", "lualatex", "pdflatex") if shutil.which(e)), None)
    ok = False
    if shutil.which("pandoc") and engine:
        ok = _run(["pandoc", str(src), "--toc", "--toc-depth=2", f"--pdf-engine={engine}",
                   "-V", "geometry:margin=2.2cm", "-V", "colorlinks=true", "-o", str(out_pdf)], outdir)
        say(f"pdf via pandoc+{engine}" if ok else f"pdf via pandoc+{engine} FAILED -> builtin", detail=True)
    if not ok:
        pdf_builtin(re.sub(r"<[^>]+>", "", md_to_html_min(text)), out_pdf)
        say("pdf via builtin writer (install pandoc + a TeX engine for a typeset manual)", detail=True)
        fallback.append("pdf")

    problems = readback(text, out_html, out_pdf)
    for pr in problems:
        say(f"READBACK: {pr}")
    say(f"# artefacts: {out_html.name} {out_html.stat().st_size} B, {out_pdf.name} {out_pdf.stat().st_size} B", detail=True)
    rc = 0
    if problems:
        rc = 1
    elif args.strict and fallback:
        say(f"--strict: fallback renderer used for {', '.join(fallback)}")
        rc = 1
    say(f"build_manual: {'ok' if rc == 0 else 'FAILED'} -- html+pdf in {outdir}"
        f"{' (fallback: ' + ', '.join(fallback) + ')' if fallback else ''}; log {log_path}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
