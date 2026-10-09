"""Each layer rule bites on a planted violation.

A structural test that never sees a violation proves nothing about its own
reach. The audit planted these exact lines into the package and the gate
stayed green: relative imports were recorded as written (so `..ui` never
matched `decitect.ui`), the domain rule was a ten-name denylist and I/O
through a builtin needed no import at all. Each plant here is one line in a
temporary file scanned as if it sat in the named package.
"""

import pytest
from layer_rules import (
    PKG,
    application_violations,
    domain_violations,
    network_imports,
    package_of,
    ui_import_violations,
)

_DOMAIN = "decitect.domain"
_DOMAIN_MODULE = PKG / "domain" / "models.py"
_APPLICATION = "decitect.application"


def test_a_real_module_resolves_to_its_own_package():
    # Without this, a silent fallback to the top level would resolve every
    # relative import in the package against the wrong base.
    assert package_of(_DOMAIN_MODULE) == _DOMAIN
    assert package_of(PKG / "__init__.py") == "decitect"


def _plant(tmp_path, source):
    path = tmp_path / "zz_plant.py"
    path.write_text(source + "\n", encoding="utf-8")
    return path


_DOMAIN_PLANTS = (
    "import asyncio",
    "import importlib",
    "import io",
    "import shutil",
    "import subprocess",
    "import time",
    "from PySide6 import QtWidgets",
    "from .. import infrastructure",
    "from ..ui import main_window",
    "from ..application import game_session",
    "from decitect.ui import main_window",
    "open('x')",
    "__import__('socket')",
    "eval('1')",
    "exec('x = 1')",
    "print('x')",
)


@pytest.mark.parametrize("source", _DOMAIN_PLANTS)
def test_the_domain_rule_bites(tmp_path, source):
    assert domain_violations(_plant(tmp_path, source), _DOMAIN), source


_DOMAIN_CLEAN = (
    "from __future__ import annotations",
    "import math",
    "from dataclasses import dataclass",
    "from enum import Enum",
    "from collections.abc import Iterable",
    "from .models import OrgState",
    "from . import errors",
    "from decitect.domain.models import Team",
)


@pytest.mark.parametrize("source", _DOMAIN_CLEAN)
def test_the_domain_rule_passes_pure_code(tmp_path, source):
    assert domain_violations(_plant(tmp_path, source), _DOMAIN) == [], source


_APPLICATION_PLANTS = (
    "from ..infrastructure import json_serialization",
    "from ..ui.widgets import org_editor",
    "from .. import ui",
    "from decitect.infrastructure import org_autosave",
    "from PySide6.QtCore import QObject",
)


@pytest.mark.parametrize("source", _APPLICATION_PLANTS)
def test_the_application_rule_bites(tmp_path, source):
    assert application_violations(_plant(tmp_path, source), _APPLICATION), source


def test_the_application_rule_passes_inward_imports(tmp_path):
    source = "from ..domain.models import OrgState\nfrom .dto import Plan"
    assert application_violations(_plant(tmp_path, source), _APPLICATION) == []


_UI_PLANTS = (
    "from ..ui import main_window",
    "from decitect.ui.widgets import org_editor",
    "from .. import ui",
    "import PySide6.QtWidgets",
    "from PySide6 import QtGui",
)


@pytest.mark.parametrize("package", ("decitect.infrastructure", "decitect.shared"))
@pytest.mark.parametrize("source", _UI_PLANTS)
def test_nothing_outside_the_ui_imports_the_ui_or_qt(tmp_path, package, source):
    assert ui_import_violations(_plant(tmp_path, source), package), source


def test_the_ui_rule_passes_inward_imports(tmp_path):
    source = "from ..domain.models import OrgState\nfrom .text import count_noun"
    assert ui_import_violations(_plant(tmp_path, source), "decitect.shared") == []


@pytest.mark.parametrize(
    "source", ("import asyncio", "from asyncio import open_connection")
)
def test_the_network_rule_bites(tmp_path, source):
    assert network_imports(_plant(tmp_path, source), _APPLICATION), source
