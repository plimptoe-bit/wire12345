# Cost, make-vs-buy and margin — GOLF-RF-2025

All prices budgetary (±30%) until quotes are in hand. Labor loading multiplier 1.6x; depreciation over 3 years; NRE amortized over the 40-week horizon.

## Cost per set at each volume (sets/week; labor mode: manual)
| Volume | Material | Labor (direct) | Labor (loaded) | Depreciation | NRE | Overhead | **Total/set** |
|---|---|---|---|---|---|---|---|
| 5 | $8.01 | $21.34 | $34.15 | $3.61 | $10.93 | $2.00 | **$58.70** |
| 15 | $8.01 | $21.34 | $34.15 | $1.20 | $3.64 | $2.00 | **$49.01** |
| 22.5 | $8.01 | $21.34 | $34.15 | $0.80 | $2.43 | $2.00 | **$47.39** |
| 30 | $8.01 | $21.34 | $34.15 | $0.60 | $1.82 | $2.00 | **$46.58** |

Per-harness split of a set: {'G-2001': 1, 'G-2002': 1} — per-harness cost is the set cost split by harness labor minutes (appendix of the spreadsheet).

NRE one-time total: **$2,185.60**; equipment capital (buy now): $2,600.00.
- PIN-SMA-174: buy named tool TOOL-SMA-HEX: $240.00
- crimp_hex:BNC-STR-58: existing tool FIX-HEX-02 (qualify): $243.20
- setup 1-port VNA for RF test: $243.20
- formboards + first-article build (assumption A-NRE: 16 h): $972.80
- training (assumption A-TRAIN: 8 h): $486.40

## Man-hours
- One-time: 35.9 h
- Recurring: 0.56 h per set

## Margin at selling price $95.00/set
| Volume | Cost/set | GM/set | GM % | GM/year |
|---|---|---|---|---|
| 5 | $58.70 | $36.30 | 38.2% | $8,712.00 |
| 15 | $49.01 | $45.99 | 48.4% | $33,112.80 |
| 22.5 | $47.39 | $47.61 | 50.1% | $51,418.80 |
| 30 | $46.58 | $48.42 | 51.0% | $69,724.80 |

Break-even: **1.43 sets/week** against weekly fixed cost $72.70.

Sensitivity (at lowest planned volume):
| Case | Cost/set | GM % |
|---|---|---|
| base | $58.70 | 38.2% |
| material +15% | $59.90 | 37.0% |
| material −15% | $57.50 | 39.5% |
| time standards +25% | $67.24 | 29.2% |
| time standards −25% | $50.16 | 47.2% |
| labor rate +10% | $62.12 | 34.6% |
