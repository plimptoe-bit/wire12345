# Multi-tier BOM — ETHDTM-2025 rev B

Volumes planned (sets/week): [10.0, 30.0, 50.0, 75.0, 100.0] — includes [1.5, 2.0] upper limits. Scrap allowance 3% (assumption).

| L | Item | Description | Qty/parent | Qty/set | UoM | Origin | Consigned | Source |
|---|---|---|---|---|---|---|---|---|
| 0 | SET ETHDTM-2025 | harness set | 1 | 1 | set | structure | no | [unverified: no document] |
| 1 | &nbsp;&nbsp;D-1001 | Ethernet backbone jumper | 1 | 1 | ea | structure | no | [customer harness drawing: D-1001, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1001/S1 | segment ETH-BB: 2000 mm of PTA-ETH-2M (preterminated) | 1 | 1 | ea | structure | no | [customer harness drawing: D-1001, Rev B, sheet 1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PTA-ETH-2M | Factory-terminated shielded Ethernet assembly, 2 m, header both ends | 1 | 1 | ea | structure | no | [customer harness drawing: D-1001, Rev B, sheet 1] |
| 1 | &nbsp;&nbsp;D-1002 | Ethernet spur (cut assembly) | 2 | 2 | ea | structure | no | [customer harness drawing: D-1002, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1002/S1 | segment ETH-SPUR: 1000 mm of PTA-ETH-2M (cut_half) | 1 | 2 | ea | structure | no | [customer harness drawing: D-1002, Rev B, sheet 1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CONN-MAT-ECU | Shielded Ethernet ECU-side housing, 2-pos | 1 | 2 | ea | structure | no | [customer harness drawing: D-1002, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PTA-ETH-2M | Factory-terminated shielded Ethernet assembly, 2 m, header both ends | 0.5 | 1 | ea | structure | no | [customer harness drawing: D-1002, Rev B, sheet 1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-MAT-CONT | Ethernet data contact 0.13-0.35 mm2 for shielded header system | 2 | 4 | ea | structure | no | [customer harness drawing: D-1002, Rev B, wire table] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SHLD-BRL-01 | Shield shell barrel for Ethernet system [added — not on customer BOM] | 1 | 2 | ea | cascade | no | [application spec: SYN-APPSPEC-2001, Rev C, table 5 (component table)] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;FIXEL-01 | Fixation element (cable-to-header clip) [added — not on customer BOM] | 1 | 2 | ea | cascade | no | [application spec: SYN-APPSPEC-2001, Rev C, table 5 + fig 9] |
| 1 | &nbsp;&nbsp;D-1003 | Sensor jumper, 4-way small pitch | 1 | 1 | ea | structure | no | [customer harness drawing: D-1003, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1003/S1 | segment SENS1: 450 mm of W-FLRY-035 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1003/S2 | segment SENS2: 450 mm of W-FLRY-035 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1003/S3 | segment SENS3: 450 mm of W-M22 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CONN-NANO-4 | Unsealed 4-way small-pitch housing | 2 | 2 | ea | structure | no | [customer harness drawing: D-1003, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-FLRY-035 | Wire 0.35 mm2 thin-wall, 105 C | 0.9 | 0.9 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-M22 | Wire 0.34 mm2 (22 AWG), measured OD 1.73-1.78 mm, 105 C | 0.45 | 0.45 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-NANO-050 | Small-pitch F-crimp terminal 0.13-0.5 mm2, Sn, insulation 1.2-1.6 mm | 6 | 6 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;LBL-01 | Wrap-around wire label, printable | 1 | 1 | ea | structure | no | [customer harness drawing: D-1003, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TPA-NANO-4 | TPA / secondary lock for 4-way small-pitch housing [spec-required; present on customer BOM] | 2 | 2 | ea | cascade | no | [application spec: SYN-APPSPEC-1001, Rev B, sec 4.2] |
| 1 | &nbsp;&nbsp;D-1004 | Sealed power jumper | 1 | 1 | ea | structure | no | [customer harness drawing: D-1004, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1004/S1 | segment PWR: 600 mm of W-FLRY-096 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1004/S2 | segment GND: 600 mm of W-FLRY-096 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;HSG-DTM-2P | Sealed 2-way plug housing, size-16 | 1 | 1 | ea | structure | no | [customer harness drawing: D-1004, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;HSG-DTM-2S | Sealed 2-way receptacle housing, size-16 | 1 | 1 | ea | structure | no | [customer harness drawing: D-1004, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-FLRY-096 | Wire 0.96 mm2 (18 AWG) thin-wall, 105 C | 1.2 | 1.2 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-DTM-16 | Size-16 machined contact, closed barrel, 0.5-1.0 mm2 | 4 | 4 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;WEDGE-DTM-2 | Wedgelock, 2-way sealed housing [added — not on customer BOM] | 1 | 1 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;WEDGE-DTM-2 | Wedgelock, 2-way sealed housing [added — not on customer BOM] | 1 | 1 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.1] |
| 1 | &nbsp;&nbsp;D-1005 | I/O harness with branch | 1 | 1 | ea | structure | no | [customer harness drawing: D-1005, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1005/S1 | segment IO1: 1800 mm of W-FLRY-096 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1005/S2 | segment IO2: 700 mm of W-FLRY-050 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1005/S3 | segment IO3: 2200 mm of W-FLRY-096 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;HSG-GC-2 | Unsealed 2-way housing for GC receptacles | 1 | 1 | ea | structure | no | [customer harness drawing: D-1005, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CONN-NANO-4 | Unsealed 4-way small-pitch housing | 1 | 1 | ea | structure | no | [customer harness drawing: D-1005, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;HSG-DTM-2S | Sealed 2-way receptacle housing, size-16 | 1 | 1 | ea | structure | no | [customer harness drawing: D-1005, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-FLRY-096 | Wire 0.96 mm2 (18 AWG) thin-wall, 105 C | 4 | 4 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-FLRY-050 | Wire 0.50 mm2 thin-wall, 105 C | 0.7 | 0.7 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RCPT-GC-075 | Receptacle contact 0.5-0.75 mm2 | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-NANO-050 | Small-pitch F-crimp terminal 0.13-0.5 mm2, Sn, insulation 1.2-1.6 mm | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-DTM-16 | Size-16 machined contact, closed barrel, 0.5-1.0 mm2 | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TAPE-SW-01 | Spiral wrap 8 mm | 0.7 | 0.7 | m | structure | no | [customer harness drawing: D-1005, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;LBL-01 | Wrap-around wire label, printable | 1 | 1 | ea | structure | no | [customer harness drawing: D-1003, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TPA-NANO-4 | TPA / secondary lock for 4-way small-pitch housing [spec-required; present on customer BOM] | 1 | 1 | ea | cascade | no | [application spec: SYN-APPSPEC-1001, Rev B, sec 4.2] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;WEDGE-DTM-2 | Wedgelock, 2-way sealed housing [added — not on customer BOM] | 1 | 1 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PLUG-DTM-16 | Cavity plug, size-16 sealed system [added — not on customer BOM] | 1 | 1 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.4] |
| 1 | &nbsp;&nbsp;D-1006 | M12 sensor plug, 3 inserts | 1 | 1 | ea | structure | no | [customer harness drawing: D-1006, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1006/S1 | segment A1/A2: 800 mm of W-TWIN-22 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1006/S2 | segment B1/B2: 800 mm of W-TWIN-22 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1006/S3 | segment C1/C2: 800 mm of W-TWIN-22 (reel) | 1 | 1 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;INSERT-M12 | M12 insert module, 2 cavities | 3 | 3 | ea | structure | no | [customer harness drawing: D-1006, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-TWIN-22 | Twin wire 2 x 0.34 mm2, core OD 1.76 mm | 2.4 | 2.4 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-PIN-N22 | Machined solid pin, nickel plated | 6 | 6 | ea | structure | no | [unverified: no document] |
| 1 | &nbsp;&nbsp;D-1007 | Diagnostic pigtail | 2 | 2 | ea | structure | no | [customer harness drawing: D-1007, Rev B] |
| 2 | &nbsp;&nbsp;&nbsp;&nbsp;D-1007/S1 | segment DIAG: 300 mm of W-FLRY-050 (reel) | 1 | 2 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;HSG-DTM-2P | Sealed 2-way plug housing, size-16 | 1 | 2 | ea | structure | no | [customer harness drawing: D-1007, Rev B] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;W-FLRY-050 | Wire 0.50 mm2 thin-wall, 105 C | 0.3 | 0.6 | m | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TERM-DTM-16 | Size-16 machined contact, closed barrel, 0.5-1.0 mm2 | 1 | 2 | ea | structure | no | [unverified: no document] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;WEDGE-DTM-2 | Wedgelock, 2-way sealed housing [added — not on customer BOM] | 1 | 2 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.1] |
| 3 | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PLUG-DTM-16 | Cavity plug, size-16 sealed system [added — not on customer BOM] | 1 | 2 | ea | cascade | no | [application spec: SYN-APPSPEC-DTM, Rev D, sec 3.4] |
