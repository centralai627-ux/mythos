"""
Mythos AI - Global Wrapper Installer
====================================
Registers Mythos as a global command callable from ANY directory in CMD,
PowerShell, or any terminal.

What it does:
  1. Creates a stable wrapper directory: %LOCALAPPDATA%\\Mythos\\bin
  2. Writes a portable `mythos.bat` there that forwards all args to the
     real entry point (mythos.py) using an absolute path.
  3. Adds that bin dir to the USER PATH (HKCU\\Environment) — no admin needed.
  4. Broadcasts WM_SETTINGCHANGE so new terminals pick it up immediately.
  5. Auto-installs missing Python dependencies (fpdf2, pypdf, etc.).

After running this once, you can type `Mythos` from anywhere.

Usage:
    python install_global.py           # install
    python install_global.py --update  # re-check deps + rewrite wrapper
    python install_global.py --remove  # uninstall
"""
from __future__ import annotations
import os
import sys
import shutil
import ctypes

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY = os.path.join(HERE, "mythos.py")

# Stable wrapper location in user profile (persists across reinstalls).
BIN_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                       "Mythos", "bin")
WRAPPER = os.path.join(BIN_DIR, "mythos.bat")

# The wrapper script content. Uses absolute paths so it works from any CWD.
WRAPPER_CONTENT = """\
@echo off
REM ================================================================
REM  Mythos AI v1.0.0 — Global Launcher
REM  Installed by install_global.py — Glasswing Edition
REM  Forwards all arguments to the Mythos CLI entry point.
REM ================================================================
setlocal
set "MYTHOS_HOME={home}"
set "MYTHOS_ENTRY={entry}"
set "PY="

REM Prefer the Python that installed this wrapper.
if exist "{pyexe}" (
    set "PY={pyexe}"
) else (
    REM Fallback: search PATH for any python.
    for %%P in (python py python3) do (
        where %%P >nul 2>&1
        if not errorlevel 1 (
            set "PY=%%P"
            goto :runit
        )
    )
    echo [Mythos] Python not found on PATH. Install Python 3.9+ and retry.
    exit /b 1
)

:runit
REM Launch Mythos with all passed arguments.
"%PY%" "%MYTHOS_ENTRY%" %*
endlocal
"""


# Required Python packages for Mythos (core + PDF capabilities).
REQUIRED_PACKAGES = {
    "requests": "requests",
    "rich": "rich",
    "colorama": "colorama",
    "fpdf": "fpdf2",
    "pypdf": "pypdf",
}


def _has_deps(python_exe: str) -> bool:
    """Check that a python.exe can import ALL required Mythos packages."""
    code = "import sys; ok=True\n"
    for mod in REQUIRED_PACKAGES:
        code += f"try:\n    import {mod}\nexcept ImportError:\n    ok=False\n"
    code += "sys.exit(0 if ok else 1)\n"
    try:
        import subprocess
        r = subprocess.run(
            [python_exe, "-c", code],
            capture_output=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def _missing_deps(python_exe: str) -> list:
    """Return list of (module_name, pip_package) that are missing."""
    missing = []
    for mod, pkg in REQUIRED_PACKAGES.items():
        code = (
            f"import sys\n"
            f"try:\n    import {mod}\n    sys.exit(0)\n"
            f"except ImportError:\n    sys.exit(1)\n"
        )
        try:
            import subprocess
            r = subprocess.run(
                [python_exe, "-c", code],
                capture_output=True, timeout=10,
            )
            if r.returncode != 0:
                missing.append(pkg)
        except Exception:
            missing.append(pkg)
    return missing


def _install_deps(python_exe: str, packages: list) -> bool:
    """Install missing packages via pip. Returns True on success."""
    if not packages:
        return True
    import subprocess
    print(f"[Mythos] Installing missing deps: {', '.join(packages)}")
    try:
        r = subprocess.run(
            [python_exe, "-m", "pip", "install", "--quiet", *packages],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            print(f"[Mythos] pip install failed: {r.stderr.strip()}")
            return False
        print(f"[Mythos] Dependencies installed successfully.")
        return True
    except Exception as e:
        print(f"[Mythos] pip install error: {e}")
        return False


def _find_python_exe() -> str:
    """Return absolute path to a Python interpreter that has Mythos deps."""
    # 1) Current interpreter (most reliable — it ran Mythos before).
    exe = os.path.abspath(sys.executable)
    if os.path.isfile(exe) and _has_deps(exe):
        return exe
    # 2) _base_executable (for venv re-exports).
    base = getattr(sys, "_base_executable", None)
    if base and os.path.isfile(base) and _has_deps(base):
        return base
    # 3) Search common candidates on PATH.
    for name in ("python.exe", "python3.exe", "py.exe"):
        p = shutil.which(name)
        if p and _has_deps(p):
            return os.path.abspath(p)
    # 4) Fallback: any python at all (deps may still be importable).
    for name in ("python.exe", "py.exe", "python3.exe"):
        p = shutil.which(name)
        if p:
            return os.path.abspath(p)
    return ""


# ----------------------- Windows PATH registry helpers ----------------------- #
def _read_user_path() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment",
                            0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, "Path")
            return val or ""
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def _write_user_path(value: str) -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment",
                            0, winreg.KEY_WRITE) as k:
            winreg.SetValueEx(k, "Path", 0, winreg.REG_EXPAND_SZ, value)
        return True
    except Exception:
        return False


def _broadcast_change() -> None:
    """Tell other apps (incl. new CMD windows) to reload environment vars."""
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        res = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            0, 5000, ctypes.byref(res)
        )
    except Exception:
        pass


# ----------------------- Install / Remove ----------------------- #
def install() -> int:
    if not os.path.isfile(ENTRY):
        print(f"[Mythos] Entry point not found: {ENTRY}")
        return 1

    pyexe = _find_python_exe()
    if not pyexe:
        print("[Mythos] No Python interpreter found. Install Python 3.9+ first.")
        return 1
    print(f"[Mythos] Using Python: {pyexe}")

    # Check and auto-install missing dependencies.
    missing = _missing_deps(pyexe)
    if missing:
        print(f"[Mythos] Missing dependencies detected: {', '.join(missing)}")
        if not _install_deps(pyexe, missing):
            print("[Mythos] WARNING: Some dependencies could not be installed.")
            print("         Install them manually: pip install " + " ".join(missing))
    else:
        print(f"[Mythos] All {len(REQUIRED_PACKAGES)} dependencies satisfied.")

    os.makedirs(BIN_DIR, exist_ok=True)

    # Write the portable wrapper.
    content = WRAPPER_CONTENT.format(
        home=HERE, entry=ENTRY, pyexe=pyexe,
    )
    with open(WRAPPER, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)
    print(f"[Mythos] Wrapper written -> {WRAPPER}")

    # Add BIN_DIR to user PATH (idempotent).
    cur = _read_user_path()
    parts = [p for p in cur.split(os.pathsep) if p]
    if BIN_DIR.lower() in (p.lower() for p in parts):
        print(f"[Mythos] PATH already contains {BIN_DIR}")
    else:
        new_path = (cur.rstrip(";") + ";" + BIN_DIR) if cur else BIN_DIR
        if _write_user_path(new_path):
            print(f"[Mythos] Added to user PATH: {BIN_DIR}")
            _broadcast_change()
        else:
            print("[Mythos] WARNING: could not write PATH registry key.")
            print("         Add this folder to PATH manually:")
            print(f"         {BIN_DIR}")

    print()
    print("=" * 56)
    print("  MYTHOS GLASSWING IS NOW INSTALLED GLOBALLY")
    print("=" * 56)
    print("  Open a NEW terminal (CMD or PowerShell) and type:")
    print()
    print("      Mythos                  <- anywhere you like")
    print()
    print("  Capabilities: code, shell, web, PDF, vision")
    print("  Auto-updates: enabled (checks on launch)")
    print("  Force update: python mythos.py --update")
    print("  Existing terminals need restart to see the PATH change.")
    print("=" * 56)
    return 0


def remove() -> int:
    removed = []
    if os.path.isfile(WRAPPER):
        os.unlink(WRAPPER)
        removed.append(WRAPPER)
    try:
        os.rmdir(BIN_DIR)
        removed.append(BIN_DIR + os.sep)
    except OSError:
        pass

    cur = _read_user_path()
    parts = [p for p in cur.split(os.pathsep) if p]
    new_parts = [p for p in parts if p.lower() != BIN_DIR.lower()]
    if new_parts != parts:
        _write_user_path(os.pathsep.join(new_parts))
        removed.append("PATH entry")
        _broadcast_change()

    if removed:
        print("[Mythos] Removed:")
        for r in removed:
            print(f"  - {r}")
    else:
        print("[Mythos] Nothing to remove.")
    return 0


def main() -> int:
    print("=" * 56)
    print("  MYTHOS AI  -  GLASSWING GLOBAL INSTALLER")
    print("  v1.0.0  |  code + shell + web + PDF + vision")
    print("=" * 56)
    args = sys.argv[1:]
    if args and args[0] in ("--remove", "-r", "uninstall"):
        return remove()
    if args and args[0] in ("--update", "-u", "update"):
        print("[Mythos] Running update: re-checking deps + rewriting wrapper...")
        return install()
    return install()


if __name__ == "__main__":
    sys.exit(main())
