"""Append nodes and graph to investigation_agent.py."""

TARGET = "/Users/babypegasus/Desktop/prototypes/Scam-likely/scam-likely-hub/app/services/investigation_agent.py"

CONTENT = '''

def forensic_analyst_node(state: InvestigationState) -> Dict[str, Any]:
    """Analyze check history and produce a forensic timeline."""
    llm = _build_llm()
    prompt = (
        "You are a forensic analyst specializing in check fraud investigation.\\n"
        "Your goal: analyze the flagged check data below and produce a forensic "
        "timeline showing when and where this fingerprint (or the suspect) appeared "
        "across bank branches. Identify patterns and anomalies.\\n\\n"
        f"Case Data:\\n{state[\'input\']}\\n\\n"
        "Produce a structured forensic timeline with dates, branches, and observations."
    )
    response = llm.invoke(prompt)
    return {"forensic_analyst_output": response.content}


def risk_scorer_node(state: InvestigationState) -> Dict[str, Any]:
    """Score the risk based on the forensic timeline."""
    llm = _build_llm()
    prompt = (
        "You are a risk scoring agent for bank check fraud.\\n"
        "Your goal: take the forensic timeline below plus the original check data, "
        "and produce a composite risk assessment with:\\n"
        "- Overall risk level: LOW / MEDIUM / HIGH / CRITICAL\\n"
        "- Confidence percentage (0-100%%)\\n"
        "- Key risk factors (bullet list)\\n"
        "- Recommended actions\\n\\n"
        f"Original Case Data:\\n{state[\'input\']}\\n\\n"
        f"Forensic Timeline:\\n{state[\'forensic_analyst_output\']}\\n\\n"
        "Produce the risk assessment now."
    )
    response = llm.invoke(prompt)
    return {"risk_scorer_output": response.content}


def report_generator_node(state: InvestigationState) -> Dict[str, Any]:
    """Generate a SAR-style report from the investigation."""
    llm = _build_llm()
    prompt = (
        "You are a compliance report generator for bank fraud investigations.\\n"
        "Your goal: produce a formatted Suspicious Activity Report (SAR) draft "
        "suitable for FinCEN filing. Include all standard SAR sections:\\n"
        "- Subject Information (use only hashed identifiers)\\n"
        "- Suspicious Activity Information\\n"
        "- Summary Narrative\\n"
        "- Supporting Documentation references\\n\\n"
        f"Original Case Data:\\n{state[\'input\']}\\n\\n"
        f"Risk Assessment:\\n{state[\'risk_scorer_output\']}\\n\\n"
        "Produce the SAR draft now."
    )
    response = llm.invoke(prompt)
    return {"report_generator_output": response.content}


# Graph (compiled once at module level)
_workflow = StateGraph(InvestigationState)
_workflow.add_node("forensic_analyst", forensic_analyst_node)
_workflow.add_node("risk_scorer", risk_scorer_node)
_workflow.add_node("report_generator", report_generator_node)
_workflow.set_entry_point("forensic_analyst")
_workflow.add_edge("forensic_analyst", "risk_scorer")
_workflow.add_edge("risk_scorer", "report_generator")
_workflow.add_edge("report_generator", END)
investigation_graph = _workflow.compile()
'''

with open(TARGET, "a") as f:
    f.write(CONTENT)
print(f"Part 2 appended")

