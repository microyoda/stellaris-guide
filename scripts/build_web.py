"""Build the Option 1 100% client-side static web version into dist-web/.

Bundles the dashboard UI, pure-Python engine modules for Pyodide, and
precomputed instant demo snapshots so the site can be hosted on GitHub Pages
or Cloudflare Pages with zero server backend and zero save uploads.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stellaris_guide.web_bridge import generate_static_demo_bundle

STATIC_DIR = ROOT / "static"
PKG_DIR = ROOT / "stellaris_guide"
OUT_DIR = ROOT / "dist-web"

WEB_PYTHON_FILES = (
    "__init__.py",
    "dlcs.py",
    "saves.py",
    "strategy.py",
    "playbooks.py",
    "playbooks.json",
    "guide_knowledge.py",
    "guide_knowledge.json",
    "traditions_data.py",
    "question_context.py",
    "advice.py",
    "tech_graph.json",
    "web_bridge.py",
)


def _rewrite_index_for_web(html: str) -> str:
    """Make asset paths relative for subpath hosting (e.g. GitHub Pages) and inject web runtime."""
    rewritten = (
        html.replace('href="/', 'href="./')
            .replace('src="/', 'src="./')
            .replace(
                '<link rel="stylesheet" href="./fleet.css">',
                '<link rel="stylesheet" href="./fleet.css">\n  <link rel="stylesheet" href="./web.css">',
            )
            .replace(
                '<script src="./art.js"></script>',
                '<script src="./dds-art.js"></script>\n  <script src="./web-runtime.js"></script>\n  <script src="./art.js"></script>',
            )
    )
    return rewritten


def build_web(output_dir: Path = OUT_DIR) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy static assets.
    for item in STATIC_DIR.iterdir():
        target = output_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        elif item.name == "index.html":
            target.write_text(_rewrite_index_for_web(item.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(item, target)

    # Copy pure-Python core modules only (never Win32 capture/tray/route_window/server).
    py_out = output_dir / "py" / "stellaris_guide"
    py_out.mkdir(parents=True, exist_ok=True)
    for name in WEB_PYTHON_FILES:
        src = PKG_DIR / name
        if not src.is_file():
            raise FileNotFoundError(f"Missing required web Python file: {src}")
        shutil.copy2(src, py_out / name)

    # Precompute instant demo snapshots for <100ms first paint.
    bundle = generate_static_demo_bundle()
    (output_dir / "demo-snapshots.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Ensure GitHub Pages serves dotfiles/subfolders cleanly.
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    return output_dir


if __name__ == "__main__":
    dest = build_web()
    print(f"Built static web companion into: {dest}")
