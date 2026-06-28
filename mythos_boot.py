#!/usr/bin/env python3
"""
Mythos Boot Guard - Entry Point
===============================
Launched automatically by Windows Task Scheduler at logon (via
install_autostart.py). Arms the anti-bypass guardian, runs the Mythos
Security Gateway lock screen, then launches Mythos on unlock.

Flow:
  1. Arm Guardian (block Alt+Tab, Win, Ctrl+Esc, kill Task Manager).
  2. Show fullscreen lock screen (Security Gateway challenge).
  3. User enters Cetharis to unlock, or Dissa to close.
  4. On unlock: disarm Guardian -> launch Mythos.
  5. On close: keep Guardian active briefly then exit (system stays at
     lock until next login, since autostart won't re-fire this session).

Usage (manual):
    python mythos_boot.py
"""
from __future__ import annotations
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from core.guardian import MythosGuardian
from core.lock_screen import LockScreen


def main() -> int:
    # 1. Arm the anti-bypass guardian FIRST (before any window appears).
    guardian = MythosGuardian()
    guardian.arm()

    try:
        # 2. Show the lock screen challenge (fullscreen, controls disabled).
        lock = LockScreen()
        result = lock.run()

        if result == "unlock":
            # 3a. Disarm, then launch Mythos interactively.
            guardian.disarm()
            # Import here so heavy deps only load after unlock.
            from core.agent import MythosAgent
            agent = MythosAgent()
            agent.start()
            return 0
        else:
            # 3b. User chose to close (Dissa). Keep desktop inaccessible by
            # staying in a holding loop until the process is ended. We keep
            # the guardian armed for a short grace period then exit; the
            # session ends here. Next login re-triggers via Task Scheduler.
            guardian.disarm()
            return 2

    except KeyboardInterrupt:
        guardian.disarm()
        return 1
    except Exception as e:
        # Never leave the guardian armed if we crash.
        guardian.disarm()
        sys.stderr.write(f"[mythos_boot] fatal: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
