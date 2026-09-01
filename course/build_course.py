#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""
build_course.py -- build the undergraduate course from one content source.

    python course/build_course.py [--outdir DIR] [--chapters DIR] [--log-dir DIR]
                                  [--skip-handout] [--verbose | --quiet] [--version]

Inputs
  course/deck/content_en.py        every slide: layout, text, figure, notes (the source of truth),
                                   plus PLACEMENT: where each remaining notebook figure gets its page
  chapters/01_*.ipynb .. 12_*.ipynb  the executed chapter notebooks -- every course figure is one of their outputs
  course/handout/handout.md        the printable companion handout (Markdown)

Outputs (under --outdir, default course/)
  figures/fig-NN.png + figures.json   the notebook's figures, numbered as in the notebook
  deck/index.html                     the reveal.js deck -- one linear sequence of slides
                                      (arrow keys / on-screen arrows only), no build animations,
                                      every notebook figure shown with its full caption
  deck/content.en.js                  the prose, loaded by shared/loader.js (data-t keys)
  deck/slides.html                    the same slides as one static page (no-JavaScript fallback)
  deck/slides.pdf                     the deck as a landscape PDF, one slide per page
                                      (via pandoc + xelatex; the fallback for any projector)
  lecturer_notes.md                   every slide's text + speaker notes, in order
  handout/handout.html, handout.pdf   via pandoc (+ xelatex); fallback = HTML only
  logs/build_course_<stamp>.log       audit log

--skip-handout skips the pandoc/xelatex artefacts (handout and slides.pdf);
slides.html is always written.  Every artefact is read back before the script
reports success: each data-t reference in index.html must resolve, each slide
must have notes, every notebook figure must appear exactly once with a caption,
no fragment classes remain, and the PDF must contain the probe glyphs.
Exit 0 ok, 1 readback failed, 2 usage.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _version() -> str:
    try:
        return (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


# ---------------------------------------------------------------- captions
_TEX = {r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\Delta": "Δ",
        r"\epsilon": "ε", r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\pi": "π",
        r"\Phi": "Φ", r"\phi": "φ", r"\sigma": "σ", r"\tau": "τ", r"\omega": "ω",
        r"\hbar": "ħ", r"\times": "×", r"\pm": "±", r"\mp": "∓", r"\le": "≤",
        r"\ge": "≥", r"\ll": "≪", r"\gg": "≫", r"\sqrt": "√", r"\propto": "∝",
        r"\infty": "∞", r"\cdot": "·", r"\ldots": "…", r"\dots": "…",
        r"\sin": "sin", r"\cos": "cos", r"\exp": "exp", r"\,": " "}


def tex_inline(text: str) -> str:
    """HTML for a caption that may contain $...$ LaTeX fragments (the closed set
    the notebook's captions use: greek letters, sub/superscripts, \\sqrt, \\pm...)."""
    def seg(m):
        s = m.group(1)
        for k, v in _TEX.items():
            s = s.replace(k, v)
        s = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", s)
        s = re.sub(r"\^(\S)", r"<sup>\1</sup>", s)
        s = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", s)
        s = re.sub(r"_(\S)", r"<sub>\1</sub>", s)
        s = s.replace("√{", "√(").replace("{", "(").replace("}", ")")
        return f'<span class="math">{s}</span>'
    parts, last = [], 0
    for m in re.finditer(r"\$([^$]+)\$", text):
        parts.append(html.escape(text[last:m.start()]))
        parts.append(seg(m))
        last = m.end()
    parts.append(html.escape(text[last:]))
    return "".join(parts)


def caption_plain(text: str) -> str:
    """The caption as plain text (for alt attributes and the lecturer notes)."""
    return re.sub(r"<[^>]+>", "", tex_inline(text)).replace("&amp;", "&")


# ---------------------------------------------------------------- figures
def chapter_notebooks(chapters: Path) -> list[Path]:
    """The twelve chapter notebooks, in course order (01_ ... 12_; the contents
    and solutions notebooks are not part of the figure sequence)."""
    return sorted(p for p in chapters.glob("[0-9][0-9]_*.ipynb") if not p.name.startswith("00_"))


def extract_figures(chapters: Path, outdir: Path) -> list[dict]:
    """Write every image/png output of the chapter notebooks to outdir/fig-NN.png,
    numbered in course order (the same numbers the notebooks' captions carry --
    the figure counter continues across chapters), and return the manifest:
    number, notebook file, cell index in that notebook, section heading, caption."""
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("fig-*.png"):
        old.unlink()
    manifest, n = [], 0
    for notebook in chapter_notebooks(chapters):
        nb = json.loads(notebook.read_text(encoding="utf-8"))
        section = ""
        for i, cell in enumerate(nb["cells"]):
            src = "".join(cell["source"])
            if cell["cell_type"] == "markdown":
                m = re.search(r"^## (\d+\. .+)$", src, re.M)
                if m:
                    section = m.group(1).strip()
                continue
            captions = re.findall(r"show_fig\(\s*r?['\"](.*?)['\"]\s*\)", src, re.S)
            pngs = [o["data"]["image/png"] for o in cell.get("outputs", []) if "image/png" in o.get("data", {})]
            for j, png in enumerate(pngs):
                n += 1
                data = png if isinstance(png, str) else "".join(png)
                (outdir / f"fig-{n:02d}.png").write_bytes(base64.b64decode(data))
                cap = captions[j] if j < len(captions) else ""
                manifest.append({"n": n, "notebook": notebook.name, "cell": i, "section": section,
                                 "caption": cap.strip()})
    (outdir / "figures.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    return manifest


# ---------------------------------------------------------------- deck
def load_content(path: Path):
    spec = importlib.util.spec_from_file_location("content_en", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DECK, mod.PLACEMENT


def _nb_section(figures: dict[int, dict], n: int) -> str:
    """The notebook section a figure belongs to, without its number prefix."""
    sec = figures.get(n, {}).get("section", "")
    return re.sub(r"^\d+\.\s*", "", sec).replace("`", "")


def expand_deck(deck: dict, placement: dict[int, str], figures: dict[int, dict]) -> tuple[dict, list[str]]:
    """Insert one generated figure page per PLACEMENT entry after the named slide,
    so that every notebook figure appears exactly once in the deck.  Returns the
    expanded deck (a new structure) and a list of consistency problems."""
    problems = []
    authored = set()
    all_ids = set()
    for sec in deck["sections"]:
        for s in sec["slides"]:
            all_ids.add(s["id"])
            authored |= set(s.get("figures", [s["figure"]] if s.get("figure") else []))
    placed = set(placement)
    if authored & placed:
        problems.append(f"figures both on a slide and in PLACEMENT: {sorted(authored & placed)}")
    missing = set(figures) - authored - placed
    if missing:
        problems.append(f"figures on no slide and not in PLACEMENT: {sorted(missing)}")
    for n, sid in placement.items():
        if sid not in all_ids:
            problems.append(f"PLACEMENT[{n}] names unknown slide {sid!r}")
        if n not in figures:
            problems.append(f"PLACEMENT names figure {n} which the notebook did not produce")
    out = {"title": deck["title"], "sections": []}
    for sec in deck["sections"]:
        slides = []
        for s in sec["slides"]:
            slides.append(s)
            for n in sorted(k for k, v in placement.items() if v == s["id"]):
                cap = figures.get(n, {}).get("caption", "")
                slides.append({"id": f"figpage-{n:02d}", "layout": "figpage", "figure": n,
                               "title": f"Figure {n} · {_nb_section(figures, n)}",
                               "notes": f"Figure {n} of the course ({_nb_where(figures, n)}). "
                                        f"{caption_plain(cap)}"})
        out["sections"].append({**sec, "slides": slides})
    return out, problems


def _nb_where(figures: dict[int, dict], n: int) -> str:
    """'<chapter notebook>, cell <i>' for a figure of the manifest."""
    m = figures.get(n, {})
    return f"{m.get('notebook', '?')}, cell {m.get('cell', '?')}"


def fig_meta(figures: dict[int, dict], n: int) -> str:
    m = figures.get(n, {})
    sec = m.get("section", "").replace("`", "")
    return f'§ {html.escape(sec)} · {html.escape(_nb_where(figures, n))}'


def fig_block(ns: list[int], figures: dict[int, dict], wide: bool = False) -> str:
    imgs = []
    for n in ns:
        cap = figures.get(n, {}).get("caption", "")
        alt = caption_plain(cap)[:120]
        imgs.append(f'<figure><img src="../figures/fig-{n:02d}.png" alt="{html.escape(alt)}">'
                    f'<figcaption><b>Fig. {n}.</b> {tex_inline(cap)}'
                    f' <span class="fig-meta">({fig_meta(figures, n)})</span></figcaption></figure>')
    return f'<div class="figs{" figs-wide" if wide else ""}">' + "".join(imgs) + "</div>"


def render_slide(sec: dict, slide: dict, figures: dict[int, dict]) -> tuple[str, dict]:
    """Return (html, content-entry) for one slide. Text lives in the content entry
    under keys the markup references with data-t="<slide id>.<key>"."""
    sid = slide["id"]
    lay = slide["layout"]
    entry: dict = {}
    parts: list[str] = [f'<section id="{sid}" data-sec="{sec["id"]}">']

    def t(key, value):
        entry[key] = value
        return f'data-t="{sid}.{key}"'

    label = f'<div class="sec-label">{html.escape(sec["name"])}</div>'
    if lay == "hero":
        parts.append('<div class="hero-wrap">')
        if slide.get("kicker"):
            parts.append(f'<p class="kicker" {t("kicker", slide["kicker"])}></p>')
        parts.append(f'<h1 {t("title", slide["title"])}></h1>')
        if slide.get("sub"):
            parts.append(f'<p class="hero-sub" {t("sub", slide["sub"])}></p>')
        parts.append("</div>")
    elif lay == "part":
        parts.append('<div class="hero-wrap part-wrap">')
        parts.append(f'<p class="kicker" {t("kicker", slide["kicker"])}></p>')
        parts.append(f'<h1 {t("title", slide["title"])}></h1>')
        parts.append(f'<p class="hero-sub" {t("sub", slide["sub"])}></p>')
        parts.append('<ul class="agenda">')
        for k, (kind, title) in enumerate(slide["agenda"], 1):
            entry[f"ag{k}"] = title
            parts.append(f'<li class="ag-{kind}" data-t="{sid}.ag{k}"></li>')
        parts.append("</ul></div>")
    elif lay == "figpage":
        parts.append(label)
        parts.append(f'<h2 {t("title", slide["title"])}></h2>')
        parts.append(fig_block([slide["figure"]], figures, wide=True))
    else:
        parts.append(label)
        parts.append(f'<h2 {t("title", slide["title"])}></h2>')
        if slide.get("lead"):
            parts.append(f'<p class="lead" {t("lead", slide["lead"])}></p>')
        bullets = slide.get("bullets", [])
        bkeys = []
        for k, b in enumerate(bullets, 1):
            entry[f"b{k}"] = b
            bkeys.append(f"b{k}")
        bullet_html = "".join(f'<li data-t="{sid}.{k}"></li>' for k in bkeys)
        figs = slide.get("figures", [slide["figure"]] if slide.get("figure") else [])
        fig_html = fig_block(figs, figures) if figs else ""
        if lay in ("figure", "figure-wide"):
            cls = "grid-2" if lay == "figure" else "stack"
            parts.append(f'<div class="{cls}">')
            if lay == "figure-wide":
                parts.append(fig_html)
            parts.append("<ul>" + bullet_html + "</ul>")
            if lay == "figure":
                parts.append(fig_html)
            parts.append("</div>")
        elif lay == "code":
            entry["code"] = html.escape(slide["code"])
            parts.append('<div class="grid-2">')
            parts.append("<ul>" + bullet_html + "</ul>")
            parts.append(f'<pre><code {t("code", entry["code"])}></code></pre>')
            parts.append("</div>")
        elif lay == "math":
            parts.append('<div class="math-block">')
            for k, (lab, eq) in enumerate(slide["equations"], 1):
                entry[f"eqlabel{k}"] = lab
                entry[f"eq{k}"] = eq
                parts.append(f'<div class="eq-row"><span class="eq-label" data-t="{sid}.eqlabel{k}"></span>'
                             f'<span class="math eq" data-t="{sid}.eq{k}"></span></div>')
            parts.append("</div>")
            if bkeys:
                parts.append("<ul class=\"after-math\">" + bullet_html + "</ul>")
        elif lay == "table":
            entry["thead"] = "".join(f"<th>{html.escape(h)}</th>" for h in slide["header"])
            parts.append(f'<table class="course-table"><thead><tr {t("thead", entry["thead"])}></tr></thead><tbody>')
            for k, row in enumerate(slide["rows"], 1):
                entry[f"row{k}"] = "".join(f"<td>{c}</td>" for c in row)
                parts.append(f'<tr data-t="{sid}.row{k}"></tr>')
            parts.append("</tbody></table>")
            if bkeys:
                parts.append("<ul class=\"after-math\">" + bullet_html + "</ul>")
        else:  # text
            parts.append("<ul>" + bullet_html + "</ul>")
    entry["notes"] = slide["notes"]
    parts.append(f'<aside class="notes" data-notes="{sid}"></aside>')
    parts.append("</section>")
    return "\n".join(parts), entry


HTML_HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../shared/reveal/dist/reset.css">
  <link rel="stylesheet" href="../shared/reveal/dist/reveal.css">
  <link rel="stylesheet" href="../shared/theme.css">
</head>
<body>
  <div class="reveal">
    <div class="slides">
"""

HTML_TAIL = """    </div>
  </div>
  <script src="content.en.js"></script>
  <script src="../shared/loader.js"></script>
  <script src="../shared/reveal/dist/reveal.js"></script>
  <script src="../shared/reveal/plugin/notes/notes.js"></script>
  <script>
    Reveal.initialize({
      width: 1920, height: 1080,
      hash: true, center: false,
      progress: true, controls: true, controlsLayout: "bottom-right",
      slideNumber: "c/t",
      transition: "fade", transitionSpeed: "fast",
      fragments: false,
      plugins: [ RevealNotes ]
    });
  </script>
</body>
</html>
"""


_AGENDA_KIND = {"figure": "fig", "figure-wide": "fig", "figpage": "fig",
                "code": "code", "math": "math", "table": "text", "text": "text", "hero": "text"}


def part_slide(i: int, total: int, sec: dict) -> dict:
    agenda = [(_AGENDA_KIND[s["layout"]], s["title"]) for s in sec["slides"]]
    return {"id": f"part-{sec['id']}", "layout": "part",
            "kicker": f"Part {i} of {total}",
            "title": sec["name"], "sub": sec.get("goal", ""),
            "agenda": agenda,
            "notes": f"Section opener. {sec.get('goal', '')} "
                     "The agenda colours say what each slide is: plain language (grey), a figure (green), "
                     "Kwant code (blue), the mathematics (pink). Say in one sentence where this stop sits "
                     "on the course map, then move on."}


def render_deck(deck: dict, figures: dict[int, dict]) -> tuple[str, dict]:
    """One flat, linear sequence: a Part opener before each section, then its
    slides.  Navigation is reveal.js's own previous/next only."""
    content = {"lang": "en", "deckTitle": deck["title"], "sections": {}, "slides": {}}
    out = [HTML_HEAD.format(title=html.escape(deck["title"]))]
    total = len(deck["sections"])
    for i, sec in enumerate(deck["sections"], 1):
        content["sections"][sec["id"]] = sec["name"]
        for slide in [part_slide(i, total, sec)] + sec["slides"] if sec["id"] != "opening" \
                else sec["slides"]:
            h, entry = render_slide(sec, slide, figures)
            content["slides"][slide["id"]] = entry
            out.append(h)
    out.append(HTML_TAIL)
    return "\n".join(out), content


def render_notes(deck: dict, figures: dict[int, dict]) -> str:
    lines = [f"# {deck['title']} — lecturer notes", "",
             "Generated by `course/build_course.py` from `course/deck/content_en.py`; do not edit by hand.",
             "The deck is one linear sequence: the sections below follow each other in order, and inside "
             "each one the slides go from plain language to Kwant code to the mathematics.", ""]
    for si, sec in enumerate(deck["sections"], 1):
        lines += [f"## {si}. {sec['name']}", ""]
        if sec.get("goal"):
            lines += [f"*Goal:* {sec['goal']}", ""]
        for slide in sec["slides"]:
            lines.append(f"### {slide['title']}")
            if slide.get("lead"):
                lines.append(f"*{slide['lead']}*")
            for b in slide.get("bullets", []):
                lines.append(f"- {b}")
            for n in slide.get("figures", [slide["figure"]] if slide.get("figure") else []):
                lines.append(f"- Figure {n} of the course ({_nb_where(figures, n)}): {caption_plain(figures[n]['caption'])}")
            for label, eq in slide.get("equations", []):
                lines.append(f"- {label}: {eq}")
            if slide.get("code"):
                lines += ["", "```python", slide["code"].rstrip(), "```"]
            lines += ["", f"**Notes.** {slide['notes']}", ""]
    text = "\n".join(lines)
    # strip only the inline tags the content uses; a raw "<" in a code block must survive
    text = re.sub(r"</?(?:strong|em|code|sup|sub|b|i|span)(?:\s[^>]*)?>", "", text)
    return html.unescape(text) + "\n"


# ---------------------------------------------------------------- slides doc (static + PDF fallback)
SLIDES_CSS = """body { font: 15px/1.5 "Segoe UI", system-ui, sans-serif; color: #1c2128; max-width: 1100px;
       margin: 1.5rem auto; padding: 0 1rem; background: #fff; }
h1 { font-size: 1.5em; color: #0d419d; border-bottom: 2px solid #d0d7de; padding-bottom: 4px; margin: 2.2em 0 0.4em 0; }
h1.part { font-size: 2em; color: #1c2128; border: none; margin-top: 3em; }
p.kicker { color: #57606a; text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.8em; margin: 3em 0 -0.5em 0; }
p.lead, p.goal { color: #57606a; font-style: italic; }
figure { margin: 1em 0; text-align: center; }
figure img { max-width: 85%; height: auto; }
figcaption { font-size: 0.85em; color: #57606a; text-align: left; max-width: 85%; margin: 0.4em auto 0 auto; }
pre { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 8px; padding: 12px 16px;
      font: 13px/1.4 Consolas, monospace; overflow-x: auto; }
table { border-collapse: collapse; } th, td { border-bottom: 1px solid #d0d7de; padding: 4px 10px; text-align: left; }
"""


def render_slides_doc(deck: dict, figures: dict[int, dict]) -> str:
    """The whole deck as one static HTML document (slides.html): the no-JavaScript
    fallback, and the pandoc input for slides.pdf (one slide per page there)."""
    total = len(deck["sections"])
    out = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           f"<title>{html.escape(deck['title'])} — slides</title>",
           f"<style>{SLIDES_CSS}</style>", "</head>", "<body>"]
    for i, sec in enumerate(deck["sections"], 1):
        out.append(f'<p class="kicker">Part {i} of {total}</p>')
        out.append(f'<h1 class="part">{sec["name"]}</h1>')
        if sec.get("goal"):
            out.append(f'<p class="goal">{sec["goal"]}</p>')
        for slide in sec["slides"]:
            if slide["layout"] == "hero":
                out.append(f'<h1>{slide["title"]}</h1>')
                if slide.get("sub"):
                    out.append(f'<p class="lead">{slide["sub"]}</p>')
            else:
                out.append(f'<h1>{slide["title"]}</h1>')
                if slide.get("lead"):
                    out.append(f'<p class="lead">{slide["lead"]}</p>')
            bullets = slide.get("bullets", [])
            if bullets:
                out.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            for label, eq in slide.get("equations", []):
                out.append(f'<p><em>{label}:</em>&ensp;{eq}</p>')
            if slide.get("code"):
                out.append(f"<pre><code>{html.escape(slide['code'].rstrip())}</code></pre>")
            if slide.get("header"):
                out.append('<table><thead><tr>' + "".join(f"<th>{html.escape(h)}</th>" for h in slide["header"])
                           + "</tr></thead><tbody>"
                           + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in slide["rows"])
                           + "</tbody></table>")
            figs = slide.get("figures", [slide["figure"]] if slide.get("figure") else [])
            for n in figs:
                cap = figures.get(n, {}).get("caption", "")
                out.append(f'<figure><img src="../figures/fig-{n:02d}.png" '
                           f'alt="{html.escape(caption_plain(cap)[:120])}">'
                           f'<figcaption><strong>Figure {n}.</strong> {tex_inline(cap)}'
                           f' <em>({fig_meta(figures, n)})</em></figcaption></figure>')
    out += ["</body>", "</html>"]
    return "\n".join(out)


def build_slides_pdf(slides_html: Path, out_pdf: Path, say) -> str:
    """slides.html -> slides.pdf via pandoc + xelatex: A4 landscape, one slide per
    page (every h1 starts a page), DejaVu fonts for full glyph coverage."""
    engine = next((e for e in ("xelatex", "lualatex") if shutil.which(e)), None)
    if not (shutil.which("pandoc") and engine):
        say("slides pdf skipped (no pandoc + TeX engine)", detail=True)
        return "pdf-skipped"
    header = (r"\usepackage{titlesec}" "\n"
              r"\newcommand{\sectionbreak}{\clearpage}" "\n"
              r"\usepackage{float}" "\n"
              r"\floatplacement{figure}{H}" "\n"
              r"\usepackage[labelformat=empty]{caption}" "\n")   # the captions carry their own "Figure N."
    header_file = out_pdf.parent / "slides-header.tex"
    header_file.write_text(header, encoding="utf-8")
    cmd = ["pandoc", str(slides_html), "--from", "html", f"--pdf-engine={engine}",
           "--resource-path", str(slides_html.parent),
           "--metadata", "title=Quantum Transport with Kwant — slides",
           "-V", "classoption=landscape", "-V", "geometry:margin=1.6cm", "-V", "fontsize=12pt",
           "-V", "mainfont=DejaVuSans.ttf",
           "-V", "mainfontoptions=BoldFont=DejaVuSans-Bold.ttf",
           "-V", "mainfontoptions=ItalicFont=DejaVuSans-Oblique.ttf",
           "-V", "mainfontoptions=BoldItalicFont=DejaVuSans-BoldOblique.ttf",
           "-V", "monofont=DejaVuSansMono.ttf",
           "--include-in-header", str(header_file),
           "-o", str(out_pdf)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    header_file.unlink(missing_ok=True)
    ok = r.returncode == 0 and out_pdf.exists()
    say(f"slides pdf via pandoc+{engine}" if ok else f"slides pdf FAILED: {r.stderr.strip()[-400:]}", detail=not ok)
    return "pdf" if ok else "pdf-FAILED"


# ---------------------------------------------------------------- handout
def build_handout(src: Path, outdir: Path, say) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    out_html, out_pdf = outdir / "handout.html", outdir / "handout.pdf"
    used = []
    if shutil.which("pandoc"):
        css = HERE / "handout" / "handout.css"
        ok = subprocess.run(["pandoc", str(src), "-s", "--toc", "--toc-depth=2", "-c", str(css), "--embed-resources",
                             "--metadata", "title=Quantum transport with Kwant — companion handout",
                             "-o", str(out_html)], capture_output=True).returncode == 0
        say(f"handout html via {'pandoc' if ok else 'pandoc FAILED'}", detail=True)
        used.append("html" if ok else "html-FAILED")
        engine = next((e for e in ("xelatex", "lualatex", "pdflatex") if shutil.which(e)), None)
        if engine:
            ok = subprocess.run(["pandoc", str(src), "--toc", "--toc-depth=2", f"--pdf-engine={engine}",
                                 "-V", "geometry:margin=2cm", "-V", "colorlinks=true",
                                 "--resource-path", str(src.parent), "-o", str(out_pdf)],
                                capture_output=True).returncode == 0
            say(f"handout pdf via pandoc+{engine}" if ok else "handout pdf FAILED", detail=True)
            used.append("pdf" if ok else "pdf-FAILED")
        else:
            say("handout pdf skipped (no TeX engine)", detail=True)
    else:
        say("handout skipped (no pandoc)", detail=True)
    return used


# ---------------------------------------------------------------- readback
def readback(index_html: str, content: dict, fig_dir: Path, manifest: list[dict],
             deck: dict, slides_html: Path, slides_pdf: Path, pdf_expected: bool) -> list[str]:
    problems = []
    refs = re.findall(r'data-t="([^"]+)"', index_html)
    for ref in refs:
        sid, key = ref.split(".", 1)
        if key not in content["slides"].get(sid, {}):
            problems.append(f"unresolved data-t {ref}")
    for sid, entry in content["slides"].items():
        if not entry.get("notes"):
            problems.append(f"slide {sid} has no notes")
    if 'class="fragment' in index_html:
        problems.append("fragment classes remain in index.html (builds were removed)")
    static = slides_html.read_text(encoding="utf-8") if slides_html.exists() else ""
    for doc, name in ((index_html, "index.html"), (static, "slides.html")):
        shown = [int(n) for n in re.findall(r"fig-(\d+)\.png", doc)]
        if sorted(set(shown)) != [m["n"] for m in manifest]:
            missing = set(m["n"] for m in manifest) - set(shown)
            problems.append(f"{name}: figures missing {sorted(missing)}" if missing
                            else f"{name}: unknown figure numbers {sorted(set(shown) - set(m['n'] for m in manifest))}")
        if len(shown) != len(set(shown)):
            dup = sorted({n for n in shown if shown.count(n) > 1})
            problems.append(f"{name}: figures shown more than once {dup}")
        if doc.count("<figcaption>") != len(set(shown)):
            problems.append(f"{name}: a figure lacks its caption")
    for src in re.findall(r'src="\.\./figures/(fig-\d+\.png)"', index_html):
        if not (fig_dir / src).exists():
            problems.append(f"missing figure file {src}")
    if len(manifest) != len(list(fig_dir.glob("fig-*.png"))):
        problems.append("figures.json and fig-*.png disagree")
    ids = [s["id"] for sec in deck["sections"] for s in sec["slides"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate slide ids")
    if pdf_expected:
        if not slides_pdf.exists():
            problems.append("slides.pdf missing")
        else:
            raw = slides_pdf.read_bytes()
            if not raw.startswith(b"%PDF-1.7"):
                problems.append(f"slides.pdf is not the typeset PDF ({raw[:8]!r})")
            if len(raw) < 1_000_000:
                problems.append(f"slides.pdf suspiciously small ({len(raw)} B): are the figures in it?")
            try:
                import pymupdf
                doc = pymupdf.open(slides_pdf)
                text = "".join(page.get_text() for page in doc)
                n_pages = doc.page_count
                doc.close()
                if n_pages < len(ids):
                    problems.append(f"slides.pdf has {n_pages} pages for {len(ids)} slides")
                for probe in ("Σ", "⟨", "Berry"):
                    if probe not in text:
                        problems.append(f"slides.pdf text readback: {probe!r} not found (missing glyphs?)")
            except ImportError:
                pass
    return problems


# ---------------------------------------------------------------- CLI
def build_parser():
    p = argparse.ArgumentParser(description="Build the course deck (linear reveal.js + static HTML + PDF), "
                                            "lecturer notes and handout from course/deck/content_en.py.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--outdir", default=str(HERE), help="course directory to write into")
    p.add_argument("--chapters", default=str(ROOT / "chapters"),
                   help="directory of the executed chapter notebooks the figures are taken from")
    p.add_argument("--log-dir", default=None, help="audit-log directory (default <outdir>/logs)")
    p.add_argument("--skip-handout", action="store_true",
                   help="skip the pandoc/xelatex artefacts (handout and slides.pdf)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--verbose", action="store_true", help="show every step")
    g.add_argument("--quiet", action="store_true", help="print only the one-line result")
    p.add_argument("--version", action="version", version=f"build_course {_version()}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    outdir = Path(args.outdir).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else outdir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"build_course_{stamp}.log"
    lines = [f"# build_course {_version()}", f"# command: {' '.join(sys.argv)}",
             f"# python: {sys.version.split()[0]}",
             f"# pandoc: {shutil.which('pandoc') or 'none'}  xelatex: {shutil.which('xelatex') or 'none'}",
             f"# outdir: {outdir}"]

    def say(msg, detail=False):
        lines.append(msg)
        if not args.quiet and (not detail or args.verbose):
            print(msg)

    manifest = extract_figures(Path(args.chapters), outdir / "figures")
    say(f"figures: {len(manifest)} extracted from {len(chapter_notebooks(Path(args.chapters)))} chapter notebooks "
        f"in {Path(args.chapters)}", detail=True)
    figures = {m["n"]: m for m in manifest}
    deck_src, placement = load_content(HERE / "deck" / "content_en.py")
    deck, problems = expand_deck(deck_src, placement, figures)
    (outdir / "deck").mkdir(parents=True, exist_ok=True)
    index_html, content = render_deck(deck, figures)
    (outdir / "deck" / "index.html").write_text(index_html, encoding="utf-8", newline="\n")
    (outdir / "deck" / "content.en.js").write_text(
        "/* Generated by course/build_course.py from content_en.py -- do not edit. */\n"
        "window.DECK_CONTENT = " + json.dumps(content, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8", newline="\n")
    n_slides = sum(len(s["slides"]) for s in deck["sections"]) + len(deck["sections"]) - 1
    say(f"deck: {len(deck['sections'])} sections, {n_slides} slides (all {len(manifest)} figures)", detail=True)
    (outdir / "lecturer_notes.md").write_text(render_notes(deck, figures), encoding="utf-8", newline="\n")
    slides_html_path = outdir / "deck" / "slides.html"
    slides_html_path.write_text(render_slides_doc(deck, figures), encoding="utf-8", newline="\n")
    say("slides.html written (static fallback)", detail=True)
    used = []
    if not args.skip_handout:
        used.append(build_slides_pdf(slides_html_path, outdir / "deck" / "slides.pdf", say))
        used += build_handout(HERE / "handout" / "handout.md", outdir / "handout", say)
    problems += readback(index_html, content, outdir / "figures", manifest, deck,
                         slides_html_path, outdir / "deck" / "slides.pdf",
                         pdf_expected=not args.skip_handout and "pdf-skipped" not in used)
    for pr in problems:
        say(f"READBACK: {pr}")
    rc = 1 if problems or any(u.endswith("FAILED") for u in used) else 0
    say(f"build_course: {'ok' if rc == 0 else 'FAILED'} -- {len(deck['sections'])} sections / {n_slides} slides, "
        f"{len(manifest)} figures, pandoc {', '.join(used) or 'skipped'}; log {log_path}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
