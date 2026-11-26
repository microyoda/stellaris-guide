"""Launch and close only Guide-owned technology route Edge app windows."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlencode


ACTIVE_ROUTES: dict[str, dict] = {}
TITLE_PREFIX = "Stellaris Guide Research Route "
ROUTE_PROFILES = Path(os.getenv("LOCALAPPDATA", Path.home())) / "StellarisGuide" / "route-windows"


def edge_executable() -> Path | None:
    if sys.platform != "win32":
        return None
    roots = [os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")]
    for root in roots:
        if root:
            candidate = Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if candidate.is_file():
                return candidate
    return None


def _route_title_present(instance: str) -> bool:
    """Check whether a route window still exists, without taking ownership of it."""
    if sys.platform != "win32":
        return True
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.EnumWindows.argtypes = [callback_type, ctypes.c_void_p]
    user32.EnumWindows.restype = ctypes.c_bool
    present = False

    @callback_type
    def visit(hwnd, _):
        nonlocal present
        length = user32.GetWindowTextLengthW(hwnd)
        if length == len(TITLE_PREFIX + instance):
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            present = present or _route_title_matches(title.value, instance)
        return not present

    user32.EnumWindows(visit, 0)
    return present


def _profile_argument_matches(command_line: str, profile: Path) -> bool:
    expected = re.escape(str(profile.resolve()))
    pattern = rf'(?<!\S)"?--user-data-dir=(?:"{expected}"|{expected})"?(?=\s|$)'
    return re.search(pattern, command_line, re.IGNORECASE) is not None


def _profile_has_live_edge(profile: Path) -> bool | None:
    """Return None when Windows cannot establish whether the profile is in use."""
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-Command", "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" "
             "-ErrorAction Stop | Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=4, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return _profile_argument_matches(result.stdout, profile)


def launch_edge_route(base_url: str, campaign_id: str, target: str) -> str:
    edge = edge_executable()
    if edge is None:
        raise ValueError("Microsoft Edge was not found. Open this route from Edge or install Edge.")
    now = time.time()
    for key, record in list(ACTIVE_ROUTES.items()):
        if now - record["created"] > 60 and not _route_title_present(key):
            ACTIVE_ROUTES.pop(key, None)
            cleanup = threading.Thread(target=_cleanup_profile, args=(record["profile"],), daemon=True)
            cleanup.start()
    if len(ACTIVE_ROUTES) >= 4:
        raise ValueError("Close an existing technology route window before opening another.")
    instance = secrets.token_urlsafe(24)
    url = f"{base_url}/tech-route.html?{urlencode({'campaign': campaign_id, 'target': target, 'instance': instance})}"
    profile = ROUTE_PROFILES / instance
    profile.mkdir(parents=True, exist_ok=False)
    try:
        subprocess.Popen([str(edge), "--new-window", f"--app={url}",
                          f"--user-data-dir={profile}", "--no-first-run"], close_fds=True)
    except OSError:
        shutil.rmtree(profile, ignore_errors=True)
        raise
    ACTIVE_ROUTES[instance] = {"created": now, "profile": profile}
    return instance


def _route_title_matches(title: str, instance: str) -> bool:
    return title == TITLE_PREFIX + instance


def _new_process(process: int, created_after: float) -> bool:
    """An older Edge window may show this URL as a tab; never close that window."""
    created = wintypes.FILETIME()
    exited = wintypes.FILETIME()
    kernel = wintypes.FILETIME()
    user = wintypes.FILETIME()
    if not ctypes.windll.kernel32.GetProcessTimes(process, ctypes.byref(created),
                                                   ctypes.byref(exited), ctypes.byref(kernel),
                                                   ctypes.byref(user)):
        return False
    epoch = ((created.dwHighDateTime << 32) | created.dwLowDateTime) / 10_000_000 - 11_644_473_600
    return epoch >= created_after - 2


def _edge_uses_profile(pid: int, profile: Path) -> bool:
    """Fail closed unless Windows reports the exact Guide-created Edge profile."""
    if not isinstance(pid, int) or pid <= 0 or sys.platform != "win32":
        return False
    command = (
        f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' "
        "-ErrorAction Stop).CommandLine"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-Command", command],
            capture_output=True, text=True, timeout=4, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    return _profile_argument_matches(result.stdout.strip(), profile)


def _matching_edge_window(instance: str) -> int | None:
    """Find the exact route title and verify the owning process is Edge."""
    if sys.platform != "win32":
        return None
    expected = TITLE_PREFIX + instance
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    found = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
    user32.EnumWindows.argtypes = [callback_type, ctypes.c_void_p]
    user32.EnumWindows.restype = ctypes.c_bool
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                                                   ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.QueryFullProcessImageNameW.restype = ctypes.c_bool
    kernel32.GetProcessTimes.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.FILETIME),
                                         ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                         ctypes.POINTER(wintypes.FILETIME)]
    kernel32.GetProcessTimes.restype = ctypes.c_bool
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_bool

    @callback_type
    def visit(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length < len(expected):
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, length + 1)
        if not _route_title_matches(title.value, instance):
            return True
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = kernel32.OpenProcess(0x1000, False, pid.value)
        if not process:
            return True
        try:
            size = ctypes.c_ulong(32768)
            name = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(process, 0, name, ctypes.byref(size)):
                record = ACTIVE_ROUTES.get(instance)
                if (record is not None and Path(name.value).name.lower() == "msedge.exe" and
                        _new_process(process, record["created"]) and
                        _edge_uses_profile(pid.value, record["profile"])):
                    found.append(int(hwnd))
        finally:
            kernel32.CloseHandle(process)
        return True

    user32.EnumWindows(visit, 0)
    return found[0] if len(found) == 1 else None


def _cleanup_profile(profile: Path) -> None:
    """Retry while Edge releases its files; never remove an unowned directory."""
    if profile.parent != ROUTE_PROFILES or not profile.name or not profile.is_dir():
        return
    for _ in range(6):
        time.sleep(3)
        if _profile_has_live_edge(profile) is not False:
            continue
        try:
            shutil.rmtree(profile)
        except OSError:
            continue
        return


def close_edge_route(instance: str) -> bool:
    if instance not in ACTIVE_ROUTES:
        return False
    hwnd = _matching_edge_window(instance)
    if hwnd is None:
        return False
    post_message = ctypes.windll.user32.PostMessageW
    post_message.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_size_t, ctypes.c_ssize_t]
    post_message.restype = ctypes.c_bool
    if not post_message(hwnd, 0x0010, 0, 0):
        return False
    record = ACTIVE_ROUTES.pop(instance, None)
    if record:
        cleanup = threading.Thread(target=_cleanup_profile, args=(record["profile"],))
        cleanup.daemon = True
        cleanup.start()
    return True
