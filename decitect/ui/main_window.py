"""The Decitect main window: menus, the header tray and the board."""

from __future__ import annotations

from random import Random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from decitect.application.game_session import GameSession, restore_session
from decitect.application.interfaces import (
    Clock,
    ExampleSource,
    OrgStore,
    PlanExporter,
    SettingsStore,
    Simulator,
)
from decitect.domain.org_size import DEFAULT_BAND
from decitect.shared.resources import (
    find_model_licence,
    find_ui_licence,
)
from decitect.ui.close_guard import install_close_guard
from decitect.ui.guide_launcher import GuideLauncher
from decitect.ui.header_tray import HeaderTray, TrayHandlers
from decitect.ui.map_palette import set_map_theme
from decitect.ui.org_intake import OrgIntakeController
from decitect.ui.plan_files import PlanFileActions
from decitect.application.update_service import UpdateService
from decitect.ui.theme import get_qss
from decitect.ui.update_check import UpdateCheckController
from decitect.ui.theme_palettes import DEFAULT_THEME, THEME_DARK, THEME_LIGHT
from decitect.ui.widgets import disabled_cue
from decitect.ui.widgets.about_dialog import AboutDialog, LicenceDialog
from decitect.ui.widgets.board_view import BoardView
from decitect.ui.widgets.book_background_dialog import BookBackgroundDialog
from decitect.ui.widgets.glossary_dialog import GlossaryDialog
from decitect.ui.widgets.keyboard_nav import KeyboardNavigator
from decitect.ui.widgets.move_record_dialog import MoveRecordDialog
from decitect.ui.widgets.provenance_dialog import ProvenanceDialog
from decitect.version import APP_NAME, APP_TAGLINE


class MainWindow(QMainWindow):
    """Wires the application services to the board and the menus."""

    def __init__(
        self,
        simulator: Simulator,
        plan_exporter: PlanExporter,
        clock: Clock,
        rng: Random,
        examples: ExampleSource,
        org_store: OrgStore | None = None,
        settings: SettingsStore | None = None,
        update_service: UpdateService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._simulator = simulator
        self._org_store = org_store
        self._settings = settings
        self._update_check = (
            UpdateCheckController(self, update_service, settings)
            if update_service is not None
            else None
        )
        self._theme = settings.load_theme() if settings is not None else DEFAULT_THEME
        set_map_theme(self._theme)
        self._session: GameSession | None = None
        self._started = False
        self._intake = OrgIntakeController(
            self,
            simulator,
            rng,
            lambda: self._session,
            self._set_session,
            examples,
        )
        self._plan_files = PlanFileActions(
            self,
            simulator,
            plan_exporter,
            clock,
            lambda: self._session,
            self._set_session,
            lambda title, text: QMessageBox.warning(self, title, text),
        )

        self.setWindowTitle(f"{APP_NAME} - {APP_TAGLINE}")
        self._board = BoardView()
        self._build_menu()
        self._build_central()
        # Every play and take-back lands in the autosave immediately, so
        # the move record survives however the app ends.
        self._board.historyChanged.connect(lambda _can: self._autosave())
        self._guide_launcher = GuideLauncher(
            self,
            simulator,
            lambda: self._session,
            self._board.refresh,
            self._inform,
            lambda: self._theme,
        )
        restored = org_store.load() if org_store is not None else None
        # A failed restore is not the same as having nothing to restore; the
        # user is the only one who can tell which happened. Held until
        # the window is shown, since a message box during construction has no
        # parent to sit over.
        self._restore_warning = self._restore_warning_text(org_store)
        if restored is not None:
            # Replay rebuilds the undo stack, so the whole record (this
            # run's predecessor included) can be taken back move by move.
            self._set_session(restore_session(restored, self._simulator))
        else:
            self._intake.generate(DEFAULT_BAND)
        # A taskbar close must quit even while a dialog is modal; Qt drops
        # that close before any filter can see it, so a native guard
        # dismisses the modals and runs the normal close flow instead.
        self._close_guard = install_close_guard(self)

    def _build_central(self) -> None:
        central = QWidget()
        # An invisible, focusable start item: on launch nothing is highlighted
        # and no menu drops; the first Tab or Right enters the ring. Mirrors
        # Meridian's initialFocusItem.
        self._focus_start = QWidget(central)
        self._focus_start.setFixedSize(0, 0)
        self._focus_start.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        layout = QVBoxLayout(central)
        self._tray = HeaderTray(
            self._theme,
            TrayHandlers(
                model_org=self._intake.model_org,
                edit_org=self._intake.edit_org,
                show_guide=self._show_guide,
                move_record=self._move_record,
                provenance=self._provenance,
                presentation=self._plan_files.export_html,
                toggle_theme=self._toggle_theme,
                glossary=self._glossary,
                inform=self._inform,
            ),
        )
        presentation_link = self._tray.presentation_link
        self._board.historyChanged.connect(presentation_link.setEnabled)
        layout.addLayout(self._tray.row)
        layout.addWidget(self._board, 1)
        self.setCentralWidget(central)
        self._install_keyboard_nav(self._tray.ring_stops())
        disabled_cue.install(
            self,
            (presentation_link, self._undo_button),
            (self._presentation_action, self._undo_action),
        )

    def _toggle_theme(self) -> None:
        self._theme = THEME_LIGHT if self._theme == THEME_DARK else THEME_DARK
        QApplication.instance().setStyleSheet(get_qss(self._theme))
        set_map_theme(self._theme)
        if self._settings is not None:
            self._settings.save_theme(self._theme)
        self._tray.apply_theme(self._theme)
        # The map paints its own colours; rebuild the board so the canvas,
        # nodes and edges repaint in the new palette immediately.
        self._board.apply_map_theme()
        self._board.refresh()

    def _install_keyboard_nav(self, buttons) -> None:
        undo_button, map_view, level_button, moves_group, signals_group = (
            self._board.nav_targets()
        )
        self._undo_button = undo_button
        self._nav = KeyboardNavigator(
            self,
            self.menuBar(),
            self.menuBar().actions(),
            (*buttons, undo_button, map_view, level_button),
            (moves_group, signals_group),
            map_view,
            neutral_start=self._focus_start,
        )

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        self._presentation_action = file_menu.addAction(
            "Create presentation", self._plan_files.export_html
        )
        self._presentation_action.setEnabled(False)
        self._board.historyChanged.connect(self._presentation_action.setEnabled)
        file_menu.addSeparator()
        file_menu.addAction("Import...", self._plan_files.import_plan)
        file_menu.addAction("Export...", self._plan_files.export_json)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        org_menu = self.menuBar().addMenu("Organisation")
        org_menu.addAction("New random organisation...", self._intake.new_random_org)
        org_menu.addAction("Model my organisation...", self._intake.model_org)
        org_menu.addAction("Edit my org...", self._intake.edit_org)
        example_menu = org_menu.addMenu("Open example organisation")
        example_menu.setToolTipsVisible(True)
        for summary in self._intake.example_entries():
            action = example_menu.addAction(
                summary.label,
                lambda checked=False, s=summary: self._intake.open_example(s),
            )
            if summary.note:
                action.setToolTip(summary.note)
                action.setStatusTip(summary.note)
        example_menu.menuAction().setEnabled(not example_menu.isEmpty())

        edit_menu = self.menuBar().addMenu("Edit")
        self._undo_action = edit_menu.addAction(
            "Take a move back", self._board.take_back
        )
        self._undo_action.setShortcut("Ctrl+Z")
        self._undo_action.setEnabled(False)
        self._board.historyChanged.connect(self._undo_action.setEnabled)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction("Move record...", self._move_record)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Decision glossary...", self._glossary)
        help_menu.addAction("Book background...", self._book_background)
        help_menu.addAction("Check for updates...", self._check_for_updates)
        help_menu.addSeparator()
        help_menu.addAction("About", self._about)
        help_menu.addAction("Model licence (GPL-3.0)", self._model_licence)
        help_menu.addAction("UI licence (LGPL-3.0)", self._ui_licence)

    def _set_session(self, session: GameSession) -> None:
        self._session = session
        self._board.set_session(session)
        self._autosave()

    def _autosave(self) -> None:
        if self._org_store is not None and self._session is not None:
            self._org_store.save(self._session.snapshot())

    def _show_guide(self) -> None:
        self._guide_launcher.show()

    def _glossary(self) -> None:
        GlossaryDialog(self).exec()

    def _provenance(self) -> None:
        ProvenanceDialog(self).exec()

    def _move_record(self) -> None:
        if self._session is None:
            return
        MoveRecordDialog(
            self._session.initial_org,
            self._session.history,
            self._session.prior_history_count,
            self._simulator,
            self,
            self._theme,
        ).exec()

    def _book_background(self) -> None:
        BookBackgroundDialog(self).exec()

    def _check_for_updates(self) -> None:
        if self._update_check is not None:
            self._update_check.check_manually()

    def _about(self) -> None:
        AboutDialog(self).exec()

    def _model_licence(self) -> None:
        LicenceDialog("Model licence - GPL-3.0", find_model_licence(), self).exec()

    def _ui_licence(self) -> None:
        LicenceDialog("UI licence - LGPL-3.0", find_ui_licence(), self).exec()

    def _inform(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    @staticmethod
    def _restore_warning_text(org_store) -> str | None:
        """Explain a failed restore; None when there is nothing to explain."""
        if org_store is None:
            return None
        if org_store.history_dropped and org_store.preserved_copy is not None:
            return (
                "The saved move record could not be read, so the organisation "
                "has been restored without it. The file as it was has been kept "
                f"at {org_store.preserved_copy}. Nothing has been deleted."
            )
        if org_store.history_dropped and org_store.is_sealed:
            return (
                "The saved move record could not be read and the file could not "
                "be moved aside, so the organisation has been restored without "
                "it and this session will not be saved over the file."
            )
        if org_store.preserved_copy is not None:
            return (
                "The saved organisation could not be read, so it has been kept "
                f"at {org_store.preserved_copy} and a new one has been started. "
                "Nothing has been deleted."
            )
        if org_store.is_sealed:
            return (
                "The saved organisation could not be read and could not be "
                "moved aside, so it has been left untouched. This session will "
                "not be saved over it."
            )
        return None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._started:
            self._started = True
            self._focus_start.setFocus(Qt.FocusReason.OtherFocusReason)
            if self._restore_warning is not None:
                self._inform("Saved organisation", self._restore_warning)
                self._restore_warning = None

    def closeEvent(self, event) -> None:
        self._autosave()
        self._board.stop_analysis()
        self._intake.shutdown()
        super().closeEvent(event)
