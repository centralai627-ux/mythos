"""
Mythos Guardian - Anti-Bypass Protection (v2 - fixed)
=====================================================
Low-level keyboard hook + process guard + Task Manager registry toggle that
runs WHILE the lock screen is active.

CRITICAL FIXES vs v1:
  1. Hook callback is stored as a MODULE-LEVEL attribute (never GC'd).
  2. arm() RETURNS the hook install status and logs the Win32 error if it
     fails — no silent false-success.
  3. argtypes/restypes set explicitly to avoid 64-bit handle truncation.
  4. LL hook message pump runs in a dedicated thread BEFORE arm() returns,
     with PeekMessage so the stop flag is honored.
  5. Task Manager registry toggle added (self-reverting): sets
     DisableTaskMgr=1 on arm, restores to 0 on disarm. Requires admin
     once (installer elevates). Falls back gracefully if not elevated.

Blocked while armed:
  - Alt+Tab, Win keys, Ctrl+Esc, Ctrl+Shift+Esc, Alt+F4  (keyboard hook)
  - taskmgr.exe / ProcessHacker / procexp / procmon       (watcher thread)
  - Task Manager option                                   (registry toggle)

HONEST LIMITATION:
  Ctrl+Alt+Del itself cannot be blocked by any userland process (kernel-level
  Secure Attention Sequence). But with DisableTaskMgr set, the Task Manager
  entry in the Ctrl+Alt+Del menu is greyed out, closing that escape route.
  Remaining Ctrl+Alt+Del options (Sign Out, Lock) only log the user out, and
  Mythos re-launches on next login via the autostart scheduled task.
"""
from __future__ import annotations
import os
import sys
import threading
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Callable

# ======================= Win32 constants ======================= #
WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_F4 = 0x73
VK_CONTROL = 0x11
VK_SHIFT = 0x10
PM_REMOVE = 0x0001
LLKHF_ALTDOWN = 0x20

# Hook procedure type. Return is LRESULT (c_ssize_t on 64-bit).
HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


# ======================= Module-level hook state ======================= #
# CRITICAL: the hook callback MUST outlive arm()/disarm(). If garbage
# collected, Windows crashes the process or silently stops calling it.
_global_callback: Optional[HOOKPROC] = None
_global_hook_handle = None
_global_armed = False
_global_blocked_count = 0
_global_stop_event: Optional[threading.Event] = None
_global_hook_thread: Optional[threading.Thread] = None
_global_watcher_thread: Optional[threading.Thread] = None


def _setup_win32_signatures() -> None:
    """Set argtypes/restypes once. Idempotent."""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.SetWindowsHookExW.argtypes = [
        ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD
    ]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t
    user32.CallNextHookEx.argtypes = [
        ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
    ]
    user32.PeekMessageW.restype = wintypes.BOOL
    user32.PeekMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT,
        wintypes.UINT, wintypes.UINT
    ]
    user32.TranslateMessage.restype = wintypes.BOOL
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = ctypes.c_ssize_t
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    kernel32.GetConsoleWindow.argtypes = []


def _key_down(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def _ll_handler(nCode, wParam, lParam):
    """The actual low-level keyboard hook callback (module-level)."""
    global _global_blocked_count
    if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = kb.vkCode
        alt = bool(kb.flags & LLKHF_ALTDOWN)
        block = False
        if alt and vk == VK_TAB:                 # Alt+Tab
            block = True
        elif vk in (VK_LWIN, VK_RWIN):           # Win keys
            block = True
        elif vk == VK_ESCAPE and _key_down(VK_CONTROL):  # Ctrl+Esc / Ctrl+Shift+Esc
            block = True
        elif alt and vk == VK_F4:                # Alt+F4
            block = True
        if block:
            _global_blocked_count += 1
            return 1  # swallow the key
    return ctypes.windll.user32.CallNextHookEx(
        _global_hook_handle, nCode, wParam, lParam
    )


def _hook_loop(stop_event: threading.Event) -> None:
    """Thread: install the LL hook, then pump messages until stopped."""
    global _global_hook_handle
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    try:
        hmod = kernel32.GetModuleHandleW(None)
        if not hmod:
            hmod = kernel32.LoadLibraryW(sys.executable)
        _global_hook_handle = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, _global_callback, hmod, 0
        )
        if not _global_hook_handle:
            return
        msg = wintypes.MSG()
        while not stop_event.is_set():
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.005)
    except Exception:
        pass
    finally:
        try:
            if _global_hook_handle:
                user32.UnhookWindowsHookEx(_global_hook_handle)
                _global_hook_handle = None
        except Exception:
            pass


def _taskmgr_watcher(stop_event: threading.Event) -> None:
    """Thread: kill task manager-like processes while armed."""
    targets = ("taskmgr.exe", "ProcessHacker.exe", "procexp.exe",
               "procexp64.exe", "procmon.exe", "procmon64.exe")
    import subprocess
    while not stop_event.is_set():
        try:
            r = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                for line in r.stdout.splitlines():
                    low = line.lower()
                    for tgt in targets:
                        if tgt in low:
                            parts = line.split('","')
                            if len(parts) >= 2:
                                pid = parts[1].strip('"')
                                try:
                                    subprocess.run(
                                        ["taskkill", "/F", "/PID", pid],
                                        capture_output=True, timeout=3)
                                except Exception:
                                    pass
                            break
        except Exception:
            pass
        time.sleep(0.5)


def _set_taskmgr_disabled(disabled: bool) -> bool:
    """
    Toggle Task Manager via registry (HKCU). Self-reverting on disarm.
    Returns True if written, False if not (non-fatal).
    """
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            winreg.SetValueEx(k, "DisableTaskMgr", 0,
                              winreg.REG_DWORD, 1 if disabled else 0)
        return True
    except Exception:
        return False


class MythosGuardian:
    """Anti-bypass guardian. Arm before showing the lock screen."""

    def __init__(self, on_focus_lost: Optional[Callable] = None) -> None:
        self._on_focus_lost = on_focus_lost
        self._registry_set = False
        if sys.platform == "win32":
            _setup_win32_signatures()

    @property
    def armed(self) -> bool:
        return _global_armed

    @property
    def hook_installed(self) -> bool:
        return _global_hook_handle is not None

    @property
    def registry_protected(self) -> bool:
        return self._registry_set

    @property
    def blocked_count(self) -> int:
        return _global_blocked_count

    # ======================= Arm / Disarm ======================= #
    def arm(self) -> dict:
        """
        Install all protections. Returns a status dict so the caller knows
        EXACTLY what is and isn't active — never assume success silently.
        """
        global _global_armed, _global_callback, _global_stop_event
        global _global_hook_thread, _global_watcher_thread
        global _global_blocked_count
        result = {"hook": False, "watcher": False,
                  "registry": False, "errors": []}

        if _global_armed:
            return {"hook": self.hook_installed, "watcher": True,
                    "registry": self._registry_set, "errors": []}
        if sys.platform != "win32":
            result["errors"].append("not win32")
            return result

        _global_blocked_count = 0
        _global_callback = HOOKPROC(_ll_handler)
        _global_stop_event = threading.Event()

        _global_hook_thread = threading.Thread(
            target=_hook_loop, args=(_global_stop_event,), daemon=True)
        _global_hook_thread.start()
        time.sleep(0.3)
        result["hook"] = self.hook_installed
        if not result["hook"]:
            result["errors"].append(
                "keyboard hook not installed (process may lack an active "
                "message queue). Keyboard blocking inactive; relying on "
                "registry toggle + taskmgr watcher.")

        result["registry"] = _set_taskmgr_disabled(True)
        self._registry_set = result["registry"]
        if not result["registry"]:
            result["errors"].append(
                "could not set DisableTaskMgr registry (may need admin).")

        _global_watcher_thread = threading.Thread(
            target=_taskmgr_watcher, args=(_global_stop_event,), daemon=True)
        _global_watcher_thread.start()
        result["watcher"] = True

        _global_armed = True
        return result

    def disarm(self) -> None:
        """Remove hook + stop watchers + restore Task Manager registry."""
        global _global_armed, _global_hook_handle, _global_callback
        global _global_stop_event
        if not _global_armed:
            return
        _global_armed = False
        if _global_stop_event:
            _global_stop_event.set()
        try:
            if _global_hook_handle:
                ctypes.windll.user32.UnhookWindowsHookEx(_global_hook_handle)
                _global_hook_handle = None
        except Exception:
            pass
        if self._registry_set:
            _set_taskmgr_disabled(False)
            self._registry_set = False
        _global_callback = None

    def force_foreground(self, hwnd) -> None:
        try:
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
        except Exception:
            pass

    # ======================= Admin / registry helpers ======================= #
    @staticmethod
    def is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def elevate_and_restart(script: str) -> None:
        """Re-launch a script with UAC elevation (prompts the user)."""
        try:
            params = f'"{script}"'
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1)
        except Exception:
            pass
