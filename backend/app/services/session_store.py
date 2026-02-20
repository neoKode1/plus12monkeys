"""Session store for wizard conversations.

Provides an abstract interface (``BaseSessionStore``) and a concrete
in-memory implementation with TTL-based expiry and a max-size cap.
Swap to a Redis- or DB-backed subclass in production by replacing
the ``sessions`` singleton below.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.models.conversation import WizardSession

logger = logging.getLogger(__name__)


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
    """In-memory store with TTL expiry and max-size eviction."""

    def __init__(
        self,
        ttl_minutes: int = 1440,
        max_count: int = 500,
    ) -> None:
        self._sessions: Dict[str, WizardSession] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_count = max_count

    # -- helpers --

    def _is_expired(self, session: WizardSession) -> bool:
        return datetime.now(timezone.utc) - session.updated_at > self._ttl

    def _evict_expired(self) -> int:
        """Remove sessions older than TTL. Returns count evicted."""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.updated_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            logger.info("Evicted %d expired session(s)", len(expired))
        return len(expired)

    def _evict_oldest(self) -> None:
        """Drop the oldest session(s) until we're under max_count."""
        while len(self._sessions) >= self._max_count:
            oldest_id = min(
                self._sessions,
                key=lambda sid: self._sessions[sid].updated_at,
            )
            del self._sessions[oldest_id]
            logger.info("Evicted oldest session %s (max_count=%d)", oldest_id, self._max_count)

    # -- public API --

    def create(self) -> WizardSession:
        self._evict_expired()
        self._evict_oldest()
        session = WizardSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[WizardSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if self._is_expired(session):
            del self._sessions[session_id]
            return None
        return session

    def save(self, session: WizardSession) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.session_id] = session

    def list_sessions(self) -> List[WizardSession]:
        self._evict_expired()
        return list(self._sessions.values())

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


# Module-level singleton (reads config at import time)
def _make_store() -> SessionStore:
    from app.core.config import settings
    return SessionStore(
        ttl_minutes=settings.session_ttl_minutes,
        max_count=settings.session_max_count,
    )

sessions: BaseSessionStore = _make_store()

