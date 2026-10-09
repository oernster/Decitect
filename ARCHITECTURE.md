# Decitect architecture

Decitect is a deterministic Decision Architecture engine inside a local-first
PySide6 desktop app. Every invariant below but the last is enforced by a test.

## Invariants

| Invariant | Enforced by |
|---|---|
| The domain is pure: an allowlist of pure-computation stdlib modules (`DOMAIN_STDLIB` in `tests/structural/layer_rules.py`) plus itself, with relative imports resolved first; the I/O and dynamic-code builtins (`open`, `__import__`, `eval`, `exec`, `compile`, `input`, `print`, `breakpoint`) refused. | `tests/structural/test_architecture.py::test_domain_imports_no_io_or_outer_layers` |
| Dependencies point inward: the application never imports infrastructure, the UI or Qt. | `tests/structural/test_architecture.py::test_application_does_not_import_infrastructure_or_ui` |
| Only the UI is Qt: infrastructure and shared never import `decitect.ui` or PySide6 (the GPL and LGPL boundary). | `tests/structural/test_architecture.py::test_infrastructure_and_shared_never_import_the_ui_or_qt` |
| Each layer rule above fails on a planted violation. | `tests/structural/test_layer_plants.py` |
| No module in the package, the tests or the installer exceeds 400 lines; the repo-root build and analysis scripts are exempt. | `tests/structural/test_architecture.py::test_modules_stay_under_the_line_limit` |
| The update check is the only network code: nothing in the package, the installer or `main.py` imports a networking module except `infrastructure/github_release_source.py`, which may import `urllib.request` alone. | `tests/structural/test_architecture.py::test_only_the_update_check_reaches_the_network` and `::test_the_update_check_exemption_is_exact` |
| The installer imports nothing from the `decitect` package. | `tests/structural/test_architecture.py::test_the_installer_stays_standalone` |
| The installer's decision modules (`installer_logic.py`, `installer_legacy.py`, `installer_scripts.py`) touch no registry, subprocess, environment or Qt. | `tests/structural/test_architecture.py::test_the_installer_decisions_touch_no_side_effects` |
| The domain, application, infrastructure, shared text helpers and installer decision modules are covered 100%. | `--cov-fail-under=100` in `pyproject.toml` with `.coveragerc` |
| One explicit composition root. | Convention, not a test: `main.py` alone constructs concrete infrastructure. |

## Layers

UI to Application to Domain, with Infrastructure pointing in to the same Domain.

- **Domain** (`decitect/domain`): frozen value objects (`OrgState`, `Team`,
  `Dependency`, `Domain`, `AuthorityClaim`), the domain hierarchy and its
  scoring frames, structural `Move`s, the scoring model (`evaluate`), the
  signals and the books' reference data. Every field is type-checked as well as
  range-checked (`field_checks`), since organisations arrive from files and NaN
  passes every comparison; `evaluate` refuses a non-finite result. Counts are
  capped at 2^53. Team and unit ids share one namespace.
- **Application** (`decitect/application`): the `Simulator` seam, the
  `GameSession`, off-thread scope analysis, the blueprint intake and its inverse
  (the round-trip editing seam), the editor's org draft, the name pool, the
  level generator, the planner and the whole-hierarchy guide with its worker
  pool, the map model, the plan report builder, the glossary and the update
  check's offer decision (`update_service`). DTOs cross the boundary.
- **Infrastructure** (`decitect/infrastructure`): JSON serialization, the plan
  repository and exporter, the session autosave (`FileOrgStore`), the settings
  store, the example library, the HTML and SVG renderers, the clock, the GitHub
  releases adapter (one urllib GET of `releases/latest`, 5 second timeout,
  injected opener; every failure is None) and `state_dir`, the one home of the
  `~/.decitect` name, whose `resolve_state_dir` moves a pre-rename `~/.fulcrum`
  into place and answers the old folder if the move fails. All atomic writes;
  all I/O lives here.
- **UI** (`decitect/ui`): the board, its two zoomable maps, the editor, the
  guide, the help dialogs and three thin controllers (`org_intake`,
  `plan_files`, `update_check`). Long help content scrolls itself through one
  shared auto-scroller. `ui_scale` sizes everything to the screen;
  `theme_palettes`, `theme` and `map_palette` carry the light and dark themes;
  `header_tray` owns the header buttons and their focus order. The update
  check's blocking call runs on a worker thread and delivers to a bound method,
  dropping an answer whose controller is gone
  (`tests/ui/test_update_check_after_close.py`). This is the only LGPL-3.0
  component.
- **Shared** (`decitect/shared`): asset discovery and pure text helpers, no Qt.

## Execution flow

`main.py` resolves the state directory once, builds the services (simulator,
plan exporter, clock, example library, org and settings stores on that
directory, update service), injects them into `MainWindow` and starts the Qt
loop. The window restores the autosaved session by replaying its moves from the
starting organisation, which refills the undo stack across runs; otherwise it
generates a fresh organisation. Every change writes the session back. An
unreadable file is moved aside before anything can be saved over it; a readable
organisation with an unreadable move record restores alone. Replacing the
organisation starts a fresh session. A played move is translated from the
focused frame onto the real teams and applied by the pure `apply_move`; scoring
and move valuation run off-thread. The editor works on an `OrgBlueprint`, so any
live organisation can be edited.

## The model

Each team has a resolution capacity that falls when it lacks local authority,
is coupled, has skewed incentives or grows past a comfortable size; propagation
delay inflates its arrivals. Each team waiting on an upstream lands
`dependent_demand_weight` of the frame's workload on the upstream's queue, so a
hub saturates as a deciding centre does. Three bounded penalties (system
backlog, the share of teams that cannot decide cleanly, mean incentive skew)
compose into a 0..100 score, then two gentle divisors apply: influence without
authority and contested ownership.

A claim is another actor asserting the right to decide for a team. Every
decision class already has a structural owner, so any standing claim makes the
team contested: its capacity takes the contest price, it counts in the
escalation share and the score divides by one plus `contested_weight` per
claim. Contest is never attenuated by scale.

Headcount enters only through the prince band (`authority_scale`): each
escalating team is priced at the population of the nearest enclosing unit
holding a clean authority. Up to 150 people the authority charges cost
`prince_attenuation` of their flat price, rising to parity by 200, then growing
with the log of the population to `prince_survivor_ceiling`.
`escalation_load_share` of each escalating team's workload lands on its
resolving authorities, unattenuated, so a saturated centre registers as
latency. A dependency between two clean sovereigns with no shared roof is an
unowned interface, weighted by `unowned_interface_weight`. A structure with no
concentration, claims or unowned interfaces scores identically at every size.

A move's value is its score delta, classified from blunder to great against
fixed bands in every frame. Every coefficient lives in `SimulationParameters`.

Dependencies follow one projection rule: each endpoint maps to the node
representing it in the current frame; edges inside one node vanish and edges
crossing the frame drop.

## Conformance suites

The decisions behind the model are recorded with their trade-offs in
[DECISIONS-TRADEOFFS.md](DECISIONS-TRADEOFFS.md). These suites pin them:

- `tests/domain/test_authority_scale.py`: the prince band (claims C1 to C10).
- `tests/domain/test_resolution_conformance.py`: resolution, load and
  fragmentation (claims C11 to C17).
- `tests/domain/test_hierarchy.py`: focused frames keep their roof.
- `tests/domain/test_simulation.py`: dependency concentration prices itself.
- `tests/application/test_org_guide_parallel.py`: the pooled guide equals the
  serial one byte for byte.
- `tests/application/test_org_guide_cancel.py` and
  `test_org_guide_pool_release.py`: cancelling stops the build and frees its
  workers.
- `tests/ui/test_donate_button.py`: the donate button's place, address and
  refusal message.

## Tooling

The builds are plain scripts: `generate_icons.py`, `generate_button_icons.py`,
`buildexe.py`, `buildinstaller.py`, `builddmg.py`, `build_flatpak.sh`,
`clean_flatpak.sh` and `stamp_version.py`. The site under `docs/` is
hand-maintained. `sensitivity.py`, `calibrate.py` and
`generate_matrixed_enterprise.py` are smoke-tested by the suite. See
[DEVELOPMENT.md](DEVELOPMENT.md).

The Windows installer under `installer/` is a second application, layered the
same way: `installer_logic.py` and `installer_legacy.py` decide,
`installer_scripts.py` builds the command text, `installer_ops.py` and
`installer_startup.py` act, `installer_lifecycle.py` composes and the Qt modules
present. `installer_legacy.py` covers an install left under the former name
(Fulcrum): it is offered for removal by name and retired after the new install
is complete, removing a shortcut or sign-in entry only when it points inside the
old install directory.

The installer and the application each write down the state directory's name
and the former name's directory, since the installer may not import the app.
`tests/installer/test_state_dir.py` holds both pairs together.

## Quality

`black` (88) and `flake8` run clean, as does `ruff check` under ruff 0.15.22,
the pinned version (0.16 widens its defaults; see [TECH_DEBT.md](TECH_DEBT.md)).
`pytest` enforces 100% coverage on the gated surface; the UI, `main.py`,
resource discovery, the Protocol definitions, the version module and the
installer's Qt and side-effect modules are excluded. See
[TESTING.md](TESTING.md).
