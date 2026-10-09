"""Autosave of the current session, so a model and its moves survive closing.

The file's top level is the current org as plain JSON (the same shape a
plan's initial_org uses; exactly what older builds wrote), with two
optional keys beside it: the starting org and the move history, which is
what lets the next launch rebuild the session by replay. Both directions
stay compatible: a pre-history file restores as an org with no moves and an
older build reading a new file still finds the org it expects at the top
level. Writes are atomic; a missing file means nothing to restore and an
unreadable history degrades to the org alone, with the file kept aside.

A file that is present but will not parse is never left where the next save
can land on it. It is moved aside first; if even that fails the store
seals itself and writes nothing at all, because the session in memory can be
replayed and the one on disk cannot be brought back.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from decitect.application.dto import SessionSnapshot
from decitect.domain.errors import DecitectError
from decitect.domain.models import OrgState
from decitect.domain.moves import Move, apply_move
from decitect.infrastructure.json_serialization import (
    move_to_dict,
    moves_from_list,
    org_from_dict,
    org_to_dict,
)
from decitect.infrastructure.state_dir import state_dir

_FILENAME = "last_org.json"
_JSON_INDENT = 2
_TMP_SUFFIX = ".tmp"
_INITIAL_KEY = "initial_org"
_HISTORY_KEY = "history"
_FOCUS_KEY = "focused_on"
# A file that is present but will not read is kept under this suffix rather
# than left in place to be overwritten. The launch that cannot restore starts
# a new session and saves it immediately, so without this the unreadable file
# (which may be a whole organisation and its record) is gone within seconds of
# the failure and nothing anywhere reports it.
_PRESERVED_SUFFIX = ".unreadable"
_PRESERVE_ATTEMPTS = 100


def move_file(source: Path, target: Path) -> bool:
    """Move a file, reporting whether it worked rather than raising.

    The caller's decision depends on the answer rather than on the reason:
    a file that cannot be moved out of the way is a file that must not be
    written over.
    """
    try:
        os.replace(source, target)
    except OSError:
        return False
    return True


def _replay(initial: OrgState, moves: tuple[Move, ...]) -> None:
    """Raise the domain's error when a stored move no longer applies.

    A history that parses but will not replay (a version skew, a hand edit)
    is as lost as one that will not parse: the restore falls back to the
    org alone, so it is found here, where the file can still be kept.
    """
    current = initial
    for move in moves:
        current = apply_move(current, move)


def default_autosave_path(directory: Path | None = None) -> Path:
    """The per-user location the current session is saved to and restored from."""
    return (directory if directory is not None else state_dir()) / _FILENAME


class FileOrgStore:
    """Implements the application's OrgStore over a single JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else default_autosave_path()
        self._preserved: Path | None = None
        self._sealed = False
        self._history_dropped = False

    @property
    def preserved_copy(self) -> Path | None:
        """Where an unreadable file was kept, once one has been found."""
        return self._preserved

    @property
    def is_sealed(self) -> bool:
        """True when saving is refused because the old file could not be kept."""
        return self._sealed

    @property
    def history_dropped(self) -> bool:
        """True when the org restored but its move record could not."""
        return self._history_dropped

    def save(self, snapshot: SessionSnapshot) -> None:
        """Write the session atomically, unless the store has been sealed.

        Sealing is the last line of defence: an existing file that could not
        be read and could not be moved aside is left exactly as it is. Losing
        this session is recoverable by replaying it; overwriting the previous
        one is not.
        """
        if self._sealed:
            return
        data = org_to_dict(snapshot.org)
        if snapshot.moves:
            data[_INITIAL_KEY] = org_to_dict(snapshot.initial_org)
            data[_HISTORY_KEY] = [move_to_dict(move) for move in snapshot.moves]
        if snapshot.focused_on is not None:
            data[_FOCUS_KEY] = snapshot.focused_on
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_name(self._path.name + _TMP_SUFFIX)
        tmp.write_text(json.dumps(data, indent=_JSON_INDENT), encoding="utf-8")
        os.replace(tmp, self._path)

    def load(self) -> SessionSnapshot | None:
        """Read the saved session; None when absent or unreadable.

        A file without history loads as the current org with no moves,
        matching the pre-history format. A file whose history fails to parse
        or replay loads the same way, though only after the file has been kept
        aside (history_dropped and preserved_copy report it), so the next
        save cannot erase the record unseen.
        """
        try:
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError:
            self._sealed = True
            return None
        try:
            data = json.loads(text)
            org = org_from_dict(data)
        except (ValueError, KeyError, TypeError, DecitectError):
            self._preserve()
            return None
        focus = data.get(_FOCUS_KEY)
        if not isinstance(focus, str):
            # Absent in files written before the focus was saved; not to be
            # trusted from a hand-edited one. Either way, no focus.
            focus = None
        try:
            moves = moves_from_list(data.get(_HISTORY_KEY, []))
            initial = org_from_dict(data[_INITIAL_KEY]) if moves else org
            _replay(initial, moves)
        except (ValueError, KeyError, TypeError, DecitectError):
            # The organisation reads but its record does not. The session
            # restores without it and the next save would write the file
            # without it too, so the file is kept aside first, exactly as
            # an unreadable organisation is.
            self._history_dropped = True
            self._preserve()
            return SessionSnapshot(org, (), org, focus)
        return SessionSnapshot(initial, moves, org, focus)

    def _preserve(self) -> None:
        """Move an unreadable file aside; seal the store when that fails."""
        candidate = self._free_preserved_path()
        if candidate is None or not move_file(self._path, candidate):
            self._sealed = True
            return
        self._preserved = candidate

    def _free_preserved_path(self) -> Path | None:
        """The first unused preserved name, so an earlier rescue is not lost."""
        for attempt in range(_PRESERVE_ATTEMPTS):
            suffix = (
                _PRESERVED_SUFFIX if attempt == 0 else f"{_PRESERVED_SUFFIX}{attempt}"
            )
            candidate = self._path.with_name(self._path.name + suffix)
            if not candidate.exists():
                return candidate
        return None
