"""The map's colour key: a small solid square per colour, then its meaning.

Each square reads its colour from the live map palette when it paints, so a
theme switch needs only a repaint. The squares paint themselves rather than
take a stylesheet, which the app's QSS would otherwise restyle.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from decitect.ui import ui_scale
from decitect.ui.map_palette import MapPalette, map_palette

_SWATCH_PX = 10
_SWATCH_GAP_PX = 6
_ENTRY_GAP_PX = 16

# (colour token, label, what the colour marks). Order follows the reading of
# a box: its border first, then the contest marker, then the move pulse.
_ENTRIES: tuple[tuple[Callable[[MapPalette], QColor], str, str], ...] = (
    (
        lambda p: p.authority,
        "Decides locally",
        (
            "Border: the teams decide for themselves. A box shades from amber "
            "to green with the share of its teams that do."
        ),
    ),
    (
        lambda p: p.no_authority,
        "Escalates",
        "Border: the teams pass their decisions up the line.",
    ),
    (
        lambda p: p.contested,
        "Contested",
        (
            "Person glyph and count: a standing claim on who decides, to be "
            "settled before the decision can be made."
        ),
    ),
    (
        lambda p: p.pulse,
        "Last move",
        "Pulse: where the last move acted. Show last move plays it again.",
    ),
)


class _Swatch(QWidget):
    """A small solid square in one map colour."""

    def __init__(self, colour_of: Callable[[MapPalette], QColor]) -> None:
        super().__init__()
        self._colour_of = colour_of
        side = ui_scale.px(_SWATCH_PX)
        self.setFixedSize(side, side)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._colour_of(map_palette()))
        painter.end()


class MapLegend(QWidget):
    """One row of colour squares, each followed by what it means."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(ui_scale.px(_SWATCH_GAP_PX))
        for index, (colour_of, label, tip) in enumerate(_ENTRIES):
            if index:
                row.addSpacing(ui_scale.px(_ENTRY_GAP_PX))
            swatch = _Swatch(colour_of)
            text = QLabel(label)
            text.setObjectName("Muted")
            for widget in (swatch, text):
                widget.setToolTip(tip)
                row.addWidget(widget)
        row.addStretch()

    def apply_map_theme(self) -> None:
        """Repaint the squares in the current palette after a theme switch."""
        for swatch in self.findChildren(_Swatch):
            swatch.update()
