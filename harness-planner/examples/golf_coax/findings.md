# Findings

| ID | Severity | Harness | Ref | Finding | Source | Proposed default |
|---|---|---|---|---|---|---|
| F001 | BLOCKER | G-2001 | T2 | Coax cable C-RG174 (group RG174) is not in connector BNC-STR-58 cable groups ['RG58'] | [product spec / part drawing: SYN-BNC-58, Rev A, table 1]; [product spec / part drawing: SYN-CD-RG174, Rev A, table 1] | Select the connector variant for this cable group. |
| F002 | BLOCKER | G-2002 | T1,T2,T3 | Wire W-HOOK-22 insulation rated 80 °C is below the 105 °C minimum for soldering to DSUB-9S | [product spec / part drawing: SYN-DSUB-9, Rev C, sec 4 (solder requirements)]; [product spec / part drawing: SYN-WD-HOOK, Rev A, table 1] | Use higher-temperature insulation or crimp variant. |
| R002 | WARNING | — | G09 | BOM line G09 'tape, see drawing' (tape, see drawing) does not resolve to a known part — placeholder or typo | [customer harness drawing: customer BOM (Golf), rev A] | Ask customer for the exact MPN; carry as consumable allowance meanwhile. |
| F005 | INFO | — | BNC-STR-58 | BNC-STR-58: MOQ 10000 ea is more than 4x the horizon need of 1200 ea — excess stock / NCNR risk | [product spec / part drawing: SYN-BNC-58, Rev A, table 1] | Quote broker/cut-tape options or ask customer to consign. |
| T001 | INFO | — | crimp_hex:BNC-STR-58 | crimp_hex:BNC-STR-58: chosen path 'existing tool FIX-HEX-02 (qualify)' uses a non-named tool — run the qualification protocol before production | [unverified: no document] | Schedule qualification during first-article build. |
| R001 | INFO | G-2002 | X1 | 6 empty cavities at X1 (DSUB-9S); no blind-plug rule found in the spec extract | [product spec / part drawing: SYN-DSUB-9, Rev C, sec 4 (solder requirements)] | Check the application spec for cavity plugs. |
