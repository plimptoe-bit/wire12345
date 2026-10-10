# ETHDTM-2025 — management summary

Customer: ACME Mobility (SYNTHETIC FIXTURE — all part numbers, documents and prices are invented regression-test data, tagged rank 1-5 only to exercise the citation plumbing) · drawing rev B · 2025-11-03

**Volumes** are stated in the customer's unit (**sets/week**): planned [10, 30, 50], plus [1.5, 2.0] upper limits.

- Labor: **2.19 h per set** (manual; planning estimate ±25%).
- At the 100 sets/week upper limit: **219 h/week, 7 technician(s)**; second shift needed.
- Cost per set: **$193.05** at 100/wk to **$201.85** at 10/wk (budgetary ±30%).
- One-time (NRE + tooling): **$2,722.00**; equipment capital: $6,500.00.
- Margin at $410.00/set: **50.8%** at 10/wk; break-even 0.45 sets/week.
- Make vs buy: **make in-house** (quote AsiaHarness Co (fixture); gaps estimated and marked).
- Findings: **7 blockers** (customer answers needed), 16 warnings. See open-items register.

## Decisions needed
- **R001** BOM line L01 calls PTA-ETH-2M a connector ("Connector, automotive Ethernet, 4-pos header") but the manufacturer document shows it is a factory-terminated cable assembly — proposed default: Treat as a bought assembly (cut in half where the drawing uses one end); drop the loose contacts and bulk wire listed for it.
- **R002** BOM line L02 lists loose contacts TERM-NANO-ETH (family MATEnet-NanoMQS-SYN) but every MATEnet-NanoMQS-SYN termination on the program comes factory-terminated on PTA-ETH-2M — contacts are not needed — proposed default: Remove the contacts (and their wire) from the buy.
- **R012** TERM-NANO-ETH: customer BOM lists 4 per set but the harness structure consumes none — spares, error, or a second termination the drawing doesn't show — proposed default: Plan to the structure-derived count; confirm the difference with the customer before ordering.
- **R013** TERM-PIN-N22: customer BOM lists 2 per set, harness structure needs 6 — proposed default: Plan to the structure-derived count; confirm the difference with the customer before ordering.
- **F001** Wire W-M22 insulation OD 1.73–1.78 mm is outside terminal TERM-NANO-050 insulation range 1.2–1.6 mm — proposed default: Select the insulation-range variant of the same terminal (see variant suggestion finding).
- **F003** Conductor 0.96 mm² of W-FLRY-096 is outside terminal RCPT-GC-075 wire range 0.5–0.75 mm² — proposed default: Ask customer to substitute a terminal validated for 0.96 mm², or change the wire; do not build as drawn.
- **F004** Terminal TERM-PIN-N22 (Ni plating) is not validated for 0.34 mm² wire per its product spec; validated combinations: [{'plating': 'Au', 'wire_mm2_range': [0.2, 0.35]}, {'plating': 'Ni', 'wire_mm2_range': [0.5, 0.6]}] — proposed default: Use the plating variant the spec validates for this wire size (customer drawing change).

## Assumptions register (top)
- A-VOL: Volumes are in SETS per week (owner confirmed; lesson 8) [confirmed]
- A-RATES: Technician $38/h, loaded 1.6x, 32 productive h/week, 48 weeks/year [confirmed]
- A-SCRAP: 3% material scrap allowance at prototype volume [open]

Appendices: BOM (bom.csv), termination map, tooling list, production plan, cost workbook (costing.xlsx), procurement CSVs, formboards (per harness).
