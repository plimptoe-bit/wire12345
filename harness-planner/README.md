# harness-planner

A planning tool for a contract wire-harness shop. It takes a customer
engineering package for a new harness program and produces everything needed
to decide whether to build it and to execute: a reconciled multi-tier BOM, a
termination map, a tooling list reconciled against our tool inventory, a line
plan with labor and capacity by volume, lead time, cost per unit, make-vs-buy
with margin, a maintenance plan, a ready-to-order procurement list, and
to-scale formboard drawings — all generated from one structured data model,
with every number traceable to a cited source.

## Clickable interface (no terminal needed)

Two ways in, both styled like a Windows 98 application:

- **Just looking?** Open `HarnessPlanner98.html` in any browser (double-click
  it). It is fully self-contained — the two example programs' deliverables,
  findings and formboards are packed inside. No install.
- **Working?** Double-click `Start Harness Planner.bat` (Windows) or
  `start-harness-planner.command` (Mac/Linux). It starts the live app at
  `http://127.0.0.1:8321` with every button wired to the real engine: run
  checks, confirm checkpoints, generate fresh deliverables, save files.
  Needs Python 3.11+ (python.org, tick "Add to PATH"). Equivalent CLI:
  `python3 -m harness_planner gui`.

The live app scans the directories you give it (default: `data/fixtures` and
the current directory) for folders containing a `program.json`. Rebuild the
standalone demo after changing examples with `python3 tools/build_demo.py`.

## Quickstart (CLI)

```bash
cd harness-planner
python3 -m pytest tests/ -q                       # regression suite

# run mode, step by step:
python3 -m harness_planner ingest   data/fixtures/previous_program
python3 -m harness_planner check    data/fixtures/previous_program
python3 -m harness_planner confirm  data/fixtures/previous_program CONFIRM_ARCHITECTURE --by "owner"
python3 -m harness_planner confirm  data/fixtures/previous_program CONFIRM_VOLUME_UNITS --by "owner"
python3 -m harness_planner generate data/fixtures/previous_program --out out/
```

Pre-generated deliverables for both sample programs are committed under
`examples/` (the previous automotive-Ethernet + sealed-connector program, 7
harnesses, 10–50 sets/week; and a synthetic solder/coax program, 2 harnesses).

Dependencies: Python 3.11+, `jsonschema`, `openpyxl`, `reportlab`; optional
`cairosvg` (formboard PDFs) and poppler (`pdftoppm`/`pdftotext`, package
ingestion). `pip install jsonschema openpyxl reportlab cairosvg pytest`.

## How it maps to the build-mode checklist

1. **Data model** — `harness_planner/model.py` +
   `harness_planner/schema/program.schema.json`. One JSON file per program:
   Program, Harness, Segment, Termination, Part, process/equipment records,
   assumptions, open items. Every record carries a `Citation`
   (rank 1 application spec → rank 6 unverified; see
   `harness_planner/sources.py`). The two-harness example filled from a sample
   program is `data/fixtures/golf_coax/program.json`.
2. **Ingestion pipeline** — `harness_planner/ingest/`. File inventory (type,
   pages, text layer, revision flags) → rasterize PDFs for visual reading →
   architecture table *generated back from the data model* for owner
   confirmation → findings. Human-confirmation checkpoints
   (`checkpoints.json`) gate the outputs: **no costing without
   CONFIRM_ARCHITECTURE + CONFIRM_VOLUME_UNITS, no procurement without
   RESOLVE_BLOCKERS, no formboard release without VALIDATE_FIRST_BOARD** —
   boards print with a DRAFT note until then.
3. **Rules engine** — `harness_planner/rules/`:
   `compatibility.py` (wire range, plating validation, insulation OD and
   variant suggestion, seal range, shield construction, contact family, coax
   cable group, solder cup/temperature, MOQ), `cascade.py` (spec-required
   accessories the drawing omits, marked “added — not on customer BOM” with
   the spec citation), `reconcile.py` (pre-terminated-assembly detection,
   cavity fill counts, BOM vs structure quantities), `tooling.py` (inventory
   match ranked exact / within tolerance — qualify / no, with evidence;
   cheapest compliant path per volume; qualification protocol generator;
   restrictions surfaced as guidance, not hard stops; calibration/cycle-life
   flags). Every finding carries document + revision + clause.
4. **Tool inventory** — `data/tool_inventory.csv` (template + current state;
   columns in `harness_planner/inventory.py`). Run-mode upkeep:
   `python3 -m harness_planner update-cycles <program> --weeks 1`, plus
   `Inventory.add()` / `set_certified()` for purchases and calibrations. The
   CSV lives in git so changes are reviewable.
5. **Generators** — `harness_planner/outputs/`: multi-tier BOM (CSV + md),
   termination map, tooling list + qualification sheets, production plan
   (line plan, time standards, capacity/labor, equipment list, trade-offs
   with payback, lead time, maintenance), costing (cost per set by volume,
   make-vs-buy with quote-gap estimation, margin with break-even and
   sensitivity, man-hours), `costing.xlsx` with **live formulas** (inputs
   blue, formulas black, assumptions sheet), management summary (md + PDF),
   procurement (ordering table + Octopart/DigiKey/Mouser import CSVs; no
   fabricated URLs — unverified links say “URL not verified”), and formboards
   (true-scale SVG + PDF with pegs, nests, cavity maps, tape/label call-outs,
   folds with keep-outs, inspection box, revision block, scale bar and
   registration marks; peg coordinate CSV; cut list with per-end allowances
   and their basis; build sequence).
6. **Test run** — `tests/` runs both fixture programs end to end. The Part 7
   lessons are regression checks (`tests/test_regression_lessons.py`): the
   pre-terminated assembly called out as a connector, the spec-cascaded shield
   barrel + fixation element missing from the BOM, the 2-vs-6 contact count,
   the 0.96 mm² wire in a 0.5–0.75 mm² receptacle, the nickel pin not
   validated for 0.34 mm², the insulation-OD variant selection, and the
   “repair and samples only” tool restriction surfaced as a waivable warning
   while the tool remains the cheapest compliant path.

**All fixture data is synthetic.** Part numbers, documents and prices under
`data/fixtures/` are invented to exercise the machinery; their citations
exist to test the plumbing, not to assert facts. In run mode, real programs
must cite real documents fetched per the source-of-truth hierarchy, and
nothing rank-6 (“unverified”) may settle a part number, dimension or price.

## Run-mode procedure (per program)

1. Put the customer package in `<program>/package/` and create
   `<program>/program.json` (start from a fixture). Run `ingest`: review the
   file inventory, read the rasterized drawings, fill the data model.
2. Review `work/03_architecture_table.md` with the owner — segment by
   segment, what is at each end — and confirm `CONFIRM_ARCHITECTURE` and
   `CONFIRM_VOLUME_UNITS` (sets vs harnesses!).
3. Run `check`; take the blocker findings to the customer in one batch, each
   with impact and a proposed default. Record answers in `open_items`, then
   confirm `RESOLVE_BLOCKERS`.
4. Run `generate`. Build one harness on the printed DRAFT overlay, measure it
   against the customer drawing, then confirm `VALIDATE_FIRST_BOARD` and
   regenerate to release the boards.
5. Weekly: `update-cycles` to keep the tool inventory current. On a design
   revision: update `program.json`, reset the affected checkpoints
   (`Checkpoints.reset`), and regenerate — the BOM, boards, cut lists and
   travellers move together because they come from the same model.

## Known limitations (v1)

- Drawing reading is not automated: the pipeline rasterizes and inventories
  the package, and the analyst (human or agent) enters what the drawings say
  into the data model; the architecture table then round-trips it for
  confirmation.
- A spec-cascaded part (e.g. a shield barrel the drawing omitted) enters the
  BOM and findings, but its *termination* is only added to the model after
  the owner confirms — so its tooling appears on the next `check` run.
- Formboard branch routing alternates sides at 90°/45° defaults when the
  drawing gives no angles; collision avoidance is minimal. Fold placement
  avoids tape/label keep-outs but complex boards deserve a manual look —
  which the VALIDATE_FIRST_BOARD checkpoint enforces anyway.
- Distributor cart building is CSV-import only; API integration (DigiKey,
  Mouser, Nexar) is stubbed out until keys are configured.
