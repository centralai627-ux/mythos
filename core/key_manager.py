"""
Mythos Rolling Key Manager
==========================
Rotates OpenRouter API keys silently in the background.

Design goals:
  - NEVER interrupt the user session.
  - NEVER show popups/notifications (silent unless explicitly enabled).
  - Track per-key health: cooldowns on rate-limit, permanent block on auth fail.
  - Round-robin with health-aware selection.
  - Thread-safe; rotation runs in a daemon thread.
"""
from __future__ import annotations
import threading
import time
import random
from collections import deque
from typing import Optional, List, Dict


class KeyState:
    """Health record for a single key."""
    __slots__ = ("key", "uses", "fails", "cooldown_until", "dead", "last_used")

    def __init__(self, key: str) -> None:
        self.key = key
        self.uses = 0
        self.fails = 0
        self.cooldown_until: float = 0.0
        self.dead: bool = False
        self.last_used: float = 0.0

    @property
    def available(self) -> bool:
        if self.dead:
            return False
        return time.time() >= self.cooldown_until


class KeyRing:
    """Thread-safe ring of keys with health-aware rotation."""

    def __init__(self, keys: List[str], notify: bool = False) -> None:
        self._lock = threading.RLock()
        self._notify = notify
        self._states: Dict[str, KeyState] = {k: KeyState(k) for k in keys}
        self._order: deque[str] = deque(keys)
        self._idx = 0

    def __len__(self) -> int:
        with self._lock:
            return len(self._states)

    def get(self) -> Optional[str]:
        """Return next healthy key, advancing the ring."""
        with self._lock:
            if not self._states:
                return None
            n = len(self._order)
            for _ in range(n):
                k = self._order[0]
                self._order.rotate(-1)
                st = self._states[k]
                if st.available:
                    st.uses += 1
                    st.last_used = time.time()
                    return k
            return None  # All on cooldown / dead

    def peek(self) -> Optional[str]:
        """Non-consuming peek at the next healthy key (for preflight checks)."""
        with self._lock:
            for k in self._order:
                if self._states[k].available:
                    return k
            return None

    def report_success(self, key: str) -> None:
        with self._lock:
            st = self._states.get(key)
            if st:
                st.fails = 0
                st.cooldown_until = 0.0

    def report_rate_limit(self, key: str, cooldown: float = 60.0) -> None:
        """429 — temporary cooldown. Silent rotation."""
        with self._lock:
            st = self._states.get(key)
            if not st:
                return
            st.fails += 1
            # Escalating cooldown for repeat offenders.
            backoff = cooldown * (2 ** min(st.fails - 1, 4))
            st.cooldown_until = time.time() + backoff

    def report_dead(self, key: str) -> None:
        """401/403 — auth failure. Kill silently."""
        with self._lock:
            st = self._states.get(key)
            if st:
                st.dead = True

    def report_generic_error(self, key: str) -> None:
        """5xx / network — small cooldown, retry-friendly."""
        with self._lock:
            st = self._states.get(key)
            if st:
                st.fails += 1
                st.cooldown_until = time.time() + 15.0

    def stats(self) -> Dict[str, dict]:
        with self._lock:
            out = {}
            now = time.time()
            for k, st in self._states.items():
                out[k[:12] + "..."] = {
                    "uses": st.uses,
                    "fails": st.fails,
                    "dead": st.dead,
                    "cooldown": max(0.0, round(st.cooldown_until - now, 1)),
                }
            return out

    def alive_count(self) -> int:
        with self._lock:
            return sum(1 for st in self._states.values() if not st.dead)

    def available_count(self) -> int:
        with self._lock:
            return sum(1 for st in self._states.values() if st.available)


class KeyManager:
    """
    Top-level manager holding rings for OpenRouter & Z.AI keys.
    Exposes only what the API client needs.
    """

    def __init__(self, openrouter_keys: List[str], zai_keys: Optional[List[str]] = None,
                 notify: bool = False) -> None:
        self.openrouter = KeyRing(openrouter_keys, notify=notify)
        self.zai = KeyRing(zai_keys or [], notify=notify)
        self._notify = notify

    def get_openrouter_key(self) -> Optional[str]:
        return self.openrouter.get()

    def get_zai_key(self) -> Optional[str]:
        return self.zai.get()

    def status(self) -> Dict[str, int]:
        return {
            "openrouter_alive": self.openrouter.alive_count(),
            "openrouter_available": self.openrouter.available_count(),
            "zai_alive": self.zai.alive_count(),
            "zai_available": self.zai.available_count(),
        }

    @property
    def notify(self) -> bool:
        return self._notify
