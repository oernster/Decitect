"""Structural tests: enforce layer boundaries and module size via AST scan.

The rules themselves live in layer_rules, where test_layer_plants proves
each one bites on a planted violation.
"""

from layer_rules import PKG as _PKG
from layer_rules import ROOT as _ROOT
from layer_rules import (
    application_violations,
    domain_violations,
    is_network_module,
    network_imports,
    ui_import_violations,
)
from layer_rules import imported_modules as _imported_modules
from layer_rules import python_files as _python_files

_INSTALLER = _ROOT / "installer"
_MAX_LINES = 400
# The installer's own payload is staged build output, not source.
_INSTALLER_PAYLOAD = "payload"


def _layer_problems(layer, rule):
    return [
        f"{path.name}: {found}"
        for path in _python_files(_PKG / layer)
        if (found := rule(path))
    ]


def test_domain_imports_no_io_or_outer_layers():
    # An allowlist of pure standard-library modules plus the domain itself,
    # with relative imports resolved and I/O builtins refused.
    assert _layer_problems("domain", domain_violations) == []


def test_application_does_not_import_infrastructure_or_ui():
    assert _layer_problems("application", application_violations) == []


def test_infrastructure_and_shared_never_import_the_ui_or_qt():
    # The GPL and LGPL boundary the LICENSE draws: only decitect.ui is Qt.
    for layer in ("infrastructure", "shared"):
        assert _layer_problems(layer, ui_import_violations) == [], layer


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
    # application: an import of decitect here would drag the whole package
    # into the setup binary and couple two release artefacts together.
    for path in _installer_sources():
        modules = _imported_modules(path)
        assert not any(m.split(".")[0] == "decitect" for m in modules), path.name


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
# it can neither widen nor outlive its purpose. The module list lives in
# layer_rules; what it cannot see is a connection a library opens through a
# module not listed there.
_UPDATE_CHECK = _PKG / "infrastructure" / "github_release_source.py"
_UPDATE_CHECK_GRANTS = {"urllib.request"}
_is_network_module = is_network_module
_network_imports = network_imports


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
    assert any(name.startswith("decitect/") for name in scanned)
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
