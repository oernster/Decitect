"""Where the application keeps its per-user state; adopting the old one.

Settings and the session autosave live under one dot-directory in the
user's home. Every release before 5.0.0 shipped under the name Fulcrum and
kept the same files under ``~/.fulcrum``; the first launch under the new
name moves that directory into place so nobody's settings or session are
left behind by the rename.
"""

from __future__ import annotations

import shutil
from pathlib import Path

STATE_DIR_NAME = ".decitect"
# The directory every release before the rename wrote. It is read only by
# the launch that finds no state of its own, which moves it across.
LEGACY_STATE_DIR_NAME = ".fulcrum"


def state_dir(home: Path | None = None) -> Path:
    """The per-user state directory under the current product name."""
    return (home if home is not None else Path.home()) / STATE_DIR_NAME


def legacy_state_dir(home: Path | None = None) -> Path:
    """The per-user state directory the product wrote before the rename."""
    return (home if home is not None else Path.home()) / LEGACY_STATE_DIR_NAME


def resolve_state_dir(home: Path) -> Path:
    """The directory this run should read and write, adopting the old one.

    The current directory wins whenever it exists: it is the record from
    then on and an old directory beside it is left alone. With no current
    directory and an old one present, the old one is moved into place. A
    move that fails answers the old directory itself, so the run still finds
    the user's session rather than starting empty and writing a new one that
    would hide the old files from every later launch.
    """
    current = state_dir(home)
    legacy = legacy_state_dir(home)
    if current.exists() or not legacy.is_dir():
        return current
    try:
        shutil.move(str(legacy), str(current))
    except OSError:
        return legacy
    return current
