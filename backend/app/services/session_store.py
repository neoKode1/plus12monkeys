"""Session store for wizard conversations.

Provides an abstract interface (``BaseSessionStore``) and a concrete
in-memory implementation.  Swap to a Redis- or DB-backed subclass in
production by replacing the ``sessions`` singleton below.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.conversation import WizardSession


# ---------------------------------------------------------------------------
# Abstract interface — subclass this for Redis / Postgres / etc.
# ---------------------------------------------------------------------------

class BaseSessionStore(ABC):
    """Contract every session-store backend must satisfy."""

    @abstractmethod
    def create(self) -> WizardSession: ...

    @abstractmethod
    def get(self, session_id: str) -> Optional[WizardSession]: ...

    @abstractmethod
    def save(self, session: WizardSession) -> None: ...

    @abstractmethod
    def list_sessions(self) -> List[WizardSession]: ...

    @abstractmethod
    def delete(self, session_id: str) -> bool: ...


# ---------------------------------------------------------------------------
# Concrete in-memory implementation
# ---------------------------------------------------------------------------

class SessionStore(BaseSessionStore):
    """Thread-safe-ish in-memory store keyed by session_id."""

    def __init__(self) -> None:
        self._sessions: Dict[str, WizardSession] = {}

    def create(self) -> WizardSession:
        session = WizardSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[WizardSession]:
        return self._sessions.get(session_id)

    def save(self, session: WizardSession) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.session_id] = session

    def list_sessions(self) -> List[WizardSession]:
        return list(self._sessions.values())

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


# Module-level singleton
sessions: BaseSessionStore = SessionStore()

