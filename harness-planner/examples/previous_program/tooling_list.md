# Tooling list — ETHDTM-2025

Policy: a tool is compatible if it forms the crimp/joint to the spec's geometry and passes the spec's inspection and pull test. The manufacturer's named tool is the default, not a requirement, at this volume (owner policy, lesson 11).

## TERM-MAT-CONT — Ethernet data contact 0.13-0.35 mm2 for shielded header system
- Joint: crimp_open_barrel, form **F**, height 0.72±0.03 mm, width 0.9±0.03 mm — spec [application spec: SYN-APPSPEC-2001, Rev C, table 3]
- Used on: D-1002; 4 terminations/set; 400 cycles/week at max volume
- Spec's named tooling: TOOL-NANO-HAND [application spec: SYN-APPSPEC-2001, Rev C, table 3]
- Inventory match:
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): **within tolerance — qualify** — height 0.72±0.03 mm within achievable 0.55–1.1 mm; width 0.9 mm within tool range
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — required height 0.72 mm outside tool achievable 1.0–2.4 mm (tool datasheet vs [application spec: SYN-APPSPEC-2001, Rev C, table 3])
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — form mismatch: tool forms 'closed', spec requires 'F' [application spec: SYN-APPSPEC-2001, Rev C, table 3]
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): no — form mismatch: tool forms 'hex', spec requires 'F' [application spec: SYN-APPSPEC-2001, Rev C, table 3]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-HT-0640 (qualify): $243.20 one-time, 1.5 min/term (qualification 4.0 h loaded; height 0.72±0.03 mm within achievable 0.55–1.1 mm; width 0.9 mm within tool range) ← **cheapest compliant path**
  - buy named tool TOOL-NANO-HAND: $480.00 one-time, 1.5 min/term (budgetary price on file)
- Qualification required before production — see `qualification_TERM-MAT-CONT.md`
- ⚠ Restriction: FIX-HT-0640: repair and samples only per SYN-IS-411 Rev A — manufacturer guidance, to be waived or followed at owner's decision; risk: joint formed outside the vendor's stated use case, mitigated by the qualification protocol and first-piece checks

## TERM-NANO-050 — Small-pitch F-crimp terminal 0.13-0.5 mm2, Sn, insulation 1.2-1.6 mm
- Joint: crimp_open_barrel, form **F**, height 0.78±0.03 mm, width 0.95±0.03 mm, wire 0.35 mm² — spec [application spec: SYN-APPSPEC-1001, Rev B, table 2]
- Used on: D-1003, D-1005; 7 terminations/set; 700 cycles/week at max volume
- Spec's named tooling: TOOL-NANO-HAND [application spec: SYN-APPSPEC-1001, Rev B, table 2]
- Inventory match:
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): **exact** — vendor lists terminal family 'NanoMQS-SYN' for this tool (SYN-TD-0640 Rev B); wire 0.35 mm² in tool range 0.13–0.5 mm²; height 0.78±0.03 mm within achievable 0.55–1.1 mm; width 0.95 mm within tool range; insulation crimp within range
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — required height 0.78 mm outside tool achievable 1.0–2.4 mm (tool datasheet vs [application spec: SYN-APPSPEC-1001, Rev B, table 2])
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — form mismatch: tool forms 'closed', spec requires 'F' [application spec: SYN-APPSPEC-1001, Rev B, table 2]
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): no — form mismatch: tool forms 'hex', spec requires 'F' [application spec: SYN-APPSPEC-1001, Rev B, table 2]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-HT-0640 (exact): $0.00 one-time, 1.5 min/term (vendor lists terminal family 'NanoMQS-SYN' for this tool (SYN-TD-0640 Rev B); wire 0.35 mm² in tool range 0.13–0.5 mm²; height 0.78±0.03 mm within achievable 0.55–1.1 mm; width 0.95 mm within tool range; insulation crimp within range) ← **cheapest compliant path**
  - buy named tool TOOL-NANO-HAND: $480.00 one-time, 1.5 min/term (budgetary price on file)
- Qualification required before production — see `qualification_TERM-NANO-050.md`
- ⚠ Restriction: FIX-HT-0640: repair and samples only per SYN-IS-411 Rev A — manufacturer guidance, to be waived or followed at owner's decision; risk: joint formed outside the vendor's stated use case, mitigated by the qualification protocol and first-piece checks

## TERM-DTM-16 — Size-16 machined contact, closed barrel, 0.5-1.0 mm2
- Joint: crimp_closed_barrel, form **closed**, wire 0.96 mm² — spec [application spec: SYN-APPSPEC-DTM, Rev D, sec 2.3]
- Used on: D-1004, D-1005, D-1007; 7 terminations/set; 700 cycles/week at max volume
- Spec's named tooling: TOOL-DTM-HAND [application spec: SYN-APPSPEC-DTM, Rev D, sec 2.3]
- Inventory match:
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): **exact** — vendor lists terminal family 'DTM-16-SYN' for this tool (SYN-TD-4IND Rev C); wire 0.96 mm² in tool range 0.5–2.0 mm²; insulation crimp within range
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): no — form mismatch: tool forms 'F', spec requires 'closed' [application spec: SYN-APPSPEC-DTM, Rev D, sec 2.3]
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — form mismatch: tool forms 'F', spec requires 'closed' [application spec: SYN-APPSPEC-DTM, Rev D, sec 2.3]
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): no — form mismatch: tool forms 'hex', spec requires 'closed' [application spec: SYN-APPSPEC-DTM, Rev D, sec 2.3]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-4IND-16 (exact): $0.00 one-time, 1.5 min/term (vendor lists terminal family 'DTM-16-SYN' for this tool (SYN-TD-4IND Rev C); wire 0.96 mm² in tool range 0.5–2.0 mm²; insulation crimp within range) ← **cheapest compliant path**
  - buy named tool TOOL-DTM-HAND: $310.00 one-time, 1.5 min/term (budgetary price on file)
- Qualification required before production — see `qualification_TERM-DTM-16.md`

## RCPT-GC-075 — Receptacle contact 0.5-0.75 mm2
- Joint: crimp_open_barrel, form **F**, height 1.9±0.05 mm, width 2.1±0.05 mm, wire 0.96 mm² — spec [product spec / part drawing: SYN-PS-GC, Rev A, table 1]
- Used on: D-1005; 1 terminations/set; 100 cycles/week at max volume
- Spec's named tooling: TOOL-GC-HAND [product spec / part drawing: SYN-PS-GC, Rev A, table 1]
- Inventory match:
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): **within tolerance — qualify** — wire 0.96 mm² in tool range 0.35–2.5 mm²; height 1.9±0.05 mm within achievable 1.0–2.4 mm; width 2.1 mm within tool range; insulation crimp within range
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): no — wire 0.96 mm² outside tool range 0.13–0.5 mm²
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — form mismatch: tool forms 'closed', spec requires 'F' [product spec / part drawing: SYN-PS-GC, Rev A, table 1]
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): no — form mismatch: tool forms 'hex', spec requires 'F' [product spec / part drawing: SYN-PS-GC, Rev A, table 1]
- Paths (one-time cost + labor min/termination):
  - existing tool FIX-HT-F2 (qualify): $243.20 one-time, 1.5 min/term (qualification 4.0 h loaded; wire 0.96 mm² in tool range 0.35–2.5 mm²; height 1.9±0.05 mm within achievable 1.0–2.4 mm; width 2.1 mm within tool range; insulation crimp within range) ← **cheapest compliant path**
  - buy named tool TOOL-GC-HAND: $395.00 one-time, 1.5 min/term (budgetary price on file)
- Qualification required before production — see `qualification_RCPT-GC-075.md`

## TERM-PIN-N22 — Machined solid pin, nickel plated
- Joint: crimp_closed_barrel, form **closed**, wire 0.34 mm² — spec [product spec / part drawing: SYN-PS-M12, Rev A, table 4 (validated combinations)]
- Used on: D-1006; 6 terminations/set; 600 cycles/week at max volume
- Spec's named tooling: TOOL-M12-HAND [product spec / part drawing: SYN-PS-M12, Rev A, table 4 (validated combinations)]
- Inventory match:
  - FIX-HT-0640 (Hand crimp tool 0.13-0.5 mm2 F-crimp small pitch): no — form mismatch: tool forms 'F', spec requires 'closed' [product spec / part drawing: SYN-PS-M12, Rev A, table 4 (validated combinations)]
  - FIX-HT-F2 (Hand crimp tool 0.35-2.5 mm2 F-crimp general purpose): no — form mismatch: tool forms 'F', spec requires 'closed' [product spec / part drawing: SYN-PS-M12, Rev A, table 4 (validated combinations)]
  - FIX-4IND-16 (4-indent hand crimp for size-16 machined contacts): no — wire 0.34 mm² outside tool range 0.5–2.0 mm²
  - FIX-HEX-02 (Hex die crimp frame 2.5-6.5 mm hex): no — form mismatch: tool forms 'hex', spec requires 'closed' [product spec / part drawing: SYN-PS-M12, Rev A, table 4 (validated combinations)]
- Paths (one-time cost + labor min/termination):
  - buy named tool TOOL-M12-HAND: $290.00 one-time, 1.5 min/term (budgetary price on file) ← **cheapest compliant path**

## Tool inventory health (chosen tools)
- FIX-HT-0640: calibration due 2026-08-31 (interval 12 months)
- FIX-4IND-16: calibration due 2026-06-19 (interval 12 months)
- FIX-HT-F2: calibration due 2026-03-14 (interval 12 months)

Cycle-time values are planning estimates (assumption A-TOOL-T) until measured.
