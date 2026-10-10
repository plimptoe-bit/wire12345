from .findings import Finding, findings_to_markdown, findings_to_open_items  # noqa: F401
from . import compatibility, cascade, reconcile, tooling  # noqa: F401


def run_all(prog, inventory=None):
    """Run every rule set; returns (findings, cascade_additions, tooling_report)."""
    findings = []
    findings += reconcile.check_preterminated(prog)
    findings += reconcile.check_cavity_fill(prog)
    additions = cascade.compute_additions(prog)
    findings += cascade.check_against_bom(prog, additions)
    findings += reconcile.check_bom_quantities(prog, additions)
    findings += compatibility.check_all(prog)
    tooling_report = None
    if inventory is not None:
        tooling_report = tooling.match_program(prog, inventory)
        findings += tooling.findings_from_report(prog, tooling_report)
    return findings, additions, tooling_report
