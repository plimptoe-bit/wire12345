"""Unit helpers: AWG <-> mm2, formatting."""

# Nominal conductor cross sections (mm2) per AWG, stranded-wire convention.
AWG_TO_MM2 = {
    30: 0.05, 28: 0.08, 26: 0.13, 24: 0.22, 22: 0.34, 20: 0.5,
    18: 0.96, 16: 1.31, 14: 2.08, 12: 3.31, 10: 5.26, 8: 8.37,
}


def awg_to_mm2(awg: int) -> float:
    if awg not in AWG_TO_MM2:
        raise ValueError(f"AWG {awg} not in table; extend units.AWG_TO_MM2")
    return AWG_TO_MM2[awg]


def mm2_to_closest_awg(mm2: float) -> int:
    return min(AWG_TO_MM2, key=lambda a: abs(AWG_TO_MM2[a] - mm2))


def fmt_mm(v: float) -> str:
    return f"{v:.1f} mm" if abs(v - round(v)) > 1e-9 else f"{int(round(v))} mm"


def fmt_money(v: float, currency: str = "USD") -> str:
    sym = {"USD": "$", "EUR": "€"}.get(currency, currency + " ")
    return f"{sym}{v:,.2f}"


def fmt_pct(v: float) -> str:
    return f"{100.0 * v:.1f}%"
