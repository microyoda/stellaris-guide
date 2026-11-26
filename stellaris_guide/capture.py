"""One-shot Windows capture for the local desktop package.

The browser capture picker cannot target a named window. PrintWindow obtains
the selected window's pixels even when another application covers the game.
Pillow encodes the one-shot image after the player clicks Camera.
"""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
from io import BytesIO
import os
from pathlib import Path


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("width", wintypes.LONG),
                ("height", wintypes.LONG), ("planes", wintypes.WORD),
                ("bits", wintypes.WORD), ("compression", wintypes.DWORD),
                ("image_size", wintypes.DWORD), ("xppm", wintypes.LONG),
                ("yppm", wintypes.LONG), ("used", wintypes.DWORD),
                ("important", wintypes.DWORD)]


class _BitmapInfo(ctypes.Structure):
    _fields_ = [("header", _BitmapInfoHeader), ("colors", wintypes.DWORD * 3)]


def available() -> bool:
    return os.name == "nt"


def _process_name(pid: int) -> str:
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                    wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return Path(buffer.value).name.lower()
    finally:
        kernel32.CloseHandle(handle)
    return ""


def list_windows() -> list[dict]:
    if not available():
        return []
    user32 = ctypes.windll.user32
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    results = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def visit(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length < 2:
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, length + 1)
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        app = _process_name(pid.value)
        if app in ("explorer.exe", "applicationframehost.exe") and not title.value:
            return True
        results.append({"id": int(hwnd), "title": title.value[:180], "app": app,
                        "stellaris": app == "stellaris.exe"})
        return True

    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumWindows(visit, 0)
    results.sort(key=lambda item: (not item["stellaris"], item["title"].lower()))
    return results[:100]


def _print_window(handle: int):
    """Copy a window's own pixels, including when another window covers it."""
    from PIL import Image, ImageStat

    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = ctypes.c_void_p
    user32.ReleaseDC.argtypes = [wintypes.HWND, ctypes.c_void_p]
    gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi32.CreateDIBSection.argtypes = [ctypes.c_void_p, ctypes.POINTER(_BitmapInfo), wintypes.UINT,
                                       ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, wintypes.DWORD]
    gdi32.CreateDIBSection.restype = ctypes.c_void_p
    gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi32.SelectObject.restype = ctypes.c_void_p
    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
    user32.PrintWindow.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.UINT]
    user32.PrintWindow.restype = wintypes.BOOL

    rect = wintypes.RECT()
    if not user32.GetWindowRect(handle, ctypes.byref(rect)):
        raise ValueError("The selected window is no longer available.")
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width < 16 or height < 16 or width > 16000 or height > 16000:
        raise ValueError("The selected window has no usable image size.")

    screen_dc = user32.GetDC(None)
    memory_dc = bitmap = old_bitmap = None
    try:
        memory_dc = gdi32.CreateCompatibleDC(screen_dc)
        info = _BitmapInfo()
        info.header.size = ctypes.sizeof(_BitmapInfoHeader)
        info.header.width = width
        info.header.height = -height  # top-down pixels
        info.header.planes = 1
        info.header.bits = 32
        pixels = ctypes.c_void_p()
        bitmap = gdi32.CreateDIBSection(screen_dc, ctypes.byref(info), 0, ctypes.byref(pixels), None, 0)
        if not memory_dc or not bitmap or not pixels.value:
            raise ValueError("Windows could not prepare the screenshot.")
        old_bitmap = gdi32.SelectObject(memory_dc, bitmap)
        if not user32.PrintWindow(handle, memory_dc, 2):
            raise ValueError("Windows could not capture this window. Try borderless or windowed mode.")
        raw = ctypes.string_at(pixels, width * height * 4)
        image = Image.frombytes("RGB", (width, height), raw, "raw", "BGRX", 0, 1)
        if max(ImageStat.Stat(image.resize((48, 48))).stddev) < 1:
            raise ValueError("The game window returned a blank image. Try borderless or windowed mode.")
        return image
    finally:
        if old_bitmap and memory_dc:
            gdi32.SelectObject(memory_dc, old_bitmap)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory_dc:
            gdi32.DeleteDC(memory_dc)
        if screen_dc:
            user32.ReleaseDC(None, screen_dc)


def capture(target: int | str) -> str:
    if not available():
        raise ValueError("Native capture is available only in the Windows app")
    from PIL import ImageGrab

    if target == "screen":
        image = ImageGrab.grab(all_screens=True)
    else:
        try:
            handle = int(target)
        except (TypeError, ValueError):
            raise ValueError("Choose a valid window") from None
        if handle not in {item["id"] for item in list_windows()}:
            raise ValueError("That window is no longer available")
        image = _print_window(handle)
    if not image or image.width < 2 or image.height < 2:
        raise ValueError("The window could not be captured. Choose another window or screen")
    image = image.convert("RGB")
    if image.width > 1800 or image.height > 1200:
        image.thumbnail((1800, 1200))
    output = BytesIO()
    image.save(output, format="JPEG", quality=86, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")
