"""Value objects refuse numbers and flags a file can carry but the model cannot.

Python's json reads NaN, Infinity and 1e999 without complaint and the old
range checks were comparisons NaN passes, so a broken organisation could
load and score a perfect 100. A string "false" read as holding authority.
A team id equal to a unit id merged two nodes into one endpoint.
"""

import math

import pytest

from fulcrum.domain.errors import InvalidOrgStateError
from fulcrum.domain.field_checks import MAX_COUNT
from fulcrum.domain.models import (
    AuthorityClaim,
    Dependency,
    Domain,
    OrgState,
    Team,
)
from fulcrum.domain.moves import Move, MoveKind, apply_move
from fulcrum.domain.simulation import evaluate

_NAN = float("nan")
_INF = float("inf")
_TOO_BIG = MAX_COUNT + 1
_NOT_COUNTS = (_NAN, _INF, -_INF, 1e308, 2.5, 3.0, "5", None, True, _TOO_BIG)


def _label(value) -> str:
    return "past the exact float range" if value is _TOO_BIG else repr(value)


@pytest.mark.parametrize("value", _NOT_COUNTS, ids=_label)
def test_a_team_size_must_be_a_whole_count(value):
    with pytest.raises(InvalidOrgStateError):
        Team("a", "A", True, size=value)


@pytest.mark.parametrize("value", _NOT_COUNTS, ids=_label)
def test_a_team_headcount_must_be_a_whole_count(value):
    with pytest.raises(InvalidOrgStateError):
        Team("a", "A", True, headcount=value)


@pytest.mark.parametrize("value", _NOT_COUNTS, ids=_label)
def test_a_propagation_delay_must_be_a_whole_count(value):
    with pytest.raises(InvalidOrgStateError):
        Dependency("a", "b", value)


@pytest.mark.parametrize("value", _NOT_COUNTS, ids=_label)
def test_a_workload_must_be_a_whole_count(value):
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(Team("a", "A", True),), workload=value)


@pytest.mark.parametrize("value", _NOT_COUNTS, ids=_label)
def test_a_domain_headcount_must_be_a_whole_count(value):
    with pytest.raises(InvalidOrgStateError):
        Domain("d", "D", headcount=value)


@pytest.mark.parametrize("value", (_NAN, _INF, "0.5", None, True), ids=repr)
def test_an_incentive_skew_must_be_a_finite_number(value):
    with pytest.raises(InvalidOrgStateError):
        Team("a", "A", True, value)


def test_whole_valued_numbers_of_either_kind_still_load():
    team = Team("a", "A", True, 0, size=2, headcount=9)
    assert team.incentive_skew == 0 and team.size == 2
    assert Domain("d", "D", headcount=0).headcount == 0


@pytest.mark.parametrize("value", ("false", "true", 0, 1, None), ids=repr)
def test_authority_must_be_a_true_flag(value):
    with pytest.raises(InvalidOrgStateError):
        Team("a", "A", value)


@pytest.mark.parametrize(
    "build",
    (
        lambda bad: Team(bad, "A", True),
        lambda bad: Team("a", bad, True),
        lambda bad: Team("a", "A", True, domain_id=bad),
        lambda bad: Team("a", "A", True, owner=bad),
        lambda bad: Dependency(bad, "b"),
        lambda bad: Dependency("a", bad),
        lambda bad: AuthorityClaim(bad, "a"),
        lambda bad: Domain(bad, "D"),
        lambda bad: Domain("d", bad),
        lambda bad: Domain("d", "D", parent_id=bad),
        lambda bad: Domain("d", "D", lead=bad),
        lambda bad: Domain("d", "D", category=bad),
    ),
)
@pytest.mark.parametrize("bad", (7, ["x"], {"x": 1}), ids=repr)
def test_text_fields_must_be_text(build, bad):
    with pytest.raises(InvalidOrgStateError):
        build(bad)


def test_collections_must_be_tuples_of_their_kind():
    team = Team("a", "A", True)
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(team, "b"))
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(team,), dependencies=(1,))
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(team,), domains=("d",))
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(team,), claims=(("x", "a"),))


def test_an_origin_must_be_an_origin():
    with pytest.raises(InvalidOrgStateError):
        OrgState(teams=(Team("a", "A", True),), origin=["generated"])


def test_a_team_id_may_not_also_name_a_unit():
    # Roots P and Q; team x in P; unit x under Q. The P to Q edge used to
    # become internal to Q in the top-level frame and vanish.
    with pytest.raises(InvalidOrgStateError):
        OrgState(
            teams=(
                Team("x", "X", True, domain_id="P"),
                Team("t3", "T3", True, domain_id="x"),
            ),
            domains=(Domain("P", "P"), Domain("Q", "Q"), Domain("x", "X", "Q")),
            dependencies=(Dependency("x", "t3"),),
        )


def test_a_loose_team_may_not_share_a_root_units_id():
    with pytest.raises(InvalidOrgStateError):
        OrgState(
            teams=(Team("ops", "Ops", True), Team("t", "T", True, domain_id="ops")),
            domains=(Domain("ops", "Ops unit"),),
        )


@pytest.mark.parametrize(
    ("kind", "targets", "taken"),
    (
        (MoveKind.SPLIT_TEAM, ("a",), "a_b"),
        (MoveKind.ADD_TEAM, ("a",), "a_owner"),
        (MoveKind.ADD_APPROVAL_LAYER, (), "approval_1"),
    ),
)
def test_a_minted_team_id_never_takes_a_units_id(kind, targets, taken):
    org = OrgState(
        teams=(Team("a", "A", False, domain_id=taken, size=2, headcount=8),),
        domains=(Domain(taken, "Unit"),),
    )
    after = apply_move(org, Move(kind, targets))
    assert len(after.teams) == len(org.teams) + 1
    assert taken not in after.team_ids


def _pair(workload) -> OrgState:
    return OrgState(
        teams=(Team("a", "A", False), Team("b", "B", True)),
        dependencies=(Dependency("a", "b"),),
        workload=workload,
    )


def test_the_largest_accepted_workload_scores_finite_and_worse():
    # At the float maximum the arithmetic overflowed to NaN and the clamp
    # made it 100; the largest count the domain accepts stays finite.
    value = evaluate(_pair(MAX_COUNT)).value
    assert math.isfinite(value)
    assert value < evaluate(_pair(1)).value


def test_a_score_that_is_not_a_number_is_refused_rather_than_clamped():
    # min(100, nan) is 100 because nan < 100 is false. Validation keeps NaN
    # out; this forces one past it to prove the last guard holds anyway.
    org = _pair(1)
    object.__setattr__(org, "workload", _NAN)
    with pytest.raises(InvalidOrgStateError):
        evaluate(org)
