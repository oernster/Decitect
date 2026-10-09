"""Installer side effects: registry, processes, shortcuts and shell-outs.

Every function here carries out a decision taken in installer_logic.py. The
split is what makes the installer testable: the decisions are pure and
covered by the suite, and this module is the thin, untested edge where the
Windows registry, the task list, PowerShell and the Win32 API are touched.
Keep it thin. Anything that chooses rather than acts belongs next door.

Failures here are best effort by design: an installer that stops dead
because a shortcut could not be written is worse than one that reports what
it managed to do. Nothing in this module imports Qt.

British spelling is used in comments. No em dashes appear anywhere.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path

import installer_legacy as legacy
import installer_logic as logic
import installer_scripts as scripts

# Best-effort shell-out timeouts.
_POWERSHELL = "powershell"
_SHORTCUT_TIMEOUT_S = 15
_TASKLIST_TIMEOUT_S = 10


# -------------------------------------------------------------------- registry


def _registry_kind(winreg, kind: str):
    """Map a logic registry kind onto the winreg constant that writes it."""
    return winreg.REG_DWORD if kind == logic.REG_DWORD else winreg.REG_SZ


def read_registry_str(key: str, name: str) -> str | None:
    """Return an HKCU string value, or None when the key or value is absent."""
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            return str(winreg.QueryValueEx(handle, name)[0])
    except OSError:
        return None


def write_uninstall_entry(values: tuple[logic.RegistryValue, ...]) -> None:
    """Register the app under HKCU so it appears in Apps and features."""
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, logic.UNINSTALL_KEY) as handle:
        for value in values:
            winreg.SetValueEx(
                handle, value.name, 0, _registry_kind(winreg, value.kind), value.value
            )


def delete_key(key: str) -> None:
    """Remove an HKCU key that has no subkeys (best effort)."""
    import winreg

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
    except OSError:
        return


def delete_uninstall_entry() -> None:
    """Remove the HKCU Uninstall registration (best effort)."""
    delete_key(logic.UNINSTALL_KEY)


def delete_toast_identity() -> None:
    """Remove the app's notification (AppUserModelId) registration.

    The app writes its toast name and icon under HKCU on launch; removing the
    key on uninstall leaves no orphaned registration behind. Best effort.
    """
    delete_key(logic.toast_identity_key())


def installed_version(key: str = logic.UNINSTALL_KEY) -> str | None:
    """Return the registered installed version; None when not installed."""
    return read_registry_str(key, "DisplayVersion")


def installed_location(key: str = logic.UNINSTALL_KEY) -> Path | None:
    """Return the registered install location; None when not installed."""
    return logic.absolute_location(read_registry_str(key, "InstallLocation"))


# ------------------------------------------------------------------ autostart


def set_autostart(enabled: bool, exe_path: Path) -> None:
    """Add or remove the per-user Run entry that starts the app at sign-in."""
    import winreg

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, logic.RUN_SUBKEY) as key:
            if enabled:
                winreg.SetValueEx(
                    key, logic.RUN_VALUE, 0, winreg.REG_SZ, f'"{exe_path}"'
                )
            else:
                try:
                    winreg.DeleteValue(key, logic.RUN_VALUE)
                except OSError:
                    pass
    except OSError:
        return


def remove_autostart(value: str = logic.RUN_VALUE) -> None:
    """Remove a per-user Run entry (best effort), used on uninstall."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, logic.RUN_SUBKEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, value)
            except OSError:
                pass
    except OSError:
        return


# ----------------------------------------------------------------- user paths


def install_target() -> Path:
    """Return the per-user install directory for the application."""
    return logic.install_target(os.environ.get(logic.ENV_LOCALAPPDATA), Path.home())


def state_dir() -> Path:
    """Return the per-user state directory the app writes (settings, saves)."""
    return logic.state_dir(Path.home())


def start_menu_link() -> Path | None:
    """Return the per-user Start Menu shortcut path, or None when unavailable."""
    return logic.start_menu_link(os.environ.get(logic.ENV_APPDATA))


def desktop_link() -> Path:
    """Return the per-user Desktop shortcut path."""
    return logic.desktop_link(Path.home())


# ------------------------------------------------------------------- processes


def is_app_running(exe_name: str = logic.EXE_NAME) -> bool:
    """Return True when the executable appears in the task list (best effort)."""
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["tasklist", "/fi", f"imagename eq {exe_name}", "/nh"],
            capture_output=True,
            text=True,
            timeout=_TASKLIST_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            creationflags=no_window,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return scripts.process_is_running(result.stdout, exe_name)


def run_powershell(command: str) -> str:
    """Run a PowerShell command; its output, empty on any failure."""
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [_POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command],
            check=False,
            timeout=_SHORTCUT_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            creationflags=no_window,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout or ""


def launch(exe_path: Path) -> subprocess.Popen | None:
    """Start the installed application without waiting for it (best effort)."""
    try:
        return subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
    except OSError:
        return None


def bring_process_window_to_front(pid: int) -> bool:
    """Front the process's first visible top-level window, if it exists yet."""
    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _on_window(hwnd, _lparam):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(_on_window, 0)
    if not found:
        return False
    user32.SetForegroundWindow(found[0])
    return True


# ------------------------------------------------------------------- shortcuts


def create_shortcut(exe_path: Path, link: Path) -> None:
    """Write a shortcut to the installed exe with the app icon (best effort)."""
    link.parent.mkdir(parents=True, exist_ok=True)
    run_powershell(scripts.shortcut_command(exe_path, link))


def remove_shortcut(link: Path | None) -> None:
    """Delete a shortcut file if present (best effort)."""
    if link is None:
        return
    try:
        link.unlink(missing_ok=True)
    except OSError:
        return


def apply_shortcuts(exe_path: Path, *, desktop: bool, start_menu: bool) -> None:
    """Create or remove the desktop and Start Menu shortcuts to match options."""
    desktop_target = desktop_link()
    if desktop:
        create_shortcut(exe_path, desktop_target)
    else:
        remove_shortcut(desktop_target)

    start_link = start_menu_link()
    if start_menu and start_link is not None:
        create_shortcut(exe_path, start_link)
    else:
        remove_shortcut(start_link)


# ----------------------------------------------------------------- deploy/ops


def original_installer_exe() -> Path:
    """Return the original onefile installer the user launched."""
    return logic.original_installer_exe(
        os.environ.get(logic.NUITKA_ONEFILE_ENV, ""),
        sys.argv[0] if sys.argv else "",
        sys.executable,
        Path(tempfile.gettempdir()).resolve(),
    )


def copy_uninstaller(install_dir: Path) -> Path:
    """Copy this installer into the install root to act as the uninstaller.

    Best effort: the application is already deployed by the time this runs, so
    a failure here degrades to using the running executable as the uninstall
    source rather than failing the whole install.
    """
    source = original_installer_exe()
    destination = logic.uninstaller_path(install_dir)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    except Exception:  # noqa: BLE001 - any failure degrades to the running exe
        return source
    return destination


def running_from_inside(install_dir: Path) -> bool:
    """Return True when this process's exe lives inside ``install_dir``."""
    return logic.running_from_inside(Path(sys.executable), install_dir)


def schedule_delete_after_exit(install_dir: Path) -> None:
    """Delete ``install_dir`` from a detached helper once this process exits.

    The registered uninstaller lives inside the install directory, so it cannot
    remove its own running exe. A hidden PowerShell process polls and deletes
    once the lock is released, rather than racing a fixed delay.
    """
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    detached = getattr(subprocess, "DETACHED_PROCESS", 0)
    try:
        subprocess.Popen(
            [
                _POWERSHELL,
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-Command",
                scripts.deferred_delete_script(install_dir),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=no_window | detached,
        )
    except (OSError, subprocess.SubprocessError):
        return


def remove_state(remove_settings: bool) -> None:
    """Remove the per-user state directories when the user asked for it.

    The former name's directory goes too: it is only still there when the
    app could not adopt it. The user asked for their settings gone.
    """
    if remove_settings:
        shutil.rmtree(state_dir(), ignore_errors=True)
        shutil.rmtree(legacy.legacy_state_dir(Path.home()), ignore_errors=True)


def remove_install_dir(install_dir: Path) -> None:
    """Remove an install directory, deferring when it holds the running exe."""
    if not install_dir.exists():
        return
    if running_from_inside(install_dir):
        schedule_delete_after_exit(install_dir)
    else:
        shutil.rmtree(install_dir, ignore_errors=True)
