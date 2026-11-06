"""The board's history row: take a move back, then show the last move again.

Both buttons follow the history: with no move played there is nothing to
take back or to show, so both are greyed out and disabled.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

_UNDO_LABEL = "Take a move back"
_UNDO_TIP = "Undo the last move played"
_SHOW_LABEL = "Show last move"
_SHOW_TIP = "Pulse the boxes the last move acted on"


class HistoryControls(QWidget):
    """The take-back and show-last-move buttons, side by side."""

    take_back_requested = Signal()
    show_last_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.undo_button = self._button(_UNDO_LABEL, _UNDO_TIP, "UndoButton")
        self.undo_button.clicked.connect(self.take_back_requested)
        self.show_button = self._button(_SHOW_LABEL, _SHOW_TIP, "ShowLastMoveButton")
        self.show_button.clicked.connect(self.show_last_requested)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.undo_button)
        row.addWidget(self.show_button)
        row.addStretch()

    @staticmethod
    def _button(label: str, tip: str, name: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName(name)
        button.setToolTip(tip)
        button.setEnabled(False)
        return button

    def sync(self, can_take_back: bool, has_last_move: bool) -> None:
        """Enable each button only when there is something for it to act on."""
        self.undo_button.setEnabled(can_take_back)
        self.show_button.setEnabled(has_last_move)
