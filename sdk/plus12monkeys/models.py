"""Data models for the +12 Monkeys SDK."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class GeneratedFile:
    """A single generated file."""
    path: str
    content: str
    language: str = "python"


@dataclass
class GeneratedPackage:
    """The complete generated package (MCP server or SDK)."""
    project_name: str
    template_id: str
    framework: str
    deployment: str
    files: List[GeneratedFile] = field(default_factory=list)
    summary: str = ""
    setup_instructions: List[str] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)


@dataclass
class GenerateResult:
    """Result of a generate call — package + repo metadata."""
    package: GeneratedPackage
    repo_name: str
    repo_owner: str
    repo_description: str
    primary_language: str

    def write_to(self, directory: str, overwrite: bool = False) -> List[str]:
        """Write all generated files to a directory on disk.

        Args:
            directory: Target directory path.
            overwrite: If True, overwrite existing files.

        Returns:
            List of absolute paths written.
        """
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        written: List[str] = []
        for f in self.package.files:
            target = out / f.path
            if target.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {target}. Use overwrite=True to replace.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.content, encoding="utf-8")
            written.append(str(target.resolve()))
        return written

    def file_paths(self) -> List[str]:
        """Return the list of file paths in the package."""
        return [f.path for f in self.package.files]

    def get_file(self, path: str) -> Optional[GeneratedFile]:
        """Get a specific file by path."""
        for f in self.package.files:
            if f.path == path:
                return f
        return None

