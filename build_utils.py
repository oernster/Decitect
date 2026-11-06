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

# Qt pieces Nuitka's "sensible" PySide6 set ships that Decitect never loads.
# Dropping them shrinks every Nuitka build (app and installer, Windows and
# macOS) without touching what remains: Qt stays as separate, unmodified
# shared libraries beside the executable, so the LGPL-3.0 terms PySide6 ships
# under are kept exactly as before.
#
# Plugin categories: tls serves QtNetwork, which the structural tests forbid
# the app to import (the update check uses Python's own urllib); styles is
# never consulted because both programs call setStyle("fusion"); iconengines
# holds only the SVG icon engine and no icon is an SVG.
UNUSED_QT_PLUGIN_CATEGORIES = ("tls", "styles", "iconengines")
# Platform plugins beyond the native one: Direct2D is an alternative Windows
# backend and minimal/offscreen serve headless runs, which only the test
# suite makes (from source, never from a build).
UNUSED_QT_PLATFORMS = ("qdirect2d", "qminimal", "qoffscreen")
# Image formats: every image the programs load is a PNG (built into QtGui) or
# the .ico, so qico is the one format plugin kept. Leaving out qpdf and qsvg
# also leaves out the Qt Pdf and Qt Svg libraries they pull in.
UNUSED_QT_IMAGE_FORMATS = (
    "qgif",
    "qicns",
    "qjpeg",
    "qpdf",
    "qsvg",
    "qtga",
    "qtiff",
    "qwbmp",
    "qwebp",
)
# Nuitka resolves a plugin's libraries before it honours the exclusions above,
# so the libraries only those plugins needed (measured with --report: Qt Pdf,
# Svg and Network, all "used by" the qpdf or qsvg plugin) are named too. The
# second three are the macOS framework spellings of the same libraries.
UNUSED_QT_LIBRARIES = ("qt6network", "qt6pdf", "qt6svg", "QtNetwork", "QtPdf", "QtSvg")
# PySide6/__init__.py imports QtNetwork only when an "openssl" folder ships
# inside the package (none does in a Nuitka build) and catches ImportError
# around it, so the module can be left out without that branch ever failing.
UNUSED_QT_MODULES = ("PySide6.QtNetwork",)


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


def qt_trim_args() -> list[str]:
    """The Nuitka options that leave out the Qt pieces Decitect never loads.

    Plugin file names differ by platform (qjpeg.dll, libqjpeg.dylib), so each
    is matched with wildcards on both sides.
    """
    args = [f"--noinclude-qt-plugins={','.join(UNUSED_QT_PLUGIN_CATEGORIES)}"]
    for name in (*UNUSED_QT_PLATFORMS, *UNUSED_QT_IMAGE_FORMATS, *UNUSED_QT_LIBRARIES):
        args.append(f"--noinclude-dlls=*{name}*")
    for module in UNUSED_QT_MODULES:
        args.append(f"--nofollow-import-to={module}")
    return args


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
