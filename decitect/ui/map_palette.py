"""The map canvas colours, resolved per theme.

The board and the complete picture paint their own colours rather than
reading QSS, so they carry their own palette pair. set_map_theme flips the
module's current palette; the views rebuild their scenes on the next
refresh, which is how a theme switch repaints the board. The encoding keeps
its meaning in both themes: a border runs from amber (escalates) to green
(decides locally); violet marks contested teams on the glyph or the count
line, never the border (violet rather than red, so it stays distinct from
the authority green under red-green colour blindness and never reads as an
error). A move is marked in sky blue; the hover ring is neutral grey. Only
the depth changes so each reads on its surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor

from decitect.ui.theme_palettes import DEFAULT_THEME, THEME_LIGHT


@dataclass(frozen=True, slots=True)
class MapPalette:
    """The colour tokens the map painters resolve."""

    bg: QColor
    team_fill: QColor
    domain_fill: QColor
    text: QColor
    text_muted: QColor
    edge: QColor
    authority: QColor
    no_authority: QColor
    contested: QColor
    # The hover and keyboard-cursor ring: a neutral grey, since pointing at a
    # box says nothing about the organisation. Green, its old colour, read as
    # authority on an amber box.
    ring: QColor
    preview: QColor
    # The last-move pulse: sky blue, kept clear of the authority green, the
    # escalation amber and the contested violet so a change never reads as
    # a state.
    pulse: QColor


DARK_MAP = MapPalette(
    bg=QColor("#0d0f12"),
    team_fill=QColor("#1a1e24"),
    domain_fill=QColor("#222831"),
    text=QColor("#e6e9ee"),
    text_muted=QColor("#9aa3af"),
    edge=QColor("#5b6470"),
    authority=QColor("#34d399"),
    no_authority=QColor("#f59e0b"),
    contested=QColor("#a855f7"),
    ring=QColor("#c9d1d9"),
    preview=QColor("#fbbf24"),
    pulse=QColor("#38bdf8"),
)

LIGHT_MAP = MapPalette(
    bg=QColor("#e9edf2"),
    team_fill=QColor("#ffffff"),
    domain_fill=QColor("#dde3eb"),
    text=QColor("#1a1e24"),
    text_muted=QColor("#5b6470"),
    edge=QColor("#8a94a4"),
    authority=QColor("#059669"),
    no_authority=QColor("#d97706"),
    contested=QColor("#7c3aed"),
    ring=QColor("#475569"),
    preview=QColor("#b45309"),
    pulse=QColor("#0284c7"),
)

_current: MapPalette = DARK_MAP if DEFAULT_THEME != THEME_LIGHT else LIGHT_MAP


def set_map_theme(theme: str) -> None:
    """Flip the current map palette; views repaint on their next rebuild."""
    global _current
    _current = LIGHT_MAP if theme == THEME_LIGHT else DARK_MAP


def map_palette() -> MapPalette:
    """The palette the painters resolve at draw time."""
    return _current


def authority_colour(ratio: float) -> QColor:
    """A border colour from the share of teams deciding locally.

    Amber at none, green at all, blended between. Contest never replaces it:
    a box marks its contested teams separately, so a delegation that lands
    in a unit holding a standing claim still shows as authority gained.
    """
    low, high = _current.no_authority, _current.authority
    return QColor(
        int(low.red() + (high.red() - low.red()) * ratio),
        int(low.green() + (high.green() - low.green()) * ratio),
        int(low.blue() + (high.blue() - low.blue()) * ratio),
    )
