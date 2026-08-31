# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Publishing playbook rule 15 (documentation guarded by the suite) and rule 16
(one product version): the manual and AGENTS.md must name every CLI option of
the two support scripts and no option that does not exist; every count stated
in prose must equal the count the notebook tests assert; VERSION, CITATION.cff,
CHANGELOG and both scripts' --version must agree."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_notebooks import EXPECTED, MAIN, N_EXERCISES, SOL

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {"verify_kwant.py": ROOT / "verify_kwant.py",
           "test_thread_safety.py": ROOT / "test_thread_safety.py"}
DOCS = {"AGENTS.md": ROOT / "AGENTS.md", "docs/USER_MANUAL.md": ROOT / "docs" / "USER_MANUAL.md"}
OPT = re.compile(r"(?<![\w-])(--[a-z][a-z-]*)")


def _read(p):
    return p.read_text(encoding="utf-8")


def help_options(script):
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True,
                       cwd=ROOT, timeout=120)
    assert r.returncode == 0, r.stderr
    return set(OPT.findall(r.stdout)) - {"--help"}


def documented_options(doc_text, script_name):
    """Options that appear on a `python <script>` command line (including its
    continuation lines) or as a `--option` table row in the given document."""
    opts, lines = set(), doc_text.splitlines()
    for i, ln in enumerate(lines):
        if f"python {script_name}" in ln:
            block = ln
            j = i + 1
            while j < len(lines) and lines[j].startswith(" ") and "--" in lines[j]:
                block += " " + lines[j]
                j += 1
            opts |= set(OPT.findall(block))
    return opts - {"--help"}


@pytest.mark.parametrize("script", list(SCRIPTS), ids=lambda s: s.split(".")[0])
@pytest.mark.parametrize("doc", list(DOCS), ids=lambda d: Path(d).stem)
def test_every_cli_option_is_documented_and_every_documented_option_exists(script, doc):
    real = help_options(SCRIPTS[script])
    text = _read(DOCS[doc])
    on_cmdline = documented_options(text, script)
    assert on_cmdline, f"{doc} has no command line for {script}"
    missing = sorted(real - on_cmdline)
    assert not missing, f"{doc}: {script} options not documented: {missing}"
    phantom = sorted(on_cmdline - real)
    assert not phantom, f"{doc}: documents options {script} does not have: {phantom}"


def test_manual_option_tables_match_help():
    """Section 6 of the manual has one table row per option of verify_kwant.py;
    every row must be a real option."""
    text = _read(DOCS["docs/USER_MANUAL.md"])
    sec = text[text.index("## 6.1"):text.index("# 7.")]
    rows = set(re.findall(r"^\| `(--[a-z-]+)`", sec, re.M))
    real = help_options(SCRIPTS["verify_kwant.py"]) | help_options(SCRIPTS["test_thread_safety.py"])
    assert rows <= real, sorted(rows - real)


def test_counts_in_prose_match_the_asserted_counts():
    m, s = EXPECTED[MAIN], EXPECTED[SOL]
    claims = {
        "README.md": [f"{m['figures']} figures", f"{N_EXERCISES} exercises"],
        "AGENTS.md": [f"{m['cells']} cells ({m['code']} code), {m['figures']} figures, {N_EXERCISES} exercises",
                      f"{s['cells']} cells ({s['code']} code), {s['figures']} figures",
                      f"{m['cells']}/{m['code']}/{m['figures']}", f"{s['cells']}/{s['code']}/{s['figures']}"],
        "docs/USER_MANUAL.md": [f"{m['cells']} cells ({m['code']} code", f"{m['figures']} figures, {N_EXERCISES} exercises",
                                f"{s['cells']} cells ({s['code']} code", f"{s['figures']} figures",
                                f"{m['cells']}/{m['code']}/{m['figures']} and {s['cells']}/{s['code']}/{s['figures']}"],
        "CITATION.cff": [f"{N_EXERCISES} exercises"],
    }
    for name, needles in claims.items():
        text = _read(ROOT / name)
        for needle in needles:
            assert needle in text, f"{name} does not state {needle!r}"


def test_one_product_version_everywhere():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    assert f'version: "{version}"' in _read(ROOT / "CITATION.cff")
    top = re.search(r"^## (\d+\.\d+\.\d+) — ", _read(ROOT / "CHANGELOG.md"), re.M)
    assert top and top.group(1) == version, "CHANGELOG's first entry is not the VERSION"
    for name, script in SCRIPTS.items():
        r = subprocess.run([sys.executable, str(script), "--version"], capture_output=True,
                           text=True, cwd=ROOT, timeout=120)
        assert r.returncode == 0 and r.stdout.strip().endswith(version), (name, r.stdout, r.stderr)
