# Tooling list — GOLF-RF-2025

Policy: a tool is compatible if it forms the crimp/joint to the spec's geometry and passes the spec's inspection and pull test. The manufacturer's named tool is the default, not a requirement, at this volume (owner policy, lesson 11).

## PIN-SMA-174 — SMA center pin, crimp, RG174 group
- Joint: crimp_hex, form **hex**, hex 4.22 mm, wire 0.2 mm² — spec [application spec: SYN-SMA-174, Rev B, table 2]
- Used on: G-2001; 1 terminations/set; 30 cycles/week at max volume
- Spec's named tooling: TOOL-SMA-HEX [application spec: SYN-SMA-174, Rev B, table 2]
- Inventory match:
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): **within tolerance — qualify** — hex 4.22 mm within die range
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): no — form mismatch: tool forms 'F', spec requires 'hex' [application spec: SYN-SMA-174, Rev B, table 2]
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — form mismatch: tool forms 'F', spec requires 'hex' [application spec: SYN-SMA-174, Rev B, table 2]
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — form mismatch: tool forms 'closed', spec requires 'hex' [application spec: SYN-SMA-174, Rev B, table 2]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-HEX-02 (qualify): $243.20 one-time, 1.5 min/term (qualification 4.0 h loaded; hex 4.22 mm within die range)
  - buy named tool TOOL-SMA-HEX: $240.00 one-time, 1.5 min/term (budgetary price on file) ← **cheapest compliant path**

## crimp_hex:BNC-STR-58 — crimp_hex
- Joint: crimp_hex, form **hex**, hex 6.48 mm, wire 0.2 mm² — spec [unverified: no document]
- Used on: G-2001; 1 terminations/set; 30 cycles/week at max volume
- Spec's named tooling: none on file — pull the application spec tooling table [unverified: no document]
- Inventory match:
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): **within tolerance — qualify** — hex 6.48 mm within die range
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): no — form mismatch: tool forms 'F', spec requires 'hex' [unverified: no document]
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — form mismatch: tool forms 'F', spec requires 'hex' [unverified: no document]
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — form mismatch: tool forms 'closed', spec requires 'hex' [unverified: no document]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-HEX-02 (qualify): $243.20 one-time, 1.5 min/term (qualification 4.0 h loaded; hex 6.48 mm within die range) ← **cheapest compliant path**
- Qualification required before production — see `qualification_crimp_hex_BNC-STR-58.md`

## solder_cup:DSUB-9S — solder_cup
- Joint: solder_cup, form **solder**, wire 0.34 mm² — spec [unverified: no document]
- Used on: G-2002; 3 terminations/set; 90 cycles/week at max volume
- Spec's named tooling: none on file — pull the application spec tooling table [unverified: no document]
- Inventory match:
  - FIX-SOLD-01 (Temperature-controlled solder station 80 W with tips): **exact** — solder joint: FIX-SOLD-01 (Temperature-controlled solder station 80 W with tips) — tip/iron selection per joint size; no crimp geometry applies
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-SOLD-01 (exact): $0.00 one-time, 3 min/term (solder joint: FIX-SOLD-01 (Temperature-controlled solder station 80 W with tips) — tip/iron selection per joint size; no crimp geometry applies) ← **cheapest compliant path**

## Tool inventory health (chosen tools)
- FIX-HEX-02: calibration due 2026-07-01 (interval 12 months)
- FIX-SOLD-01: calibration due 2026-02-10 (interval 6 months)

Cycle-time values are planning estimates (assumption A-TOOL-T) until measured.
