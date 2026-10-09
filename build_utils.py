#!/usr/bin/env python3
"""Shared shell helpers for the Decitect build scripts."""

from __future__ import annotations

import importlib.metadata
import itertools
import shutil
import subprocess
import sys

# The Nuitka the packaged builds are written against: the release Stellody
# moved to on 2026-09-13. An older one left in the environment stops the build
# here, rather than a release nobody chose compiling what ships.
NUITKA_MINIMUM = (4, 2, 1)


def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check, **kwargs)


def require(tool: str, brew_pkg: str | None = None) -> None:
    if shutil.which(tool):
        return
    pkg = brew_pkg or tool
    print(f"{tool} not found, installing via brew...")
    run(["brew", "install", pkg])
    if not shutil.which(tool):
        sys.exit(f"ERROR: {tool} still not found after brew install. Aborting.")


def require_nuitka() -> None:
    """Stop where Nuitka is missing or older than the build is written against."""
    try:
        installed = importlib.metadata.version("nuitka")
    except importlib.metadata.PackageNotFoundError:
        installed = None
    if installed is not None and _release(installed) >= NUITKA_MINIMUM:
        return
    wanted = ".".join(str(number) for number in NUITKA_MINIMUM)
    found = (
        f"Nuitka {installed} is installed" if installed else "Nuitka is not installed"
    )
    sys.exit(
        f"ERROR: {found}; this build needs {wanted} or later:\n"
        "    python -m pip install -r requirements-dev.txt"
    )


def _release(version: str) -> tuple[int, ...]:
    """The numeric release of a version string, '4.2.1rc1' reading as 4.2.1."""
    return tuple(
        int("".join(itertools.takewhile(str.isdigit, part)) or 0)
        for part in version.split(".")
    )


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
