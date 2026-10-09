"""A plan that will not read or replay says so instead of failing silently.

The replay loop used to sit outside the import's try, so a move aimed at a
team the plan does not hold (or a field of the wrong type) raised out of
the Qt slot: no message, the session unchanged and the user never told.
No dialog is opened here; the warning is an injected callable.
"""

import json

import pytest

from decitect.application.simulator import DeterministicSimulator
from decitect.domain.models import OrgState, Origin, Team
from decitect.infrastructure.json_serialization import org_to_dict
from decitect.infrastructure.plan_exporter import FilePlanExporter
from decitect.ui.plan_files import PlanFileActions


def _org_dict() -> dict:
    org = OrgState(
        teams=(Team("a", "A", False), Team("b", "B", True)),
        workload=3,
        origin=Origin.MODELLED,
    )
    return org_to_dict(org)


def _plan(moves, initial=None) -> dict:
    return {
        "initial_org": _org_dict() if initial is None else initial,
        "moves": moves,
        "created_at": "2026-10-03T00:00:00+00:00",
    }


class _Recorder:
    def __init__(self):
        self.warnings = []
        self.sessions = []

    def warn(self, title, text):
        self.warnings.append((title, text))

    def set_session(self, session):
        self.sessions.append(session)


def _actions(recorder) -> PlanFileActions:
    return PlanFileActions(
        None,
        DeterministicSimulator(),
        FilePlanExporter(),
        None,
        lambda: None,
        recorder.set_session,
        recorder.warn,
    )


def _team_field(name, value) -> dict:
    data = _org_dict()
    data["teams"][0][name] = value
    return data


_BAD_PLANS = {
    "a move on a missing team": _plan(
        [
            {"kind": "delegate_authority", "targets": ["a"], "label": ""},
            {"kind": "delegate_authority", "targets": ["ghost"], "label": ""},
        ]
    ),
    "targets as a number": _plan(
        [{"kind": "delegate_authority", "targets": 7, "label": ""}]
    ),
    "a move kind as a number": _plan([{"kind": 5, "targets": [], "label": ""}]),
    "moves not a list": _plan({"kind": "delegate_authority"}),
    "initial org a list": _plan([], []),
    "teams null": _plan([], dict(_org_dict(), teams=None)),
    "skew as text": _plan([], _team_field("incentive_skew", "0.5")),
    "workload as text": _plan([], dict(_org_dict(), workload="5")),
    "origin a list": _plan([], dict(_org_dict(), origin=["x"])),
    "a plan that is a list": [],
    "created_at a number": dict(_plan([]), created_at=7),
}


@pytest.mark.parametrize("case", sorted(_BAD_PLANS))
def test_a_bad_plan_warns_and_keeps_the_session(tmp_path, case):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_BAD_PLANS[case]), encoding="utf-8")
    recorder = _Recorder()
    _actions(recorder).open_plan(str(path))
    assert recorder.sessions == []
    assert len(recorder.warnings) == 1
    assert recorder.warnings[0][0] == "Could not open plan"


def test_the_warning_names_the_move_that_will_not_replay(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_BAD_PLANS["a move on a missing team"]), "utf-8")
    recorder = _Recorder()
    _actions(recorder).open_plan(str(path))
    text = recorder.warnings[0][1]
    assert "move 2" in text and "ghost" in text


def test_a_good_plan_replaces_the_session_without_a_warning(tmp_path):
    path = tmp_path / "plan.json"
    moves = [{"kind": "delegate_authority", "targets": ["a"], "label": "go"}]
    path.write_text(json.dumps(_plan(moves)), encoding="utf-8")
    recorder = _Recorder()
    _actions(recorder).open_plan(str(path))
    assert recorder.warnings == []
    (session,) = recorder.sessions
    assert len(session.history) == 1
    assert session.prior_history_count == 1
