# GOLF-RF-2025 — management summary

Customer: Golf Instruments (SYNTHETIC FIXTURE — solder/coax sample; all part numbers, documents and prices invented) · drawing rev A · 2025-12-01

**Volumes** are stated in the customer's unit (**sets/week**): planned [5, 15], plus [1.5, 2.0] upper limits.

- Labor: **0.56 h per set** (manual; planning estimate ±25%).
- At the 30 sets/week upper limit: **17 h/week, 1 technician(s)**.
- Cost per set: **$46.58** at 30/wk to **$58.70** at 5/wk (budgetary ±30%).
- One-time (NRE + tooling): **$2,185.60**; equipment capital: $2,600.00.
- Margin at $95.00/set: **38.2%** at 5/wk; break-even 1.43 sets/week.
- Findings: **2 blockers** (customer answers needed), 1 warnings. See open-items register.

## Decisions needed
- **F001** Coax cable C-RG174 (group RG174) is not in connector BNC-STR-58 cable groups ['RG58'] — proposed default: Select the connector variant for this cable group.
- **F002** Wire W-HOOK-22 insulation rated 80 °C is below the 105 °C minimum for soldering to DSUB-9S — proposed default: Use higher-temperature insulation or crimp variant.

## Assumptions register (top)
- A-VOL-G: Volumes are in SETS per week [confirmed]
- A-SOLDER: Hand solder, SAC305, iron 370 C; class 2 workmanship [open]

Appendices: BOM (bom.csv), termination map, tooling list, production plan, cost workbook (costing.xlsx), procurement CSVs, formboards (per harness).
