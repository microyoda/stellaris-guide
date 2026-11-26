"""Read optional artwork from the user's own Stellaris installation."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re

from PIL import Image


DEFAULT_GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stellaris")
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_\-]+(?:\.dds)?$")


def _safe_file(folder: Path, name: str) -> Path | None:
    if not name or not SAFE_NAME.fullmatch(name):
        return None
    path = folder / name
    return path if path.is_file() else None


def _png(image: Image.Image) -> bytes:
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


@lru_cache(maxsize=8)
def flag_colors(game_dir: str) -> dict[str, tuple[int, int, int]]:
    path = Path(game_dir) / "flags" / "colors.txt"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return {}
    # Each palette entry starts with its name and flag RGB. Restrict parsing to
    # the color file and ignore its map and ship tint channels.
    return {name: (int(r), int(g), int(b)) for name, r, g, b in re.findall(
        r"(?m)^\s*([a-z_]+)\s*=\s*\{\s*flag\s*=\s*rgb\s*\{\s*(\d+)\s+(\d+)\s+(\d+)",
        text)}


@lru_cache(maxsize=32)
def render_flag(game_dir: str, category: str, icon_file: str,
                background_file: str, colors: tuple[str, ...]) -> bytes | None:
    root = Path(game_dir) / "flags"
    if not SAFE_NAME.fullmatch(category):
        return None
    icon_path = _safe_file(root / category, icon_file)
    background_path = _safe_file(root / "backgrounds", background_file)
    if not icon_path or not background_path:
        return None
    palette = flag_colors(game_dir)
    swatches = [palette.get(name, (32, 42, 58)) for name in colors[:3]]
    swatches += [(0, 0, 0)] * (3 - len(swatches))
    try:
        with Image.open(background_path) as source:
            background = source.convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
        pixels = []
        for y in range(background.height):
            for x in range(background.width):
                weights = background.getpixel((x, y))
                pixels.append(tuple(min(255, sum(weights[i] * swatches[i][channel] for i in range(3)) // 255)
                                    for channel in range(3)) + (255,))
        result = Image.new("RGBA", (128, 128))
        result.putdata(pixels)
        with Image.open(icon_path) as source:
            icon = source.convert("RGBA")
        icon.thumbnail((100, 100), Image.Resampling.LANCZOS)
        layer = Image.new("RGBA", (128, 128))
        layer.alpha_composite(icon, ((128 - icon.width) // 2, (128 - icon.height) // 2))
        result.alpha_composite(layer)
        return _png(result)
    except (OSError, ValueError):
        return None


@lru_cache(maxsize=128)
def game_icon(game_dir: str, kind: str, identifier: str) -> bytes | None:
    if not SAFE_NAME.fullmatch(identifier):
        return None
    subdir = {"technology": "technologies", "planet": "concepts/planet_classes"}.get(kind)
    if subdir is None:
        return None
    path = _safe_file(Path(game_dir) / "gfx" / "interface" / "icons" / subdir,
                      identifier + ".dds")
    if not path:
        return None
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")
            image.thumbnail((128, 128), Image.Resampling.LANCZOS)
            return _png(image)
    except (OSError, ValueError):
        return None
