# Decitect development

Working on Decitect from source. For the design see
[ARCHITECTURE.md](ARCHITECTURE.md); for the suite see [TESTING.md](TESTING.md).

## Environment

Python 3.11 or newer; developed on 3.13.

Windows:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python main.py
```

macOS and Linux:

```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python main.py
```

`requirements.txt` holds the one runtime dependency, PySide6.
`requirements-dev.txt` adds pytest (with pytest-cov and pytest-qt), Pillow,
black, flake8, ruff and Nuitka 4.2.1 or later; the Nuitka builds stop with the
install command when Nuitka is missing or older.

## Project layout

```
decitect/
  domain/          pure model: org state, moves, scoring, frames, signals, books
  application/     simulator seam, session, org draft, planner, guide and its
                   worker pool, plan, glossary, update decision
  infrastructure/  JSON, plan export, HTML and SVG renderers, autosave,
                   settings, state directory, GitHub releases adapter
  ui/              PySide6 board, maps, editor and dialogs
  shared/          asset discovery and text helpers (no Qt)
installer/         the Windows setup program, layered like the app
tests/             one area per layer plus installer, scripts, structural, ui
assets/            book covers, header-button icons, the donate master
examples/          reference organisations, including examples/calibration
docs/              the GitHub Pages site (hand-maintained)
main.py            the composition root
```

## Quality gate

Run all four from the repo root before pushing:

```
pytest
black --check .
flake8 .
ruff check .
```

`.flake8` holds the exclusions and `pyproject.toml` mirrors them for ruff.
`ruff check .` is clean under the pinned 0.15.22; 0.16 widens its defaults (see
[TECH_DEBT.md](TECH_DEBT.md)). The structural tests in `tests/structural`
enforce the layer rules, so a feature placed in the wrong layer fails the suite.

## Build scripts

Run each from the repo root with the venv active, on the platform it targets.

### Icons

```
python generate_icons.py
python generate_button_icons.py
```

`generate_icons.py` renders the PNG set and `decitect.ico` from the
`decitect.png` master, applying the glow treatment and trim.
`generate_button_icons.py` draws the header-button icons into `assets/buttons`
(one variant per theme) and derives the app's donate mark from
`assets/donate.png`, scaled to four times the header's icon height
(`BUTTON_ICON_PX`). Both are deterministic: edit the script, never the PNGs. The
site's `docs/donate.png` is the shared mark, not generated.

### Windows executable

```
python buildexe.py
```

Builds a standalone executable with Nuitka into `installer/payload/Decitect`,
with its assets, `VERSION` and licences beside it. `DECITECT_DEBUG_CONSOLE=1`
gives a console build. `main.py` calls `multiprocessing.freeze_support()`, so
several `decitect.exe` processes during guide planning are the worker pool.

### Windows installer

```
python buildinstaller.py
```

Run `buildexe.py` first. Produces `dist-installer/DecitectSetup.exe`, which
installs per user to `%LOCALAPPDATA%\Programs\Decitect`, registers in the Apps
list and creates shortcuts. In `installer/`, `installer_logic.py` and
`installer_legacy.py` decide (the latter for an old Fulcrum install) and are
gated at 100%; `installer_scripts.py` builds the command text; `installer_ops.py`
and `installer_startup.py` act; `installer_lifecycle.py` composes; the Qt
modules present; `app.py` is the entry point. Nothing there imports `decitect`.

### macOS disk image

```
python builddmg.py
```

Compiles `Decitect.app` with Nuitka into `decitect.dmg`. Needs Xcode
command-line tools, Homebrew and `create-dmg`. Always signed (identity from
`DEVELOPER_ID_APPLICATION` when set) and notarized, using `APPLE_ID` with an
app-specific `APPLE_APP_PASSWORD` or else the keychain profile `Decitect` (or
`APPLE_KEYCHAIN_PROFILE`). A missing or rejected credential stops the build;
`ALLOW_UNNOTARIZED=1` skips notarization for a local build that must never ship.
Run `generate_icons.py` first: the `.icns` comes from `decitect_1024.png` down.

### Linux Flatpak

```
./build_flatpak.sh
./clean_flatpak.sh
```

Builds against `org.freedesktop.Platform//25.08` from pre-downloaded wheels, so
the build is offline, installs for the current user and writes
`decitect.flatpak` (`--no-bundle` skips the bundle). The sandbox grants
`--share=network` for the update check. Needs `flatpak` and `flatpak-builder`
with the 25.08 runtime and SDK. `clean_flatpak.sh` uninstalls it and removes the
Flatpak artefacts only.

### GitHub Pages site

The site is hand-written HTML in `docs/`, served from `main` `/docs`: `index`,
`tool` (with `vocabulary` and `play`), `why`, `model` (with `weights`,
`assumptions` and `testing`) and `download`, sharing `styles.css`. Edit the
pages directly. Versions sit between `<!--VERSION-->` delimiters. This stamps
them and the stylesheet's content hash:

```
python stamp_version.py
```

The Windows builds stamp automatically; the macOS and Linux builds do not.
Screenshots in `docs/assets/screenshots/` are captured from the running app.

### Analysis scripts

```
python sensitivity.py
python calibrate.py
```

`sensitivity.py` re-scores the ten archetypes with every coefficient scaled by
0.8 and 1.2, then jointly; it exits non-zero if a published conclusion fails.
`calibrate.py` scores `examples/calibration/` against each case's expected band.
Calibration cases are modelled with outcome knowledge, so they can never join
the blind validation set (PREREGISTRATION.md); add one from `TEMPLATE.json`.
`generate_matrixed_enterprise.py` writes the large case; rerun it rather than
editing its JSON. All three are smoke-tested in `tests/scripts`.

## Conventions

- No magic numbers: values come from data, configuration or named constants.
- Frozen dataclasses in the domain; constructor injection; one composition root.
- `black` line length 88; no em dashes anywhere.
- UI sizes go through `ui_scale.px(...)`; verify UI changes on a real window.
