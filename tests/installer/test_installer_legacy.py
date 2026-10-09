"""Finding an install under the former name and proving what belongs to it.

These decide what setup offers to delete from a user's machine, so the
cases that matter most are the ones where it must leave something alone.
"""

from pathlib import Path

import installer_legacy as legacy
import installer_logic as logic
import installer_scripts as scripts


class _UnresolvablePath(type(Path())):
    """A path whose resolution fails, standing in for a broken location."""

    def resolve(self, strict=False):
        raise OSError("cannot resolve")


def test_the_default_location_sits_beside_the_new_install(tmp_path):
    default = legacy.default_location(str(tmp_path), tmp_path)
    assert default == tmp_path / "Programs" / "Fulcrum"
    assert default.parent == logic.install_target(str(tmp_path), tmp_path).parent


def test_a_registered_location_that_exists_is_found(tmp_path):
    registered = tmp_path / "Fulcrum"
    registered.mkdir()
    found = legacy.find_legacy("4.6.0", registered, tmp_path / "absent")
    assert found == legacy.LegacyInstall(location=registered, version="4.6.0")


def test_an_unregistered_default_directory_still_counts(tmp_path):
    default = tmp_path / "Fulcrum"
    default.mkdir()
    found = legacy.find_legacy(None, None, default)
    assert found == legacy.LegacyInstall(location=default, version="")


def test_a_registration_whose_directory_is_gone_falls_back_to_the_default(
    tmp_path,
):
    default = tmp_path / "Fulcrum"
    default.mkdir()
    found = legacy.find_legacy("4.6.0", tmp_path / "gone", default)
    assert found is not None
    assert found.location == default


def test_nothing_on_disk_means_no_old_install(tmp_path):
    assert legacy.find_legacy("4.6.0", tmp_path / "gone", tmp_path / "no") is None


def test_the_option_names_the_version_and_the_path(tmp_path):
    named = legacy.LegacyInstall(location=tmp_path, version="4.6.0")
    assert legacy.option_text(named) == (
        f"Remove the old Fulcrum 4.6.0 install at {tmp_path}"
    )
    unversioned = legacy.LegacyInstall(location=tmp_path, version="")
    assert legacy.option_text(unversioned) == (
        f"Remove the old Fulcrum install at {tmp_path}"
    )


def test_the_shortcuts_looked_for_carry_the_former_name(tmp_path):
    appdata = tmp_path / "Roaming"
    links = legacy.shortcut_links(str(appdata), tmp_path)
    assert links == (
        tmp_path / "Desktop" / "Fulcrum.lnk",
        appdata.joinpath(
            "Microsoft", "Windows", "Start Menu", "Programs", "Fulcrum.lnk"
        ),
    )


def test_without_appdata_only_the_desktop_shortcut_is_looked_for(tmp_path):
    assert legacy.shortcut_links(None, tmp_path) == (
        tmp_path / "Desktop" / "Fulcrum.lnk",
    )


def test_a_target_inside_the_old_install_belongs_to_it(tmp_path):
    exe = tmp_path / "fulcrum.exe"
    assert legacy.points_inside(str(exe), tmp_path) is True
    assert legacy.points_inside(f'"{exe}"', tmp_path) is True
    assert legacy.points_inside(f"  {exe}\r\n", tmp_path) is True
    assert legacy.points_inside(str(tmp_path), tmp_path) is True


def test_anything_not_shown_to_be_inside_is_left_alone(tmp_path):
    inside = tmp_path / "Fulcrum"
    elsewhere = tmp_path / "Elsewhere" / "fulcrum.exe"
    assert legacy.points_inside(str(elsewhere), inside) is False
    assert legacy.points_inside("", inside) is False
    assert legacy.points_inside(None, inside) is False
    assert legacy.points_inside("fulcrum.exe", inside) is False


def test_an_unresolvable_location_is_not_shown_to_own_anything(tmp_path):
    broken = _UnresolvablePath(tmp_path)
    assert legacy.points_inside(str(tmp_path / "fulcrum.exe"), broken) is False


def test_the_old_identity_keys_are_the_ones_fulcrum_wrote(tmp_path):
    assert legacy.toast_identity_key() == (
        r"Software\Classes\AppUserModelId\uk.codecrafter.fulcrum"
    )
    assert legacy.LEGACY_UNINSTALL_KEY.endswith(r"\Uninstall\Fulcrum")
    assert legacy.legacy_state_dir(tmp_path) == tmp_path / ".fulcrum"


def test_the_old_identity_never_collides_with_the_new_one():
    assert legacy.LEGACY_UNINSTALL_KEY != logic.UNINSTALL_KEY
    assert legacy.LEGACY_RUN_VALUE != logic.RUN_VALUE
    assert legacy.LEGACY_AUMID != logic.APP_AUMID
    assert legacy.LEGACY_EXE_NAME != logic.EXE_NAME


def test_the_shortcut_target_read_quotes_the_link_safely():
    command = scripts.shortcut_target_command(Path(r"C:\Users\O'Neil\F.lnk"))
    assert command == (
        "(New-Object -ComObject WScript.Shell).CreateShortcut("
        r"'C:\Users\O''Neil\F.lnk').TargetPath"
    )


def test_the_task_list_match_takes_the_executable_to_look_for():
    listing = "FULCRUM.EXE  1234 Console"
    assert scripts.process_is_running(listing, legacy.LEGACY_EXE_NAME) is True
    assert scripts.process_is_running(listing) is False
