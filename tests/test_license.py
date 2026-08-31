# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Publishing playbook rule 17: the warranty disclaimer and limitation of
liability must survive every rewrite -- in LICENSE, visibly in the README --
NOTICE must exist, and every source file and both notebooks must carry the
SPDX identifier."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPDX = "SPDX-License-Identifier: Apache-2.0"


def _read(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8", errors="replace")


def test_license_is_apache_2_with_disclaimers():
    text = _read("LICENSE")
    assert "Apache License" in text and "Version 2.0" in text
    assert "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND" in text
    assert "Limitation of Liability" in text


def test_notice_names_project_and_upstream_licence():
    text = _read("NOTICE")
    assert "Kwant - Theory and Practice" in text and "Apache License, Version 2.0" in text
    assert "BSD 2-clause" in text            # Kwant's own licence, by origin
    assert "not affiliated" in text


def test_readme_carries_visible_disclaimer_and_non_affiliation_under_licence():
    text = _read("README.md")
    assert "## Licence" in text and "### Disclaimer" in text
    assert text.index("## Licence") < text.index("### Disclaimer")
    low = text.lower()
    assert "without warrant" in low and "liable" in low
    assert "not affiliated" in low and "anthropic" in low and "kwant" in low


def test_citation_matches_licence():
    assert "license: Apache-2.0" in _read("CITATION.cff")


def test_every_tracked_script_has_spdx_header():
    out = subprocess.run(["git", "ls-files", "*.py", "*.ps1", "*.bat"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    assert len(out) >= 30, out
    missing = [f for f in out if SPDX not in _read(f)[:400]]
    assert not missing, missing


def test_both_notebooks_carry_the_spdx_identifier():
    for name in ("Kwant_Theory_and_Practice.ipynb", "Kwant_Exercises_Solutions.ipynb"):
        nb = json.loads(_read(name))
        md = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
        assert SPDX in md, name
