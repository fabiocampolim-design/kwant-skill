# course/ — Quantum Transport with Kwant, the undergraduate course

Slides, a printable handout and lecturer notes for a course taught from the
chapter notebooks in `chapters/`. Everything is generated from one content
source and from the executed chapters; nothing here is drawn or written twice.

| What | Open | Source of truth |
|---|---|---|
| **Deck** (10 sections, 79 slides in one linear sequence, speaker notes on `S`) | `deck/index.html` | `deck/content_en.py` |
| **Deck as PDF** (landscape, one slide per page — the projector fallback) | `deck/slides.pdf` | generated with the deck |
| **Deck as one static page** (no JavaScript) | `deck/slides.html` | generated with the deck |
| **Handout** (A4, 7 sections: map, reference card, equations, models, pitfalls, running it, reading) | `handout/handout.html` · `handout/handout.pdf` | `handout/handout.md` |
| **Lecturer notes** (every slide's text + notes, in order) | `lecturer_notes.md` | generated from `deck/content_en.py` |
| **Figures** (all 68 of the course, numbered as in the chapters — the counter is continuous across them) | `figures/fig-NN.png` + `figures/figures.json` | extracted from the executed chapter notebooks |

## Presenting

Double-click `deck/index.html` — it runs offline (reveal.js is vendored under
`shared/`). The deck is **one linear sequence**: `→` / `←`, Space, a clicker,
or the two on-screen arrows move one slide at a time, and nothing else
intercepts the keys. There are no build animations — every slide arrives
complete. A generated opener starts each section: its name, its goal, and an
agenda coloured by what each slide is (grey plain language, green a figure,
blue Kwant code, pink the mathematics), in that order inside every section —
skip forward past the code or the maths and the thread survives.

- `S` — speaker notes (every slide's notes end with one anticipated audience
  question); `F` fullscreen; `B` blackout; `Esc` overview grid
- the slide counter (bottom right) and the progress bar keep the position

Every notebook figure is in the deck: the ones the story needs sit on the
authored slides, the rest follow on their own full-width pages, and each one
carries its complete notebook caption plus its section, chapter notebook and
cell. If reveal.js
misbehaves on a lecture-hall machine, present `deck/slides.pdf` instead — the
same slides, one per page.

Ten stops: Opening · From Schrödinger to a lattice · Leads and conductance ·
Shapes, potentials, parameters · Spin, graphene, superconductors · Magnetic
fields · Toolbox · Topology in one dimension · Topology in two and three
dimensions · Close. Stops 8–9 are Part II of the course (chapters 8–12) and
make a second lecture on their own.

## Rebuilding

```
python course/build_course.py [--outdir DIR] [--chapters DIR] [--skip-handout] [--quiet]
```

Extracts every `image/png` output of the twelve chapter notebooks, in course
order, into `figures/` (so a figure exists here only if a notebook cell
produced it), renders
`deck/index.html` + `deck/content.en.js`, `deck/slides.html`, `deck/slides.pdf`
(pandoc + xelatex) and `lecturer_notes.md` from `deck/content_en.py`, and
builds the handout with pandoc (+ xelatex for the PDF). `--skip-handout`
skips the pandoc/xelatex artefacts. Every artefact is read back before the
script reports success — including that all notebook figures appear exactly
once, each with a caption, and that the PDF carries its glyphs; the suite
(`tests/test_course.py`) repeats the readback on the committed files.
Re-execute a chapter first if you changed it (`AGENTS.md`, Commands).

Figures are referenced by their course number; `figures/figures.json` maps
each number to the chapter notebook and cell that made it, and its caption.

## Licence

Apache License 2.0, as the rest of the repository (`LICENSE`, `NOTICE`).
reveal.js (`shared/reveal/`) is © Hakim El Hattab and contributors, MIT
(`shared/reveal/LICENSE`). The content loader (`shared/loader.js`) is the
author's own, shared with the AILECTURE decks.
