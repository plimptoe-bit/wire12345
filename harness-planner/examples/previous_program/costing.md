# Cost, make-vs-buy and margin — ETHDTM-2025

All prices budgetary (±30%) until quotes are in hand. Labor loading multiplier 1.6x; depreciation over 3 years; NRE amortized over the 52-week horizon.

## Cost per set at each volume (sets/week; labor mode: manual)
| Volume | Material | Labor (direct) | Labor (loaded) | Depreciation | NRE | Overhead | **Total/set** |
|---|---|---|---|---|---|---|---|
| 10 | $55.15 | $83.09 | $132.95 | $4.51 | $5.23 | $4.00 | **$201.85** |
| 30 | $55.13 | $83.09 | $132.95 | $1.50 | $1.74 | $4.00 | **$195.33** |
| 50 | $55.13 | $83.09 | $132.95 | $0.90 | $1.05 | $4.00 | **$194.03** |
| 75 | $55.13 | $83.09 | $132.95 | $0.60 | $0.70 | $4.00 | **$193.38** |
| 100 | $55.13 | $83.09 | $132.95 | $0.45 | $0.52 | $4.00 | **$193.05** |

Per-harness split of a set: {'D-1001': 1, 'D-1002': 2, 'D-1003': 1, 'D-1004': 1, 'D-1005': 1, 'D-1006': 1, 'D-1007': 2} — per-harness cost is the set cost split by harness labor minutes (appendix of the spreadsheet).

NRE one-time total: **$2,722.00**; equipment capital (buy now): $6,500.00.
- TERM-MAT-CONT: existing tool FIX-HT-0640 (qualify): $243.20
- RCPT-GC-075: existing tool FIX-HT-F2 (qualify): $243.20
- TERM-PIN-N22: buy named tool TOOL-M12-HAND: $290.00
- setup Harness continuity/hipot tester: $486.40
- formboards + first-article build (assumption A-NRE: 16 h): $972.80
- training (assumption A-TRAIN: 8 h): $486.40

## Man-hours
- One-time: 44.8 h
- Recurring: 2.19 h per set

## Make vs buy (quote: AsiaHarness Co (fixture))
Quoted $310.00/set — its line items extend to only $32.69, so the quoted price carries labor/overhead not itemized; reconcile before relying on it (lesson 10).
Quote does not cover 17 part(s) (FIXEL-01, HSG-DTM-2P, HSG-DTM-2S, HSG-GC-2, INSERT-M12, LBL-01, PLUG-DTM-16, RCPT-GC-075, SHLD-BRL-01, TAPE-SW-01, TERM-DTM-16, TERM-PIN-N22, TPA-NANO-4, W-FLRY-050, W-FLRY-096, W-TWIN-22, WEDGE-DTM-2) — gap estimated at $24.03/set and **marked as our estimate** (lesson 10). Quote covers Ethernet and sensor harnesses only; DTM/M12 parts excluded ('quoted separately on request').

| Volume | Make/set | Buy/set (incl. gap) | Weekly diff (buy−make) | Annual diff | Cheaper |
|---|---|---|---|---|---|
| 10 | $201.85 | $334.03 | $1,321.81 | $63,446.83 | make |
| 30 | $195.33 | $334.03 | $4,161.03 | $199,729.30 | make |
| 50 | $194.03 | $334.03 | $7,000.04 | $336,002.16 | make |
| 75 | $193.38 | $334.03 | $10,548.82 | $506,343.24 | make |
| 100 | $193.05 | $334.03 | $14,098.09 | $676,708.32 | make |

**Recommendation: make in-house.** In-house: ECO turnaround in days not weeks, quality ownership, no NCNR exposure on customer changes, capacity under our control; headcount and training are ours to carry. Outside: frees floor space and technicians, but FAI lead time on every revision and margin goes to the supplier.

## Margin at selling price $410.00/set
| Volume | Cost/set | GM/set | GM % | GM/year |
|---|---|---|---|---|
| 10 | $201.85 | $208.15 | 50.8% | $99,912.00 |
| 30 | $195.33 | $214.67 | 52.4% | $309,124.80 |
| 50 | $194.03 | $215.97 | 52.7% | $518,328.00 |
| 75 | $193.38 | $216.62 | 52.8% | $779,832.00 |
| 100 | $193.05 | $216.95 | 52.9% | $1,041,360.00 |

Break-even: **0.45 sets/week** against weekly fixed cost $97.49.

Sensitivity (at lowest planned volume):
| Case | Cost/set | GM % |
|---|---|---|
| base | $201.84 | 50.8% |
| material +15% | $210.11 | 48.8% |
| material −15% | $193.57 | 52.8% |
| time standards +25% | $235.08 | 42.7% |
| time standards −25% | $168.60 | 58.9% |
| labor rate +10% | $215.13 | 47.5% |
