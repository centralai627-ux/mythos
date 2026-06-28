"""
Mythos AI - Module Init
=======================
Modular CLI AI assistant focused on coding & shell execution.

Internal aliasing (never shown to user):
  - Mythos-Code  <- cohere/north-mini-code:free       (primary coding)
  - Mythos-Ultra <- nvidia/nemotron-3-ultra-550b-a55b:free (complex reasoning)
  - Mythos-Vision<- nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free (vision)
"""
from .config import config, load_config
from .key_manager import KeyManager, KeyRing
from .api_client import MythosAPI
from .executor import ShellExecutor
from .ai_brain import MythosBrain
from .vision import MythosVision
from .ui import MythosUI
from .agent import MythosAgent

__version__ = "1.0.0"
__app_name__ = "Mythos"

__all__ = [
    "config", "load_config",
    "KeyManager", "KeyRing",
    "MythosAPI", "ShellExecutor",
    "MythosBrain", "MythosVision", "MythosUI", "MythosAgent",
]
