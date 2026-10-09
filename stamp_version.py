#!/usr/bin/env python3
"""Stamp the single-source version into static documentation files.

The repository keeps exactly one real version string: the VERSION file in the
project root. Python code reads it at runtime (decitect.version, the dynamic
pyproject metadata and the build scripts). Static files cannot read VERSION at
render time, so they instead carry a delimited token:

    <!--VERSION-->0.2.0<!--/VERSION-->

This script reads VERSION and rewrites whatever sits between every such token's
delimiters, across the GitHub Pages site under docs/. No documentation outside
the site carries version data, so the site is the whole stamped surface. It
is idempotent: stamping an already-current file changes nothing. Static files
are stamped from VERSION, never hand-edited, so a version cannot drift.

It also versions every site page's local stylesheet and script links by
content: each carries ?v=<hash> of the file it names. GitHub Pages lets a
browser keep a cached stylesheet for minutes after a deploy, so without the
hash a new page can render against old CSS. Any change to the file is a new
address. A link to a file that does not exist stops the run with its path.

Usage (from the project root):

    python stamp_version.py

Run it on every version bump and before each packaging build, so a release
always ships documentation whose version matches VERSION.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
DOCS_DIR = PROJECT_ROOT / "docs"
DEFAULT_VERSION = "0.0.0-dev"

# Delimiters that bracket a stamped version in any static file. The text
# between them is owned by this script and overwritten from VERSION each run.
VERSION_TOKEN_OPEN = "<!--VERSION-->"
VERSION_TOKEN_CLOSE = "<!--/VERSION-->"
VERSION_TOKEN_PATTERN = re.compile(
    re.escape(VERSION_TOKEN_OPEN) + ".*?" + re.escape(VERSION_TOKEN_CLOSE),
    re.DOTALL,
)

# A local stylesheet or script link and any query it already carries. A colon
# in the path means a scheme (http:, https:), so absolute URLs never match;
# root-absolute and protocol-relative paths are skipped in version_assets.
ASSET_HASH_LENGTH = 10
ASSET_LINK_PATTERN = re.compile(
    r'\b(?P<attribute>href|src)="(?P<path>[^"?#:]+\.(?:css|js))(?:\?[^"#]*)?"'
)


def read_version() -> str:
    """Return the project version from VERSION; a safe default if it is unset."""
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        version = ""
    return version or DEFAULT_VERSION


def target_files() -> list[Path]:
    """Return the static files that may carry a version token, deduplicated.

    The surface is the GitHub Pages site under docs/ (its HTML and any
    Markdown). Documentation outside the site carries no version data.
    """
    candidates: set[Path] = set()
    if DOCS_DIR.is_dir():
        candidates.update(DOCS_DIR.rglob("*.html"))
        candidates.update(DOCS_DIR.rglob("*.md"))
    return sorted(candidates)


def stamp_file(path: Path, version: str) -> bool:
    """Rewrite version tokens in one file. Return True if the file changed."""
    original = path.read_bytes().decode("utf-8")
    stamped = VERSION_TOKEN_PATTERN.sub(
        lambda _match: f"{VERSION_TOKEN_OPEN}{version}{VERSION_TOKEN_CLOSE}",
        original,
    )
    if stamped == original:
        return False
    path.write_bytes(stamped.encode("utf-8"))
    return True


def asset_hash(path: Path) -> str:
    """Return the short content hash of one site asset.

    CRLF is folded to LF first, so a Windows checkout and the LF blob GitHub
    serves give the same hash and a run on another machine churns nothing.
    """
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()[:ASSET_HASH_LENGTH]


def version_assets(page: Path) -> bool:
    """Set ?v=<hash> on one page's local asset links. Return True if changed."""
    original = page.read_bytes().decode("utf-8")

    def versioned(match: re.Match[str]) -> str:
        link = match.group("path")
        if link.startswith("/"):
            return match.group(0)
        asset = page.parent / unquote(link)
        if not asset.is_file():
            raise FileNotFoundError(f"{page} links {link}; {asset} does not exist")
        return f'{match.group("attribute")}="{link}?v={asset_hash(asset)}"'

    stamped = ASSET_LINK_PATTERN.sub(versioned, original)
    if stamped == original:
        return False
    page.write_bytes(stamped.encode("utf-8"))
    return True


def main() -> int:
    version = read_version()
    changed = [path for path in target_files() if stamp_file(path, version)]
    pages = [path for path in target_files() if path.suffix == ".html"]
    versioned = [path for path in pages if version_assets(path)]
    print(f"[stamp_version] VERSION = {version}")
    if not changed and not versioned:
        print("[stamp_version] No files needed stamping.")
        return 0
    for path in changed:
        print(f"[stamp_version] Stamped {path.relative_to(PROJECT_ROOT)}")
    for path in versioned:
        print(f"[stamp_version] Versioned assets in {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
