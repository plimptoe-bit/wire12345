# Production plan — GOLF-RF-2025

## Line plan
Flow: incoming material → Cutting / stripping → Cable preparation (shield / coax prep) → Crimp / solder → Connector assembly → Layout / tape / label → Test / inspect / pack → ship. One-piece flow at prototype volume; a WIP buffer of one set between crimp and assembly; rework loops back to the failing station with a red tag and re-test.
Families on program: coax, solder. Floor space: one bench per station plus formboard tables (assumption A-FLOOR: ~6 m² per station).

## Time standards (planning estimates — assumption A-TIME, ±25% until measured)

| Harness | Family | Cutting / stripping | Cable preparation (shield / coax prep) | Crimp / solder | Connector assembly | Layout / tape / label | Test / inspect / pack | Total manual (min) | Total semi-auto (min) |
|---|---|---|---|---|---|---|---|---|---|
| G-2001 | coax | 0.8/0.25 | 3/3 | 3/0.5 | 2.3/2.3 | 2.4/2.4 | 2.2/2.2 | 13.7 | 10.7 |
| G-2002 | solder | 2.4/0.75 | 0/0 | 9/9 | 2/2 | 4.3/4.3 | 2.3/2.3 | 20.0 | 18.4 |

Minutes per **set**: 33.7 manual / 29.0 semi-auto (cells show manual/semi-auto).
Share of labor by station (manual): Crimp / solder 35.6%, Layout / tape / label 19.9%, Test / inspect / pack 13.4%, Connector assembly 12.8%, Cutting / stripping 9.5%, Cable preparation (shield / coax prep) 8.9%

## Capacity and labor
Productive hours: 32 h/wk per technician (program input); second shift above 4 technicians (assumption A-SHIFT).

| Volume (sets/week) | Hours/week (manual) | Technicians | Bottleneck | Second shift? |
|---|---|---|---|---|
| 5 | 2.8 | 1 | Crimp / solder (1.0 h/wk) | no |
| 15 | 8.4 | 1 | Crimp / solder (3.0 h/wk) | no |
| 22.5 | 12.6 | 1 | Crimp / solder (4.5 h/wk) | no |
| 30 | 16.9 | 1 | Crimp / solder (6.0 h/wk) | no |

## Equipment list
| Equipment | Cost low–high | Rate | Setup (h) | Changeover (min) | Service | Calib. cost/yr | Life (yr) | Phase | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 1-port VNA for RF test | $1,200.00–$4,000.00 | 20/h | 4 | 5 | annual | $300.00 | 8 | buy_now | return-loss test is a drawing requirement (G-2001) |

## Equipment trade-offs (payback in weeks)
No parameterized options on file.

## Lead time to first shipment
- Longest-lead material: SMA-STR-174 (5 wk)
- Tooling delivery: 4 wk
- First article + qualification: 2 wk (assumption A-FAI)
- Training: 1 wk (assumption A-TRAIN)
- **Critical path: 8 weeks** — FAI/qualification and training run after the longer of material and tooling arrival; values are assumptions until scheduled.

## Maintenance plan
| Tool | Class | Calib. interval (mo) | PM | Consumables | Spares | Certified by | Cycles/wk added | Cost/yr |
|---|---|---|---|---|---|---|---|---|
| FIX-HEX-02 | hex_die | 12.0 | clean + inspect dies weekly; lubricate per instruction sheet | n/a | — | external lab (crimp height gauge traceable) | 30.0 | $120.00 |
| FIX-SOLD-01 | solder_station | 6.0 | clean + inspect dies weekly; lubricate per instruction sheet | tips, flux, solder | — | external lab (crimp height gauge traceable) | 90.0 | $240.00 |

Calibration cost per event is assumption A-CAL ($120.00) until quoted.
