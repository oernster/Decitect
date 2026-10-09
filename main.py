"""Decitect entry point: composition root and Qt event loop."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path
from random import Random

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from decitect.application.simulator import DeterministicSimulator
from decitect.application.update_service import UpdateService, platform_key_for
from decitect.infrastructure.example_library import FileExampleLibrary
from decitect.infrastructure.github_release_source import GitHubReleaseSource
from decitect.infrastructure.org_autosave import FileOrgStore, default_autosave_path
from decitect.infrastructure.plan_exporter import FilePlanExporter
from decitect.infrastructure.settings_store import (
    FileSettingsStore,
    default_settings_path,
)
from decitect.infrastructure.state_dir import resolve_state_dir
from decitect.infrastructure.system_clock import SystemClock
from decitect.shared.resources import find_app_icon, find_examples_dir
from decitect.ui import ui_scale
from decitect.ui.main_window import MainWindow
from decitect.ui.theme import get_qss
from decitect.version import __version__

_UI_SCALE_REFERENCE_HEIGHT = 1260.0
_MAX_UI_SCALE = 1.5
_WIDTH_FRACTION = 0.5
_HEIGHT_FRACTION = 0.85
_MIN_WIDTH = 720
_MIN_HEIGHT = 640


def _size_window(window: MainWindow, avail) -> None:
    width = min(max(int(avail.width() * _WIDTH_FRACTION), _MIN_WIDTH), avail.width())
    height = min(
        max(int(avail.height() * _HEIGHT_FRACTION), _MIN_HEIGHT), avail.height()
    )
    x = avail.x() + (avail.width() - width) // 2
    y = avail.y() + (avail.height() - height) // 2
    window.setGeometry(x, y, width, height)


def main() -> int:
    app = QApplication(sys.argv)

    # The app is themed entirely by stylesheet. The native windows11 style
    # paints its own chrome over stylesheet borders (truncated focus and
    # hover rings on combos and fields), so pin the style Fusion renders
    # QSS faithfully on and every platform shares.
    app.setStyle("fusion")

    avail = app.primaryScreen().availableGeometry()
    ui_scale.init(min(avail.height() / _UI_SCALE_REFERENCE_HEIGHT, _MAX_UI_SCALE))
    # Resolved once, before either store opens a file, so a pre-rename
    # ~/.fulcrum is adopted before anything could write a fresh directory.
    state = resolve_state_dir(Path.home())
    settings = FileSettingsStore(default_settings_path(state))
    app.setStyleSheet(get_qss(settings.load_theme()))

    icon_path = find_app_icon()
    icon = QIcon(str(icon_path)) if icon_path is not None else None
    if icon is not None:
        app.setWindowIcon(icon)

    window = MainWindow(
        simulator=DeterministicSimulator(),
        plan_exporter=FilePlanExporter(),
        clock=SystemClock(),
        rng=Random(),
        examples=FileExampleLibrary(find_examples_dir()),
        org_store=FileOrgStore(default_autosave_path(state)),
        settings=settings,
        update_service=UpdateService(
            GitHubReleaseSource(), __version__, platform_key_for(sys.platform)
        ),
    )
    if icon is not None:
        window.setWindowIcon(icon)
    # The sized, centred geometry is what un-maximising restores to; the
    # app itself opens maximised so the side panel never truncates.
    _size_window(window, avail)
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    # The guide's worker pool spawns processes; in a frozen build each
    # worker relaunches this executable, and freeze_support must run
    # before anything else so a worker never starts a second app.
    multiprocessing.freeze_support()
    sys.exit(main())
