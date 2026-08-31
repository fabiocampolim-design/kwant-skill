# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Publishing playbook rule 14: check the artefact, not the return code.

docs/build_manual.py renders USER_MANUAL.md to .html and .pdf and both are
committed. These tests read the committed artefacts back: every heading of
the Markdown must be in the HTML, and the PDF must be the typeset
(pandoc + TeX) one, not the plain-text fallback the builder writes when no
TeX engine is installed.
"""
import html
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
MD, HTML, PDF = DOCS / "USER_MANUAL.md", DOCS / "USER_MANUAL.html", DOCS / "USER_MANUAL.pdf"


def headings():
    text = MD.read_text(encoding="utf-8")
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)      # front matter
    text = re.sub(r"```.*?```", "", text, flags=re.S)                     # fenced code
    return [re.sub(r"`", "", h).strip() for h in re.findall(r"^#{1,2} (.+)$", text, re.M)]


def test_markdown_has_the_sections_the_readme_promises():
    hs = headings()
    assert len(hs) >= 20, hs
    for needle in ("Installation", "The support scripts", "Known limitations", "Licence"):
        assert any(needle in h for h in hs), needle


def test_html_contains_every_heading():
    page = html.unescape(re.sub(r"<[^>]+>", "", HTML.read_text(encoding="utf-8")))
    page = re.sub(r"\s+", " ", page)
    missing = [h for h in headings() if re.sub(r"\s+", " ", h) not in page]
    assert not missing, missing
    assert "Kwant" in page


def test_pdf_is_the_typeset_one_and_not_the_fallback():
    raw = PDF.read_bytes()
    assert raw.startswith(b"%PDF-1.7"), raw[:12]          # the fallback writer emits PDF-1.4
    assert b"/BaseFont /Courier" not in raw               # the fallback's only font
    assert len(raw) > 40_000, len(raw)                    # the fallback is a few kB
    assert raw.rstrip().endswith(b"%%EOF")


def test_pdf_text_readback_when_a_reader_is_installed():
    fitz = pytest.importorskip("pymupdf")
    doc = fitz.open(str(PDF))
    assert doc.page_count >= 5, doc.page_count
    text = re.sub(r"\s+", " ", "".join(p.get_text() for p in doc))
    missing = [h for h in headings() if re.sub(r"\s+", " ", h) not in text]
    assert not missing, missing
