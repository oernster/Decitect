"""The layer rules the structural tests enforce, one checker per rule.

Each checker takes one source file and returns its violations, so the same
rule runs over the real package and over a planted file in a temporary
directory; the plant tests prove each rule bites rather than trusting it.

Relative imports are resolved against the file's own package before any
rule reads them: `from ..ui import x` inside `decitect.domain` is an import
of `decitect.ui.x`, whatever it looks like on the page.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "decitect"

# The domain is an allowlist, not a denylist: pure computation from the
# standard library and the domain itself. Anything else (I/O, clocks,
# randomness, processes, dynamic import, frameworks, an outer layer) is a
# violation by default, so a module nobody thought to ban is still caught.
DOMAIN_STDLIB = frozenset(
    {
        "__future__",
        "abc",
        "bisect",
        "collections",
        "copy",
        "dataclasses",
        "decimal",
        "enum",
        "fractions",
        "functools",
        "heapq",
        "itertools",
        "math",
        "numbers",
        "operator",
        "re",
        "statistics",
        "string",
        "types",
        "typing",
    }
)
_DOMAIN_PACKAGE = "decitect.domain"
_TOP_PACKAGE = "decitect"
# Builtins that reach outside the process or load code by name, so I/O or
# an import can happen with no import statement at all.
FORBIDDEN_CALLS = frozenset(
    {"open", "__import__", "eval", "exec", "compile", "input", "print", "breakpoint"}
)
FORBIDDEN_FOR_APPLICATION = ("decitect.infrastructure", "decitect.ui", "PySide6")
# The UI is the only LGPL component and the only Qt client; nothing in the
# GPL layers beneath it may import either.
UI_AND_QT = ("decitect.ui", "PySide6")


def python_files(directory):
    return sorted(directory.rglob("*.py"))


def package_of(path):
    """The dotted package a source file under the repo root belongs to.

    A file outside the repo (a probe in a temporary directory) is read as a
    top-level module; a plant that needs a package passes one explicitly.
    """
    try:
        parts = path.resolve().relative_to(ROOT).with_suffix("").parts
    except ValueError:
        return ""
    return ".".join(parts[:-1])


def _resolve(node, package):
    """The absolute module an ImportFrom names, relative levels resolved."""
    if node.level == 0:
        return node.module
    parts = package.split(".") if package else []
    base = ".".join(parts[: len(parts) - (node.level - 1)])
    if node.module:
        return f"{base}.{node.module}" if base else node.module
    return base


def _matches(module, prefix):
    return module == prefix or module.startswith(prefix + ".")


def imported_modules(path, package=None):
    # `from a import b` records `a.b` as well, because `b` may be a submodule:
    # `from PySide6 import QtNetwork` is an import of `PySide6.QtNetwork`.
    if package is None:
        package = package_of(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            base = _resolve(node, package)
            if base:
                found.add(base)
                found.add(base.split(".")[0])
            found.update(
                f"{base}.{alias.name}" if base else alias.name for alias in node.names
            )
    return found


def forbidden_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sorted(
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in FORBIDDEN_CALLS
    )


def _domain_allows(module):
    if module == _TOP_PACKAGE or _matches(module, _DOMAIN_PACKAGE):
        return True
    return module.split(".")[0] in DOMAIN_STDLIB


def domain_violations(path, package=None):
    modules = imported_modules(path, package)
    bad = sorted(m for m in modules if not _domain_allows(m))
    return bad + forbidden_calls(path)


def application_violations(path, package=None):
    modules = imported_modules(path, package)
    return sorted(
        m for m in modules if any(_matches(m, p) for p in FORBIDDEN_FOR_APPLICATION)
    )


def ui_import_violations(path, package=None):
    modules = imported_modules(path, package)
    return sorted(m for m in modules if any(_matches(m, p) for p in UI_AND_QT))


# What this cannot see: a connection a library opens through a module not
# listed here.
NETWORK_ROOTS = {
    "socket",
    "ssl",
    "http",
    "asyncio",
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
NETWORK_PREFIXES = (
    "urllib.request",
    "urllib.error",
    "PySide6.QtNetwork",
    "PySide6.QtWebEngine",
    "PySide6.QtWebSockets",
)


def is_network_module(module):
    return module.split(".")[0] in NETWORK_ROOTS or module.startswith(NETWORK_PREFIXES)


def network_imports(path, package=None):
    return {m for m in imported_modules(path, package) if is_network_module(m)}
