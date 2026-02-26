"""Patch Scam Likely hub files to add the investigation endpoint."""
import os

HUB = "/Users/babypegasus/Desktop/prototypes/Scam-likely/scam-likely-hub"

# ---- 1. Add InvestigationResponse schema to schemas.py ----
schemas_path = os.path.join(HUB, "app/api/schemas.py")
with open(schemas_path, "r") as f:
    schemas = f.read()

investigation_schema = '''

# ============================================================================
# Investigation Schemas (AI Agent Pipeline)
# ============================================================================

class InvestigationResponse(BaseModel):
    """Response from the AI investigation pipeline."""

    check_id: int
    forensic_timeline: str = Field(..., description="Forensic analyst output")
    risk_assessment: str = Field(..., description="Risk scorer output")
    sar_report: str = Field(..., description="SAR report draft")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
'''

if "InvestigationResponse" not in schemas:
    with open(schemas_path, "w") as f:
        f.write(schemas.rstrip() + "\n" + investigation_schema + "\n")
    print("schemas.py: InvestigationResponse added")
else:
    print("schemas.py: InvestigationResponse already exists")

# ---- 2. Add anthropic_api_key to config.py ----
config_path = os.path.join(HUB, "app/core/config.py")
with open(config_path, "r") as f:
    config = f.read()

if "anthropic_api_key" not in config:
    # Insert before the line "settings = Settings()"
    config = config.replace(
        "settings = Settings()",
        '    # AI Investigation Agent\n    anthropic_api_key: str = ""\n\n\nsettings = Settings()',
    )
    with open(config_path, "w") as f:
        f.write(config)
    print("config.py: anthropic_api_key added")
else:
    print("config.py: anthropic_api_key already exists")

# ---- 3. Add ANTHROPIC_API_KEY to .env ----
env_path = os.path.join(HUB, ".env")
with open(env_path, "r") as f:
    env = f.read()

if "ANTHROPIC_API_KEY" not in env:
    env = env.rstrip() + "\n\n# AI Investigation Agent (LangGraph pipeline)\nANTHROPIC_API_KEY=\n"
    with open(env_path, "w") as f:
        f.write(env)
    print(".env: ANTHROPIC_API_KEY placeholder added")
else:
    print(".env: ANTHROPIC_API_KEY already exists")

# ---- 4. Add investigate endpoint to checks.py ----
checks_path = os.path.join(HUB, "app/api/endpoints/checks.py")
with open(checks_path, "r") as f:
    checks = f.read()

if "investigate" not in checks:
    # Add InvestigationResponse to the imports
    checks = checks.replace(
        "    AlertResponse,\n)",
        "    AlertResponse,\n    InvestigationResponse,\n)",
    )
    # Add Suspect model import
    checks = checks.replace(
        "from app.models.check import CheckFingerprint, Branch, Alert",
        "from app.models.check import CheckFingerprint, Branch, Alert, Suspect",
    )

    endpoint_code = '''


@router.post("/{check_id}/investigate", response_model=InvestigationResponse)
async def investigate_check(
    check_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_dashboard_auth),
):
    """
    Run AI investigation pipeline on a check.

    Uses LangGraph to run 3 agents sequentially:
    1. Forensic Analyst - produces a forensic timeline
    2. Risk Scorer - produces a risk assessment
    3. Report Generator - produces a SAR report draft
    """
    from app.services.investigation_agent import build_case_input, run_investigation

    # Fetch the check
    check = db.query(CheckFingerprint).filter(CheckFingerprint.id == check_id).first()
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Check {check_id} not found",
        )

    # Resolve branch name
    branch = db.query(Branch).filter(Branch.id == check.branch_id).first()
    branch_name = branch.name if branch else check.branch_id

    # Get related alerts
    related_alerts = (
        db.query(Alert)
        .filter(Alert.check_id == check_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    # Get scan history (same fingerprint at any branch)
    scan_history = (
        db.query(CheckFingerprint)
        .filter(
            CheckFingerprint.fingerprint == check.fingerprint,
            CheckFingerprint.id != check.id,
        )
        .order_by(CheckFingerprint.scanned_at.desc())
        .all()
    )

    # Get suspect if linked
    suspect = None
    if check.suspect_id:
        suspect = db.query(Suspect).filter(Suspect.id == check.suspect_id).first()

    # Build case input and run pipeline
    case_input = build_case_input(
        check=check,
        branch_name=branch_name,
        scan_history=scan_history,
        related_alerts=related_alerts,
        suspect=suspect,
    )

    result = await run_investigation(case_input)

    return InvestigationResponse(
        check_id=check.id,
        forensic_timeline=result["forensic_timeline"],
        risk_assessment=result["risk_assessment"],
        sar_report=result["sar_report"],
    )
'''

    with open(checks_path, "w") as f:
        f.write(checks.rstrip() + endpoint_code + "\n")
    print("checks.py: investigate endpoint added")
else:
    print("checks.py: investigate endpoint already exists")

print("\nAll patches applied.")

