"""
Mythos AI - Installer
=====================
Verifies dependencies, optionally adds Mythos to PATH, and runs a
quick self-test to confirm the system is ready.
"""
from __future__ import annotations
import os
import sys
import subprocess
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

REQUIRED = {
    "requests": "requests",
    "rich": "rich",
    "colorama": "colorama",
    "prompt_toolkit": "prompt_toolkit",
    "fpdf": "fpdf2",
    "pypdf": "pypdf",
}


def check_python() -> bool:
    v = sys.version_info
    if v < (3, 9):
        print(f"✗ Python 3.9+ required (you have {v.major}.{v.minor}).")
        return False
    print(f"✓ Python {v.major}.{v.minor}.{v.micro}")
    return True


def check_deps() -> bool:
    missing = []
    for mod, pkg in REQUIRED.items():
        try:
            __import__(mod)
            print(f"✓ {pkg}")
        except ImportError:
            print(f"✗ {pkg} (missing)")
            missing.append(pkg)
    if missing:
        print(f"\nInstalling missing: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", *missing]
        )
        return True
    return True


def install_path() -> None:
    """Offer to add Mythos directory to user PATH (Windows)."""
    if os.name != "nt":
        return
    try:
        import winreg
    except ImportError:
        return
    try:
        ans = input("\nAdd Mythos to user PATH? (y/N): ").strip().lower()
    except EOFError:
        return  # Non-interactive mode — skip silently.
    if ans != "y":
        return
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE
    )
    try:
        cur, _ = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        cur = ""
    if HERE in cur.split(os.pathsep):
        print("✓ Already in PATH.")
        winreg.CloseKey(key)
        return
    new = (cur.rstrip(";") + ";" + HERE) if cur else HERE
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new)
    winreg.CloseKey(key)
    # Broadcast WM_SETTINGCHANGE so other shells pick it up.
    import ctypes
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 1000, None
    )
    print(f"✓ Added {HERE} to user PATH. Restart your terminal to use `Mythos`.")


def ensure_boot_venv() -> bool:
    """
    Create a dedicated venv inside Mythos for boot-time lock screen.
    This venv is standalone and works without any external environment.
    """
    venv_dir = os.path.join(HERE, ".mythos_venv")
    venv_py = os.path.join(venv_dir, "Scripts", "python.exe")

    # Check if venv already exists and works.
    if os.path.isfile(venv_py):
        try:
            r = subprocess.run(
                [venv_py, "-c", "import rich; import colorama; print('ok')"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and "ok" in r.stdout:
                print(f"✓ Boot venv ready: {venv_dir}")
                return True
        except Exception:
            pass

    print("\n— Creating boot venv —")
    print(f"  Creating venv at: {venv_dir}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "venv", venv_dir],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create venv: {e}")
        return False

    # Install deps into the venv.
    pkgs = [v for v in REQUIRED.values()]
    print(f"  Installing: {', '.join(pkgs)}")
    try:
        subprocess.check_call(
            [venv_py, "-m", "pip", "install", "--quiet", *pkgs],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install deps into venv: {e}")
        return False

    print(f"✓ Boot venv ready: {venv_dir}")
    return True


def self_test() -> bool:
    print("\n— Self-test —")
    try:
        sys.path.insert(0, HERE)
        from core.config import config
        print(f"✓ config loaded: {len(config.openrouter_keys)} OR keys, "
              f"{len(config.zai_keys)} ZAI keys")
        from core.key_manager import KeyManager
        km = KeyManager(config.openrouter_keys, config.zai_keys)
        print(f"✓ key ring ready: {km.openrouter.alive_count()} alive")
        from core.executor import ShellExecutor
        ex = ShellExecutor()
        shells = ex.detect_shells()
        avail = [k for k, v in shells.items() if v]
        print(f"✓ shells detected: {', '.join(avail) or 'none'}")
        r = ex.run("echo mythos-ok", shell="cmd")
        if r.success and "mythos-ok" in r.stdout:
            print("✓ CMD execution works")
        else:
            print(f"⚠ CMD test: exit={r.exit_code}")
        return True
    except Exception as e:
        print(f"✗ Self-test failed: {e}")
        return False


def main() -> int:
    args = sys.argv[1:]

    # Handle auto-start commands.
    if args and args[0] in ("--install-autostart", "-a"):
        print("=" * 52)
        print("  MYTHOS AI  ·  AUTO-START INSTALLER")
        print("=" * 52)
        from core.lock_screen import install_autostart
        if install_autostart():
            print("\n✓ Lock screen will appear on next boot.")
            print("  Answers: Cetharis (unlock) / Dissa (close)")
        else:
            print("\n✗ Auto-start installation failed.")
            return 1
        return 0

    if args and args[0] in ("--remove-autostart",):
        print("=" * 52)
        print("  MYTHOS AI  ·  AUTO-START REMOVAL")
        print("=" * 52)
        from core.lock_screen import uninstall_autostart
        uninstall_autostart()
        return 0

    print("=" * 52)
    print("  MYTHOS AI  ·  INSTALLER")
    print("=" * 52)
    if not check_python():
        return 1
    check_deps()
    ensure_boot_venv()
    self_test()
    install_path()
    print("\n" + "=" * 52)
    print("  Done. Launch with:  Mythos    (or  python mythos.py)")
    print()
    print("  Security:  python install.py --install-autostart")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
