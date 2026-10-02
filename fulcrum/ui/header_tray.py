"""The main window's header tray: its buttons, their order and their ring.

Left to right: the three organisation buttons; at the centre the app icon,
its golden provenance kin and the presentation; on the right the donate
mark, the theme toggle and the glossary. The focus ring visits them in the
same order they are drawn. The tray is a row rather than a widget, so no
container can take focus or paint a border.

The donate mark sits immediately left of the theme toggle because it belongs
to nothing else on screen. A press hands the address to the desktop; the
application never fetches the page itself.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from fulcrum.ui import header_buttons, links
from fulcrum.ui.icons import button_icon
from fulcrum.version import DONATE_URL

_ICON_LINK = "IconLink"
_GLOSSARY_GLYPH = "\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16}"
_GLOSSARY_TOOLTIP = "Decision glossary"
_RECORD_TOOLTIP = "Move record: every move to date, with the position before and after"
_PRESENTATION_GLYPH = "\N{CHART WITH UPWARDS TREND}"
_PRESENTATION_TOOLTIP = "Create the presentation and open it"
_MODEL_ORG_TOOLTIP = "Model my organisation"
_EDIT_ORG_TOOLTIP = "Edit my org: reopen and edit the current organisation"
_GUIDE_TOOLTIP = "Show the guide"
_PROVENANCE_TOOLTIP = (
    "What grounds the numbers: every coefficient, its source and its fragility"
)
DONATE_REFUSED_TITLE = "Donate"
DONATE_REFUSED_TEXT = (
    "Could not open a browser for the donation page. " f"The page is at {DONATE_URL}"
)


@dataclass(frozen=True, slots=True)
class TrayHandlers:
    """What each tray button does, plus where a refusal is reported."""

    model_org: Callable[[], None]
    edit_org: Callable[[], None]
    show_guide: Callable[[], None]
    move_record: Callable[[], None]
    provenance: Callable[[], None]
    presentation: Callable[[], None]
    toggle_theme: Callable[[], None]
    glossary: Callable[[], None]
    inform: Callable[[str, str], None]


def _glyph_link(glyph: str, tooltip: str, handler) -> QPushButton:
    button = QPushButton(glyph)
    button.setObjectName(_ICON_LINK)
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(handler)
    return button


class HeaderTray:
    """Builds the header row and answers its buttons in ring order.

    Its owner must hold it: Qt keeps no reference to a plain object whose
    method a signal is connected to, so a dropped tray takes the donate
    press with it (measured: a test pressing an unheld tray saw no call).
    """

    def __init__(self, theme: str, handlers: TrayHandlers) -> None:
        self._inform = handlers.inform
        # The generated header icons carry a variant per theme; apply_theme
        # re-dresses each of these (button, icon name) pairs on switch.
        self._themed: list[tuple[QPushButton, str]] = []
        left = (
            self._icon("model_org", _MODEL_ORG_TOOLTIP, handlers.model_org, theme),
            self._icon("edit_org", _EDIT_ORG_TOOLTIP, handlers.edit_org, theme),
            self._icon("guide", _GUIDE_TOOLTIP, handlers.show_guide, theme),
        )
        # The presentation joins the glow pair at the centre rather than
        # sitting out on the right edge with the utilities: it is what the
        # board is for; on the edge it read as an afterthought.
        self.presentation_link = _glyph_link(
            _PRESENTATION_GLYPH, _PRESENTATION_TOOLTIP, handlers.presentation
        )
        self.presentation_link.setEnabled(False)
        centre = (
            header_buttons.app_icon_button(_RECORD_TOOLTIP, handlers.move_record),
            header_buttons.provenance_icon_button(
                _PROVENANCE_TOOLTIP, handlers.provenance
            ),
            self.presentation_link,
        )
        self.donate_button = header_buttons.donate_button(self.open_donation)
        self.theme_toggle = header_buttons.theme_toggle_button(handlers.toggle_theme)
        header_buttons.dress_theme_toggle(self.theme_toggle, theme)
        right = (
            self.donate_button,
            self.theme_toggle,
            _glyph_link(_GLOSSARY_GLYPH, _GLOSSARY_TOOLTIP, handlers.glossary),
        )
        self.row = QHBoxLayout()
        for group in (left, centre):
            for button in group:
                self.row.addWidget(button)
            self.row.addStretch()
        for button in right:
            self.row.addWidget(button)
        self._stops = (*left, *centre, *right)

    def _icon(self, name: str, tooltip: str, handler, theme: str) -> QPushButton:
        button = header_buttons.icon_button(name, tooltip, handler, theme)
        self._themed.append((button, name))
        return button

    def ring_stops(self) -> tuple[QPushButton, ...]:
        """This tray's controls, left to right as they are drawn."""
        return self._stops

    def apply_theme(self, theme: str) -> None:
        """Re-dress the toggle and every generated icon for a theme."""
        header_buttons.dress_theme_toggle(self.theme_toggle, theme)
        for button, name in self._themed:
            button.setIcon(button_icon(name, theme))

    def open_donation(self) -> None:
        """Hand the donation page to whatever the desktop opens links with.

        A desktop that declines must say so; silence would leave a button
        that appears to do nothing.
        """
        if not links.open_externally(DONATE_URL):
            self._inform(DONATE_REFUSED_TITLE, DONATE_REFUSED_TEXT)
