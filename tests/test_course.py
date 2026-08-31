# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""The undergraduate course (publishing playbook rule 22, as amended 2026-08-31):
the committed deck is one linear sequence with no build animations, every
notebook figure appears exactly once — full caption, section and cell — in the
deck AND in the PDF/static fallbacks, every data-t reference resolves, every
slide has notes, and the course builder has a CLI."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_notebooks import EXPECTED, MAIN

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course"
DECK = COURSE / "deck"
sys.path.insert(0, str(DECK))
import content_en  # noqa: E402

N_FIGS = EXPECTED[MAIN]["figures"]


def _manifest():
    return json.loads((COURSE / "figures" / "figures.json").read_text(encoding="utf-8"))


def _content_js():
    text = (DECK / "content.en.js").read_text(encoding="utf-8")
    body = text[text.index("window.DECK_CONTENT = ") + len("window.DECK_CONTENT = "):].rstrip().rstrip(";")
    return json.loads(body)


def test_content_source_is_well_formed():
    deck = content_en.DECK
    ids = [s["id"] for sec in deck["sections"] for s in sec["slides"]]
    assert len(ids) == len(set(ids)), "duplicate slide ids"
    assert len(deck["sections"]) == 10
    assert len(ids) >= 40
    for sec in deck["sections"]:
        assert sec["slides"], sec["id"]
        for s in sec["slides"]:
            assert s["layout"] in ("hero", "text", "figure", "figure-wide", "code", "math", "table"), s["id"]
            assert s["notes"].rstrip().endswith((".", "?", "!")), s["id"]
            assert "Q:" in s["notes"], f"{s['id']}: notes need one anticipated question"


def test_placement_covers_every_remaining_figure_exactly_once():
    deck = content_en.DECK
    authored = set()
    all_ids = set()
    for sec in deck["sections"]:
        for s in sec["slides"]:
            all_ids.add(s["id"])
            authored |= set(s.get("figures", [s["figure"]] if s.get("figure") else []))
    placed = set(content_en.PLACEMENT)
    assert not authored & placed, sorted(authored & placed)
    assert authored | placed == set(range(1, N_FIGS + 1)), \
        sorted(set(range(1, N_FIGS + 1)) - authored - placed)
    for n, sid in content_en.PLACEMENT.items():
        assert sid in all_ids, f"PLACEMENT[{n}] -> unknown slide {sid}"


def test_deck_is_linear_with_no_build_animations():
    html = (DECK / "index.html").read_text(encoding="utf-8")
    assert 'class="fragment' not in html, "build animations were removed (rule 22)"
    assert "nav.js" not in html and "DeckNav" not in html, "single-level navigation only"
    assert not (COURSE / "shared" / "nav.js").exists()
    body = html[html.index('<div class="slides">'):html.index("</div>\n  </div>")]
    assert "<section" in body and body.count("<section") == body.count("</section>"), "malformed sections"
    # flat: no <section> nested inside another
    depth = 0
    for tag in re.findall(r"</?section", body):
        depth += 1 if tag == "<section" else -1
        assert depth in (0, 1), "nested sections: the deck is not linear"
    # a part opener for every section but the opening
    for sec in content_en.DECK["sections"][1:]:
        assert f'id="part-{sec["id"]}"' in html, sec["id"]
    assert "controls: true" in html and "slideNumber" in html


def test_every_data_t_reference_resolves_and_every_slide_has_notes():
    html = (DECK / "index.html").read_text(encoding="utf-8")
    content = _content_js()
    refs = re.findall(r'data-t="([^"]+)"', html)
    assert len(refs) > 300
    for ref in refs:
        sid, key = ref.split(".", 1)
        assert key in content["slides"][sid], ref
    for sid in re.findall(r'data-notes="([^"]+)"', html):
        assert content["slides"][sid]["notes"], sid
    assert set(re.findall(r'data-sec="([^"]+)"', html)) == set(content["sections"])


@pytest.mark.parametrize("doc", ["index.html", "slides.html"])
def test_every_notebook_figure_appears_exactly_once_with_its_caption(doc):
    manifest = _manifest()
    text = (DECK / doc).read_text(encoding="utf-8")
    shown = [int(n) for n in re.findall(r"fig-(\d+)\.png", text)]
    assert sorted(shown) == [m["n"] for m in manifest], f"{doc}: figure coverage broken"
    assert text.count("<figcaption>") == len(manifest)
    for m in manifest:
        probe = m["caption"].split("$")[0][:40].strip()
        probe = probe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if len(probe) >= 10:
            assert probe in text, f"{doc}: caption of figure {m['n']} missing ({probe!r})"
        assert f"cell {m['cell']})" in text, f"{doc}: cell reference of figure {m['n']} missing"


def test_figures_are_the_notebooks_figures():
    manifest = _manifest()
    assert len(manifest) == N_FIGS
    assert [m["n"] for m in manifest] == list(range(1, N_FIGS + 1))
    files = sorted(p.name for p in (COURSE / "figures").glob("fig-*.png"))
    assert files == [f"fig-{n:02d}.png" for n in range(1, N_FIGS + 1)]
    nb = json.loads(MAIN.read_text(encoding="utf-8"))
    for m in manifest:
        cell = nb["cells"][m["cell"]]
        assert cell["cell_type"] == "code"
        assert any("image/png" in o.get("data", {}) for o in cell.get("outputs", [])), m
        assert len(m["caption"]) >= 40, f"figure {m['n']}: caption too thin to stand alone"


def test_generated_files_are_current():
    """content.en.js and lecturer_notes.md must be what content_en.py produces."""
    content = _content_js()
    deck = content_en.DECK
    assert content["deckTitle"] == deck["title"]
    assert list(content["sections"]) == [s["id"] for s in deck["sections"]]
    for sec in deck["sections"]:
        for s in sec["slides"]:
            assert content["slides"][s["id"]]["notes"] == s["notes"], s["id"]
    for n in content_en.PLACEMENT:
        assert f"figpage-{n:02d}" in content["slides"], n
    notes = (COURSE / "lecturer_notes.md").read_text(encoding="utf-8")
    for sec in deck["sections"]:
        assert sec["name"] in notes, sec["name"]
        for s in sec["slides"]:
            assert re.sub(r"<[^>]+>", "", s["title"]) in notes, s["id"]


def test_slides_pdf_is_the_whole_deck():
    pdf = DECK / "slides.pdf"
    assert pdf.exists(), "slides.pdf is the committed projector fallback"
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-1.7"), raw[:8]
    assert len(raw) > 2_000_000, "all 68 figures should be embedded"
    assert raw.rstrip().endswith(b"%%EOF")
    try:
        import pymupdf
    except ImportError:
        pytest.skip("pymupdf not installed")
    doc = pymupdf.open(pdf)
    n_slides = len(re.findall(r"<section", (DECK / "index.html").read_text(encoding="utf-8")))
    assert doc.page_count >= n_slides, (doc.page_count, n_slides)
    text = "".join(page.get_text() for page in doc)
    doc.close()
    for probe in ("Σ", "⟨", "Berry", "Landauer", f"Figure {N_FIGS}"):
        assert probe in text, f"slides.pdf: {probe!r} missing (glyphs or pages lost)"


def test_slides_html_is_static():
    text = (DECK / "slides.html").read_text(encoding="utf-8")
    assert "<script" not in text
    assert "http://" not in text and "https://" not in text


def test_handout_carries_its_sections_and_the_reference_card():
    md = (COURSE / "handout" / "handout.md").read_text(encoding="utf-8")
    heads = re.findall(r"^# (.+)$", md, re.M)
    assert len(heads) >= 7
    for needle in ("reference card", "Key equations", "models of Part II", "Pitfalls", "Running it", "Reading"):
        assert any(needle in h for h in heads), needle
    html = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (COURSE / "handout" / "handout.html").read_text(encoding="utf-8")))
    for h in heads:
        assert h in html, h
    assert "kwant.smatrix" in md and "MUMPS is not re-entrant" in md
    pdf = COURSE / "handout" / "handout.pdf"
    assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF-1.7")


def test_deck_runs_offline_from_vendored_files():
    html = (DECK / "index.html").read_text(encoding="utf-8")
    assert "http://" not in html and "https://" not in html
    for rel in ("shared/reveal/dist/reveal.js", "shared/reveal/dist/reveal.css", "shared/reveal/dist/reset.css",
                "shared/reveal/plugin/notes/notes.js", "shared/reveal/LICENSE", "shared/loader.js",
                "shared/theme.css"):
        assert (COURSE / rel).exists(), rel


def test_builder_cli():
    r = subprocess.run([sys.executable, str(COURSE / "build_course.py"), "--help"], capture_output=True, text=True,
                       cwd=ROOT, timeout=120)
    assert r.returncode == 0
    for opt in ("--outdir", "--notebook", "--log-dir", "--skip-handout", "--verbose", "--quiet", "--version"):
        assert opt in r.stdout, opt
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    r = subprocess.run([sys.executable, str(COURSE / "build_course.py"), "--version"], capture_output=True,
                       text=True, cwd=ROOT, timeout=120)
    assert r.stdout.strip() == f"build_course {version}"


@pytest.mark.skipif(not (COURSE / "figures" / "figures.json").exists(), reason="course not built")
def test_rebuild_into_a_temporary_directory_reproduces_the_deck(tmp_path):
    r = subprocess.run([sys.executable, str(COURSE / "build_course.py"), "--outdir", str(tmp_path),
                        "--skip-handout", "--quiet"], capture_output=True, text=True, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    for rel in ("deck/index.html", "deck/slides.html"):
        assert (tmp_path / rel).read_text(encoding="utf-8") == (COURSE / rel).read_text(encoding="utf-8"), rel
    assert (tmp_path / "figures" / "figures.json").read_text(encoding="utf-8") == \
        (COURSE / "figures" / "figures.json").read_text(encoding="utf-8")
