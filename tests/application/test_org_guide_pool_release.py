"""A cancelled pooled build releases its CPU, not only its bar.

The pool used to shut down without waiting and leave abandoned workers to
finish their current chunk; on a large organisation that kept every core
busy for a chunk's length after the user cancelled because the machine was
struggling. A build that unwinds with an exception now ends its workers.
"""

import multiprocessing
import time

import pytest

from fulcrum.application.org_guide_parallel import GuideWorkers
from fulcrum.application.planner import GuideBuildCancelled
from fulcrum.domain.models import OrgState, Team
from fulcrum.domain.moves import Move, MoveKind

# Long enough that a worker still holding its chunk at the check can only
# be one that was left running, short enough that a red run cleans itself.
_WORKER_HOLD_S = 30.0
_RELEASE_WITHIN_S = 10.0
_POLL_S = 0.05
_POOL_SIZE = 2


class _SlowSimulator:
    """Marks that a worker has started, then holds its chunk."""

    def __init__(self, marker):
        self._marker = marker

    def valuate_moves(self, org, moves):
        self._marker.write_text("started", encoding="utf-8")
        time.sleep(_WORKER_HOLD_S)
        return ()


def _org():
    return OrgState(teams=(Team("a", "A", False),), workload=1)


def _alive(pids):
    return _live_pids() & pids


class _CancelOnceStarted:
    """Fires once a worker holds its chunk, noting which workers were live."""

    def __init__(self, marker, before):
        self._marker = marker
        self._before = before
        self.workers = set()

    def __call__(self):
        if not self._marker.exists():
            return False
        self.workers = _live_pids() - self._before
        return True


def _live_pids():
    return {p.pid for p in multiprocessing.active_children()}


def test_a_cancelled_build_ends_its_workers(tmp_path):
    marker = tmp_path / "started"
    cancel = _CancelOnceStarted(marker, _live_pids())
    moves = (Move(MoveKind.DELEGATE_AUTHORITY, ("a",)),)
    with pytest.raises(GuideBuildCancelled):
        with GuideWorkers(_POOL_SIZE) as workers:
            workers.valuate_moves(_SlowSimulator(marker), _org(), moves, None, cancel)
    ours = cancel.workers
    assert ours, "positive control: the pool's workers were seen running"
    deadline = time.monotonic() + _RELEASE_WITHIN_S
    while _alive(ours) and time.monotonic() < deadline:
        time.sleep(_POLL_S)
    assert _alive(ours) == set()


def test_a_completed_build_still_leaves_without_waiting():
    # A normal exit has nothing in flight; it must not start terminating
    # or waiting, which is what made a cancel look frozen before.
    started = time.monotonic()
    with GuideWorkers(_POOL_SIZE):
        pass
    assert time.monotonic() - started < _RELEASE_WITHIN_S
