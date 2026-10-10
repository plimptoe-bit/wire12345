# Harness architecture — confirm before any costing

Program: **GOLF-RF-2025** rev A — volumes planned: [5, 15] **sets/week** (plus upper limits [1.5, 2.0]); please confirm the unit.

## G-2001 rev A — RF jumper SMA-BNC (x1 per set)
Dimension convention applied: *connector reference plane to reference plane*

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 RF1 | X1 (connector SMA-STR-174) | C-RG174: 0.2 mm² | braid | 1200 ±10 mm | X2 (connector BNC-STR-58) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (radio) | SMA-STR-174 | ? | T1:crimp_hex |
| X2 (antenna) | BNC-STR-58 | ? | T2:crimp_hex |

## G-2002 rev A — Control pigtail, D-Sub solder (x1 per set)

| Segment | From (end A) | Conductor / construction | Shield | Length | To (end B) | Source |
|---|---|---|---|---|---|---|
| S1 C1 | X1 (connector DSUB-9S) | W-HOOK-22: 0.34 mm², OD 1.6 mm | none | 500 ±5 mm | E1 (end) | reel |
| S2 C2 | X1 (connector DSUB-9S) | W-HOOK-22: 0.34 mm², OD 1.6 mm | none | 500 ±5 mm | E2 (end) | reel |
| S3 C3 | X1 (connector DSUB-9S) | W-HOOK-22: 0.34 mm², OD 1.6 mm | none | 500 ±5 mm | E3 (end) | reel |

| Node | Housing | Cavities used | Terminations |
|---|---|---|---|
| X1 (controller) | DSUB-9S | 1, 2, 3 | T1:solder_cup, T2:solder_cup, T3:solder_cup |

> **Checkpoint CONFIRM_ARCHITECTURE** — owner: reply with corrections or 'confirmed'. Most errors come from misreading what a called-out part actually is (lessons 1–2).
