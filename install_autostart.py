"""
Mythos Boot Guard - Autostart Installer
=======================================
Registers Mythos Security Gateway to launch IMMEDIATELY after Windows login,
before the user can interact with the desktop.

Method: Windows Task Scheduler with trigger "On first logon".
Why Task Scheduler (not Startup folder)?
  - Runs faster (within ~1-2s of login, before Startup folder apps).
  - Cannot be bypassed by closing a normal app.
  - Persists across reboots automatically.
  - Survives Explorer restarts.

Usage:
    python install_autostart.py            # install
    python install_autostart.py --remove   # remove
    python install_autostart.py --status   # check status
"""
from __future__ import annotations
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_NAME = "MythosBootGuard"
BOOT_SCRIPT = os.path.join(HERE, "mythos_boot.py")


def _find_python() -> str:
    """Find a Python interpreter that has Mythos deps."""
    candidates = []
    exe = getattr(sys, "executable", None)
    if exe and os.path.isfile(exe):
        candidates.append(exe)
    for name in ("python.exe", "py.exe", "python3.exe"):
        try:
            p = subprocess.run(["where", name], capture_output=True,
                               text=True, timeout=5)
            if p.returncode == 0:
                for line in p.stdout.strip().splitlines():
                    candidates.append(line.strip())
        except Exception:
            pass
    # Verify deps.
    for c in candidates:
        try:
            r = subprocess.run(
                [c, "-c", "import requests, rich; print('ok')"],
                capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    return candidates[0] if candidates else ""


def _run_schtasks(args: list, capture: bool = True) -> tuple:
    """Run schtasks.exe with admin-aware invocation."""
    cmd = ["schtasks"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def is_installed() -> bool:
    rc, out, _ = _run_schtasks(["/Query", "/TN", TASK_NAME, "/FO", "LIST"])
    return rc == 0


def install() -> int:
    if not os.path.isfile(BOOT_SCRIPT):
        print(f"[Mythos] Boot script not found: {BOOT_SCRIPT}")
        return 1

    py = _find_python()
    if not py:
        print("[Mythos] No Python interpreter with deps found.")
        return 1
    print(f"[Mythos] Using Python: {py}")

    if is_installed():
        print(f"[Mythos] Task '{TASK_NAME}' already exists. Removing old one...")
        _run_schtasks(["/Delete", "/TN", TASK_NAME, "/F"])

    # Build the scheduled task XML for maximum control + speed.
    # Trigger: At logon of current user (fires within ~1s of login).
    # Action: run mythos_boot.py via pythonw (no extra console) — actually
    # we use python.exe so the fullscreen console lock screen is visible.
    # Settings: high priority, no time limit, run even on battery, restart on fail.
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Mythos Security Gateway - boot protection</Description>
    <Author>Mythos</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT0S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>5</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{_xml_escape(py)}</Command>
      <Arguments>"{_xml_escape(BOOT_SCRIPT)}"</Arguments>
      <WorkingDirectory>{_xml_escape(HERE)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
    xml_path = os.path.join(os.environ.get("TEMP", HERE), "_mythos_task.xml")
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml)

    rc, out, err = _run_schtasks(
        ["/Create", "/TN", TASK_NAME, "/XML", xml_path, "/F"]
    )
    try:
        os.unlink(xml_path)
    except OSError:
        pass

    if rc != 0:
        print(f"[Mythos] Failed to create task (exit {rc}).")
        print(f"         stdout: {out}")
        print(f"         stderr: {err}")
        print()
        print("If access denied, run this installer from an ELEVATED terminal:")
        print("  Right-click CMD -> Run as administrator -> run this script.")
        return 1

    print(f"[Mythos] Task '{TASK_NAME}' created successfully.")
    print()
    print("=" * 56)
    print("  MYTHOS BOOT GUARD INSTALLED")
    print("=" * 56)
    print(f"  Trigger   : At user logon (fires within ~1 second)")
    print(f"  Action    : {py}")
    print(f"               {BOOT_SCRIPT}")
    print(f"  Priority  : Above normal (starts fast)")
    print(f"  Restart   : Auto-restarts on crash (1 min, 999 tries)")
    print(f"  Battery   : Runs even on battery")
    print()
    print("  Next time you log into Windows, Mythos Security Gateway")
    print("  will appear BEFORE the desktop is usable.")
    print("=" * 56)
    return 0


def remove() -> int:
    if not is_installed():
        print(f"[Mythos] Task '{TASK_NAME}' is not installed.")
        return 0
    rc, _, err = _run_schtasks(["/Delete", "/TN", TASK_NAME, "/F"])
    if rc == 0:
        print(f"[Mythos] Task '{TASK_NAME}' removed.")
        return 0
    print(f"[Mythos] Failed to remove task: {err}")
    return 1


def status() -> int:
    rc, out, err = _run_schtasks(["/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"])
    if rc != 0:
        print(f"[Mythos] Task '{TASK_NAME}' is NOT installed.")
        print(f"         Run: python install_autostart.py")
        return 1
    print(out)
    return 0


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def main() -> int:
    print("=" * 56)
    print("  MYTHOS BOOT GUARD - AUTOSTART INSTALLER")
    print("=" * 56)
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--remove", "-r", "uninstall", "remove"):
            return remove()
        if arg in ("--status", "-s", "status"):
            return status()
        if arg in ("--install", "-i", "install"):
            return install()
    return install()


if __name__ == "__main__":
    sys.exit(main())
