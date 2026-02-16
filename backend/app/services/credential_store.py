"""Per-project credential store with Fernet encryption.

Stores MCP server environment variables (API keys, tokens, etc.) encrypted
in-memory. In production this would persist to a database; for now it
provides the same interface with an in-memory backend.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from cryptography.fernet import Fernet

from app.models.mcp import CredentialEntry, ProjectCredentials


# ---------------------------------------------------------------------------
# Encryption key — derived from env or auto-generated for dev
# ---------------------------------------------------------------------------

_ENCRYPTION_KEY: Optional[bytes] = None


def _get_fernet() -> Fernet:
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is None:
        raw = os.environ.get("CREDENTIAL_ENCRYPTION_KEY", "")
        if raw:
            _ENCRYPTION_KEY = raw.encode()
        else:
            # Auto-generate for dev — will lose data on restart
            _ENCRYPTION_KEY = Fernet.generate_key()
    return Fernet(_ENCRYPTION_KEY)


# ---------------------------------------------------------------------------
# In-memory store  {project_id: ProjectCredentials}
# ---------------------------------------------------------------------------

_STORE: Dict[str, ProjectCredentials] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_credentials(
    project_id: str,
    server_id: str,
    credentials: Dict[str, str],
) -> ProjectCredentials:
    """Store (or overwrite) credentials for a given project + server.

    Values are encrypted before storage.
    """
    f = _get_fernet()

    # Get or create project entry
    proj = _STORE.get(project_id, ProjectCredentials(project_id=project_id))

    # Remove existing creds for this server
    proj.credentials = [c for c in proj.credentials if c.server_id != server_id]

    # Add new encrypted creds
    for key, value in credentials.items():
        encrypted = f.encrypt(value.encode()).decode()
        proj.credentials.append(
            CredentialEntry(key=key, value=encrypted, server_id=server_id)
        )

    proj.updated_at = datetime.utcnow()
    _STORE[project_id] = proj
    return proj


def get_credentials(
    project_id: str,
    server_id: Optional[str] = None,
) -> List[CredentialEntry]:
    """Retrieve credentials for a project, optionally filtered by server.

    Returns entries with values STILL ENCRYPTED — call decrypt_value() to read.
    """
    proj = _STORE.get(project_id)
    if not proj:
        return []
    creds = proj.credentials
    if server_id:
        creds = [c for c in creds if c.server_id == server_id]
    return creds


def get_decrypted_env(
    project_id: str,
    server_id: Optional[str] = None,
) -> Dict[str, str]:
    """Return decrypted {KEY: value} dict for a project/server.

    Useful for passing as env overrides when spawning MCP servers.
    """
    creds = get_credentials(project_id, server_id)
    f = _get_fernet()
    return {c.key: f.decrypt(c.value.encode()).decode() for c in creds}


def delete_credentials(project_id: str, server_id: Optional[str] = None) -> bool:
    """Remove credentials. If server_id given, only remove that server's creds."""
    proj = _STORE.get(project_id)
    if not proj:
        return False
    if server_id:
        proj.credentials = [c for c in proj.credentials if c.server_id != server_id]
    else:
        del _STORE[project_id]
    return True


def get_credential_summary(project_id: str) -> Dict[str, List[str]]:
    """Return {server_id: [key_names]} for a project (no values returned)."""
    creds = get_credentials(project_id)
    summary: Dict[str, List[str]] = {}
    for c in creds:
        summary.setdefault(c.server_id, []).append(c.key)
    return summary
