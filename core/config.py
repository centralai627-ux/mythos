"""
Mythos Configuration Loader
===========================
Loads settings, applies runtime overrides, and exposes them globally.
"""
from __future__ import annotations
import json
import os
from copy import deepcopy
from typing import Any, Dict, Optional

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")
_STATE_PATH = os.path.join(_BASE_DIR, "core", "state.json")


class MythosConfig:
    """Runtime configuration with persistent key-state tracking."""

    def __init__(self, path: str = _CONFIG_PATH) -> None:
        self.path = path
        self._data: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {}
        self.load()

    # ----------------------- I/O ----------------------- #
    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        if os.path.exists(_STATE_PATH):
            try:
                with open(_STATE_PATH, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._state = {}
        else:
            self._state = {}

    def save_state(self) -> None:
        """Persist rolling-key state without interrupting the user."""
        try:
            tmp = _STATE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            os.replace(tmp, _STATE_PATH)
        except OSError:
            pass  # Silent: rolling must never block UX.

    # ----------------------- Accessors ----------------------- #
    @property
    def llm(self) -> Dict[str, Any]:
        return self._data.get("llm", {})

    @property
    def models(self) -> Dict[str, str]:
        return self._data.get("models", {})

    @property
    def system(self) -> Dict[str, Any]:
        return self._data.get("system", {})

    @property
    def optimization(self) -> Dict[str, Any]:
        return self._data.get("optimization", {})

    @property
    def base_url(self) -> str:
        return self.llm.get("base_url", "https://openrouter.ai/api/v1")

    @property
    def timeout(self) -> int:
        return int(self.llm.get("timeout", 60))

    @property
    def temperature(self) -> float:
        return float(self.llm.get("temperature", 0.2))

    @property
    def shannon(self) -> Dict[str, Any]:
        return self._data.get("shannon", {})

    @property
    def shannon_keys(self) -> list:
        return list(self.shannon.get("keys", []))

    @property
    def shannon_base_url(self) -> str:
        return self.shannon.get("base_url", "https://api.shannon-ai.com/v1")

    def get_shannon_model(self, alias: str) -> str:
        """Resolve internal Shannon model alias (shannon-1/shannon-2)."""
        models = self.shannon.get("models", {})
        return models.get(alias, models.get("shannon-1", "shannon-coder-1"))

    @property
    def mimo(self) -> Dict[str, Any]:
        """Get MiMo configuration."""
        return self._data.get("mimo", {})
    
    @property
    def mimo_keys(self) -> list:
        """Get MiMo API keys."""
        return list(self.mimo.get("keys", []))
    
    @property
    def mimo_base_url(self) -> str:
        """Get MiMo API base URL."""
        return self.mimo.get("base_url", "https://api.xiaomimimo.com/v1")
    
    def get_mimo_model(self, alias: str) -> str:
        """Resolve internal MiMo model alias."""
        models = self.mimo.get("models", {})
        return models.get(alias, models.get("mimo-v2-pro", "mimo-v2-pro"))
    
    @property
    def mimo_tts_config(self) -> Dict[str, Any]:
        """Get MiMo TTS configuration."""
        return self.mimo.get("tts", {})

    @property
    def max_tokens(self) -> int:
        return int(self.optimization.get("max_tokens", 2048))

    @property
    def openrouter_keys(self) -> list:
        return list(self.llm.get("openrouter_keys", []))

    @property
    def zai_keys(self) -> list:
        return list(self.llm.get("zai_keys", []))

    @property
    def notify_rolling(self) -> bool:
        return bool(self.system.get("notify_rolling", False))

    def get_model(self, alias: str) -> str:
        """Resolve internal alias to real model id (NEVER exposed to user)."""
        return self.models.get(alias, self.models.get("code"))

    # ----------------------- State (key rotation) ----------------------- #
    def get_key_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_key_state(self, key: str, value: Any) -> None:
        self._state[key] = value
        self.save_state()

    def __getitem__(self, item: str) -> Any:
        return self._data[item]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


# Global singleton.
config = MythosConfig()


def load_config(path: Optional[str] = None) -> MythosConfig:
    """Re-load config from disk (used by tests & manual refresh)."""
    global config
    if path:
        config = MythosConfig(path)
    else:
        config.load()
    return config
