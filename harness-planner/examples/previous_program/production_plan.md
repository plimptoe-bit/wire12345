# Production plan — ETHDTM-2025

## Line plan
Flow: incoming material → Cutting / stripping → Cable preparation (shield / coax prep) → Crimp / solder → Connector assembly → Layout / tape / label → Test / inspect / pack → ship. One-piece flow at prototype volume; a WIP buffer of one set between crimp and assembly; rework loops back to the failing station with a red tag and re-test.
Families on program: ethernet, io, power, sensor. Floor space: one bench per station plus formboard tables (assumption A-FLOOR: ~6 m² per station).

## Time standards (planning estimates — assumption A-TIME, ±25% until measured)

| Harness | Family | Cutting / stripping | Cable preparation (shield / coax prep) | Crimp / solder | Connector assembly | Layout / tape / label | Test / inspect / pack | Total manual (min) | Total semi-auto (min) |
|---|---|---|---|---|---|---|---|---|---|
| D-1001 | ethernet | 0/0 | 0/0 | 0/0 | 1/1 | 4/4 | 2/2 | 7.0 | 7.0 |
| D-1002 | ethernet | 0/0 | 2.5/2.5 | 3/0.5 | 2/2 | 2/2 | 5.2/5.2 | 14.7 | 12.2 |
| D-1003 | sensor | 2.4/0.75 | 0/0 | 9/1.5 | 4/4 | 3.2/3.2 | 2.6/2.6 | 21.2 | 12.1 |
| D-1004 | power | 1.6/0.5 | 0/0 | 6/1 | 3/3 | 2.4/2.4 | 2.4/2.4 | 15.4 | 9.3 |
| D-1005 | io | 2.4/0.75 | 0/0 | 4.5/0.75 | 3/3 | 10.7/10.7 | 2.3/2.3 | 22.9 | 17.5 |
| D-1006 | sensor | 2.4/0.75 | 0/0 | 9/1.5 | 4.5/4.5 | 4.8/4.8 | 2.6/2.6 | 23.3 | 14.2 |
| D-1007 | power | 0.8/0.25 | 0/0 | 1.5/0.25 | 1/1 | 0.6/0.6 | 2.1/2.1 | 6.0 | 4.2 |

Minutes per **set**: 131.2 manual / 92.8 semi-auto (cells show manual/semi-auto).
Share of labor by station (manual): Crimp / solder 28.6%, Layout / tape / label 23.1%, Test / inspect / pack 20.2%, Connector assembly 16.4%, Cutting / stripping 7.9%, Cable preparation (shield / coax prep) 3.8%

## Capacity and labor
Productive hours: 32 h/wk per technician (program input); second shift above 4 technicians (assumption A-SHIFT).

| Volume (sets/week) | Hours/week (manual) | Technicians | Bottleneck | Second shift? |
|---|---|---|---|---|
| 10 | 21.9 | 1 | Crimp / solder (6.2 h/wk) | no |
| 30 | 65.6 | 3 | Crimp / solder (18.8 h/wk) | no |
| 50 | 109.3 | 4 | Crimp / solder (31.2 h/wk) | no |
| 75 | 164.0 | 6 | Crimp / solder (46.9 h/wk) | YES |
| 100 | 218.7 | 7 | Crimp / solder (62.5 h/wk) | YES |

## Equipment list
| Equipment | Cost low–high | Rate | Setup (h) | Changeover (min) | Service | Calib. cost/yr | Life (yr) | Phase | Reason |
|---|---|---|---|---|---|---|---|---|---|
| Harness continuity/hipot tester | $4,000.00–$9,000.00 | 30/h | 8 | 10 | annual | $250.00 | 8 | buy_now | 500 V insulation test is a drawing requirement (D-1004) |
| Benchtop cut & strip machine | $8,000.00–$15,000.00 | 500/h | 16 | 5 | annual | $150.00 | 8 | at_volume | payback only above ~50 sets/week |
| Applicators for bench press (reel feed) | $7,000.00–$12,000.00 | 1200/h | 24 | 15 | 100k cycles | $200.00 | 10 | optional | hand tools qualified for prototype volume; revisit at 75+ sets/week |

## Equipment trade-offs (payback in weeks)
| Option | Cost (mid) | Min saved/set | @10 | @30 | @50 | @75 | @100 | Pays back in horizon at |
|---|---|---|---|---|---|---|---|---|
| Benchtop cut & strip machine | $11,500.00 | 7.28 | 155.9 | 52.0 | 31.2 | 20.8 | 15.6 | 30 sets/week |
| Applicators for bench press (reel feed) | $9,500.00 | 22.5 | 41.7 | 13.9 | 8.3 | 5.6 | 4.2 | 10 sets/week |

## Lead time to first shipment
- Longest-lead material: PTA-ETH-2M (10 wk)
- Tooling delivery: 6 wk
- First article + qualification: 2 wk (assumption A-FAI)
- Training: 1 wk (assumption A-TRAIN)
- **Critical path: 13 weeks** — FAI/qualification and training run after the longer of material and tooling arrival; values are assumptions until scheduled.

## Maintenance plan
| Tool | Class | Calib. interval (mo) | PM | Consumables | Spares | Certified by | Cycles/wk added | Cost/yr |
|---|---|---|---|---|---|---|---|---|
| FIX-4IND-16 | hand_crimp | 12.0 | clean + inspect dies weekly; lubricate per instruction sheet | n/a | die set / nest | external lab (crimp height gauge traceable) | 700.0 | $120.00 |
| FIX-HT-0640 | hand_crimp | 12.0 | clean + inspect dies weekly; lubricate per instruction sheet | n/a | die set / nest | external lab (crimp height gauge traceable) | 1100.0 | $120.00 |
| FIX-HT-F2 | hand_crimp | 12.0 | clean + inspect dies weekly; lubricate per instruction sheet | n/a | die set / nest | external lab (crimp height gauge traceable) | 100.0 | $120.00 |

Calibration cost per event is assumption A-CAL ($120.00) until quoted.
