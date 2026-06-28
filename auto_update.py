"""
Mythos Auto-Update Wrapper
==========================
Self-updating wrapper that detects changes and rebuilds automatically.
"""
from __future__ import annotations
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

HERE = Path(__file__).parent.resolve()
BIN_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Mythos" / "bin"
WRAPPER = BIN_DIR / "mythos.bat"
STATE_FILE = BIN_DIR / ".update_state.json"

# Files to watch for changes
WATCH_FILES = [
    "mythos.py",
    "auto_update.py",
    "core/agent.py",
    "core/commands.py",
    "core/ai_brain.py",
    "core/tools.py",
    "core/ui.py",
    "core/config.py",
    "core/executor.py",
    "core/key_manager.py",
    "core/api_client.py",
    "core/vision.py",
]


def _file_hash(path: Path) -> str:
    """Get MD5 hash of a file."""
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load_state() -> dict:
    """Load previous state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"hashes": {}, "version": "0.0.0"}


def _save_state(state: dict) -> None:
    """Save current state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _check_changes() -> list:
    """Check which files have changed since last check."""
    state = _load_state()
    changed = []
    
    for fname in WATCH_FILES:
        fpath = HERE / fname
        current_hash = _file_hash(fpath)
        prev_hash = state.get("hashes", {}).get(fname, "")
        
        if current_hash != prev_hash:
            changed.append(fname)
            state.setdefault("hashes", {})[fname] = current_hash
    
    _save_state(state)
    return changed


def _regenerate_wrapper() -> bool:
    """Regenerate the global wrapper bat file."""
    try:
        # Find Python executable
        pyexe = sys.executable
        if not os.path.isfile(pyexe):
            pyexe = ""
        
        wrapper_content = f"""@echo off
REM ================================================================
REM  Mythos AI v1.0.0 - Global Launcher (Auto-Updated)
REM  Forwards all arguments to the Mythos CLI entry point.
REM ================================================================
setlocal
set "MYTHOS_HOME={HERE}"
set "MYTHOS_ENTRY={HERE / 'mythos.py'}"
set "PY="

if exist "{pyexe}" (
    set "PY={pyexe}"
) else (
    for %%P in (python py python3) do (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            set "PY=%%P"
            goto :runit
        )
    )
    echo [Mythos] Python not found. Install Python 3.9+ and retry.
    exit /b 1
)

:runit
"%PY%" "%MYTHOS_ENTRY%" %*
endlocal
"""
        
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        WRAPPER.write_text(wrapper_content, encoding="utf-8", newline="\r\n")
        return True
    except Exception as e:
        print(f"[Mythos Auto-Update] Failed to regenerate wrapper: {e}")
        return False


def _broadcast_change() -> None:
    """Notify Windows about PATH changes."""
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        res = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            0, 5000, ctypes.byref(res)
        )
    except Exception:
        pass


def check_and_update() -> bool:
    """
    Check for changes and auto-update if needed.
    Returns True if an update was performed.
    """
    changed = _check_changes()
    
    if not changed:
        return False
    
    print(f"[Mythos] Detected changes in: {', '.join(changed)}")
    print("[Mythos] Auto-updating wrapper...")
    
    if _regenerate_wrapper():
        _broadcast_change()
        print("[Mythos] Wrapper updated successfully.")
        return True
    else:
        print("[Mythos] Wrapper update failed.")
        return False


def force_update() -> None:
    """Force a full update regardless of changes."""
    state = _load_state()
    state["hashes"] = {}  # Clear all hashes to force re-check
    _save_state(state)
    check_and_update()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        force_update()
    else:
        check_and_update()
