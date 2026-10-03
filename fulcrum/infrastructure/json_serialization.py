"""Shared JSON serialization for org states and moves.

These helpers translate the domain's org and move objects to and from plain
dictionaries. They are the single conversion layer used when a plan is written
to or read from a JSON file, so the on-disk shape stays defined in one place.
"""

from __future__ import annotations

from fulcrum.domain.errors import InvalidOrgStateError
from fulcrum.domain.models import (
    DEFAULT_CATEGORY,
    DEFAULT_HEADCOUNT,
    AuthorityClaim,
    Dependency,
    Domain,
    OrgState,
    Origin,
    Team,
)
from fulcrum.domain.moves import Move, MoveKind

_DEFAULT_SIZE = 1
_DEFAULT_OWNER = ""

# Origins written by retired features, normalised here so old files load
# without the domain carrying dead members. The quick-org wizard built orgs
# by hand, so its files read as modelled.
_LEGACY_ORIGINS: dict[str, str] = {"wizard": Origin.MODELLED.value}


def _team_to_dict(team: Team) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "has_local_authority": team.has_local_authority,
        "incentive_skew": team.incentive_skew,
        "domain_id": team.domain_id,
        "size": team.size,
        "owner": team.owner,
        "headcount": team.headcount,
    }


def _domain_to_dict(domain: Domain) -> dict:
    return {
        "id": domain.id,
        "name": domain.name,
        "parent_id": domain.parent_id,
        "lead": domain.lead,
        "category": domain.category,
        "headcount": domain.headcount,
    }


def _dependency_to_dict(dep: Dependency) -> dict:
    return {
        "upstream": dep.upstream,
        "downstream": dep.downstream,
        "propagation_delay": dep.propagation_delay,
    }


def _claim_to_dict(claim: AuthorityClaim) -> dict:
    return {"claimant": claim.claimant, "subject": claim.subject}


def org_to_dict(org: OrgState) -> dict:
    return {
        "teams": [_team_to_dict(t) for t in org.teams],
        "dependencies": [_dependency_to_dict(d) for d in org.dependencies],
        "workload": org.workload,
        "origin": org.origin.value,
        "domains": [_domain_to_dict(d) for d in org.domains],
        "claims": [_claim_to_dict(c) for c in org.claims],
    }


def move_to_dict(move: Move) -> dict:
    return {
        "kind": move.kind.value,
        "targets": list(move.targets),
        "label": move.label,
    }


def _record(value: object, what: str) -> dict:
    """A JSON object; otherwise the domain's error naming what was malformed.

    Files arrive from outside the app, so a list, null or number where an
    object belongs is refused with the same error type an invalid org
    raises; every reader then handles one failure kind, never a TypeError.
    """
    if not isinstance(value, dict):
        raise InvalidOrgStateError(f"{what} must be a JSON object")
    return value


def _records(data: dict, key: str, what: str, required: bool = True) -> list:
    """A JSON array of objects under key; absent reads as empty if optional."""
    if key not in data and not required:
        return []
    values = data[key]
    if not isinstance(values, list):
        raise InvalidOrgStateError(f"{key} must be a JSON array")
    return [_record(value, what) for value in values]


def _origin(value: object) -> Origin:
    if not isinstance(value, str):
        raise InvalidOrgStateError("origin must be text")
    return Origin(_LEGACY_ORIGINS.get(value, value))


def org_from_dict(data: object) -> OrgState:
    data = _record(data, "an organisation")
    teams = tuple(
        Team(
            t["id"],
            t["name"],
            t["has_local_authority"],
            t["incentive_skew"],
            t.get("domain_id"),
            t.get("size", _DEFAULT_SIZE),
            t.get("owner", _DEFAULT_OWNER),
            t.get("headcount", DEFAULT_HEADCOUNT),
        )
        for t in _records(data, "teams", "a team")
    )
    dependencies = tuple(
        Dependency(d["upstream"], d["downstream"], d["propagation_delay"])
        for d in _records(data, "dependencies", "a dependency")
    )
    domains = tuple(
        Domain(
            d["id"],
            d["name"],
            d.get("parent_id"),
            d.get("lead", ""),
            d.get("category", DEFAULT_CATEGORY),
            d.get("headcount", 0),
        )
        for d in _records(data, "domains", "a unit", required=False)
    )
    claims = tuple(
        AuthorityClaim(c["claimant"], c["subject"])
        for c in _records(data, "claims", "a claim", required=False)
    )
    return OrgState(
        teams=teams,
        dependencies=dependencies,
        workload=data["workload"],
        origin=_origin(data["origin"]),
        domains=domains,
        claims=claims,
    )


def move_from_dict(data: object) -> Move:
    data = _record(data, "a move")
    kind = data["kind"]
    targets = data["targets"]
    label = data["label"]
    if not isinstance(kind, str) or not isinstance(label, str):
        raise InvalidOrgStateError("a move's kind and label must be text")
    if not isinstance(targets, list) or not all(isinstance(t, str) for t in targets):
        raise InvalidOrgStateError("a move's targets must be a list of ids")
    return Move(MoveKind(kind), tuple(targets), label)


def moves_from_list(values: object) -> tuple[Move, ...]:
    """A JSON array of moves, refused whole when it is not an array."""
    if not isinstance(values, list):
        raise InvalidOrgStateError("a move history must be a JSON array")
    return tuple(move_from_dict(value) for value in values)
