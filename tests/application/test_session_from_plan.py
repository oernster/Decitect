"""An imported plan replays into a session or names the move that will not."""

import pytest
from session_support import FakeSimulator, flat_org

from fulcrum.application.dto import Plan
from fulcrum.application.game_session import session_from_plan
from fulcrum.domain.errors import InvalidMoveError
from fulcrum.domain.moves import Move, MoveKind

_CREATED = "2026-10-03T00:00:00+00:00"


def test_a_plan_replays_and_its_moves_become_the_prior_record():
    move = Move(MoveKind.DELEGATE_AUTHORITY, ("b",), "empower b")
    session = session_from_plan(Plan(flat_org(), (move,), _CREATED), FakeSimulator())
    assert session.org.team("b").has_local_authority is True
    assert session.prior_history_count == 1


def test_a_move_that_will_not_replay_is_named_by_its_position():
    good = Move(MoveKind.DELEGATE_AUTHORITY, ("b",))
    ghost = Move(MoveKind.DELEGATE_AUTHORITY, ("ghost",), "empower ghost")
    plan = Plan(flat_org(), (good, ghost), _CREATED)
    with pytest.raises(InvalidMoveError, match=r"move 2 \(empower ghost\)"):
        session_from_plan(plan, FakeSimulator())
