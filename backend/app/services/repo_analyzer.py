"""Repo Analyzer — fetch and analyze GitHub / HuggingFace repositories.

Given a URL, fetches repo metadata and key files via public APIs (no cloning),
detects language, framework, entry points, and produces a RepoAnalysis that the
orchestrator injects into the Claude context.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------
_GH_HTTPS = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/\s#?.]+)"
)
_GH_SSH = re.compile(
    r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/\s#?.]+?)(?:\.git)?$"
)
_HF_HTTPS = re.compile(
    r"https?://huggingface\.co/(?P<owner>[^/]+)/(?P<repo>[^/\s#?.]+)"
)

# Files that reveal language / framework
_KEY_FILES = [
    "README.md", "readme.md",
    "package.json", "tsconfig.json",
    "requirements.txt", "setup.py", "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml",
    "Makefile",
]

_LANG_SIGNALS: Dict[str, str] = {
    "package.json": "typescript",
    "tsconfig.json": "typescript",
    "requirements.txt": "python",
    "setup.py": "python",
    "pyproject.toml": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
}


@dataclass
class RepoAnalysis:
    """Result of analysing a repository."""
    url: str
    owner: str
    name: str
    source: str  # "github" | "huggingface"
    description: str = ""
    primary_language: str = "python"
    languages: List[str] = field(default_factory=list)
    stars: int = 0
    default_branch: str = "main"
    topics: List[str] = field(default_factory=list)
    tree_summary: List[str] = field(default_factory=list)  # top-level paths
    key_files: Dict[str, str] = field(default_factory=dict)  # filename → content (trimmed)
    detected_framework: Optional[str] = None
    entry_points: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_repo_url(text: str) -> Optional[Tuple[str, str, str]]:
    """Extract (source, owner, repo) from a URL string. Returns None if no match."""
    for pattern, source in [(_GH_HTTPS, "github"), (_GH_SSH, "github"), (_HF_HTTPS, "huggingface")]:
        m = pattern.search(text)
        if m:
            repo = m.group("repo").removesuffix(".git")
            return source, m.group("owner"), repo
    return None


def contains_repo_url(text: str) -> bool:
    """Quick check: does the text contain a GitHub / HuggingFace repo URL?"""
    return parse_repo_url(text) is not None


async def analyze_repo(url: str) -> RepoAnalysis:
    """Fetch and analyze a repository. Works for GitHub and HuggingFace."""
    parsed = parse_repo_url(url)
    if not parsed:
        return RepoAnalysis(url=url, owner="", name="", source="unknown", error="Unrecognized URL format")

    source, owner, repo = parsed
    if source == "github":
        return await _analyze_github(url, owner, repo)
    elif source == "huggingface":
        return await _analyze_huggingface(url, owner, repo)
    return RepoAnalysis(url=url, owner=owner, name=repo, source=source, error=f"Unsupported source: {source}")


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

async def _analyze_github(url: str, owner: str, repo: str) -> RepoAnalysis:
    """Analyze a GitHub repo via the public REST API."""
    analysis = RepoAnalysis(url=url, owner=owner, name=repo, source="github")
    base = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "plus12monkeys/1.0"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Repo metadata
        try:
            r = await client.get(base, headers=headers)
            if r.status_code != 200:
                analysis.error = f"GitHub API returned {r.status_code}"
                return analysis
            meta = r.json()
            analysis.description = meta.get("description") or ""
            analysis.primary_language = (meta.get("language") or "Python").lower()
            analysis.stars = meta.get("stargazers_count", 0)
            analysis.default_branch = meta.get("default_branch", "main")
            analysis.topics = meta.get("topics", [])
        except Exception as exc:
            analysis.error = f"Failed to fetch repo metadata: {exc}"
            return analysis

        # 2. File tree (top-level)
        try:
            r = await client.get(f"{base}/git/trees/{analysis.default_branch}", headers=headers)
            if r.status_code == 200:
                tree = r.json().get("tree", [])
                analysis.tree_summary = [t["path"] for t in tree[:50]]
        except Exception:
            pass

        # 3. Fetch key files (README, deps, config)
        for fname in _KEY_FILES:
            if fname.lower() in [p.lower() for p in analysis.tree_summary]:
                await _fetch_github_file(client, base, headers, fname, analysis)

    # 4. Detect language & framework from fetched files
    _detect_language_and_framework(analysis)
    _detect_entry_points(analysis)
    return analysis


async def _fetch_github_file(
    client: httpx.AsyncClient, base: str, headers: dict, fname: str, analysis: RepoAnalysis
) -> None:
    """Fetch a single file's content from GitHub (raw)."""
    try:
        r = await client.get(
            f"https://raw.githubusercontent.com/{analysis.owner}/{analysis.name}/{analysis.default_branch}/{fname}",
            headers={"User-Agent": "plus12monkeys/1.0"},
        )
        if r.status_code == 200:
            # Trim to 3000 chars to keep context manageable
            analysis.key_files[fname] = r.text[:3000]
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HuggingFace
# ---------------------------------------------------------------------------

async def _analyze_huggingface(url: str, owner: str, repo: str) -> RepoAnalysis:
    """Analyze a HuggingFace repo via its API."""
    analysis = RepoAnalysis(url=url, owner=owner, name=repo, source="huggingface")
    api_base = f"https://huggingface.co/api/models/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Model metadata
        try:
            r = await client.get(api_base)
            if r.status_code == 200:
                meta = r.json()
                analysis.description = meta.get("description") or meta.get("cardData", {}).get("description", "")
                analysis.topics = meta.get("tags", [])
                analysis.primary_language = "python"  # HF models are typically Python
                # Try siblings for file list
                siblings = meta.get("siblings", [])
                analysis.tree_summary = [s.get("rfilename", "") for s in siblings[:50]]
            else:
                # Maybe it's a dataset or space
                for endpoint in ["datasets", "spaces"]:
                    alt = f"https://huggingface.co/api/{endpoint}/{owner}/{repo}"
                    r2 = await client.get(alt)
                    if r2.status_code == 200:
                        meta = r2.json()
                        analysis.description = meta.get("description", "")
                        analysis.topics = meta.get("tags", [])
                        siblings = meta.get("siblings", [])
                        analysis.tree_summary = [s.get("rfilename", "") for s in siblings[:50]]
                        break
                else:
                    analysis.error = f"HuggingFace API returned {r.status_code}"
                    return analysis
        except Exception as exc:
            analysis.error = f"Failed to fetch HuggingFace metadata: {exc}"
            return analysis

        # 2. Fetch README
        try:
            r = await client.get(f"https://huggingface.co/{owner}/{repo}/raw/main/README.md")
            if r.status_code == 200:
                analysis.key_files["README.md"] = r.text[:3000]
        except Exception:
            pass

        # 3. Fetch requirements.txt if present
        if "requirements.txt" in analysis.tree_summary:
            try:
                r = await client.get(f"https://huggingface.co/{owner}/{repo}/raw/main/requirements.txt")
                if r.status_code == 200:
                    analysis.key_files["requirements.txt"] = r.text[:2000]
            except Exception:
                pass

    _detect_language_and_framework(analysis)
    _detect_entry_points(analysis)
    return analysis


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _detect_language_and_framework(analysis: RepoAnalysis) -> None:
    """Detect primary language and framework from fetched key files."""
    langs = set()
    for fname, lang in _LANG_SIGNALS.items():
        if fname in analysis.key_files or fname.lower() in [p.lower() for p in analysis.tree_summary]:
            langs.add(lang)
    if langs:
        analysis.languages = sorted(langs)
        # Primary language: trust GitHub's detection first, else first detected
        if analysis.primary_language not in langs and langs:
            analysis.primary_language = sorted(langs)[0]

    # Framework detection from file contents
    pkg = analysis.key_files.get("package.json", "")
    req = analysis.key_files.get("requirements.txt", "")
    pyproject = analysis.key_files.get("pyproject.toml", "")
    cargo = analysis.key_files.get("Cargo.toml", "")
    all_deps = pkg + req + pyproject + cargo

    fw_signals = [
        ("langchain", "langgraph"), ("langgraph", "langgraph"),
        ("crewai", "crewai"), ("autogen", "autogen"),
        ("semantic-kernel", "semantic-kernel"), ("semantic_kernel", "semantic-kernel"),
        ("@ai-sdk", "vercel-ai"), ("ai-sdk", "vercel-ai"),
        ("rig-core", "rig"),
        ("fastapi", "fastapi"), ("flask", "flask"), ("django", "django"),
        ("express", "express"), ("next", "nextjs"),
        ("transformers", "huggingface-transformers"),
        ("torch", "pytorch"), ("tensorflow", "tensorflow"),
    ]
    for signal, fw in fw_signals:
        if signal in all_deps.lower():
            analysis.detected_framework = fw
            break


def _detect_entry_points(analysis: RepoAnalysis) -> None:
    """Guess the main entry points from the file tree."""
    entry_candidates = [
        "main.py", "app.py", "server.py", "index.py", "run.py", "cli.py",
        "src/main.py", "src/app.py", "src/index.py",
        "agent.ts", "index.ts", "server.ts", "app.ts",
        "src/main.rs", "main.go", "cmd/main.go",
    ]
    for candidate in entry_candidates:
        if candidate in analysis.tree_summary or candidate.lower() in [p.lower() for p in analysis.tree_summary]:
            analysis.entry_points.append(candidate)


def format_repo_context(analysis: RepoAnalysis) -> str:
    """Format a RepoAnalysis into a context block for the Claude system prompt."""
    parts = [
        f"\n\n--- REPO ANALYSIS: {analysis.owner}/{analysis.name} ---",
        f"Source: {analysis.source} | URL: {analysis.url}",
        f"Primary language: {analysis.primary_language}",
    ]
    if analysis.languages:
        parts.append(f"Languages detected: {', '.join(analysis.languages)}")
    if analysis.description:
        parts.append(f"Description: {analysis.description}")
    if analysis.stars:
        parts.append(f"Stars: {analysis.stars}")
    if analysis.topics:
        parts.append(f"Topics: {', '.join(analysis.topics)}")
    if analysis.detected_framework:
        parts.append(f"Detected framework: {analysis.detected_framework}")
    if analysis.entry_points:
        parts.append(f"Entry points: {', '.join(analysis.entry_points)}")
    if analysis.tree_summary:
        parts.append(f"Top-level files: {', '.join(analysis.tree_summary[:20])}")

    # Include key file snippets
    for fname, content in analysis.key_files.items():
        if fname.lower().startswith("readme"):
            # Just first 500 chars of README
            parts.append(f"\n[{fname} excerpt]:\n{content[:500]}")
        else:
            parts.append(f"\n[{fname}]:\n{content[:1000]}")

    parts.append("--- END REPO ANALYSIS ---")
    return "\n".join(parts)

