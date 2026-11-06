"""The whole main window builds, as main.py builds it.

Each widget has its own tests; nothing else constructs the window that wires
them together. A board that gained a keyboard stop the window did not
unpack passed every other test and stopped the packaged app at launch.
"""

from __future__ import annotations

from random import Random

from decitect.application.simulator import DeterministicSimulator
from decitect.infrastructure.example_library import FileExampleLibrary
from decitect.infrastructure.plan_exporter import FilePlanExporter
from decitect.infrastructure.system_clock import SystemClock
from decitect.shared.resources import find_examples_dir
from decitect.ui.main_window import MainWindow


def build_window() -> MainWindow:
    """The window main.py builds, minus the autosave, settings and update check."""
    return MainWindow(
        simulator=DeterministicSimulator(),
        plan_exporter=FilePlanExporter(),
        clock=SystemClock(),
        rng=Random(0),
        examples=FileExampleLibrary(find_examples_dir()),
    )


def test_the_main_window_builds(qapp) -> None:
    window = build_window()
    try:
        assert window.windowTitle()
    finally:
        window._board.stop_analysis()
        window.close()
