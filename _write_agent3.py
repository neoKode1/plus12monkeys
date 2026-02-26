"""Append public API functions to investigation_agent.py."""

TARGET = "/Users/babypegasus/Desktop/prototypes/Scam-likely/scam-likely-hub/app/services/investigation_agent.py"

CONTENT = '''

def build_case_input(
    check,
    branch_name: str,
    scan_history: list,
    related_alerts: list,
    suspect=None,
) -> str:
    """Build a structured text summary of the case for the agent pipeline."""
    lines = [
        f"=== FLAGGED CHECK (ID: {check.id}) ===",
        f"Fingerprint: {check.fingerprint}",
        f"Branch: {branch_name} ({check.branch_id})",
        f"Scanned at: {check.scanned_at}",
        f"Fraud score: {check.fraud_score}",
        f"Is fraud: {check.is_fraud}",
        f"Edge density: {check.edge_density}",
        f"Texture variance: {check.texture_variance}",
    ]
    if check.flagged_by:
        lines.append(f"Flagged by: {check.flagged_by} at {check.flagged_at}")
        lines.append(f"Flag notes: {check.flag_notes}")
        lines.append(f"Flag severity: {check.flag_severity}")

    if suspect:
        lines.append("")
        lines.append("=== SUSPECT ===")
        lines.append(f"Identifier hash: {suspect.identifier_hash}")
        lines.append(f"Risk level: {suspect.risk_level}")
        lines.append(f"Total fraud attempts: {suspect.total_fraud_attempts}")
        lines.append(f"Total fraud confirmed: {suspect.total_fraud_confirmed}")
        lines.append(f"Is flagged: {suspect.is_flagged}")

    if scan_history:
        lines.append("")
        lines.append(f"=== SCAN HISTORY ({len(scan_history)} records) ===")
        for s in scan_history[:20]:
            b_name = getattr(getattr(s, "branch", None), "name", None) or s.branch_id
            lines.append(
                f"  - {s.scanned_at} | Branch: {b_name} | "
                f"Score: {s.fraud_score} | Fraud: {s.is_fraud}"
            )

    if related_alerts:
        lines.append("")
        lines.append(f"=== RELATED ALERTS ({len(related_alerts)} records) ===")
        for a in related_alerts[:20]:
            lines.append(
                f"  - [{a.severity.upper()}] {a.alert_type}: {a.title}"
            )

    return "\\n".join(lines)


async def run_investigation(case_input: str) -> dict:
    """
    Run the 3-stage investigation pipeline.

    Returns dict with keys:
      - forensic_timeline
      - risk_assessment
      - sar_report
    """
    logger.info("Starting fraud investigation pipeline...")
    result = await investigation_graph.ainvoke({"input": case_input})
    return {
        "forensic_timeline": result.get("forensic_analyst_output", ""),
        "risk_assessment": result.get("risk_scorer_output", ""),
        "sar_report": result.get("report_generator_output", ""),
    }
'''

with open(TARGET, "a") as f:
    f.write(CONTENT)
print("Part 3 appended - file complete")

