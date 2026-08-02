"""Reusable in-memory rolling conversation store.

Shared by the meal-specific AI chat and the general AI Nutrition
Assistant.  Provides per-key session memory with a rolling window
(max messages), a session cap, and idle-TTL eviction.

Conversations are intentionally NOT persisted to the database — they
live only for the lifetime of the process (consistent with the
project's chat design).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Defaults (kept aligned with the previous ChatAIService behaviour).
DEFAULT_MAX_MESSAGES = 10
DEFAULT_MAX_SESSIONS = 256
DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour


@dataclass
class ConversationSession:
    """A single in-memory conversation.

    ``history`` holds alternating ``{"role": "user"|"model",
    "content": str}`` entries.  ``data`` is an opaque payload that the
    owning service may use (e.g. meal context).
    """

    history: List[Dict[str, str]] = field(default_factory=list)
    data: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)


class ConversationStore:
    """Thread-safe store of conversations keyed by an arbitrary key.

    Usage::

        store = ConversationStore(max_messages=10)
        session = store.get_or_create("user:42", factory=lambda: ConversationSession(data=...))
        store.append("user:42", "hello", "hi there")
    """

    def __init__(
        self,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.max_messages = max_messages
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self.sessions: Dict[Any, ConversationSession] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(
        self,
        key: Any,
        factory: Optional[Any] = None,
    ) -> ConversationSession:
        """Return the session for *key*, creating it if absent.

        ``factory`` is a zero-argument callable that produces the
        session payload; when ``None`` a plain ``ConversationSession`` is
        created.
        """
        with self._lock:
            session = self.sessions.get(key)
            if session is None:
                session = factory() if factory else ConversationSession()
                self.sessions[key] = session
            session.last_access = time.time()
            self._evict()
            return session

    def append(self, key: Any, user_message: str, model_reply: str) -> None:
        """Append one user/model exchange, truncating to the window."""
        with self._lock:
            session = self.sessions.get(key)
            if session is None:
                return
            session.history.append({"role": "user", "content": user_message})
            session.history.append({"role": "model", "content": model_reply})
            session.last_access = time.time()
            session.history = session.history[-self.max_messages:]

    def get(self, key: Any) -> Optional[ConversationSession]:
        with self._lock:
            return self.sessions.get(key)

    def clear(self, key: Any) -> None:
        with self._lock:
            self.sessions.pop(key, None)

    # ------------------------------------------------------------------
    # Eviction
    # ------------------------------------------------------------------

    def _evict(self) -> None:
        """Drop idle sessions; over capacity, drop least-recently-used."""
        now = time.time()

        # Always evict sessions idle longer than the TTL.
        stale = [
            k for k, s in self.sessions.items()
            if (now - s.last_access) > self.ttl_seconds
        ]
        for key in stale:
            del self.sessions[key]

        if len(self.sessions) <= self.max_sessions:
            return

        ordered = sorted(
            self.sessions.items(),
            key=lambda kv: kv[1].last_access,
        )
        for key, _ in ordered[: (len(self.sessions) - self.max_sessions)]:
            del self.sessions[key]
