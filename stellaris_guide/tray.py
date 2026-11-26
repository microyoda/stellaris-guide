"""Windows notification-area controls for reopening and closing the guide."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path


def start_tray(icon_path: Path, url: str, server, refresh_callback):
    """Start a tray icon on a background thread and return it.

    Importing the optional desktop packages here keeps parser tests and source
    use functional even before the Windows packaging dependencies are installed.
    """
    try:
        import pystray
        from PIL import Image
    except ImportError:
        return None

    image = Image.open(icon_path).convert("RGBA")

    def open_dashboard(_icon=None, _item=None):
        webbrowser.open(url)

    def refresh_save(_icon=None, _item=None):
        threading.Thread(target=refresh_callback, daemon=True).start()

    def quit_guide(icon, _item=None):
        icon.visible = False
        threading.Thread(target=server.shutdown, daemon=True).start()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open dashboard", open_dashboard, default=True),
        pystray.MenuItem("Refresh latest save", refresh_save),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Stellaris Guide", quit_guide),
    )
    icon = pystray.Icon("stellaris-guide", image, "Stellaris Guide", menu)
    threading.Thread(target=icon.run, name="StellarisGuideTray", daemon=True).start()
    return icon
