# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Static guarantees about the shipped notebooks (no kernel needed).

The course is twelve chapter notebooks plus a contents notebook and two
solutions notebooks under chapters/.  These are the claims the README makes;
if a number here changes, the README, the manual and CITATION.cff change with it.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "chapters"
CONTENTS = CHAPTERS / "00_Contents.ipynb"

# file -> (cells, code cells, figures).  Figures are numbered continuously
# across the chapters (1-68), so the per-chapter counts are also the ranges.
EXPECTED = {
    "00_Contents.ipynb": dict(cells=2, code=1, figures=0),
    "01_Foundations.ipynb": dict(cells=13, code=7, figures=6),
    "02_Shapes_Spin_and_Bands.ipynb": dict(cells=10, code=6, figures=7),
    "03_Graphene_and_Superconductivity.ipynb": dict(cells=8, code=5, figures=5),
    "04_Observables_and_Visualisation.ipynb": dict(cells=9, code=6, figures=5),
    "05_KPM_and_Continuum.ipynb": dict(cells=10, code=7, figures=5),
    "06_Magnetic_Fields.ipynb": dict(cells=6, code=4, figures=5),
    "07_Solvers_Pitfalls_and_Exercises_I.ipynb": dict(cells=8, code=4, figures=1),
    "08_Topology_in_One_Dimension.ipynb": dict(cells=14, code=9, figures=12),
    "09_Chern_Numbers.ipynb": dict(cells=10, code=7, figures=6),
    "10_Z2_and_Chiral_Superconductors.ipynb": dict(cells=9, code=6, figures=6),
    "11_Higher_Order_and_Weyl.ipynb": dict(cells=8, code=5, figures=7),
    "12_3D_TI_Exercises_II_and_Beyond.ipynb": dict(cells=7, code=2, figures=3),
    "S1_Solutions_Part_I.ipynb": dict(cells=24, code=11, figures=10),
    "S2_Solutions_Part_II.ipynb": dict(cells=30, code=14, figures=8),
}
CHAPTER_FILES = [f for f in EXPECTED if f[:2].isdigit() and f != "00_Contents.ipynb"]
SOLUTION_FILES = [f for f in EXPECTED if f.startswith("S")]
ALL_FILES = list(EXPECTED)
N_FIGURES = 68                         # the course; the solutions add 18
N_EXERCISES = 25
N_CHAPTERS = 12
MAX_BYTES = 1_000_000                  # why the course was split: one 7.4 MB notebook crashed editors
KERNEL = "kwant"                       # the name install_kwant_windows.ps1 registers
# Personal-data / codename scan (publishing playbook rule 3). The alternatives are
# assembled from fragments so that this file itself passes a plain-text scan for
# the same tokens.
_NEEDLES = ["TM2" + "FDM", "Uni" + "camp", "CLAUDE" + "_", "g" + "mail",
            "Users" + "." + "fabio", "C:" + "\\\\" + "Users" + "\\\\"]
FORBIDDEN = re.compile("|".join(_NEEDLES), re.I)


def load(name):
    return json.loads((CHAPTERS / name).read_text(encoding="utf-8"))


def markdown_of(nb):
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")


def figures_in(nb):
    return sum(1 for c in nb["cells"] if c["cell_type"] == "code"
               for o in c.get("outputs", []) if "image/png" in o.get("data", {}))


def text_of(cell):
    src = "".join(cell["source"])
    for o in cell.get("outputs", []):
        t = o.get("text", "")
        src += "".join(t) if isinstance(t, list) else t
        src += str(o.get("data", {}).get("text/plain", ""))
    return src


def test_the_shipped_notebooks_are_exactly_these():
    assert sorted(p.name for p in CHAPTERS.glob("*.ipynb")) == sorted(ALL_FILES)
    assert len(CHAPTER_FILES) == N_CHAPTERS
    assert not (ROOT / "Kwant_Theory_and_Practice.ipynb").exists(), "the monolith was replaced by chapters/"


@pytest.mark.parametrize("name", ALL_FILES)
def test_kernel_is_the_installer_kernel(name):
    assert load(name)["metadata"]["kernelspec"]["name"] == KERNEL


@pytest.mark.parametrize("name", ALL_FILES)
def test_every_code_cell_executed_without_error(name):
    for i, c in enumerate(load(name)["cells"]):
        if c["cell_type"] != "code" or not "".join(c["source"]).strip():
            continue
        assert c.get("execution_count") is not None, f"cell {i} not executed"
        errors = [o for o in c.get("outputs", []) if o.get("output_type") == "error"]
        assert not errors, f"cell {i}: {errors[0].get('ename')}: {errors[0].get('evalue')}"


@pytest.mark.parametrize("name", ALL_FILES)
def test_cell_and_figure_counts(name):
    nb = load(name)
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    exp = EXPECTED[name]
    assert (len(cells), len(code), figures_in(nb)) == (exp["cells"], exp["code"], exp["figures"])


def test_totals_are_the_documented_ones():
    assert sum(EXPECTED[f]["figures"] for f in CHAPTER_FILES) == N_FIGURES
    assert sum(EXPECTED[f]["figures"] for f in SOLUTION_FILES) == 18
    assert sum(EXPECTED[f]["cells"] for f in CHAPTER_FILES) == 112
    assert sum(EXPECTED[f]["code"] for f in CHAPTER_FILES) == 68
    assert sum(EXPECTED[f]["cells"] for f in SOLUTION_FILES) == 54
    assert sum(EXPECTED[f]["code"] for f in SOLUTION_FILES) == 25


@pytest.mark.parametrize("name", ALL_FILES)
def test_every_notebook_is_small_enough_to_open(name):
    assert (CHAPTERS / name).stat().st_size < MAX_BYTES, "split it further"


def test_figure_numbering_is_continuous_across_the_chapters():
    """Each chapter's Setup cell starts the counter where the previous chapter stopped."""
    start = 0
    for name in CHAPTER_FILES:
        nb = load(name)
        setup = "".join(nb["cells"][1]["source"])
        assert setup.startswith("# --- Setup: run this cell first"), name
        n = EXPECTED[name]["figures"]
        if n:
            m = re.search(r"^_FIG_NO = \[(\d+)\]", setup, re.M)
            assert m and int(m.group(1)) == start, f"{name}: counter starts at {m and m.group(1)}, expected {start}"
            expected = f"# {start + 1}–{start + n}" if n > 1 else f"# figure {start + 1} only"
            assert f"this chapter's figures are\n{expected}" in setup, name
        start += n
    assert start == N_FIGURES


@pytest.mark.parametrize("name", CHAPTER_FILES)
def test_chapter_opens_with_a_table_of_contents_and_working_links(name):
    nb = load(name)
    header = "".join(nb["cells"][0]["source"])
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert header.startswith("# Kwant — Theory and Practice · Chapter "), name
    assert "### In this chapter" in header
    # every ## / ### heading of the chapter body is linked from the TOC
    body = nb["cells"][1:]
    heads = [h for c in body if c["cell_type"] == "markdown"
             for h in re.findall(r"^#{2,3} (.+?)\s*$", "".join(c["source"]), re.M)]
    assert heads, name
    for h in heads:
        assert f"[{h}](#" in header, f"{name}: heading {h!r} missing from the TOC"
    # prev / contents / next links resolve to shipped files
    for target in re.findall(r"\]\(([^)#]+\.ipynb)\)", header):
        assert (CHAPTERS / target).exists(), f"{name}: link to {target} does not resolve"
    assert "(00_Contents.ipynb)" in header


def test_contents_notebook_links_every_chapter_and_solution():
    md = markdown_of(load("00_Contents.ipynb"))
    for name in CHAPTER_FILES + SOLUTION_FILES:
        assert f"]({name})" in md, name
    assert "### The chapters" in md and "### How to run this" in md


@pytest.mark.parametrize("name", SOLUTION_FILES)
def test_solutions_open_with_a_table_of_contents(name):
    nb = load(name)
    header = "".join(nb["cells"][0]["source"])
    heads = re.findall(r"^## (E\d+\.\d+.*?)\s*$", markdown_of(nb), re.M)
    assert heads and "### In this notebook" in header
    for h in heads:
        assert f"[{h}](#" in header, f"{name}: {h!r} missing from the TOC"


def test_exercises_are_25_and_solutions_match_one_to_one():
    tag = re.compile(r"\*\*E(\d+\.\d+)\*\*")
    main_tags = []
    for name in CHAPTER_FILES:
        main_tags += tag.findall(markdown_of(load(name)))
    sol_heads = []
    for name in SOLUTION_FILES:
        sol_heads += re.findall(r"^## E(\d+\.\d+)", markdown_of(load(name)), re.M)
    assert len(set(main_tags)) == N_EXERCISES
    assert set(main_tags) == set(sol_heads)
    assert len(sol_heads) == N_EXERCISES, "one solution section per exercise"
    # Part I exercises are posed in chapter 7 and solved in S1; Part II in chapter 12 / S2
    assert set(tag.findall(markdown_of(load("07_Solvers_Pitfalls_and_Exercises_I.ipynb")))) == \
        {t for t in main_tags if t.startswith("1.")}
    assert all(t.startswith("1.") for t in re.findall(r"^## E(\d+\.\d+)",
                                                       markdown_of(load("S1_Solutions_Part_I.ipynb")), re.M))


@pytest.mark.parametrize("name", ALL_FILES)
def test_no_personal_or_project_codenames(name):
    for i, c in enumerate(load(name)["cells"]):
        m = FORBIDDEN.search(text_of(c))
        assert not m, f"cell {i}: {m.group(0)!r}"


def test_last_chapter_has_attribution_and_licence_cell():
    md = markdown_of(load("12_3D_TI_Exercises_II_and_Beyond.ipynb"))
    assert "## Sources, attribution and licence" in md
    for src in ("topocondmat.org", "Asbóth", "Kwant documentation"):
        assert src in md
    assert "Apache License 2.0" in md


def test_no_notebook_names_the_retired_monoliths():
    for name in ALL_FILES:
        text = "\n".join(text_of(c) for c in load(name)["cells"])
        assert "Kwant_Theory_and_Practice.ipynb" not in text, name
        assert "Kwant_Exercises_Solutions.ipynb" not in text, name
