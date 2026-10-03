"""An autosave of the wrong shape is kept aside, never raised and never lost.

Valid JSON that is not an organisation (a list, null, a field of the wrong
type) used to raise out of load and stop the window being built at all. A
history that would not parse or replay used to be dropped silently, so the
next save erased the move record with no copy kept.
"""

import json

import pytest

from fulcrum.application.dto import SessionSnapshot
from fulcrum.domain.models import OrgState, Origin, Team
from fulcrum.infrastructure.json_serialization import org_to_dict
from fulcrum.infrastructure.org_autosave import _PRESERVE_ATTEMPTS, FileOrgStore


def _org() -> OrgState:
    return OrgState(
        teams=(
            Team("a", "A", False, 0.2),
            Team("b", "B", True, 0.1),
        ),
        workload=4,
        origin=Origin.MODELLED,
    )


def _with(**fields) -> dict:
    data = org_to_dict(_org())
    data.update(fields)
    return data


def _with_team_field(name, value) -> dict:
    data = org_to_dict(_org())
    data["teams"][0][name] = value
    return data


_WRONG_SHAPES = {
    "a list": [],
    "null": None,
    "a bare string": "organisation",
    "teams null": _with(teams=None),
    "a team that is a number": _with(teams=[1]),
    "skew as text": _with_team_field("incentive_skew", "0.5"),
    "workload as text": _with(workload="5"),
    "dependencies null": _with(dependencies=None),
    "origin a list": _with(origin=["x"]),
    "domains a mapping": _with(domains={"x": 1}),
    "a claim that is a list": _with(claims=[["a", "b"]]),
    "team id a number": _with_team_field("id", 7),
}


@pytest.mark.parametrize("shape", sorted(_WRONG_SHAPES))
def test_a_wrong_shape_is_kept_aside_and_never_raised(tmp_path, shape):
    path = tmp_path / "last_org.json"
    text = json.dumps(_WRONG_SHAPES[shape])
    path.write_text(text, encoding="utf-8")
    store = FileOrgStore(path)
    assert store.load() is None
    assert store.preserved_copy is not None
    assert store.preserved_copy.read_text(encoding="utf-8") == text
    assert not path.exists()


def _history_file(path, history, initial=None) -> str:
    data = org_to_dict(_org())
    data["history"] = history
    data["initial_org"] = org_to_dict(_org()) if initial is None else initial
    text = json.dumps(data)
    path.write_text(text, encoding="utf-8")
    return text


_BAD_HISTORIES = {
    "an unknown kind": ([{"kind": "not-a-kind", "targets": [], "label": ""}], None),
    "a move that will not replay": (
        [{"kind": "delegate_authority", "targets": ["ghost"], "label": ""}],
        None,
    ),
    "targets that are a number": (
        [{"kind": "delegate_authority", "targets": 7, "label": ""}],
        None,
    ),
    "history not a list": ({"kind": "delegate_authority"}, None),
    "a kind that is a number": ([{"kind": 5, "targets": [], "label": ""}], None),
    "a move that is a list": ([["delegate_authority", ["a"], ""]], None),
    "an initial org of the wrong shape": (
        [{"kind": "delegate_authority", "targets": ["a"], "label": ""}],
        [],
    ),
}


@pytest.mark.parametrize("case", sorted(_BAD_HISTORIES))
def test_a_bad_history_keeps_the_file_before_the_next_save(tmp_path, case):
    path = tmp_path / "last_org.json"
    history, initial = _BAD_HISTORIES[case]
    text = _history_file(path, history, initial)
    store = FileOrgStore(path)
    assert store.load() == SessionSnapshot(_org(), (), _org())
    assert store.history_dropped is True
    kept = store.preserved_copy
    assert kept is not None and kept.read_text(encoding="utf-8") == text
    store.save(SessionSnapshot(_org(), (), _org()))
    assert kept.read_text(encoding="utf-8") == text


def test_a_good_history_drops_nothing(tmp_path):
    path = tmp_path / "last_org.json"
    _history_file(
        path, [{"kind": "delegate_authority", "targets": ["a"], "label": "go"}]
    )
    store = FileOrgStore(path)
    assert len(store.load().moves) == 1
    assert store.history_dropped is False
    assert store.preserved_copy is None


def test_a_bad_history_that_cannot_be_kept_seals_the_store(tmp_path):
    path = tmp_path / "last_org.json"
    text = _history_file(path, [{"kind": "not-a-kind", "targets": [], "label": ""}])
    # Every preserved name taken: the file cannot be kept, so it must not be
    # saved over either.
    for attempt in range(_PRESERVE_ATTEMPTS):
        suffix = ".unreadable" if attempt == 0 else f".unreadable{attempt}"
        path.with_name(path.name + suffix).write_text("taken", encoding="utf-8")
    store = FileOrgStore(path)
    assert store.load() == SessionSnapshot(_org(), (), _org())
    assert store.is_sealed is True
    store.save(SessionSnapshot(_org(), (), _org()))
    assert path.read_text(encoding="utf-8") == text
