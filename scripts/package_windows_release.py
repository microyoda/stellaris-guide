"""Package only the v1.6.4 player files and installed dependency notices."""

from __future__ import annotations

import importlib.metadata as metadata
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.6.4"
OUTPUT = ROOT / "dist" / f"StellarisGuide-Windows-{VERSION}.zip"
FILES = {
    "StellarisGuide.exe": ROOT / "dist" / f"release-{VERSION}" / "StellarisGuide.exe",
    "INSTALL-WINDOWS.txt": ROOT / "INSTALL-WINDOWS.txt",
    "docs/INSTALL.md": ROOT / "docs" / "INSTALL.md",
    "docs/RELEASE-1.6.4.md": ROOT / "docs" / "RELEASE-1.6.4.md",
}
DEPENDENCIES = ("Pillow", "pystray", "six", "PyInstaller", "altgraph",
                "pefile", "pywin32-ctypes")


def release_entries() -> dict[str, Path]:
    entries = dict(FILES)
    python_license = Path(sys.executable).parent / "LICENSE.txt"
    if not python_license.is_file():
        raise FileNotFoundError("Python runtime license text missing")
    entries["licenses/Python-LICENSE.txt"] = python_license
    for package in DEPENDENCIES:
        distribution = metadata.distribution(package)
        package_root = Path(distribution.locate_file("")).resolve()
        found = False
        for relative in distribution.files or ():
            name = str(relative).replace("\\", "/")
            if "license" not in name.casefold() and "copying" not in name.casefold():
                continue
            if not relative.parts or not str(relative.parts[0]).casefold().endswith(".dist-info"):
                continue
            source = Path(distribution.locate_file(relative)).resolve()
            if (source.is_relative_to(package_root) and source.is_file()
                    and source.stat().st_size <= 2_000_000):
                entries[f"licenses/{package}/{source.name}"] = source
                found = True
        if not found:
            raise RuntimeError(f"Missing license text for {package}")
    missing = [str(path) for path in entries.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Release file missing: " + ", ".join(missing))
    return entries


def main() -> None:
    entries = release_entries()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, source in entries.items():
            archive.write(source, archive_name)
    print(f"Packaged {len(entries)} allowed files: {OUTPUT}")


if __name__ == "__main__":
    main()
