# Harness architecture — confirm before any costing

Program: **ETHDTM-2025** rev B — volumes planned: [10, 30, 50] **sets/week** (plus upper limits [1.5, 2.0]); please confirm the unit.

## D-1001 rev B — Ethernet backbone jumper (x1 per set)
Dimension convention applied: *connector face to connector face*

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 ETH-BB | X1 (connector CONN-MAT-HDR) | pre-terminated assembly PTA-ETH-2M | both | 2000 ±10 mm | X2 (connector CONN-MAT-HDR) | preterminated |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (ECU A) | CONN-MAT-HDR | ? | T1:preterminated |
| X2 (ECU B) | CONN-MAT-HDR | ? | T2:preterminated |

## D-1002 rev B — Ethernet spur (cut assembly) (x2 per set)
Dimension convention applied: *connector face to connector face*

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 ETH-SPUR | X1 (connector CONN-MAT-HDR) | pre-terminated assembly PTA-ETH-2M | both | 1000 ±8 mm | X2 (connector CONN-MAT-ECU) | cut_half |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (spur plug (factory end)) | CONN-MAT-HDR | ? | T1:preterminated |
| X2 (ECU C (cut end)) | CONN-MAT-ECU | 1, 2 | T2:crimp_open_barrel, T3:crimp_open_barrel |

## D-1003 rev B — Sensor jumper, 4-way small pitch (x1 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 SENS1 | X1 (connector CONN-NANO-4) | W-FLRY-035: 0.35 mm², OD 1.4 mm | none | 450 ±5 mm | X2 (connector CONN-NANO-4) | reel |
| S2 SENS2 | X1 (connector CONN-NANO-4) | W-FLRY-035: 0.35 mm², OD 1.4 mm | none | 450 ±5 mm | X2 (connector CONN-NANO-4) | reel |
| S3 SENS3 | X1 (connector CONN-NANO-4) | W-M22: 0.34 mm², OD 1.755 mm | none | 450 ±5 mm | X2 (connector CONN-NANO-4) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (sensor side) | CONN-NANO-4 | 1, 2, 3 | T1:crimp_open_barrel, T2:crimp_open_barrel, T3:crimp_open_barrel |
| X2 (ECU side) | CONN-NANO-4 | 1, 2, 3 | T4:crimp_open_barrel, T5:crimp_open_barrel, T6:crimp_open_barrel |

## D-1004 rev B — Sealed power jumper (x1 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 PWR | X1 (connector HSG-DTM-2P) | W-FLRY-096: 0.96 mm², OD 2.1 mm | none | 600 ±8 mm | X2 (connector HSG-DTM-2S) | reel |
| S2 GND | X1 (connector HSG-DTM-2P) | W-FLRY-096: 0.96 mm², OD 2.1 mm | none | 600 ±8 mm | X2 (connector HSG-DTM-2S) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (battery) | HSG-DTM-2P | 1, 2 | T1:crimp_closed_barrel, T2:crimp_closed_barrel |
| X2 (load) | HSG-DTM-2S | 1, 2 | T3:crimp_closed_barrel, T4:crimp_closed_barrel |

## D-1005 rev B — I/O harness with branch (x1 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 IO1 | X1 (connector HSG-GC-2) | W-FLRY-096: 0.96 mm², OD 2.1 mm | none | 1800 ±10 mm | BR1 (breakout) | reel |
| S2 IO2 | BR1 (breakout) | W-FLRY-050: 0.5 mm², OD 1.45 mm | none | 700 ±8 mm | X2 (connector CONN-NANO-4) | reel |
| S3 IO3 | BR1 (breakout) | W-FLRY-096: 0.96 mm², OD 2.1 mm | none | 2200 ±10 mm | X3 (connector HSG-DTM-2S) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (controller) | HSG-GC-2 | 1 | T1:crimp_open_barrel |
| X2 (sensor) | CONN-NANO-4 | 1 | T2:crimp_open_barrel |
| X3 (actuator) | HSG-DTM-2S | 1 | T3:crimp_closed_barrel |

## D-1006 rev B — M12 sensor plug, 3 inserts (x1 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 A1/A2 | X1A (connector INSERT-M12) | W-TWIN-22: 0.34 mm², OD 1.76 mm | none | 800 ±10 mm | E1 (end) | reel |
| S2 B1/B2 | X1B (connector INSERT-M12) | W-TWIN-22: 0.34 mm², OD 1.76 mm | none | 800 ±10 mm | E2 (end) | reel |
| S3 C1/C2 | X1C (connector INSERT-M12) | W-TWIN-22: 0.34 mm², OD 1.76 mm | none | 800 ±10 mm | E3 (end) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1A (insert A) | INSERT-M12 | 1, 2 | T1:crimp_closed_barrel, T2:crimp_closed_barrel |
| X1B (insert B) | INSERT-M12 | 1, 2 | T3:crimp_closed_barrel, T4:crimp_closed_barrel |
| X1C (insert C) | INSERT-M12 | 1, 2 | T5:crimp_closed_barrel, T6:crimp_closed_barrel |

## D-1007 rev B — Diagnostic pigtail (x2 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 DIAG | X1 (connector HSG-DTM-2P) | W-FLRY-050: 0.5 mm², OD 1.45 mm | none | 300 ±5 mm | E1 (end) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (diag) | HSG-DTM-2P | 1 | T1:crimp_closed_barrel |

> **Checkpoint CONFIRM_ARCHITECTURE** — owner: reply with corrections or 'confirmed'. Most errors come from misreading what a called-out part actually is (lessons 1–2).
