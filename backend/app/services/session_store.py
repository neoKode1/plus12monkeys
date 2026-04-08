"""Session store for wizard conversations.

Provides an abstract interface (``BaseSessionStore``), an in-memory
implementation for development, and a Redis-backed implementation
for production (sessions survive deploys).

Set REDIS_URL to enable the Redis backend automatically.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.models.conversation import WizardSession

logger = logging.getLogger(__name__)

_KEY_PREFIX = "p12m:session:"


# ---------------------------------------------------------------------------
# Abstract interface
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
# In-memory implementation (dev / fallback)
# ---------------------------------------------------------------------------

class InMemorySessionStore(BaseSessionStore):
    """In-memory store with TTL expiry and max-size eviction."""

    def __init__(self, ttl_minutes: int = 1440, max_count: int = 500) -> None:
        self._sessions: Dict[str, WizardSession] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_count = max_count

    def _is_expired(self, session: WizardSession) -> bool:
        return datetime.now(timezone.utc) - session.updated_at > self._ttl

    def _evict_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [sid for sid, s in self._sessions.items() if now - s.updated_at > self._ttl]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            logger.info("Evicted %d expired session(s)", len(expired))
        return len(expired)

    def _evict_oldest(self) -> None:
        while len(self._sessions) >= self._max_count:
            oldest_id = min(self._sessions, key=lambda sid: self._sessions[sid].updated_at)
            del self._sessions[oldest_id]
            logger.info("Evicted oldest session %s (max_count=%d)", oldest_id, self._max_count)

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


# ---------------------------------------------------------------------------
# Redis implementation (production)
# ---------------------------------------------------------------------------

class RedisSessionStore(BaseSessionStore):
    """Redis-backed session store. Sessions survive deploys."""

    def __init__(self, redis_url: str, ttl_minutes: int = 1440) -> None:
        import redis
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_minutes * 60
        # Test connection
        self._redis.ping()
        logger.info("RedisSessionStore connected to %s", redis_url.split("@")[-1])

    def _key(self, session_id: str) -> str:
        return f"{_KEY_PREFIX}{session_id}"

    def create(self) -> WizardSession:
        session = WizardSession()
        self.save(session)
        return session

    def get(self, session_id: str) -> Optional[WizardSession]:
        data = self._redis.get(self._key(session_id))
        if data is None:
            return None
        return WizardSession.model_validate_json(data)

    def save(self, session: WizardSession) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._redis.setex(
            self._key(session.session_id),
            self._ttl_seconds,
            session.model_dump_json(),
        )

    def list_sessions(self) -> List[WizardSession]:
        keys = self._redis.keys(f"{_KEY_PREFIX}*")
        results: List[WizardSession] = []
        for key in keys:
            data = self._redis.get(key)
            if data:
                results.append(WizardSession.model_validate_json(data))
        return results

    def delete(self, session_id: str) -> bool:
        return self._redis.delete(self._key(session_id)) > 0


# ---------------------------------------------------------------------------
# Factory — auto-selects Redis if REDIS_URL is set
# ---------------------------------------------------------------------------

def _make_store() -> BaseSessionStore:
    from app.core.config import settings

    if settings.redis_url:
        try:
            store = RedisSessionStore(
                redis_url=settings.redis_url,
                ttl_minutes=settings.session_ttl_minutes,
            )
            logger.info("✅ Using RedisSessionStore (sessions survive deploys)")
            return store
        except Exception as exc:
            logger.warning("Redis unavailable (%s), falling back to in-memory", exc)

    logger.info("⚠️  Using InMemorySessionStore (sessions lost on deploy)")
    return InMemorySessionStore(
        ttl_minutes=settings.session_ttl_minutes,
        max_count=settings.session_max_count,
    )


sessions: BaseSessionStore = _make_store()

