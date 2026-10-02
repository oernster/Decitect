"""Construction of the main window's header-tray buttons.

The tray holds four kinds of control: icon-only buttons built from the
generated per-theme glyphs (their old text living on as tooltips), the app
icon standing at the centre as the organisation-overview button, the donate
mark and the sun/moon theme toggle. The toggle shows the ACTION a press
performs, never the state: in dark mode it wears the sun (press for light),
in light mode the moon.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QImageReader
from PySide6.QtWidgets import QPushButton

from fulcrum.shared.resources import (
    find_about_png,
    find_donate_png,
    find_provenance_png,
)
from fulcrum.ui import ui_scale
from fulcrum.ui.icons import button_icon
from fulcrum.ui.theme_palettes import THEME_DARK

_ICON_LINK = "IconLink"
_TRAY_GLOW = "TrayGlow"
# The height every picture in the tray is drawn at; generate_button_icons.py
# reads it too, so the donate render is derived from the height it is shown at.
BUTTON_ICON_PX = 24
# The centred glow pair (the app icon and its golden provenance kin) sits
# larger than the other header buttons, on a tighter plate (see the
# TrayGlow padding rule in theme.py), so the marks read at full presence.
_APP_ICON_PX = 36
_SUN_GLYPH = "\N{BLACK SUN WITH RAYS}\N{VARIATION SELECTOR-16}"
_MOON_GLYPH = "\N{CRESCENT MOON}"
_TO_LIGHT_TOOLTIP = "Switch to light mode"
_TO_DARK_TOOLTIP = "Switch to dark mode"
# A beer and a coffee do not say that pressing them leaves the application,
# so the tooltip does.
DONATE_TOOLTIP = "Buy the author a drink (opens your browser)"


def _square(side: int) -> QSize:
    scaled = ui_scale.px(side)
    return QSize(scaled, scaled)


def _picture_button(icon: QIcon, size: QSize, tooltip: str, handler) -> QPushButton:
    """The one shape every picture button in the tray is built from."""
    button = QPushButton()
    button.setIcon(icon)
    button.setIconSize(size)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(handler)
    return button


def icon_button(name: str, tooltip: str, handler, theme: str) -> QPushButton:
    """An icon-only header button whose old text lives on as the tooltip."""
    return _picture_button(
        button_icon(name, theme), _square(BUTTON_ICON_PX), tooltip, handler
    )


def _glow_button(icon_path: Path | None, tooltip: str, handler) -> QPushButton:
    """A centred-tray glow button: standard plate, tight padding, large mark.

    Deliberately NOT an icon link: it keeps the standard button plate the
    other header icon buttons have, so the glowing mark sits on the same
    grey square in both themes instead of washing out on a light surface.
    """
    icon = QIcon(str(icon_path)) if icon_path is not None else QIcon()
    button = _picture_button(icon, _square(_APP_ICON_PX), tooltip, handler)
    button.setObjectName(_TRAY_GLOW)
    return button


def app_icon_button(tooltip: str, handler) -> QPushButton:
    """The app icon as a button: sits at the tray's centre, opens the overview."""
    return _glow_button(find_about_png(), tooltip, handler)


def provenance_icon_button(tooltip: str, handler) -> QPushButton:
    """The golden kin of the app icon: opens what grounds the numbers."""
    return _glow_button(find_provenance_png(), tooltip, handler)


def donate_button(handler) -> QPushButton:
    """The donate mark at the tray's own glyph height, as wide as it draws.

    The mark is a wide picture, so a square icon size would shrink it to fit
    the width; the size takes the render's own aspect instead.
    """
    path = find_donate_png()
    if path is None:
        return _picture_button(
            QIcon(), _square(BUTTON_ICON_PX), DONATE_TOOLTIP, handler
        )
    natural = QImageReader(str(path)).size()
    height = ui_scale.px(BUTTON_ICON_PX)
    width = round(height * natural.width() / natural.height())
    return _picture_button(
        QIcon(str(path)), QSize(width, height), DONATE_TOOLTIP, handler
    )


def theme_toggle_button(handler) -> QPushButton:
    """The sun/moon theme toggle; dress_theme_toggle sets its face."""
    button = QPushButton()
    button.setObjectName(_ICON_LINK)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(handler)
    return button


def dress_theme_toggle(button: QPushButton, theme: str) -> None:
    """Show the theme a press switches TO: sun in the dark, moon in the light."""
    dark = theme == THEME_DARK
    button.setText(_SUN_GLYPH if dark else _MOON_GLYPH)
    tooltip = _TO_LIGHT_TOOLTIP if dark else _TO_DARK_TOOLTIP
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
