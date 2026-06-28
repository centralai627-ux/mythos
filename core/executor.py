"""
Mythos Shell Executor
=====================
High-precision CMD & PowerShell execution with output capture,
exit-code handling, and safe structured execution.

Design:
  - Detect available shells on Windows (cmd.exe / powershell.exe / pwsh).
  - Run commands with timeout & encoding safety.
  - Capture stdout/stderr separately for clean UI rendering.
  - Atomic file operations for code-writing.
  - Never block the main UI thread unexpectedly.
"""
from __future__ import annotations
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field


@dataclass
class ExecResult:
    """Structured result of a shell command."""
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    shell: str = ""
    command: str = ""
    timed_out: bool = False

    def short(self, max_lines: int = 20) -> str:
        out = self.stdout.strip()
        if not out:
            return "(no output)"
        lines = out.splitlines()
        if len(lines) <= max_lines:
            return out
        return "\n".join(lines[:max_lines]) + f"\n... [{len(lines) - max_lines} more lines]"


class ShellExecutor:
    """
    Shell abstraction for Windows (cmd / powershell / pwsh) and POSIX fallback.
    Auto-detects best shell and routes commands accordingly.
    """

    # Markers used to wrap PowerShell output for clean parsing.
    _PS_START = "__MYTHOS_OUT_START__"
    _PS_END = "__MYTHOS_OUT_END__"

    def __init__(self, cwd: Optional[str] = None) -> None:
        self.cwd = cwd or os.getcwd()
        self._lock = threading.Lock()
        self._encoding = "utf-8"

    # ----------------------- Detection ----------------------- #
    def detect_shells(self) -> Dict[str, Optional[str]]:
        """Find available shells."""
        return {
            "cmd": shutil.which("cmd.exe") or shutil.which("cmd"),
            "powershell": shutil.which("powershell.exe") or shutil.which("powershell"),
            "pwsh": shutil.which("pwsh.exe") or shutil.which("pwsh"),
            "bash": shutil.which("bash"),
        }

    def best_shell(self) -> str:
        """Pick the most capable shell available."""
        shells = self.detect_shells()
        for name in ("pwsh", "powershell", "bash", "cmd"):
            if shells.get(name):
                return name
        return "cmd"  # Always present on Windows.

    # ----------------------- Public API ----------------------- #
    def run(
        self,
        command: str,
        shell: Optional[str] = None,
        timeout: float = 120.0,
        cwd: Optional[str] = None,
    ) -> ExecResult:
        """Execute a single command and return a structured result."""
        shell = shell or self._auto_detect(command)
        cwd = cwd or self.cwd
        start = time.time()
        try:
            if shell in ("powershell", "pwsh"):
                res = self._run_powershell(command, shell, timeout, cwd)
            elif shell == "bash":
                res = self._run_posix(command, timeout, cwd)
            else:
                res = self._run_cmd(command, timeout, cwd)
        except subprocess.TimeoutExpired:
            return ExecResult(
                success=False, exit_code=-1, shell=shell, command=command,
                timed_out=True, duration=time.time() - start,
                stderr=f"Command timed out after {timeout}s.",
            )
        except Exception as e:
            return ExecResult(
                success=False, exit_code=-2, shell=shell, command=command,
                duration=time.time() - start, stderr=str(e),
            )

        res.duration = time.time() - start
        res.shell = shell
        res.command = command
        return res

    def run_batch(self, commands: List[str], shell: Optional[str] = None,
                  timeout: float = 300.0) -> List[ExecResult]:
        """Run a sequence of commands, stopping on first failure."""
        results: List[ExecResult] = []
        for cmd in commands:
            r = self.run(cmd, shell=shell, timeout=timeout)
            results.append(r)
            if not r.success:
                break
        return results

    # ----------------------- Shell-specific runners ----------------------- #
    def _auto_detect(self, command: str) -> str:
        """Pick shell based on command content."""
        # PowerShell-ish patterns.
        ps_patterns = [
            r"Get-\w+", r"Set-\w+", r"New-\w+", r"Remove-\w+",
            r"\$\w+", r"^\s*-", r"\| ?Where-Object", r"Write-",
            r"Invoke-", r"Select-String", r"-Filter\b", r"-Name\b",
        ]
        for pat in ps_patterns:
            if re.search(pat, command):
                return "powershell"
        # Bash-ish patterns.
        if any(tok in command for tok in ("&&", "||", ">", "|")):
            return self.best_shell()
        return self.best_shell()

    def _run_cmd(self, command: str, timeout: float, cwd: str) -> ExecResult:
        proc = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True,
            text=True, encoding=self._encoding, errors="replace",
            timeout=timeout,
        )
        return ExecResult(
            success=(proc.returncode == 0),
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )

    def _run_powershell(self, command: str, shell: str, timeout: float,
                        cwd: str) -> ExecResult:
        exe = "pwsh" if shell == "pwsh" else "powershell"
        # Build a clean wrapper: set error pref, run the command, capture
        # $LASTEXITCODE. We invoke via -Command so the user expression is
        # evaluated directly (no scriptblock double-wrapping).
        # Use base64-safe approach: write a temp .ps1 and run it. This avoids
        # quoting/escaping pitfalls for complex pipelines.
        import tempfile as _tf
        ps_script = (
            "$ErrorActionPreference='Continue'\n"
            f"{command}\n"
            "Write-Output \"__MYTHOS_EXIT__:$LASTEXITCODE\"\n"
        )
        fd, tmp_ps1 = _tf.mkstemp(suffix=".ps1")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(ps_script)
            proc = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", tmp_ps1],
                cwd=cwd, capture_output=True, text=True,
                encoding=self._encoding, errors="replace", timeout=timeout,
            )
        finally:
            try:
                os.unlink(tmp_ps1)
            except OSError:
                pass

        out = proc.stdout or ""
        stderr = proc.stderr or ""
        body, exit_code = self._extract_exit(out)
        if stderr.strip():
            body = (body + ("\n" if body else "") + stderr).strip()
        return ExecResult(
            success=(exit_code == 0),
            exit_code=exit_code,
            stdout=body,
            stderr="",
        )

    def _extract_exit(self, raw: str) -> Tuple[str, int]:
        """Strip the trailing __MYTHOS_EXIT__ line and return (body, code)."""
        exit_code = 0
        body = raw
        # Marker may have a number (native exe set $LASTEXITCODE) or be empty
        # (cmdlet-only commands leave it null). Handle both.
        m = re.search(r"__MYTHOS_EXIT__:(-?\d+)?\s*$", raw)
        if m:
            if m.group(1) is not None:
                exit_code = int(m.group(1))
            body = raw[:m.start()].rstrip()
        body = body.lstrip("\ufeff")
        return body, exit_code

    def _run_posix(self, command: str, timeout: float, cwd: str) -> ExecResult:
        proc = subprocess.run(
            ["bash", "-c", command], cwd=cwd, capture_output=True,
            text=True, encoding=self._encoding, errors="replace",
            timeout=timeout,
        )
        return ExecResult(
            success=(proc.returncode == 0),
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )

    # ----------------------- File operations ----------------------- #
    def atomic_write(self, path: str, content: str) -> bool:
        """Atomic file write — never leaves a half-written file."""
        with self._lock:
            try:
                d = os.path.dirname(os.path.abspath(path)) or "."
                os.makedirs(d, exist_ok=True)
                fd, tmp = tempfile.mkstemp(
                    dir=d, prefix=".mythos_", suffix=".tmp"
                )
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                os.replace(tmp, path)
                return True
            except OSError:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                return False

    def safe_read(self, path: str, max_bytes: int = 2_000_000) -> Optional[str]:
        """Read a file safely with size guard."""
        try:
            size = os.path.getsize(path)
            if size > max_bytes:
                return None
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return None
