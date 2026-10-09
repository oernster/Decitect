# <img width="128" height="128" alt="decitect" src="https://github.com/user-attachments/assets/09cac293-f20c-4e3d-b4dc-a737688ae8a6" /> Decitect

**Decision Architecture Organisational Software**

Decitect turns the Decision Architecture model into an engine you operate. You
fix a failing organisation with structural moves (delegate authority, stabilise
interfaces, realign incentives, collapse a boundary, resolve contested
ownership) and a deterministic model scores the result from 0 to 100.

It is a local-first desktop app: nothing about you or your organisations leaves
your machine. Its one network call is an anonymous daily ask of GitHub's
releases API for a newer version; a failed check is silent. A short tour is at
<https://decitect.com/>.

Decitect was previously called Fulcrum. The first launch moves `~/.fulcrum`
into `~/.decitect`; the Windows setup offers to remove an old Fulcrum install.

> **Commercial licences available.** Decitect is free and open source under
> GPL-3.0, with its interface layer under LGPL-3.0. If those terms do not suit
> what you are building, such as a closed-source product, a commercial licence
> can be bought from me separately. It covers my own code; PySide6 keeps its
> own LGPL-3.0 licence. See
> [commercial licensing](https://ernster.dev/commercial-licensing.html).

## Who it is for

- Software architects, senior engineers and CTOs who reason about org structure
  as a system of decisions rather than a headcount chart.
- Readers of the Decision Architecture series who want the model in their hands.

## Who it is not for

It is not an HR tool, a project tracker or a cloud service; there is no account
and no server.

## Capabilities

- **Model your organisation** in a two-pane editor: units nest to any depth with
  teams as leaves, rows drag like folders, headcounts roll up and dependencies
  join any two items, team or unit.
- **Matrix and dual reporting** as authority claims: a claimed team is
  contested, drawn violet and gets its own repair moves.
- **Play generated levels** (each leaf seeded so a great move is reachable) or
  open the bundled calibration organisations.
- **The board** opens on the complete picture; click a section to drill in,
  play any level and zoom either map.
- **Moves graded from blunder to great**, each played move ringed on the maps
  and kept in a move record that survives restarts. Take moves back with
  Ctrl+Z, across runs.
- **The guide** plans every level at once; leaf lines compose into an honest
  whole-org before and after, with an optional growth line. Large
  organisations plan deterministically across every core but one; every
  planning bar can be cancelled.
- **Prince band**: concentrated authority is priced by the population it
  governs, forgiven up to 150 people and priced harder beyond 200.
- **Seven signals to watch**, each with its own definition.
- **Autosave** of the organisation, its moves and your focus; an unreadable save
  is kept aside, never overwritten.
- **Export** a self-contained HTML report to Downloads or JSON you can
  re-import; every move is judged against the whole org and its own frame.
- **Keyboard navigation** on one explicit focus ring; light and dark themes.
- **Update check** a few seconds after launch and daily, with Download, Skip
  This Version and Later.
- **Help built in**: glossary, the books, signal definitions and a provenance
  page for every number.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ (developed on 3.13) |
| UI | PySide6 (Qt for Python) |
| Persistence | Local JSON files |
| Tests | pytest, 100% gate on domain, application, infrastructure, shared and the installer's decision layer |
| Format and lint | black (line length 88), flake8, ruff |
| Packaging | Nuitka (Windows and macOS), Flatpak (Linux) |
| Site | hand-maintained static HTML under `docs/`, served on GitHub Pages |
| Licence | model GPL-3.0, UI LGPL-3.0 |

## Install and run

Windows:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

macOS and Linux:

```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Test

```
pytest
```

The suite fails below 100% coverage on the gated layers; see
[TESTING.md](TESTING.md).

## Build

Icons, the Windows executable and installer, the macOS disk image, the Linux
Flatpak and the site: see [DEVELOPMENT.md](DEVELOPMENT.md).

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md): layers, invariants and the model.
- [DEVELOPMENT.md](DEVELOPMENT.md): working from source and the build scripts.
- [TESTING.md](TESTING.md): the suite and how to read its result.
- [TECH_DEBT.md](TECH_DEBT.md): what is still open, what is deliberately left
  and what only looks like debt.
- [DECISIONS-TRADEOFFS.md](DECISIONS-TRADEOFFS.md): the decisions Decitect rests
  on, with their gains and costs.
- [PREREGISTRATION.md](PREREGISTRATION.md): the blind external validation
  protocol.

## Supporting the project

Decitect is free and stays free: no paid tier, no licence key and no feature
held back behind a donation. If it has been useful, a donation supports its
maintenance. The same link sits in the app's header beside the theme toggle;
pressing it hands the address to your browser.

<a href="https://www.paypal.com/ncp/payment/4PRXS7C94A3HA"><img src="docs/donate.png" alt="Donate to Decitect" width="120"></a>

## Licence

Dual-licensed by component: the model under GPL-3.0 and the user interface (the
PySide6 layer) under LGPL-3.0. See [LICENSE](LICENSE) for the split, with the
full texts in [LICENSE-GPL-3.0.txt](LICENSE-GPL-3.0.txt) and
[LICENSE-LGPL-3.0.txt](LICENSE-LGPL-3.0.txt).

A commercial licence for my own code is also available, separately from the
open-source licences: see
[commercial licensing](https://ernster.dev/commercial-licensing.html).
