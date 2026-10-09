"""The launch message says which part of a saved session was lost and where
the file went. No window is built: the text comes from a static method fed
a hand-written store."""

from pathlib import Path

from decitect.ui.main_window import MainWindow

_KEPT = Path("kept") / "last_org.json.unreadable"


class _Store:
    def __init__(self, preserved=None, sealed=False, history_dropped=False):
        self.preserved_copy = preserved
        self.is_sealed = sealed
        self.history_dropped = history_dropped


def test_a_dropped_record_names_the_kept_file_and_the_restored_org():
    text = MainWindow._restore_warning_text(_Store(_KEPT, history_dropped=True))
    assert "move record" in text and str(_KEPT) in text
    assert "restored without it" in text


def test_a_dropped_record_that_could_not_be_kept_says_nothing_is_saved_over_it():
    text = MainWindow._restore_warning_text(_Store(sealed=True, history_dropped=True))
    assert "move record" in text and "will not be saved over" in text


def test_an_unreadable_organisation_keeps_its_own_message():
    text = MainWindow._restore_warning_text(_Store(_KEPT))
    assert "a new one has been started" in text


def test_a_clean_restore_says_nothing():
    assert MainWindow._restore_warning_text(_Store()) is None
    assert MainWindow._restore_warning_text(None) is None
