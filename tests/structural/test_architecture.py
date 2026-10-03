"""Structural tests: enforce layer boundaries and module size via AST scan."""

import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_PKG = _ROOT / "fulcrum"
_INSTALLER = _ROOT / "installer"
_MAX_LINES = 400
# The installer's own payload is staged build output, not source.
_INSTALLER_PAYLOAD = "payload"

_DOMAIN_FORBIDDEN = {
    "os",
    "sys",
    "pathlib",
    "time",
    "random",
    "threading",
    "logging",
    "datetime",
    "json",
    "csv",
}
_OUTER_LAYERS = ("fulcrum.application", "fulcrum.infrastructure", "fulcrum.ui")
_FORBIDDEN_FOR_APPLICATION = ("fulcrum.infrastructure", "fulcrum.ui")


def _python_files(directory):
    return sorted(directory.rglob("*.py"))


def _imported_modules(path):
    # `from a import b` records `a.b` as well, because `b` may be a submodule:
    # `from PySide6 import QtNetwork` is an import of `PySide6.QtNetwork`.
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.add(node.module.split(".")[0])
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def test_domain_imports_no_io_or_outer_layers():
    for path in _python_files(_PKG / "domain"):
        modules = _imported_modules(path)
        assert not (modules & _DOMAIN_FORBIDDEN), path.name
        assert not any(m.startswith(_OUTER_LAYERS) for m in modules), path.name


def test_application_does_not_import_infrastructure_or_ui():
    for path in _python_files(_PKG / "application"):
        modules = _imported_modules(path)
        assert not any(
            m.startswith(_FORBIDDEN_FOR_APPLICATION) for m in modules
        ), path.name


def _installer_sources():
    return [
        path
        for path in _python_files(_INSTALLER)
        if _INSTALLER_PAYLOAD not in path.parts
    ]


def test_modules_stay_under_the_line_limit():
    # Test modules are held to the same cap as source: an oversized test
    # file hides structure exactly the way an oversized source file does.
    # The installer is a second application, not a build recipe, so it is
    # held to the cap as well.
    paths = list(_python_files(_PKG)) + list(_python_files(_ROOT / "tests"))
    paths += _installer_sources()
    for path in paths:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert line_count <= _MAX_LINES, f"{path.name}: {line_count}"


def test_the_installer_stays_standalone():
    # The installer is compiled separately and must pull in nothing from the
    # application: an import of fulcrum here would drag the whole package
    # into the setup binary and couple two release artefacts together.
    for path in _installer_sources():
        modules = _imported_modules(path)
        assert not any(m.split(".")[0] == "fulcrum" for m in modules), path.name


def test_the_installer_decisions_touch_no_side_effects():
    # installer_logic decides and installer_scripts builds the text those
    # decisions are carried out with. Both are gated; both are testable
    # precisely because neither reaches the registry, a subprocess, the
    # environment or Qt. Only installer_ops is allowed to act.
    forbidden = {"winreg", "subprocess", "os", "sys", "ctypes", "PySide6"}
    for name in ("installer_logic.py", "installer_scripts.py"):
        assert not (_imported_modules(_INSTALLER / name) & forbidden), name


# The update check is the only network code (DECISIONS-TRADEOFFS.md). Until
# these tests the claim was held by the documents alone, so a new outbound call
# would have passed. The scope is everything a user installs: the package, the
# setup program and the composition root. The exemption is asserted whole, so
# it can neither widen nor outlive its purpose. What this cannot see: a
# connection a library opens through a module not listed here.
_NETWORK_ROOTS = {
    "socket",
    "ssl",
    "http",
    "smtplib",
    "imaplib",
    "poplib",
    "ftplib",
    "telnetlib",
    "xmlrpc",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "websocket",
    "websockets",
}
# Matched as prefixes: the Qt names cover every WebEngine module at once.
_NETWORK_PREFIXES = (
    "urllib.request",
    "urllib.error",
    "PySide6.QtNetwork",
    "PySide6.QtWebEngine",
    "PySide6.QtWebSockets",
)
_UPDATE_CHECK = _PKG / "infrastructure" / "github_release_source.py"
_UPDATE_CHECK_GRANTS = {"urllib.request"}


def _is_network_module(module):
    return module.split(".")[0] in _NETWORK_ROOTS or module.startswith(
        _NETWORK_PREFIXES
    )


def _network_imports(path):
    return {m for m in _imported_modules(path) if _is_network_module(m)}


def _shipped_sources():
    return [_ROOT / "main.py", *_python_files(_PKG), *_installer_sources()]


def test_only_the_update_check_reaches_the_network():
    problems = [
        f"{path.relative_to(_ROOT).as_posix()} imports {sorted(found)}"
        for path in _shipped_sources()
        if path != _UPDATE_CHECK and (found := _network_imports(path))
    ]
    assert problems == []


def test_the_update_check_exemption_is_exact():
    found = _network_imports(_UPDATE_CHECK)
    assert _UPDATE_CHECK_GRANTS <= found, "the exemption has outlived its reason"
    assert found <= _UPDATE_CHECK_GRANTS, f"the exemption has widened: {found}"


def test_the_network_scan_covers_what_ships():
    scanned = {p.relative_to(_ROOT).as_posix() for p in _shipped_sources()}
    assert {"main.py", "installer/app.py"} <= scanned
    assert any(name.startswith("fulcrum/") for name in scanned)
    assert not any(_INSTALLER_PAYLOAD in name.split("/") for name in scanned)


def test_network_module_recognition_is_exact():
    for module in ("socket", "http.client", "urllib.request", "PySide6.QtNetwork"):
        assert _is_network_module(module), module
    for module in ("PySide6.QtWebEngineWidgets", "requests.adapters"):
        assert _is_network_module(module), module
    for module in ("urllib.parse", "json", "socketless", "PySide6.QtWidgets"):
        assert not _is_network_module(module), module


def test_a_submodule_imported_from_its_package_is_seen(tmp_path):
    probe = tmp_path / "probe.py"
    probe.write_text("from PySide6 import QtNetwork\n", encoding="utf-8")
    assert "PySide6.QtNetwork" in _imported_modules(probe)
