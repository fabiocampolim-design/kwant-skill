# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# --- BUILD-HISTORY GUARD ------------------------------------------------------
# This script was a one-shot step (2026-09-01): it split the two monolithic
# notebooks (Kwant_Theory_and_Practice.ipynb, 7.4 MB, and
# Kwant_Exercises_Solutions.ipynb) into the chapter notebooks under chapters/.
# The monoliths were removed from the tree afterwards, so it cannot run again
# without them.  It is kept as the record of how the chapters were derived.
# To run it anyway, set KWANT_NB_REBUILD=1 in the environment.
import os as _os, sys as _sys
if _os.environ.get("KWANT_NB_REBUILD") != "1":
    _sys.exit(__file__ + ": already applied; set KWANT_NB_REBUILD=1 to re-run (see dev/build-history/README.md)")
# -----------------------------------------------------------------------------
"""Split the monolithic notebooks into chapters.

    python dev/build-history/split_chapters.py [--root DIR] [--outdir DIR]

Every chapter notebook gets: a header cell with the chapter's table of contents
and prev/contents/next links, one Setup cell (imports, warning filters, and the
figure helper whose counter CONTINUES the course-wide numbering, so figure N of
the course is figure N in every chapter, the deck and the manifest), and -- where
a chapter uses an object built in an earlier chapter -- one "carried over" cell
whose code is extracted verbatim from the defining cell of the monolith.  The
cells themselves are copied unchanged (outputs included; the caller re-executes
every chapter afterwards so that the committed outputs are the chapter's own).
"""
import argparse
import ast
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MAIN = "Kwant_Theory_and_Practice.ipynb"
SOL = "Kwant_Exercises_Solutions.ipynb"
CONTENTS = "00_Contents.ipynb"
SPDX = "`SPDX-License-Identifier: Apache-2.0` — Copyright 2026 Fabio Campolim."

# Chapter plan: cell ranges are inclusive indices into the monolith (checked
# against the section headings below before anything is written).
CHAPTERS = [
    dict(num=1, slug="Foundations", part="I", cells=(3, 13), first="## 1. Theory",
         title="Foundations — from the Schrödinger equation to a first conductance", carry=[]),
    dict(num=2, slug="Shapes_Spin_and_Bands", part="I", cells=(14, 21), first="## 5. Shapes",
         title="Shapes, spin and band structure", carry=[]),
    dict(num=3, slug="Graphene_and_Superconductivity", part="I", cells=(22, 27), first="## 8. Beyond",
         title="Graphene and superconductivity", carry=[]),
    dict(num=4, slug="Observables_and_Visualisation", part="I", cells=(28, 33), first="## 10. Local",
         title="Local observables and visualisation", carry=["rashba"]),
    dict(num=5, slug="KPM_and_Continuum", part="I", cells=(34, 41), first="## 12. The Kernel",
         title="Spectral densities by KPM and symbolic Hamiltonians with `kwant.continuum`", carry=[]),
    dict(num=6, slug="Magnetic_Fields", part="I", cells=(42, 45), first="## 14. Magnetic",
         title="Magnetic fields — Peierls substitution, Landau levels, the Hofstadter butterfly", carry=[]),
    dict(num=7, slug="Solvers_Pitfalls_and_Exercises_I", part="I", cells=(46, 50), first="## 15. Solvers",
         title="Solvers, performance, pitfalls — and the exercises for Part I", carry=["wire"]),
    dict(num=8, slug="Topology_in_One_Dimension", part="II", cells=(51, 62), first="# Part II",
         title="Topology in one dimension — SSH, Kitaev, the Majorana nanowire", carry=[]),
    dict(num=9, slug="Chern_Numbers", part="II", cells=(63, 70), first="## 20. The Thouless",
         title="Chern numbers — the Thouless pump and the Haldane model", carry=[]),
    dict(num=10, slug="Z2_and_Chiral_Superconductors", part="II", cells=(71, 75), first="## 22. The Kane",
         title="Z₂ and chiral superconductors — Kane–Mele and p+ip", carry=["chern", "bloch"]),
    dict(num=11, slug="Higher_Order_and_Weyl", part="II", cells=(76, 80), first="## 24. The BBH",
         title="Higher-order topology and Weyl semimetals", carry=["chern"]),
    dict(num=12, slug="3D_TI_Exercises_II_and_Beyond", part="II", cells=(81, 85), first="## 26. The 3D",
         title="The 3D topological insulator, the exercises for Part II, and where to go next", carry=[]),
]

SOLUTIONS = [
    dict(slug="S1_Solutions_Part_I", part="I", cells=(2, 22), chapter=7,
         title="Solutions to the exercises of Part I (E1.1–E1.11)"),
    dict(slug="S2_Solutions_Part_II", part="II", cells=(23, 49), chapter=12,
         title="Solutions to the exercises of Part II (E2.1–E2.14)"),
]

# Where each carried-over object is defined in the monolith and what to keep.
CARRY = {
    "wire": dict(cell=8, section=3, upto="make_wire", tail="fsyst = make_wire().finalized()",
                 what="the two-terminal quantum wire `fsyst` of § 3 (used by the parallel sweep)"),
    "rashba": dict(cell=18, section=6, upto="make_rashba", tail="fsyst_r = make_rashba().finalized()",
                   what="the Rashba + Zeeman wire `fsyst_r` of § 6 (the density and current maps are drawn on it)"),
    "chern": dict(cell=65, section=20, funcs=["chern_fhs"],
                  what="`chern_fhs`, the Fukui–Hatsugai–Suzuki Chern number of § 20"),
    "bloch": dict(cell=68, section=21, funcs=["bloch_hamiltonian"],
                  what="`bloch_hamiltonian`, the wraparound Bloch Hamiltonian of § 21"),
}

SETUP = '''# --- Setup: run this cell first ----------------------------------------------
# Imports, the sparse-solver report, three muted library warnings, and the
# figure helper.  Every chapter of the course starts with this cell.
import kwant
import numpy as np
import scipy
import tinyarray as ta                   # noqa: F401  (used by later cells)
import matplotlib
from matplotlib import pyplot

print("kwant", kwant.__version__, "| numpy", np.__version__,
      "| scipy", scipy.__version__, "| matplotlib", matplotlib.__version__)

# Which sparse solver is active? MUMPS is much faster than SciPy's SuperLU.
import kwant.solvers.default
print("default solver:", kwant.solvers.default.__name__)
try:
    import kwant.solvers.mumps          # noqa: F401
    print("MUMPS available: yes")
except ImportError:
    print("MUMPS available: no  (falling back to scipy sparse -> slower)")

matplotlib.rcParams['figure.figsize'] = (7, 5)

# Mute three library warnings that are not ours to fix and would otherwise be
# printed under some figures.  Done by wrapping warnings.showwarning rather than
# with warnings.filterwarnings(), because kwant.plotter calls
# warnings.resetwarnings() on every 3D plot, which silently deletes all user
# filters (reported upstream).  Only these three messages are muted:
#  * kwant 1.5.0's 3D plotter calls a matplotlib function deprecated in 3.10
#    (fixed on Kwant's main branch, unreleased);
#  * mpmath (via sympy) uses a deprecated bitcount helper;
#  * kwant.plotter.map notes that a few density values exceed the colour range,
#    which is expected for the delta-like densities in sections 6 and 12.
import warnings
_MUTED = ('proj_transform_clip', 'bitcount function is deprecated', 'overflowing upper limit')
_showwarning = warnings.showwarning

def _quiet_showwarning(message, category, filename, lineno, file=None, line=None):
    if not any(k in str(message) for k in _MUTED):
        _showwarning(message, category, filename, lineno, file, line)

warnings.showwarning = _quiet_showwarning

# --- Figure helper ------------------------------------------------------------
# Every figure ends with show_fig("..."), which stamps an auto-numbered italic
# caption under the figure and then shows it.  Figures are numbered
# continuously across the chapters of the course: this chapter's figures are
# {first}–{last}, so the counter starts at {start}.  (Re-running a single cell out of
# order advances it -- harmless, but numbers shift.)
_FIG_NO = [{start}]

def show_fig(caption=None):
    if caption:
        _FIG_NO[0] += 1
        fig = pyplot.gcf()
        fig.text(0.5, -0.02, f"Figure {{_FIG_NO[0]}}: {{caption}}",
                 ha='center', va='top', fontsize=9, style='italic',
                 wrap=True, transform=fig.transFigure)
    pyplot.show()
'''

SETUP_NOFIG = SETUP.split("# --- Figure helper")[0] + "print('setup done')\n"


def src_of(cell):
    return "".join(cell["source"])


def md_cell(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code_cell(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text}


def n_png(cell):
    return sum(1 for o in cell.get("outputs", []) if "image/png" in o.get("data", {}))


def anchor(heading):
    """Jupyter's heading anchor: the rendered text with spaces replaced by hyphens."""
    text = re.sub(r"[`*]", "", heading).strip()
    return text.replace(" ", "-")


def headings_of(cells):
    """[(level, text)] of the ##/### headings in a run of cells, in order."""
    out = []
    for c in cells:
        if c["cell_type"] != "markdown":
            continue
        for line in src_of(c).splitlines():
            m = re.match(r"^(#{1,3}) (.+?)\s*$", line)
            if m:
                out.append((len(m.group(1)), m.group(2)))
    return out


def carry_source(nb, key):
    spec = CARRY[key]
    src = src_of(nb["cells"][spec["cell"]])
    tree = ast.parse(src)
    parts = [f"# --- Carried over from section {spec['section']} -----------------------------------\n"
             f"# {spec['what']}.\n"
             f"# The code is the definition of section {spec['section']}, verbatim.\n"]
    if "upto" in spec:
        for node in tree.body:
            parts.append(ast.get_source_segment(src, node) + "\n")
            if isinstance(node, ast.FunctionDef) and node.name == spec["upto"]:
                break
        else:
            raise SystemExit(f"{key}: def {spec['upto']} not found in cell {spec['cell']}")
        parts.append("\n" + spec["tail"] + "\n")
    else:
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                parts.append(ast.get_source_segment(src, node) + "\n")
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in spec["funcs"]:
                parts.append("\n" + ast.get_source_segment(src, node) + "\n")
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        missing = set(spec["funcs"]) - names
        if missing:
            raise SystemExit(f"{key}: {missing} not found in cell {spec['cell']}")
        parts.append(f"\nprint({', '.join(spec['funcs'])!r}, 'ready')\n")
    return "".join(parts)


def fname(ch):
    return f"{ch['num']:02d}_{ch['slug']}.ipynb"


def nav(prev_name, next_name, prev_label, next_label):
    items = []
    if prev_name:
        items.append(f"[← {prev_label}]({prev_name})")
    items.append(f"[Contents]({CONTENTS})")
    if next_name:
        items.append(f"[{next_label} →]({next_name})")
    return " · ".join(items)


def chapter_header(ch, cells, first_fig, n_figs, prev_ch, next_ch, exercises):
    heads = headings_of(cells)
    toc = []
    for level, text in heads:
        if level == 1:
            toc.append(f"- **{text}**")
        elif level == 2:
            toc.append(f"- [{text}](#{anchor(text)})")
        else:
            toc.append(f"    - [{text}](#{anchor(text)})")
    if n_figs:
        figs = f"Figures {first_fig}–{first_fig + n_figs - 1}" if n_figs > 1 else f"Figure {first_fig}"
    else:
        figs = "no figures"
    secs = sorted({int(m.group(1)) for _, t in heads for m in [re.match(r"^(\d+)\.", t)] if m})
    sec_txt = f"Sections {secs[0]}–{secs[-1]}" if len(secs) > 1 else f"Section {secs[0]}"
    ex_line = ""
    if exercises:
        ex_line = (f"\n**Exercises** {exercises['tags']} are posed at the end of this chapter; "
                   f"the worked, asserted solutions are in "
                   f"[`{exercises['file']}`]({exercises['file']}).\n")
    prev_name = fname(prev_ch) if prev_ch else CONTENTS
    prev_label = f"Chapter {prev_ch['num']}" if prev_ch else "Contents"
    next_name = fname(next_ch) if next_ch else None
    next_label = f"Chapter {next_ch['num']}" if next_ch else ""
    links = nav(prev_name if prev_ch else None, next_name, prev_label, next_label)
    return (
        f"# Kwant — Theory and Practice · Chapter {ch['num']}\n"
        f"## {ch['title']}\n\n"
        f"*Part {ch['part']} · {sec_txt} · {figs}* &nbsp;·&nbsp; {links}\n\n"
        f"### In this chapter\n\n" + "\n".join(toc) + "\n" + ex_line +
        "\nRun the **Setup** cell first: it imports Kwant, reports the sparse solver, mutes three "
        "library warnings and defines `show_fig`, whose figure counter continues the course-wide "
        "numbering. Each chapter is self-contained given its Setup cell (a *carried over* cell, "
        "where present, rebuilds an object defined in an earlier chapter). Installation, the "
        f"`kwant` kernel and the conventions are in [`{CONTENTS}`]({CONTENTS}).\n\n"
        f"{SPDX}\n"
    )


def build_chapters(nb, outdir):
    cells = nb["cells"]
    fig_before = [0]
    for c in cells:
        fig_before.append(fig_before[-1] + (n_png(c) if c["cell_type"] == "code" else 0))
    written = []
    plan = []
    for i, ch in enumerate(CHAPTERS):
        lo, hi = ch["cells"]
        assert src_of(cells[lo]).lstrip("-\n ").startswith(ch["first"].lstrip("# ")) or \
            ch["first"] in src_of(cells[lo]), (ch["num"], src_of(cells[lo])[:60])
        if i:
            assert lo == CHAPTERS[i - 1]["cells"][1] + 1, ch["num"]
        body = copy.deepcopy(cells[lo:hi + 1])
        for c in body:                                   # the sources need retargeting
            s = src_of(c)
            s = s.replace("Worked solutions for every exercise are in the companion notebook\n"
                          "**`Kwant_Exercises_Solutions.ipynb`** (same folder).",
                          "Worked solutions for every exercise are in the companion notebook\n"
                          "**`S1_Solutions_Part_I.ipynb`** (same folder).")
            s = s.replace("Solutions in **`Kwant_Exercises_Solutions.ipynb`**.",
                          "Solutions in **`S2_Solutions_Part_II.ipynb`** (same folder).")
            s = s.replace("This notebook and its companion `Kwant_Exercises_Solutions.ipynb` are released",
                          "The chapter notebooks of this course and their two solutions notebooks are released")
            s = s.replace("*Sources: this notebook was written against",
                          "*Sources: these notebooks were written against")
            c["source"] = s
        first_fig = fig_before[lo] + 1
        n_figs = fig_before[hi + 1] - fig_before[lo]
        exercises = None
        if ch["num"] == 7:
            exercises = dict(tags="E1.1–E1.11", file="S1_Solutions_Part_I.ipynb")
        if ch["num"] == 12:
            exercises = dict(tags="E2.1–E2.14", file="S2_Solutions_Part_II.ipynb")
        prev_ch = CHAPTERS[i - 1] if i else None
        next_ch = CHAPTERS[i + 1] if i + 1 < len(CHAPTERS) else None
        header = md_cell(chapter_header(ch, body, first_fig, n_figs, prev_ch, next_ch, exercises))
        setup = code_cell((SETUP if n_figs else SETUP_NOFIG).format(
            first=first_fig, last=first_fig + n_figs - 1, start=first_fig - 1))
        carry = [code_cell(carry_source(nb, k)) for k in ch["carry"]]
        out = {"cells": [header, setup] + carry + body,
               "metadata": {**nb["metadata"], "title": f"Kwant - Theory and Practice - Chapter {ch['num']}: "
                            + re.sub(r"[`]", "", ch["title"])},
               "nbformat": nb["nbformat"], "nbformat_minor": nb["nbformat_minor"]}
        path = outdir / fname(ch)
        path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)
        plan.append(dict(num=ch["num"], file=fname(ch), title=ch["title"], part=ch["part"],
                         sections=sorted({int(m.group(1)) for _, t in headings_of(body)
                                          for m in [re.match(r"^(\d+)\.", t)] if m}),
                         first_fig=first_fig, n_figs=n_figs, n_cells=len(out["cells"]),
                         exercises=exercises["tags"] if exercises else ""))
    assert fig_before[-1] == sum(p["n_figs"] for p in plan)
    return written, plan


def contents_notebook(nb, plan, sol_plan, outdir):
    cell0 = src_of(nb["cells"][0])
    intro, rest = cell0.split("| § | Topic | Theory | API |", 1)
    table, howto = rest.split("---\n\n### How to run this", 1)
    intro = intro.replace("**A complete, self-contained course in one notebook: the physics, the numerics, and the API.**",
                          "**A complete, self-contained course in twelve chapter notebooks: the physics, the numerics, and the API.**")
    intro = intro.replace("This notebook is built against **Kwant 1.5** and is organised as alternating\n"
                          "**theory** and **runnable code**:",
                          "The course is built against **Kwant 1.5** and is organised as alternating **theory** and\n"
                          "**runnable code**. It is split into twelve chapter notebooks (each opens with its own table\n"
                          "of contents and a Setup cell, and is self-contained given that cell) plus two solutions\n"
                          "notebooks. Figures are numbered continuously across the chapters.\n\n"
                          "### The chapters\n\n"
                          "| Chapter | Notebook | Part | Sections | Figures | Exercises |\n|---|---|---|---|---|---|\n"
                          + "\n".join(
                              f"| {p['num']} | [{p['title']}]({p['file']}) | {p['part']} | "
                              + (f"{p['sections'][0]}–{p['sections'][-1]}" if len(p['sections']) > 1 else str(p['sections'][0])) + " | "
                              + (f"{p['first_fig']}–{p['first_fig'] + p['n_figs'] - 1}" if p['n_figs'] > 1
                                 else (str(p['first_fig']) if p['n_figs'] else "—"))
                              + f" | {p['exercises'] or '—'} |" for p in plan)
                          + "\n" + "\n".join(
                              f"| {s['slug'][:2]} | [{s['title']}]({s['slug']}.ipynb) | {s['part']} | — | "
                              f"{s['n_figs']} figures | {s['tags']} |" for s in sol_plan)
                          + "\n\n### The sections\n")
    table = ("| § | Topic | Theory | API |" + table.rstrip() + "\n"
             "| 17 | The SSH chain | winding number, Zak phase | `TranslationalSymmetry`, 1D leads |\n"
             "| 18 | The Kitaev chain | Majorana zero modes, BdG | `particle_hole` |\n"
             "| 19 | The Majorana nanowire | Kitaev physics in a real device | matrix hoppings, NS leads |\n"
             "| 20 | The Thouless pump | Chern number in $(k, t)$ | `wraparound`, FHS plaquettes |\n"
             "| 21 | The Haldane model | Chern insulator, Berry curvature | `HoppingKind` on sublattices |\n"
             "| 22 | The Kane–Mele model | $\\mathbb{Z}_2$, quantum spin Hall | spin Chern numbers |\n"
             "| 23 | The p+ip superconductor | chiral Majorana edges | BdG Chern number |\n"
             "| 24 | The BBH quadrupole | higher-order topology, nested Wilson loops | corner states |\n"
             "| 25 | Weyl semimetals | sliced Chern numbers, Fermi arcs | 3D lattices, slabs |\n"
             "| 26 | The 3D topological insulator | Fu–Kane parities, surface Dirac cone | 3D transport |\n"
             "| 27 | Where to go next | — | the rest of the API, ecosystem, reading |\n\n")
    howto = howto.replace("- *VS Code* — install the Microsoft **Python** and **Jupyter** extensions, open this file,",
                          "- *VS Code* — install the Microsoft **Python** and **Jupyter** extensions, open a chapter,")
    howto = howto.replace("Then: `Kernel → Restart & Run All`. The § 15 scaling cell takes a minute or two; everything\nelse is fast.",
                          "Then open a chapter and `Kernel → Restart & Run All`. The § 15 scaling cell (Chapter 7) takes a\n"
                          "minute or two; everything else is fast. The environment check below is the same one every\n"
                          "chapter's Setup cell performs.")
    header = intro + table + "---\n\n### How to run this" + howto.rstrip() + "\n\n" + SPDX + "\n"
    envcheck = code_cell(src_of(nb["cells"][1]))
    out = {"cells": [md_cell(header), envcheck],
           "metadata": {**nb["metadata"], "title": "Kwant - Theory and Practice - Contents"},
           "nbformat": nb["nbformat"], "nbformat_minor": nb["nbformat_minor"]}
    (outdir / CONTENTS).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def build_solutions(sol, outdir):
    cells = sol["cells"]
    preamble = src_of(cells[1])
    sol_plan = []
    for k, s in enumerate(SOLUTIONS):
        lo, hi = s["cells"]
        body = copy.deepcopy(cells[lo:hi + 1])
        heads = [t for lvl, t in headings_of(body) if lvl == 2]
        assert all(h.startswith(f"E{1 if s['part'] == 'I' else 2}.") for h in heads), heads
        tags = re.findall(r"^E(\d+\.\d+)", "\n".join(heads), re.M)
        toc = "\n".join(f"- [{h}](#{anchor(h)})" for h in heads)
        other = SOLUTIONS[1 - k]
        chapter = f"{s['chapter']:02d}_" + next(c["slug"] for c in CHAPTERS if c["num"] == s["chapter"]) + ".ipynb"
        header = (
            f"# Kwant — Theory and Practice · {s['title']}\n\n"
            f"*[Contents]({CONTENTS}) · exercises posed in [Chapter {s['chapter']}]({chapter}) · "
            f"the other solutions notebook: [`{other['slug']}.ipynb`]({other['slug']}.ipynb)*\n\n"
            f"Worked solutions for the exercises of Part {s['part']} (posed at the end of Chapter {s['chapter']}). "
            "Each solution is self-contained given the preamble cell below, restates the task in one line, "
            "flags the exercise's origin, and ends in at least one `assert` that encodes the expected physics. "
            "Difficulty: ◦ direct, • some thought, ★ mini-project.\n\n"
            f"### In this notebook\n\n{toc}\n\n"
            f"{SPDX}\n"
        )
        footer = md_cell(f"---\n*End of the Part {s['part']} solutions.  Solutions marked \"original\" were written\n"
                         "for this course; all others follow the flagged source.  If a solution\n"
                         "disagrees with your own, trust neither blindly: re-derive.*\n")
        out = {"cells": [md_cell(header), code_cell(preamble)] + body + [footer],
               "metadata": {**sol["metadata"], "title": f"Kwant - Theory and Practice - {s['title']}"},
               "nbformat": sol["nbformat"], "nbformat_minor": sol["nbformat_minor"]}
        (outdir / f"{s['slug']}.ipynb").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
        sol_plan.append(dict(slug=s["slug"], title=s["title"], part=s["part"], tags=f"E{tags[0]}–E{tags[-1]}",
                             n_figs=sum(n_png(c) for c in body if c["cell_type"] == "code"),
                             n_cells=len(out["cells"])))
    return sol_plan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT), help="directory holding the two monolithic notebooks")
    ap.add_argument("--outdir", default=str(ROOT / "chapters"))
    args = ap.parse_args()
    root, outdir = Path(args.root), Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    nb = json.loads((root / MAIN).read_text(encoding="utf-8"))
    sol = json.loads((root / SOL).read_text(encoding="utf-8"))
    assert len(nb["cells"]) == 86 and len(sol["cells"]) == 51, "not the 1.2.0 monoliths"
    written, plan = build_chapters(nb, outdir)
    sol_plan = build_solutions(sol, outdir)
    contents_notebook(nb, plan, sol_plan, outdir)
    for p in plan:
        print(f"ch{p['num']:02d} {p['file']:45s} sections {p['sections'][0]:>2}-{p['sections'][-1]:<2} "
              f"figs {p['first_fig']:>2}-{p['first_fig'] + p['n_figs'] - 1:<2} ({p['n_figs']:2d}) cells {p['n_cells']}")
    for s in sol_plan:
        print(f"     {s['slug'] + '.ipynb':45s} {s['tags']:14s} figs {s['n_figs']:2d} cells {s['n_cells']}")
    (outdir / "_split_plan.json").write_text(json.dumps({"chapters": plan, "solutions": sol_plan}, indent=1,
                                                        ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
