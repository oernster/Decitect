"""An update check whose controller is deleted before its answer comes back.

The controller is a child of the main window, so deleting the window deletes
it. Measured on 2026-10-02, quitting the real ``main()`` did not do that: the
window and the controller were both still alive after it returned. This is
therefore hardening, not a reproduction of a seen crash. Without it the
worker emits through a controller that no longer exists and the emit raises
on that thread. Nobody is left to tell, so the answer is dropped; what must
not happen is an exception escaping a thread this application started.
"""

from __future__ import annotations

import threading

import shiboken6
from PySide6.QtWidgets import QWidget

from fulcrum.application.update_info import ReleaseInfo
from fulcrum.application.update_service import UpdateService, platform_key_for
from fulcrum.ui.update_check import UpdateCheckController

CURRENT = "4.4.0"

# Far longer than a check against a stand-in takes, so only a hang reaches it.
WAIT_SECONDS = 5


class HeldSource:
    """A release source that answers only once the test lets it."""

    def __init__(self) -> None:
        self.asked = threading.Event()
        self.answer = threading.Event()
        self.worker: threading.Thread | None = None

    def latest_release(self) -> ReleaseInfo | None:
        """Say it has been asked, then wait to be allowed to answer."""
        self.worker = threading.current_thread()
        self.asked.set()
        self.answer.wait(WAIT_SECONDS)
        return None


def test_an_answer_with_nowhere_to_go_is_dropped_not_raised(qapp, monkeypatch) -> None:
    escaped: list[BaseException | None] = []
    monkeypatch.setattr(
        threading, "excepthook", lambda raised: escaped.append(raised.exc_value)
    )
    source = HeldSource()
    window = QWidget()
    UpdateCheckController(
        window, UpdateService(source, CURRENT, platform_key_for("win32")), None
    ).check_manually()
    assert source.asked.wait(WAIT_SECONDS), "the check never started"
    shiboken6.delete(window)
    source.answer.set()
    source.worker.join(WAIT_SECONDS)
    assert not source.worker.is_alive(), "the check never finished"
    assert escaped == []
