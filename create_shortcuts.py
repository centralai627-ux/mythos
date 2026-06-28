"""
Mythos Shortcut Creator
=======================
Creates desktop shortcuts with modern Mythos logo.
No console window - runs silently.
"""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path

# Paths
MYTHOS_HOME = Path(__file__).parent.resolve()
DESKTOP = Path.home() / "Desktop"
START_MENU = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
MYTHOS_BAT = Path(os.environ.get("LOCALAPPDATA", "")) / "Mythos" / "bin" / "mythos.bat"
ICON_ICO = MYTHOS_HOME / "Mythos Desktop APp" / "desktop" / "assets" / "mythos.ico"


def find_python() -> str:
    """Find Python executable."""
    # Check Mythos venv first
    venv_py = MYTHOS_HOME / ".mythos_venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    
    # Check pythonw (no console)
    for name in ["pythonw.exe", "python.exe", "python3.exe", "py.exe"]:
        import shutil
        p = shutil.which(name)
        if p:
            return p
    
    return "python"


def find_pythonw() -> str:
    """Find pythonw.exe (no console window)."""
    import shutil
    
    # Check Mythos venv
    venv_pyw = MYTHOS_HOME / ".mythos_venv" / "Scripts" / "pythonw.exe"
    if venv_pyw.exists():
        return str(venv_pyw)
    
    # Check system pythonw
    p = shutil.which("pythonw.exe")
    if p:
        return p
    
    # Fallback to python.exe
    return find_python()


def create_vbs_launcher(vbs_path: Path, python_exe: str, script: str, args: str = "") -> None:
    """Create a VBS launcher that runs without console window."""
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """" & "{python_exe}" & """ """ & "{script}" & """ {args}", 0, False
'''
    vbs_path.write_text(vbs_content, encoding='utf-8')


def create_shortcut_vbs(
    name: str,
    vbs_path: Path,
    working_dir: str = "",
    description: str = "",
    icon: str = ""
) -> bool:
    """Create a Windows shortcut using PowerShell."""
    shortcut_path = DESKTOP / f"{name}.lnk"
    
    icon_arg = f', "{icon}"' if icon else ""
    
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{vbs_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "{description}"
$Shortcut.IconLocation = "{icon}{icon_arg}"
$Shortcut.Save()
'''
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_shortcut_direct(
    name: str,
    target: str,
    arguments: str = "",
    working_dir: str = "",
    description: str = "",
    icon: str = ""
) -> bool:
    """Create a shortcut directly to an executable."""
    shortcut_path = DESKTOP / f"{name}.lnk"
    
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "{description}"
$Shortcut.IconLocation = "{icon}"
$Shortcut.Save()
'''
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_mythos_shortcuts() -> None:
    """Create all Mythos shortcuts."""
    print("=" * 50)
    print("  MYTHOS AI - Shortcut Creator")
    print("=" * 50)
    
    python_exe = find_python()
    pythonw_exe = find_pythonw()
    mythos_py = str(MYTHOS_HOME / "mythos.py")
    icon_path = str(ICON_ICO) if ICON_ICO.exists() else ""
    
    # Create VBS launchers folder
    vbs_dir = MYTHOS_HOME / ".mythos_launchers"
    vbs_dir.mkdir(exist_ok=True)
    
    # 1. Main Mythos CLI (Terminal)
    print("\n[1/3] Creating Mythos CLI shortcut...")
    cli_vbs = vbs_dir / "mythos_cli.vbs"
    create_vbs_launcher(cli_vbs, python_exe, mythos_py)
    create_shortcut_vbs(
        name="Mythos CLI",
        vbs_path=cli_vbs,
        working_dir=str(MYTHOS_HOME),
        description="Mythos AI Command Line",
        icon=icon_path
    )
    
    # 2. Mythos Desktop App (Electron)
    print("[2/3] Creating Mythos Desktop App shortcut...")
    desktop_app = MYTHOS_HOME / "Mythos Desktop APp" / "desktop"
    
    # Check if node_modules exists (npm install was run)
    node_modules = desktop_app / "node_modules"
    electron_exe = desktop_app / "node_modules" / ".bin" / "electron.cmd"
    
    if electron_exe.exists():
        # Run Electron directly (no console)
        desktop_vbs = vbs_dir / "mythos_desktop.vbs"
        electron_main = desktop_app / "main.js"
        
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """ & "{electron_exe}" & """ """ & "{electron_main}" & """", 0, False
'''
        desktop_vbs.write_text(vbs_content, encoding='utf-8')
        
        create_shortcut_vbs(
            name="Mythos Desktop App",
            vbs_path=desktop_vbs,
            working_dir=str(desktop_app),
            description="Mythos AI Desktop Application",
            icon=icon_path
        )
    else:
        # Create batch that runs npm and hide console
        start_vbs = vbs_dir / "mythos_desktop.vbs"
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{desktop_app}"
WshShell.Run "cmd /c npm run dev", 0, False
'''
        start_vbs.write_text(vbs_content, encoding='utf-8')
        
        create_shortcut_vbs(
            name="Mythos Desktop App",
            vbs_path=start_vbs,
            working_dir=str(desktop_app),
            description="Mythos AI Desktop Application",
            icon=icon_path
        )
        print("  (Run 'npm install' in desktop folder first)")
    
    # 3. Start Menu shortcuts
    print("[3/3] Creating Start Menu shortcuts...")
    startmenu_dir = START_MENU / "Mythos AI"
    startmenu_dir.mkdir(parents=True, exist_ok=True)
    
    # CLI in Start Menu
    cli_shortcut_sm = startmenu_dir / "Mythos CLI.lnk"
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{cli_shortcut_sm}")
$Shortcut.TargetPath = "{cli_vbs}"
$Shortcut.WorkingDirectory = "{MYTHOS_HOME}"
$Shortcut.Description = "Mythos AI Command Line"
$Shortcut.IconLocation = "{icon_path}"
$Shortcut.Save()
'''
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    
    print()
    print("=" * 50)
    print("  Shortcuts created!")
    print("=" * 50)
    print()
    print("  Desktop:")
    print("    - Mythos CLI (opens terminal)")
    print("    - Mythos Desktop App (GUI)")
    print()
    print("  Start Menu > Mythos AI:")
    print("    - Mythos CLI")
    print("=" * 50)


def remove_shortcuts() -> None:
    """Remove all Mythos shortcuts."""
    print("Removing shortcuts...")
    
    shortcuts = [
        DESKTOP / "Mythos CLI.lnk",
        DESKTOP / "Mythos Desktop App.lnk",
        DESKTOP / "Mythos AI.lnk",
        START_MENU / "Mythos AI" / "Mythos CLI.lnk",
    ]
    
    for shortcut in shortcuts:
        if shortcut.exists():
            shortcut.unlink()
            print(f"  Removed: {shortcut.name}")
    
    # Remove VBS launchers
    vbs_dir = MYTHOS_HOME / ".mythos_launchers"
    if vbs_dir.exists():
        import shutil
        shutil.rmtree(vbs_dir)
        print("  Removed launcher scripts")
    
    print("Done!")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if args and args[0] in ("--remove", "-r", "uninstall"):
        remove_shortcuts()
    else:
        create_mythos_shortcuts()
