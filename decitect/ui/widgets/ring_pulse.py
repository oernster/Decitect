"""The last-move pulse: a ring that glows in and out a few times, then goes.

The box border already carries the state (authority, escalation, contest),
so the marker for where a move landed must not look like a state. It glows
in the pulse colour a fixed number of times and leaves the map as it was.
Both board maps own one; each passes the rects it draws for the targets.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import QEasingCurve, QObject, QRectF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen

from decitect.ui.map_palette import map_palette

PULSES = 3
# One glow in and back out; slow enough to read as calm rather than alarm.
PULSE_MS = 900
_DARK = 0.0
_BRIGHT = 1.0
_PEAK_AT = 0.5
# A soft halo twice the ring's width under the crisp ring gives the glow. A
# pen is centred on its line, so the halo reaches one ring width past it,
# which the views' fit margins (inset plus ring pen) already leave room for.
_HALO_SCALE = 2.0
_HALO_ALPHA = 0.35


class RingPulse(QObject):
    """Drives the pulse's strength and paints it around the given rects."""

    def __init__(self, repaint: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self._repaint = repaint
        self._targets: frozenset[str] = frozenset()
        self._strength = _DARK
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(_DARK)
        self._animation.setKeyValueAt(_PEAK_AT, _BRIGHT)
        self._animation.setEndValue(_DARK)
        self._animation.setDuration(PULSE_MS)
        self._animation.setLoopCount(PULSES)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.valueChanged.connect(self._on_value)
        self._animation.finished.connect(self._on_finished)

    @property
    def targets(self) -> frozenset[str]:
        """The node ids pulsing now; empty when no pulse is running."""
        return self._targets

    @property
    def running(self) -> bool:
        return bool(self._targets)

    def start(self, node_ids: Iterable[str]) -> None:
        """Pulse these nodes from the start, replacing any pulse running."""
        self._animation.stop()
        self._targets = frozenset(node_ids)
        if self._targets:
            self._animation.start()
        self._repaint()

    def _on_value(self, value) -> None:
        self._strength = float(value)
        self._repaint()

    def _on_finished(self) -> None:
        self._targets = frozenset()
        self._strength = _DARK
        self._repaint()

    def paint(
        self,
        scene_painter: QPainter,
        rects: Iterable[QRectF],
        geometry: tuple[float, float, float],
    ) -> None:
        """Draw the glow outside each rect at the pulse's current strength.

        geometry is the view's own (inset, ring pen, corner), so the pulse
        sits exactly where that view's hover ring does.
        """
        if not self._targets or self._strength <= _DARK:
            return
        inset, pen, corner = geometry
        radius = corner + inset
        layers = ((pen * _HALO_SCALE, _HALO_ALPHA), (pen, _BRIGHT))
        scene_painter.save()
        scene_painter.setBrush(Qt.BrushStyle.NoBrush)
        for rect in rects:
            outer = rect.adjusted(-inset, -inset, inset, inset)
            for width, alpha in layers:
                colour = QColor(map_palette().pulse)
                colour.setAlphaF(alpha * self._strength)
                scene_painter.setPen(QPen(colour, width))
                scene_painter.drawRoundedRect(outer, radius, radius)
        scene_painter.restore()
