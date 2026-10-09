"""Adopting the pre-rename state directory without ever losing a session."""

import shutil

from decitect.infrastructure.state_dir import (
    legacy_state_dir,
    resolve_state_dir,
    state_dir,
)

_SESSION = "last_org.json"
_PAYLOAD = '{"teams": []}'


def _write_legacy(home):
    legacy = legacy_state_dir(home)
    legacy.mkdir()
    (legacy / _SESSION).write_text(_PAYLOAD, encoding="utf-8")
    return legacy


def test_the_directories_are_named_for_the_old_and_new_products(tmp_path):
    assert state_dir(tmp_path) == tmp_path / ".decitect"
    assert legacy_state_dir(tmp_path) == tmp_path / ".fulcrum"


def test_the_directories_default_to_the_users_home(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert state_dir() == tmp_path / ".decitect"
    assert legacy_state_dir() == tmp_path / ".fulcrum"


def test_a_first_run_with_nothing_on_disk_answers_the_new_directory(tmp_path):
    assert resolve_state_dir(tmp_path) == state_dir(tmp_path)
    assert not state_dir(tmp_path).exists()


def test_the_old_directory_is_moved_into_place_with_its_files(tmp_path):
    legacy = _write_legacy(tmp_path)
    resolved = resolve_state_dir(tmp_path)
    assert resolved == state_dir(tmp_path)
    assert (resolved / _SESSION).read_text(encoding="utf-8") == _PAYLOAD
    assert not legacy.exists()


def test_an_existing_new_directory_wins_and_the_old_one_is_left_alone(tmp_path):
    legacy = _write_legacy(tmp_path)
    state_dir(tmp_path).mkdir()
    assert resolve_state_dir(tmp_path) == state_dir(tmp_path)
    assert (legacy / _SESSION).is_file()
    assert not (state_dir(tmp_path) / _SESSION).exists()


def test_a_file_named_like_the_old_directory_is_not_adopted(tmp_path):
    legacy_state_dir(tmp_path).write_text("", encoding="utf-8")
    assert resolve_state_dir(tmp_path) == state_dir(tmp_path)
    assert legacy_state_dir(tmp_path).is_file()


def test_a_failed_move_keeps_using_the_old_directory(tmp_path, monkeypatch):
    legacy = _write_legacy(tmp_path)

    def _refuse(*_args, **_kwargs):
        raise OSError("in use")

    monkeypatch.setattr(shutil, "move", _refuse)
    assert resolve_state_dir(tmp_path) == legacy
    assert (legacy / _SESSION).is_file()
    assert not state_dir(tmp_path).exists()
