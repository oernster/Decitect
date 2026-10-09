"""Finding and retiring an install left by the product's former name.

Every release before 5.0.0 shipped as Fulcrum: its own install directory,
Apps list entry, sign-in entry, shortcuts and notification identity. Setup
under the new name finds such an install, says exactly what it found and
removes it only when the user leaves that option ticked. Anything it cannot
show belongs to that install (a shortcut or a sign-in entry pointing
elsewhere) is left where it is.

The user's state directory is deliberately not in the plan: the application
adopts ``~/.fulcrum`` on its first launch, so removing it here would throw
away the very session the rename promises to keep.

Like installer_logic, this module decides and never acts. Nothing here
imports from the ``decitect`` package.

British spelling is used in comments. No em dashes appear anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import installer_logic as logic

LEGACY_APP_NAME = "Fulcrum"
LEGACY_EXE_NAME = "fulcrum.exe"
LEGACY_UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Fulcrum"
LEGACY_RUN_VALUE = "Fulcrum"
LEGACY_AUMID = "uk.codecrafter.fulcrum"
# Must match the application's LEGACY_STATE_DIR_NAME, so an uninstall that
# removes settings also removes a directory a failed adoption left behind.
# tests/installer/test_state_dir.py pins the two together.
LEGACY_STATE_DIR_NAME = ".fulcrum"

_QUOTE = '"'


@dataclass(frozen=True, slots=True)
class LegacyInstall:
    """An install under the former name: where it is and what it said it was."""

    location: Path
    version: str


def default_location(local_appdata: str | None, home: Path) -> Path:
    """Return where the former name's installer put the application."""
    return logic.programs_dir(local_appdata, home) / LEGACY_APP_NAME


def find_legacy(
    version: str | None, registered: Path | None, default: Path
) -> LegacyInstall | None:
    """Return the install under the former name, else None.

    The registered location wins; with no registration the default location
    still counts when the directory is there, since a half-removed install
    is exactly the one a user cannot clear by hand.
    """
    for location in (registered, default):
        if location is not None and location.is_dir():
            return LegacyInstall(location=location, version=version or "")
    return None


def option_text(legacy: LegacyInstall) -> str:
    """Return the caption of the option that removes the old install."""
    named = f"{LEGACY_APP_NAME} {legacy.version}".strip()
    return f"Remove the old {named} install at {legacy.location}"


def shortcut_links(appdata: str | None, home: Path) -> tuple[Path, ...]:
    """Return where the former name's shortcuts would be, nearest first."""
    links = [logic.desktop_link(home, LEGACY_APP_NAME)]
    start_menu = logic.start_menu_link(appdata, LEGACY_APP_NAME)
    if start_menu is not None:
        links.append(start_menu)
    return tuple(links)


def points_inside(target: str | None, location: Path) -> bool:
    """True when a shortcut or sign-in target lies inside ``location``.

    A target that is empty, relative or unresolvable is not shown to belong
    to the old install, so it answers False and the item is left alone.
    """
    if not target:
        return False
    path = Path(target.strip().strip(_QUOTE))
    if not path.is_absolute():
        return False
    try:
        resolved = path.resolve()
        root = location.resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents


def toast_identity_key() -> str:
    """Return the HKCU key holding the former name's notification identity."""
    return rf"{logic.AUMID_CLASSES_SUBKEY}\{LEGACY_AUMID}"


def legacy_state_dir(home: Path) -> Path:
    """Return the state directory the former name wrote."""
    return home / LEGACY_STATE_DIR_NAME
