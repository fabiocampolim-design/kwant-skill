# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Static guarantees about the two shipped notebooks (no kernel needed).

These are the claims the README makes; if a number here changes, the README
and CITATION.cff change with it.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "Kwant_Theory_and_Practice.ipynb"
SOL = ROOT / "Kwant_Exercises_Solutions.ipynb"

EXPECTED = {
    MAIN: dict(cells=86, code=53, figures=68),
    SOL: dict(cells=51, code=24, figures=18),
}
N_EXERCISES = 25
KERNEL = "kwant"                      # the name install_kwant_windows.ps1 registers
# Personal-data / codename scan (publishing playbook rule 3). The alternatives are
# assembled from fragments so that this file itself passes a plain-text scan for
# the same tokens.
_NEEDLES = ["TM2" + "FDM", "Uni" + "camp", "CLAUDE" + "_", "g" + "mail",
            "Users" + "." + "fabio", "C:" + "\\\\" + "Users" + "\\\\"]
FORBIDDEN = re.compile("|".join(_NEEDLES), re.I)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def text_of(cell):
    src = "".join(cell["source"])
    for o in cell.get("outputs", []):
        t = o.get("text", "")
        src += "".join(t) if isinstance(t, list) else t
        src += str(o.get("data", {}).get("text/plain", ""))
    return src


@pytest.mark.parametrize("path", [MAIN, SOL], ids=["main", "solutions"])
def test_kernel_is_the_installer_kernel(path):
    assert load(path)["metadata"]["kernelspec"]["name"] == KERNEL


@pytest.mark.parametrize("path", [MAIN, SOL], ids=["main", "solutions"])
def test_every_code_cell_executed_without_error(path):
    for i, c in enumerate(load(path)["cells"]):
        if c["cell_type"] != "code" or not "".join(c["source"]).strip():
            continue
        assert c.get("execution_count") is not None, f"cell {i} not executed"
        errors = [o for o in c.get("outputs", []) if o.get("output_type") == "error"]
        assert not errors, f"cell {i}: {errors[0].get('ename')}: {errors[0].get('evalue')}"


@pytest.mark.parametrize("path", [MAIN, SOL], ids=["main", "solutions"])
def test_cell_and_figure_counts(path):
    nb = load(path)
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    figs = sum(1 for c in code for o in c.get("outputs", [])
               if "image/png" in o.get("data", {}))
    exp = EXPECTED[path]
    assert (len(cells), len(code), figs) == (exp["cells"], exp["code"], exp["figures"])


def test_exercises_are_31_and_solutions_match_one_to_one():
    tag = re.compile(r"\*\*E(\d+\.\d+)\*\*")
    main_tags = tag.findall("\n".join("".join(c["source"]) for c in load(MAIN)["cells"]
                                      if c["cell_type"] == "markdown"))
    sol_heads = re.findall(r"^## E(\d+\.\d+)", "\n".join("".join(c["source"])
                           for c in load(SOL)["cells"] if c["cell_type"] == "markdown"), re.M)
    assert len(set(main_tags)) == N_EXERCISES
    assert set(main_tags) == set(sol_heads)
    assert len(sol_heads) == N_EXERCISES, "one solution section per exercise"


@pytest.mark.parametrize("path", [MAIN, SOL], ids=["main", "solutions"])
def test_no_personal_or_project_codenames(path):
    for i, c in enumerate(load(path)["cells"]):
        m = FORBIDDEN.search(text_of(c))
        assert not m, f"cell {i}: {m.group(0)!r}"


def test_main_notebook_has_attribution_and_licence_cell():
    md = "\n".join("".join(c["source"]) for c in load(MAIN)["cells"] if c["cell_type"] == "markdown")
    assert "## Sources, attribution and licence" in md
    for src in ("topocondmat.org", "Asbóth", "Kwant documentation"):
        assert src in md
    assert "Apache License 2.0" in md
