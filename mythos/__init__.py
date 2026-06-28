#!/usr/bin/env python3
"""
Mythos AI - Entry Point
=======================
Launch the Mythos CLI agent.

Usage:
    mythos                     # Interactive REPL
    mythos "question"          # One-shot mode
    mythos --lock              # Launch lock screen (security)
    mythos --version
    mythos --update            # Force update wrapper
"""
from __future__ import annotations
import os
import sys

# Get the package root directory
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PACKAGE_DIR)

# Ensure local imports work regardless of CWD.
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _PACKAGE_DIR not in sys.path:
    sys.path.insert(0, _PACKAGE_DIR)

# Auto-update check on launch
try:
    from auto_update import check_and_update
    check_and_update()
except Exception:
    pass

from core.agent import MythosAgent  # noqa: E402
from core.api_client import APIError  # noqa: E402


BANNER_FALLBACK = "MYTHOS"


def main() -> int:
    args = sys.argv[1:]

    # --lock : launch security lock screen.
    if args and args[0] in ("--lock", "-l"):
        from core.lock_screen import LockScreen
        ls = LockScreen()
        result = ls.run()
        if result == "unlock":
            # Proceed to normal Mythos.
            args = args[1:]  # remove --lock
            if not args:
                # No further args -> interactive REPL.
                pass
            else:
                # Fall through to one-shot or other modes.
                return _run_normal(args)
        else:
            # "close" -> exit.
            return 0

    # --version / --help / --update
    if args and args[0] in ("-v", "--version"):
        print("Mythos v1.0.0")
        return 0
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args and args[0] in ("--update", "-u"):
        from auto_update import force_update
        force_update()
        print("Wrapper updated. Restart terminal to use latest version.")
        return 0

    return _run_normal(args)


def _run_normal(args: list) -> int:
    """Run Mythos in normal mode (REPL or one-shot)."""
    agent = MythosAgent()

    # One-shot mode: a single quoted request.
    if args:
        user_text = " ".join(args)
        try:
            agent.ui.boot_screen(
                version="1.0.0",
                keys_alive=agent.keys.openrouter.alive_count(),
            )
            agent._process_request(user_text)
        except APIError as e:
            agent.ui.error(str(e))
            return 1
        return 0

    # Interactive REPL.
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.ui.info("\nInterrupted. Exiting.")
    except APIError as e:
        agent.ui.error(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
