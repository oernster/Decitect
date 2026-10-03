# Fulcrum testing

The suite is `pytest` with a hard 100% coverage gate on the layers that carry
logic. For the design see [ARCHITECTURE.md](ARCHITECTURE.md); for the wider
workflow see [DEVELOPMENT.md](DEVELOPMENT.md).

## Running

From the repo root with the venv active:

```
pytest
```

The configuration in `pyproject.toml` runs coverage automatically and fails the
run below 100% on the gated layers. To format and lint as well:

```
black --check .
flake8 .
ruff check .
```

Run from the repo root so the installer and the build scripts are read too.
`ruff check .` is clean under ruff 0.15.22, the version `requirements-dev.txt`
pins; ruff 0.16 widens its defaults (see [TECH_DEBT.md](TECH_DEBT.md)).

## Reading the result

Trust the exit code, not the text. Because coverage runs with
`--cov-fail-under=100`, a passing run prints the coverage table last and emits
no "N passed" summary line, so a glance at the tail shows coverage rows rather
than a result. Exit code 0 means every test passed and the coverage gate was
met; a non-zero code means something failed, with the failures printed above the
coverage table. For a plain count, run `pytest --no-cov -q`.

## Layout

The tests mirror the package, one area per layer:

| Area | Kind | I/O |
|---|---|---|
| `tests/domain` | pure unit tests of the model, moves, signals and books | none |
| `tests/application` | unit tests over the Protocol seams, using hand-written fakes; the guide's worker pool is also exercised live with a real two-worker process pool and asserted bit-identical to the serial path | none |
| `tests/infrastructure` | integration tests against real files in a temp directory | temp files |
| `tests/installer` | unit tests of the Windows installer's decisions, deploying real zips into a temp directory | temp files |
| `tests/scripts` | smoke tests of the three analysis scripts at the repo root | reads examples |
| `tests/structural` | an AST scan that enforces the architectural invariants | reads source |
| `tests/ui` | Qt tests on a real `QApplication` (pytest-qt's `qapp`) that never show a window: the update check, the donate button, the plan import's failure message and the launch message after a damaged autosave | temp files |

## Coverage scope

`.coveragerc` gates the domain, the application, the infrastructure, the
shared text helpers and the installer's pure modules
(`installer/installer_logic.py` and `installer/installer_scripts.py`) at
100%. It omits the surfaces that are
composition or framework glue: the UI, `main.py`, the shared asset discovery,
the application Protocol definitions, the version module,
`generate_icons.py` plus the installer's Qt surface and side-effect modules.
Those carry no branching logic, so they are verified by running the app
rather than by the gate.

The installer is gated because it is a second application, not a build
recipe: a defect in its registry writes, path resolution, extraction or
shortcut targets lands on a user's machine before Fulcrum ever starts. The
decisions live in `installer_logic.py` with no registry, no subprocess, no
environment and no Qt, which is exactly what makes them testable; the
exact command text those decisions are carried out with lives beside it in
`installer_scripts.py` so it can be asserted character by character; the
module that acts on them (`installer_ops.py`) stays outside the gate with the
widgets. The analysis scripts at the repo root are outside the gate too but
not outside the suite: `tests/scripts` asserts each one runs and exits zero.

One invariant cannot be reached from either side alone. The installer is
compiled separately and may not import the application, so the name of the
per-user state directory is necessarily written down twice.
`tests/installer/test_state_dir.py` holds the two together by comparing the
paths both sides compute, because that drift is silent: an uninstaller
clearing the wrong directory reports success either way.

## Structural invariants

`tests/structural/test_architecture.py` is part of the suite, not a separate
check. It fails the build if the domain imports anything beyond an allowlist
of pure standard-library modules and itself; if the domain calls an I/O or
dynamic-code builtin such as `open` or `__import__`; if the application
imports infrastructure, the UI or Qt; if infrastructure or shared imports
the UI or Qt; if any module exceeds 400
lines, the test modules and the installer included (an oversized test file
hides structure the same way an oversized source file does); if anything
under `installer/` imports from the `fulcrum` package, which would drag the
whole application into the setup binary; or if `installer_logic.py` or
`installer_scripts.py` reaches for the registry, a subprocess, the
environment or Qt; or if anything shipped but the update check imports a
networking module. Relative imports are resolved against the file's own
package before any rule reads them, so `from ..ui import x` is seen as the
import of `fulcrum.ui` it is.

The rules live in `tests/structural/layer_rules.py`, one checker per rule
taking one file, so `tests/structural/test_layer_plants.py` can run each
rule over a planted violation in a temporary directory and assert it
fails: the relative imports, Qt, I/O modules and builtins that once passed
the old denylist unseen. A rule that never meets a violation proves
nothing about its reach; these do. What the network rule still cannot see
is a connection a library opens through a module its list does not name.
Within that limit the architectural rules are tested, not merely
documented.

## Verifying the UI

`tests/ui` holds four behaviours that matter beyond their pixels. An update
check whose controller is deleted before its answer arrives drops the answer
rather than raising on the worker thread. The donate button sits immediately
left of the theme toggle, in the row and in the focus ring alike, asks the
desktop for its one address and says so when the desktop refuses; the
`fulcrum.ui.links` seam is replaced in those tests, so no browser ever opens.
A plan file that will not read or replay produces one warning (through an
injected callable, so no dialog opens) and leaves the session as it was.
The launch message after a damaged autosave says whether the organisation
or only its move record was lost and where the file was kept.
No UI test shows a window. Set `QT_QPA_PLATFORM=offscreen` to run the suite
with no display at all.

The UI is outside the coverage gate, so it is checked two ways: by constructing
widgets headlessly (an offscreen `QApplication`) and asserting their structure
and behaviour, then by eye on a real window. Two caveats are worth knowing: a
`QSpinBox` paints its stepper arrows only in a genuinely shown window, so
spinbox styling is verified with a real `show()` rather than an offscreen grab;
and the offscreen platform resolves no real fonts (every glyph renders as a
placeholder box), so anything that measures rendered glyph geometry must run on
the native platform, grabbing widgets without ever showing a window.

That second caveat has a sharp edge worth naming, because it produces
confident wrong answers rather than errors. Under the offscreen platform Qt
resolves no font family at all and reports a flat one-em advance for every
character, so `QFontMetrics` there will happily measure a string at roughly
twice its real width. Nothing that needs true text metrics may be measured
that way. The exported map's node sizing is the case in point: the advance
table in `fulcrum/infrastructure/svg_map.py` was derived by measuring the
real `segoeui.ttf` and `arial.ttf` files in both weights and taking the
widest member of each character class, so the estimate is an upper bound by
construction. `tests/infrastructure/test_svg_map.py` then checks the emitted
SVG itself, asserting every `<text>` fits the `<rect>` it sits in, which
needs no font engine at all.
