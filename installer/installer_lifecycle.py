"""The install, repair and uninstall sequences, with no Qt.

Each function here is a composition: it asks installer_logic what should
happen and installer_ops to make it happen, in the order that leaves a
working machine at every point. The order matters. Files are deployed
before the uninstaller is registered, so a registration always points at
something that exists; the install directory is removed last on
uninstall, so a failure part way through still leaves the app findable.

British spelling is used in comments. No em dashes appear anywhere.
"""

from __future__ import annotations

import os
from pathlib import Path

import installer_bundle as bundle
import installer_legacy as legacy
import installer_logic as logic
import installer_ops as ops
import installer_scripts as scripts


def _deploy(target: Path) -> Path:
    """Extract the bundled application archive to ``target``; return the exe."""
    return logic.deploy_files(logic.payload_archive(bundle.bundle_root()), target)


def _register(install_dir: Path, uninstaller: Path) -> None:
    """Write the HKCU Apps and features registration for a deployed install."""
    ops.write_uninstall_entry(
        logic.uninstall_entry_values(
            install_dir,
            uninstaller,
            bundle.app_version() or logic.FALLBACK_VERSION,
            logic.dir_size_kb(install_dir),
        )
    )


def install(
    target: Path,
    *,
    desktop: bool,
    start_menu: bool,
    autostart: bool,
    retire: legacy.LegacyInstall | None = None,
) -> Path:
    """Run the full install/upgrade/reinstall: files, registry and shortcuts.

    An install under the former name, when the user chose to remove it, goes
    last: the new install is complete before anything of the old one is
    touched, so a failure part way still leaves a working application.
    """
    exe_path = _deploy(target)
    _register(target, ops.copy_uninstaller(target))
    ops.apply_shortcuts(exe_path, desktop=desktop, start_menu=start_menu)
    ops.set_autostart(autostart, exe_path)
    if retire is not None:
        retire_legacy(retire)
    return exe_path


def find_legacy() -> legacy.LegacyInstall | None:
    """Return an install left under the product's former name, else None."""
    return legacy.find_legacy(
        ops.installed_version(legacy.LEGACY_UNINSTALL_KEY),
        ops.installed_location(legacy.LEGACY_UNINSTALL_KEY),
        legacy.default_location(os.environ.get(logic.ENV_LOCALAPPDATA), Path.home()),
    )


def retire_legacy(found: legacy.LegacyInstall) -> None:
    """Remove an install under the former name, keeping the user's state.

    A shortcut or sign-in entry is removed only when it points inside the
    old install; one pointing anywhere else is not shown to be its own.
    """
    links = legacy.shortcut_links(os.environ.get(logic.ENV_APPDATA), Path.home())
    for link in links:
        if not link.exists():
            continue
        target = ops.run_powershell(scripts.shortcut_target_command(link))
        if legacy.points_inside(target, found.location):
            ops.remove_shortcut(link)
    sign_in = ops.read_registry_str(logic.RUN_SUBKEY, legacy.LEGACY_RUN_VALUE)
    if legacy.points_inside(sign_in, found.location):
        ops.remove_autostart(legacy.LEGACY_RUN_VALUE)
    ops.delete_key(legacy.toast_identity_key())
    ops.delete_key(legacy.LEGACY_UNINSTALL_KEY)
    ops.remove_install_dir(found.location)


def repair(install_dir: Path) -> Path:
    """Re-deploy the application files over an existing install, then register.

    Without a per-file manifest the safe, simple repair is a full re-copy of the
    bundled files: it restores anything missing or altered. User settings live
    outside the install directory, so they are untouched.
    """
    exe_path = _deploy(install_dir)
    _register(install_dir, ops.copy_uninstaller(install_dir))
    ops.apply_shortcuts(exe_path, desktop=True, start_menu=True)
    return exe_path


def uninstall(*, remove_settings: bool) -> None:
    """Remove shortcuts, registry, autostart, user state and the install dir."""
    install_dir = ops.installed_location() or ops.install_target()
    ops.remove_shortcut(ops.desktop_link())
    ops.remove_shortcut(ops.start_menu_link())
    ops.remove_autostart()
    ops.delete_uninstall_entry()
    ops.delete_toast_identity()
    ops.remove_state(remove_settings)
    ops.remove_install_dir(install_dir)


def detect_state() -> str:
    """Classify the current install against the bundled version."""
    return logic.detect_state(
        ops.installed_version(), ops.installed_location(), bundle.app_version()
    )


def primary_label(state: str) -> str:
    """Return the primary button caption for an install state."""
    return logic.primary_label(state, bundle.app_version())
