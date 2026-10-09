# Decitect testing

`pytest` with a hard 100% coverage gate on the layers that carry logic. For the
design see [ARCHITECTURE.md](ARCHITECTURE.md); for the workflow see
[DEVELOPMENT.md](DEVELOPMENT.md).

## Running

From the repo root with the venv active:

```
pytest
black --check .
flake8 .
ruff check .
```

`pyproject.toml` runs coverage and fails below 100% on the gated layers. ruff is
clean under the pinned 0.15.22 (see [TECH_DEBT.md](TECH_DEBT.md)). Set
`QT_QPA_PLATFORM=offscreen` to run with no display; no test shows a window.

## Reading the result

Trust the exit code. A passing run prints the coverage table, the gate line and
"N passed"; a text search for "passed" or "error" also matches coverage rows for
files with those words in their names. Exit 0 means every test passed and the
gate was met. For a plain count, run `pytest --no-cov -q`.

## Layout

| Area | Kind | I/O |
|---|---|---|
| `tests/domain` | unit tests of the model, moves, signals and books | none |
| `tests/application` | unit tests over the Protocol seams with hand-written fakes; the guide's pool also runs live on two real workers and must match the serial path | none |
| `tests/infrastructure` | integration tests against real files in a temp directory | temp files |
| `tests/installer` | the installer's decisions, deploying real zips into a temp directory | temp files |
| `tests/scripts` | smoke tests of the three analysis scripts | reads examples |
| `tests/structural` | AST scans enforcing the architectural invariants | reads source |
| `tests/ui` | Qt tests on a real `QApplication`: the update check, the donate button, plan-import failure and the message after a damaged autosave | temp files |

## Coverage scope

`.coveragerc` gates the domain, application, infrastructure, shared text helpers
and the installer's pure modules (`installer_logic.py`, `installer_legacy.py`,
`installer_scripts.py`) at 100%. It omits composition and framework glue: the
UI, `main.py`, asset discovery, the Protocol definitions, the version module,
`generate_icons.py` and the installer's Qt and side-effect modules
(`installer_ops.py`, `installer_startup.py` among them). The analysis scripts
are outside the gate but inside the suite.

The installer is gated because its defects land on a user's machine before
Decitect starts. Its decisions avoid the registry, subprocesses, the
environment and Qt, which is what makes them testable.

The installer may not import the app, so the state directory's name and the
former name's directory are written down on both sides.
`tests/installer/test_state_dir.py` compares the paths each side computes,
since an uninstaller clearing the wrong directory reports success either way.

## Structural invariants

`tests/structural/test_architecture.py` fails the build if the domain imports
beyond its stdlib allowlist or calls an I/O or dynamic-code builtin; if the
application imports infrastructure, the UI or Qt; if infrastructure or shared
imports the UI or Qt; if any module, tests and installer included, exceeds 400
lines; if the installer imports `decitect`; if an installer decision module
reaches for the registry, a subprocess, the environment or Qt; or if anything
but the update check imports a networking module. Relative imports are
resolved before any rule reads them.

The rules live in `tests/structural/layer_rules.py`, one checker per rule, so
`tests/structural/test_layer_plants.py` runs each over a planted violation and
asserts it fails. The network rule cannot see a connection a library opens
through a module it does not list.

## Verifying the UI

The UI is outside the gate, so it is checked by constructing widgets headlessly
and asserting their behaviour, then by eye on a real window. Two limits of the
offscreen platform: a `QSpinBox` paints its stepper arrows only in a shown
window; no real fonts resolve, so `QFontMetrics` reports one em per character. Nothing needing true text metrics may be measured offscreen. The SVG
exporter's advance table was therefore measured from the real `segoeui.ttf` and
`arial.ttf` as an upper bound; `tests/infrastructure/test_svg_map.py`
asserts every `<text>` fits its `<rect>` with no font engine at all.
