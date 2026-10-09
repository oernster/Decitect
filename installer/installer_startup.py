"""What the installer process sets up for itself before any window opens.

Two things, both done once by the entry point: a crash log (a
console-disabled onefile otherwise dies with no traceback anywhere) plus a
taskbar identity of its own. Like installer_ops this is the thin, untested
edge where Windows is touched; nothing here imports Qt.

British spelling is used in comments. No em dashes appear anywhere.
"""

from __future__ import annotations

import ctypes
import sys
import tempfile
import traceback
from pathlib import Path
from types import TracebackType

import installer_logic as logic


def installer_log_path() -> Path:
    """Return the crash-log path under the per-user temporary directory."""
    return Path(tempfile.gettempdir()) / logic.INSTALLER_LOG_NAME


def install_crash_logging() -> None:
    """Log unhandled exceptions to a file before the default handler runs.

    The installer is a console-disabled onefile; a crash otherwise leaves no
    visible traceback. This excepthook appends one to a known log file and
    then chains to the default handler so behaviour is unchanged.
    """
    log_path = installer_log_path()

    def _hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        try:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write("\n=== Unhandled exception ===\n")
                traceback.print_exception(exc_type, exc, tb, file=handle)
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


def set_app_user_model_id() -> None:
    """Give the installer a stable taskbar identity (best effort)."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"{logic.APP_AUMID}.installer"
        )
    except (OSError, AttributeError):
        return
