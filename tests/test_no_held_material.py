# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Withheld-material guard (publishing playbook rule 18).

Part of the owner's ongoing, unpublished research (the former Part III) was
removed from this repository on 2026-08-29 and must not come back into any
tracked file -- text, code, notebook sources or outputs, docs -- until it is
published. The forbidden tokens are stored as SHA-256 hashes in
``tests/held_terms.txt`` so that neither this file nor that list names the
topic. The full material lives in the gitignored ``private/`` directory.
"""
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TERMS_FILE = Path(__file__).resolve().parent / "held_terms.txt"
TEXT_EXT = {".py", ".md", ".ipynb", ".txt", ".yml", ".yaml", ".json", ".ps1",
            ".bat", ".bib", ".cff", ".patch", ".mbox", ".html"}
TOKEN = re.compile(r"[^\W\d_](?:[\w\-]*[^\W\d_])?", re.UNICODE)   # words, incl. hyphenated


def held_hashes():
    with open(TERMS_FILE, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def tracked_text_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout
    except Exception:  # noqa: BLE001 - no git: scan the tree instead
        return [p for p in ROOT.rglob("*") if p.suffix in TEXT_EXT and ".git" not in p.parts]
    return [ROOT / p for p in out.split() if Path(p).suffix in TEXT_EXT]


def offending_tokens(text, hashes):
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        for cand in {tok.lower(), tok.lower().replace("-", "")}:
            if hashlib.sha256(cand.encode("utf-8")).hexdigest() in hashes:
                return tok
    return None


def test_no_tracked_file_mentions_held_material():
    hashes = held_hashes()
    assert hashes, "held_terms.txt is empty"
    hits = []
    for path in tracked_text_files():
        tok = offending_tokens(path.read_text(encoding="utf-8", errors="replace"), hashes)
        if tok:
            hits.append(f"{path.relative_to(ROOT)}: {tok!r}")
    assert not hits, hits


def test_guard_detects_a_planted_token():
    """The guard must actually fire: hash a dummy word, plant it, expect a hit."""
    dummy = "zzqx-held-dummy"
    hashes = {hashlib.sha256(dummy.encode()).hexdigest()}
    assert offending_tokens(f"text with {dummy} inside", hashes) == dummy
    assert offending_tokens(f"text with {dummy.upper()} inside", hashes) == dummy.upper()
    assert offending_tokens("clean line", hashes) is None
    real = held_hashes()
    assert real and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in real)


def test_private_directory_is_ignored_and_untracked():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "private/" in gi
    try:
        out = subprocess.run(["git", "ls-files", "private"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout
    except Exception:  # noqa: BLE001
        pytest.skip("not inside a git repository")
    assert out.strip() == "", "private/ must never be tracked"
