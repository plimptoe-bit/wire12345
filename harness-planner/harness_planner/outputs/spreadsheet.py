"""Costing workbook with live formulas (deliverable rule 10).

Inputs are blue, formulas black, assumptions documented on their own sheet.
Changing a blue cell (rate, price, minutes, volume) recomputes the workbook.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from ..model import ProgramData
from .costing import CostModel
from .planning import HarnessTimes, STATIONS, station_minutes_per_set

BLUE = Font(color="0000CC")
BOLD = Font(bold=True)
HDR_FILL = PatternFill("solid", fgColor="DDDDDD")


def _hdr(ws, row, values):
    for col, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=col, value=v)
        c.font = BOLD
        c.fill = HDR_FILL


def build_workbook(prog: ProgramData, cm: CostModel, times: list[HarnessTimes],
                   path: Path):
    r = prog.meta.rates
    wb = Workbook()

    # ---- Inputs -------------------------------------------------------- #
    ws = wb.active
    ws.title = "Inputs"
    ws["A1"] = ("INPUTS — blue cells are inputs; every other sheet computes "
                "from them. Prices budgetary ±30% until quoted.")
    ws["A1"].font = BOLD
    rows = [
        ("technician rate /h", r.technician_rate_per_hour),
        ("loaded multiplier", r.loaded_multiplier),
        ("productive hours /wk", r.productive_hours_per_week),
        ("weeks per year", r.weeks_per_year),
        ("depreciation years", r.depreciation_years),
        ("overhead per set", r.overhead_per_set),
        ("scrap fraction", r.scrap_fraction),
        ("horizon weeks", prog.meta.horizon_weeks),
        ("selling price per set", prog.meta.selling_price_per_set or 0),
        ("equipment capital (buy now)", cm.equipment_capital),
        ("NRE one-time total", cm.nre_one_time),
    ]
    for i, (label, val) in enumerate(rows, start=2):
        ws.cell(row=i, column=1, value=label)
        c = ws.cell(row=i, column=2, value=val)
        c.font = BLUE
    ws["A14"] = f"volumes ({prog.meta.volume_unit})"
    vols = prog.meta.planned_volumes()
    for i, v in enumerate(vols):
        c = ws.cell(row=15 + i, column=1, value=v)
        c.font = BLUE
    # fixed addresses used by formulas below
    A = {"rate": "Inputs!$B$2", "loaded": "Inputs!$B$3", "prod_h": "Inputs!$B$4",
         "wpy": "Inputs!$B$5", "dep": "Inputs!$B$6", "oh": "Inputs!$B$7",
         "scrap": "Inputs!$B$8", "horizon": "Inputs!$B$9", "price": "Inputs!$B$10",
         "capital": "Inputs!$B$11", "nre": "Inputs!$B$12"}

    # ---- BOM (material) ------------------------------------------------- #
    ws = wb.create_sheet("BOM")
    _hdr(ws, 1, ["MPN", "qty/set", "unit price", "note",
                 "ext/set (=qty*price*(1+scrap))"])
    row = 2
    for d in cm.material_detail:
        ws.cell(row=row, column=1, value=d["mpn"])
        q = ws.cell(row=row, column=2, value=d["qty_per_set"]); q.font = BLUE
        p = ws.cell(row=row, column=3, value=d["unit_price"]); p.font = BLUE
        ws.cell(row=row, column=4, value=d["note"])
        ws.cell(row=row, column=5,
                value=f"=IF(C{row}=\"\",0,B{row}*C{row}*(1+{A['scrap']}))")
        row += 1
    ws.cell(row=row, column=4, value="MATERIAL PER SET").font = BOLD
    ws.cell(row=row, column=5, value=f"=SUM(E2:E{row - 1})").font = BOLD
    mat_ref = f"BOM!$E${row}"

    # ---- Labor ----------------------------------------------------------- #
    ws = wb.create_sheet("Labor")
    _hdr(ws, 1, ["harness", "qty/set"] + [n for _, n in STATIONS]
         + ["min/harness (sum)", "min contributed/set"])
    row = 2
    ncols = len(STATIONS)
    for ht in times:
        ws.cell(row=row, column=1, value=ht.drawing_number)
        ws.cell(row=row, column=2, value=ht.qty_per_set).font = BLUE
        for j, (k, _) in enumerate(STATIONS):
            ws.cell(row=row, column=3 + j,
                    value=ht.manual.get(k, 0)).font = BLUE
        first = ws.cell(row=row, column=3).coordinate
        last = ws.cell(row=row, column=2 + ncols).coordinate
        ws.cell(row=row, column=3 + ncols, value=f"=SUM({first}:{last})")
        ws.cell(row=row, column=4 + ncols,
                value=f"=B{row}*{ws.cell(row=row, column=3 + ncols).coordinate}")
        row += 1
    ws.cell(row=row, column=3 + ncols, value="MIN PER SET").font = BOLD
    col = ws.cell(row=2, column=4 + ncols).column_letter
    ws.cell(row=row, column=4 + ncols,
            value=f"=SUM({col}2:{col}{row - 1})").font = BOLD
    min_ref = f"Labor!${col}${row}"
    ws.cell(row=row + 1, column=1,
            value="Station minutes are planning estimates (A-TIME) — overwrite "
                  "blue cells with measured values when available.")

    # ---- Cost per volume -------------------------------------------------- #
    ws = wb.create_sheet("Cost")
    _hdr(ws, 1, ["volume (sets/wk)", "material/set", "labor direct/set",
                 "labor loaded/set", "depreciation/set", "NRE/set",
                 "overhead/set", "TOTAL/set"])
    for i, v in enumerate(vols):
        row = 2 + i
        ws.cell(row=row, column=1, value=v).font = BLUE
        ws.cell(row=row, column=2, value=f"={mat_ref}")
        ws.cell(row=row, column=3, value=f"={min_ref}/60*{A['rate']}")
        ws.cell(row=row, column=4, value=f"=C{row}*{A['loaded']}")
        ws.cell(row=row, column=5,
                value=f"={A['capital']}/({A['dep']}*{A['wpy']})/A{row}")
        ws.cell(row=row, column=6, value=f"={A['nre']}/(A{row}*{A['horizon']})")
        ws.cell(row=row, column=7, value=f"={A['oh']}")
        ws.cell(row=row, column=8, value=f"=B{row}+D{row}+E{row}+F{row}+G{row}")
        ws.cell(row=row, column=8).font = BOLD
    n = len(vols)

    # ---- Capacity --------------------------------------------------------- #
    ws = wb.create_sheet("Capacity")
    _hdr(ws, 1, ["volume", "hours/week", "technicians (ceil)", "share of a "
                 "4-tech shift"])
    for i, v in enumerate(vols):
        row = 2 + i
        ws.cell(row=row, column=1, value=f"=Cost!A{row}")
        ws.cell(row=row, column=2, value=f"=A{row}*{min_ref}/60")
        ws.cell(row=row, column=3, value=f"=CEILING(B{row}/{A['prod_h']},1)")
        ws.cell(row=row, column=4, value=f"=C{row}/4")

    # ---- Make vs buy ------------------------------------------------------ #
    if prog.supplier_quote:
        ws = wb.create_sheet("MakeVsBuy")
        _hdr(ws, 1, ["volume", "make/set (=Cost)", "buy/set incl. gap",
                     "weekly diff (buy-make)", "annual diff"])
        quoted = prog.supplier_quote.get("quoted_per_set") or 0
        for i, v in enumerate(vols):
            row = 2 + i
            ws.cell(row=row, column=1, value=f"=Cost!A{row}")
            ws.cell(row=row, column=2, value=f"=Cost!H{row}")
            c = ws.cell(row=row, column=3, value=quoted); c.font = BLUE
            ws.cell(row=row, column=4, value=f"=(C{row}-B{row})*A{row}")
            ws.cell(row=row, column=5, value=f"=D{row}*{A['wpy']}")
        ws.cell(row=2 + n, column=1,
                value="buy/set is the quote plus our gap estimate — see the "
                      "make-vs-buy report; blue = overwrite with final quote")

    # ---- Margin ------------------------------------------------------------ #
    if prog.meta.selling_price_per_set is not None:
        ws = wb.create_sheet("Margin")
        _hdr(ws, 1, ["volume", "cost/set", "GM/set", "GM %", "GM/year"])
        for i, v in enumerate(vols):
            row = 2 + i
            ws.cell(row=row, column=1, value=f"=Cost!A{row}")
            ws.cell(row=row, column=2, value=f"=Cost!H{row}")
            ws.cell(row=row, column=3, value=f"={A['price']}-B{row}")
            ws.cell(row=row, column=4, value=f"=C{row}/{A['price']}")
            ws.cell(row=row, column=5, value=f"=C{row}*A{row}*{A['wpy']}")

    # ---- Assumptions -------------------------------------------------------- #
    ws = wb.create_sheet("Assumptions")
    _hdr(ws, 1, ["id", "assumption", "value", "impact", "status", "source"])
    row = 2
    for a in prog.assumptions:
        ws.cell(row=row, column=1, value=a.id)
        ws.cell(row=row, column=2, value=a.text)
        ws.cell(row=row, column=3, value=str(a.value) if a.value is not None else "")
        ws.cell(row=row, column=4, value=a.impact)
        ws.cell(row=row, column=5, value=a.status)
        ws.cell(row=row, column=6, value=a.source.short())
        row += 1
    builtins = [
        ("A-TIME", "station unit times are planning estimates until measured "
                   "(±25% carried in margin sensitivity)"),
        ("A-TOOL-T", "hand crimp 1.5 min, press 0.25 min, solder 3.0 min per "
                     "termination"),
        ("A-CAL", "external calibration 120/event"),
        ("A-FAI", "first article + qualification 2 weeks"),
        ("A-TRAIN", "training 1 week / 8 h"),
        ("A-SHIFT", "second shift above 4 technicians"),
        ("A-FB-SHIELD", "25 mm shield fold-back allowance on shielded ends"),
    ]
    for aid, txt in builtins:
        ws.cell(row=row, column=1, value=aid)
        ws.cell(row=row, column=2, value=txt)
        ws.cell(row=row, column=5, value="open")
        row += 1

    wb.save(path)
