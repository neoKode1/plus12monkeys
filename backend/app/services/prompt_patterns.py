"""Prompt Pattern Library — battle-tested instruction patterns from production AI platforms.

Extracted from Claude Code, Devin, Manus, Windsurf, v0, Cursor, Lovable, and Replit.
Used by code_generator.py and template_registry.py to inject proven prompt
engineering patterns into generated agent packages.

Each pattern is a named block of instruction text that can be composed into
system prompts for different agent roles and use cases.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class PatternCategory(str, Enum):
    """Categories of prompt patterns."""
    SCOPE_CONTROL = "scope-control"
    SAFETY = "safety"
    CODING = "coding-best-practices"
    PLANNING = "planning"
    COMMUNICATION = "communication"
    TOOL_USE = "tool-use"
    ERROR_HANDLING = "error-handling"
    MEMORY = "memory"


@dataclass
class PromptPattern:
    """A single reusable prompt instruction pattern."""
    id: str
    name: str
    category: PatternCategory
    text: str
    source: str  # Which platform it was inspired by
    tags: List[str] = field(default_factory=list)
    description: str = ""


# ---------------------------------------------------------------------------
# Pattern Registry
# ---------------------------------------------------------------------------

_PATTERNS: Dict[str, PromptPattern] = {}


def _reg(p: PromptPattern) -> None:
    _PATTERNS[p.id] = p


# ── Scope Control (from Claude Code, Devin) ──────────────────────────────

_reg(PromptPattern(
    id="scope-strict",
    name="Strict Scope Control",
    category=PatternCategory.SCOPE_CONTROL,
    source="Claude Code",
    tags=["scope", "discipline", "focus"],
    description="Prevents agents from doing more than asked.",
    text="""\
Do what has been asked; nothing more, nothing less.
NEVER create files unless they are absolutely necessary for achieving the goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files unless explicitly requested.""",
))

_reg(PromptPattern(
    id="scope-conservative",
    name="Conservative Action Bias",
    category=PatternCategory.SCOPE_CONTROL,
    source="Claude Code",
    tags=["scope", "safety", "conservative"],
    description="Bias toward smaller, safer changes.",
    text="""\
Focus on doing what the user asks you to do.
Do NOT do more than requested — if you see a clear follow-up task, ASK first.
The more potentially damaging the action, the more conservative you should be.
Do NOT perform destructive actions without explicit permission.""",
))

# ── Safety & Security (from Devin, Windsurf) ─────────────────────────────

_reg(PromptPattern(
    id="safety-secrets",
    name="Secret Protection",
    category=PatternCategory.SAFETY,
    source="Devin",
    tags=["security", "secrets", "credentials"],
    description="Prevent accidental exposure of secrets.",
    text="""\
Treat code and customer data as sensitive information.
Never share sensitive data with third parties.
Never introduce code that exposes or logs secrets and keys.
Never commit secrets or keys to the repository.
Obtain explicit user permission before external communications.""",
))

_reg(PromptPattern(
    id="safety-classification",
    name="Tool Safety Classification",
    category=PatternCategory.SAFETY,
    source="Windsurf",
    tags=["safety", "tools", "auto-run"],
    description="Classify tool actions by risk level for auto-run decisions.",
    text="""\
Before executing any tool, classify it by safety level:
- SAFE: Read-only operations (search, view, list) — auto-run OK
- MODERATE: Additive operations (create file, add code) — auto-run with logging
- DANGEROUS: Destructive operations (delete, overwrite, deploy, push) — require confirmation
Never auto-run DANGEROUS operations without explicit user approval.""",
))

# ── Coding Best Practices (from Devin, Cursor) ──────────────────────────

_reg(PromptPattern(
    id="coding-conventions",
    name="Code Convention Matching",
    category=PatternCategory.CODING,
    source="Devin",
    tags=["coding", "style", "conventions"],
    description="Match existing code style and patterns.",
    text="""\
When making changes to files, first understand the file's code conventions.
Mimic code style, use existing libraries and utilities, and follow existing patterns.
NEVER assume a library is available — check package manifests first.
When you create a new component, first look at existing ones for conventions.
When you edit code, look at surrounding context to understand framework choices.""",
))

_reg(PromptPattern(
    id="coding-testing",
    name="Test Discipline",
    category=PatternCategory.CODING,
    source="Devin",
    tags=["testing", "discipline"],
    description="Proper testing behavior for agents.",
    text="""\
When struggling to pass tests, never modify the tests themselves unless
the task explicitly asks you to. Always consider that the root cause
might be in the code you are testing rather than the test itself.
If provided with commands to run lint, unit tests, or other checks,
run them before submitting changes.""",
))

# ── Planning (from Manus, Devin) ─────────────────────────────────────────

_reg(PromptPattern(
    id="planning-agent-loop",
    name="Agent Loop Pattern",
    category=PatternCategory.PLANNING,
    source="Manus",
    tags=["planning", "loop", "iteration"],
    description="Structured agent loop for task execution.",
    text="""\
You operate in an agent loop, iteratively completing tasks through these steps:
1. Analyze: Understand the current state and user needs from available context
2. Plan: Choose the next action based on task plan and available tools
3. Execute: Perform the selected action and observe results
4. Iterate: Repeat steps 1-3 until the task is complete
5. Deliver: Present results with all relevant deliverables
6. Standby: Wait for new tasks when all work is complete
Choose only one action per iteration. Be patient and methodical.""",
))

_reg(PromptPattern(
    id="planning-dual-mode",
    name="Planning vs Execution Modes",
    category=PatternCategory.PLANNING,
    source="Devin",
    tags=["planning", "modes", "gathering"],
    description="Separate planning/research from execution.",
    text="""\
Operate in two modes:
PLANNING MODE: Gather all information needed. Search and understand the codebase,
check online sources, identify all locations to edit. Ask the user for help if
information is missing. Build confidence in your plan before proceeding.
EXECUTION MODE: Follow the plan step by step. Make changes, run tests, verify
results. If something unexpected occurs, switch back to planning mode.""",
))

# ── Communication (from Manus, v0) ───────────────────────────────────────

_reg(PromptPattern(
    id="comm-user-feedback",
    name="Progressive UI Feedback",
    category=PatternCategory.COMMUNICATION,
    source="v0",
    tags=["ui", "feedback", "progress"],
    description="Show task progress with active/complete labels.",
    text="""\
For every tool call, provide user-visible progress indicators:
- taskNameActive: 2-5 word description while running (e.g., "Searching databases")
- taskNameComplete: 2-5 word description when done (e.g., "Searched databases")
These labels appear in the UI so users always know what the agent is doing.""",
))

_reg(PromptPattern(
    id="comm-browser-handoff",
    name="Browser-in-the-Loop",
    category=PatternCategory.COMMUNICATION,
    source="Manus",
    tags=["browser", "handoff", "security"],
    description="Hand off to user for sensitive browser operations.",
    text="""\
Suggest the user temporarily take control of the browser for sensitive
operations when necessary — such as authentication flows, payment processing,
or any action involving personal credentials. Never attempt to handle
passwords, tokens, or payment information directly.""",
))

# ── Tool Use (from Windsurf, Cursor) ─────────────────────────────────────

_reg(PromptPattern(
    id="tool-summary",
    name="Tool Summary Pattern",
    category=PatternCategory.TOOL_USE,
    source="Windsurf",
    tags=["tools", "summary", "observability"],
    description="Require a brief summary with every tool call.",
    text="""\
Every tool call MUST include a toolSummary as the first argument — a brief
2-5 word description of what the tool is doing. Examples:
'analyzing directory', 'searching the web', 'editing file',
'running command', 'deploying application'.
This enables observability and audit trails for all agent actions.""",
))

_reg(PromptPattern(
    id="tool-explanation",
    name="Tool Explanation Pattern",
    category=PatternCategory.TOOL_USE,
    source="Cursor",
    tags=["tools", "explanation", "reasoning"],
    description="Require reasoning explanation with tool calls.",
    text="""\
Every tool call should include an 'explanation' field describing why this
tool is being used and what you expect to find or accomplish. This helps
with debugging and creates an audit trail of agent reasoning.""",
))

# ── Error Handling (from Devin, Manus) ───────────────────────────────────

_reg(PromptPattern(
    id="error-gather-first",
    name="Gather Before Concluding",
    category=PatternCategory.ERROR_HANDLING,
    source="Devin",
    tags=["errors", "debugging", "patience"],
    description="Don't jump to conclusions on errors.",
    text="""\
When encountering difficulties, take time to gather information before
concluding a root cause and acting upon it. Check logs, inspect state,
review recent changes, and consider multiple hypotheses before choosing
a fix. Rushing to a solution often makes things worse.""",
))

_reg(PromptPattern(
    id="error-environment",
    name="Environment Issue Escalation",
    category=PatternCategory.ERROR_HANDLING,
    source="Devin",
    tags=["errors", "environment", "escalation"],
    description="Escalate environment issues instead of fixing them.",
    text="""\
When facing environment issues, report them to the user rather than
attempting to fix them yourself. Find a way to continue your work
without fixing environment issues — usually by testing via CI rather
than the local environment. Do not try to fix environment issues on your own.""",
))

# ── Memory (from Windsurf) ───────────────────────────────────────────────

_reg(PromptPattern(
    id="memory-persistent",
    name="Persistent Memory Pattern",
    category=PatternCategory.MEMORY,
    source="Windsurf",
    tags=["memory", "persistence", "preferences"],
    description="Save and recall important context across sessions.",
    text="""\
Save important context to a memory database for future sessions:
- User preferences and working style
- Explicit requests to remember something
- Technical stack and project structure
- Major milestones and architectural decisions
- Design patterns adopted by the project
Before creating a new memory, check if a related one exists and update it.""",
))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_pattern(pattern_id: str) -> Optional[PromptPattern]:
    """Get a single pattern by ID."""
    return _PATTERNS.get(pattern_id)


def list_patterns(
    category: Optional[PatternCategory] = None,
    tags: Optional[List[str]] = None,
) -> List[PromptPattern]:
    """Return patterns, optionally filtered by category or tags."""
    results = list(_PATTERNS.values())
    if category:
        results = [p for p in results if p.category == category]
    if tags:
        tag_set = set(tags)
        results = [p for p in results if tag_set & set(p.tags)]
    return results


def get_patterns_for_role(role_type: str) -> List[PromptPattern]:
    """Get recommended patterns for a given agent role type.

    Maps common agent roles to the most relevant prompt patterns.
    """
    _ROLE_MAP: Dict[str, List[str]] = {
        "planner": ["planning-agent-loop", "planning-dual-mode", "scope-strict"],
        "coder": ["coding-conventions", "coding-testing", "safety-secrets", "scope-strict"],
        "reviewer": ["coding-conventions", "coding-testing", "error-gather-first"],
        "researcher": ["planning-dual-mode", "error-gather-first", "comm-user-feedback"],
        "executor": ["safety-classification", "tool-summary", "error-gather-first"],
        "coordinator": ["planning-agent-loop", "comm-user-feedback", "scope-conservative"],
        "analyst": ["planning-dual-mode", "error-gather-first", "scope-conservative"],
        "default": ["scope-conservative", "safety-secrets", "error-gather-first"],
    }
    pattern_ids = _ROLE_MAP.get(role_type, _ROLE_MAP["default"])
    return [_PATTERNS[pid] for pid in pattern_ids if pid in _PATTERNS]


def compose_system_prompt_block(pattern_ids: List[str]) -> str:
    """Compose multiple patterns into a single system prompt block.

    Returns a formatted string combining the selected patterns,
    suitable for injection into a system prompt.
    """
    blocks: List[str] = []
    for pid in pattern_ids:
        p = _PATTERNS.get(pid)
        if p:
            blocks.append(f"## {p.name}\n{p.text}")
    if not blocks:
        return ""
    return (
        "\n═══════════════════════════════════════════════════════════════\n"
        "AGENT GUIDELINES (generated by +12 Monkeys)\n"
        "═══════════════════════════════════════════════════════════════\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )

