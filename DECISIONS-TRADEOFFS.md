# Decisions and trade-offs

The deliberate choices Fulcrum rests on: what was chosen, what was given up
for it and why. Each entry is the decision as the product makes it today.
The detail behind each one, with the tests that hold it, lives in
[ARCHITECTURE.md](ARCHITECTURE.md) and [TESTING.md](TESTING.md); the
validation protocol is in [PREREGISTRATION.md](PREREGISTRATION.md);
[TECH_DEBT.md](TECH_DEBT.md) holds what is still open and what only looks
like debt.

## The product as a whole

### Local first, one person, one machine

Everything Fulcrum keeps (the current organisation with its moves, the theme
and a skipped update) sits in plain JSON files in a folder in the user's home
directory.

- **Rather than:** an account, a server or anything synchronised.
- **Gains:** nothing to sign in to; nothing about an organisation leaves the
  computer; it works with the network switched off.
- **Costs:** the model belongs to that machine. Moving it elsewhere means
  exporting a file.

### Python and PySide6

The application is written in Python on Qt for Python. The scoring sits
behind a simulator seam.

- **Rather than:** Go with a React front end.
- **Gains:** a drawing-heavy desktop tool is Qt's home ground; a faster
  scoring kernel stays a reversible choice behind the seam.
- **Costs:** scoring in pure Python is slow enough at scale that large
  organisations need a playable size limit and worker processes.

### A deterministic score

The same structure always gets the same score. The scoring model draws no
random numbers and reads no clock; a structural test forbids the domain from
importing either.

- **Rather than:** a stochastic simulation run many times.
- **Gains:** a move's value is reproducible; tests pin exact numbers; the
  model can be frozen and tested against outcomes.
- **Costs:** the score carries no spread or uncertainty of its own.

### What Fulcrum deliberately is not

It scores organisation structure as a system of decisions. It is not an HR
tool, a project tracker or a cloud service.

- **Rather than:** a general organisation-management suite.
- **Gains:** a small surface held to a high bar.
- **Costs:** those jobs need other tools.

### A test that could fail, written down first

A blind validation protocol fixes the hypothesis, the sample floor and the
thresholds for support and for falsification before any organisation is
scored under it. Calibration cases, modelled with knowledge of their outcomes,
are permanently excluded from it.

- **Rather than:** tuning against known cases and calling the fit
  validation.
- **Gains:** a result, when one comes, means something in either direction.
- **Costs:** no validation result exists yet; a change to any coefficient
  after deposit needs a fresh registration.

## Privacy and the network

### One way out

The update check is the only code that opens a network connection: one
request to GitHub's releases API with a short timeout. Opening a link (the
releases page, a saved report, the donation page) hands the address to the
desktop's own browser; Fulcrum fetches nothing itself.

- **Rather than:** any feature reaching out on its own account.
- **Gains:** the README can say plainly what Fulcrum asks the network.
- **Costs:** a structural test holds the rule, so a second way out fails the
  suite until it is argued for; the test reads source, so a connection a
  library opens through a module it does not list is outside it.

### Support asked for in one quiet place

A donate button sits in the header's row of icon buttons, immediately left of
the light and dark toggle, in the drawn order and the keyboard ring alike. A
press hands the payment page to the browser. The app is free, with nothing
held back behind a donation.

- **Rather than:** a band of its own along the foot of the window; a prompt
  that asks; a paid tier or features held back.
- **Gains:** the ask is visible without interrupting anyone; the app opens no
  connection for it.
- **Costs:** the picture alone does not say it leaves the app, so its tooltip
  does; a desktop that refuses to open the page is answered with the address
  in a message box.

### The update check names nobody

The request sends no identifier and not even the installed version; the
comparison is made on the machine.

- **Rather than:** reporting the version or any usage.
- **Gains:** the release server learns nothing about the user, the machine
  or their organisations.
- **Costs:** no usage figures to steer development.

### Update checks: daily, quiet unless there is news

A check runs a few seconds after launch and then once a day. It says
nothing unless there is a newer release; a skipped version never prompts
again. A check from the Help menu always answers and ignores the skip. A
version that cannot be read is never treated as newer. Only a published
release can prompt, since the endpoint returns nothing else.

- **Rather than:** no check at all; opening the releases page and leaving
  the comparing to the user, as Help once did.
- **Gains:** updates are found without nagging; a malformed tag or a tag
  pushed mid-development never raises a prompt.
- **Costs:** one unprompted request a day.

## The model

### Every coefficient in one place, validated

All scoring coefficients live in one parameters object that checks itself
on construction: the three penalty shares must sum to one and the prince
band must be ordered, among other bounds.

- **Rather than:** constants written where they are used.
- **Gains:** no hidden constants; the sensitivity sweep can perturb every
  coefficient.
- **Costs:** a new effect needs its parameter and its validation before it
  can exist.

### Total-system latency, not accumulated queue

Backlog is read as the system's total imbalance over its total arrivals.

- **Rather than:** summing each team's accumulated queue.
- **Gains:** bounded and stable, so adding a saturated approval gate is
  robustly harmful rather than an artefact of averaging.
- **Costs:** none recorded.

### New effects as gentle multiplicative terms

Cognitive load and influence without authority divide the score by a term
that is zero in the benign case.

- **Rather than:** additive penalties that shift every score.
- **Gains:** an existing position is never disturbed; a term bites only
  where its gap is real.
- **Costs:** none recorded.

### Proportional, not absolute

The influence penalty and the claim penalty read the per-team mean rather
than the absolute load.

- **Rather than:** absolute counts, under which one advisory hub cost a large
  organisation half its score.
- **Gains:** one overloaded hub costs a proportionate slice of a large
  organisation.
- **Costs:** none recorded.

### Classification bands absolute in every frame

A move is graded from blunder to great by fixed bands on its score change,
the same bands in every frame.

- **Rather than:** bands scaled to the depth of the focus.
- **Gains:** "great" is never stamped on a negligible change at the summit;
  the same physical move reads larger the deeper the focus, which is the
  model's own result about where value lives.
- **Costs:** high scopes often offer nothing better than neutral; the board
  has to tell the player to look deeper.

### Headcount enters through one door

Population affects the score only through the prince band. Up to the Dunbar
horizon concentrated authority costs a fraction of its flat price; the price
rises to parity across a short band, then grows with the log of the
population up to a ceiling.
Each frame is priced at its own population. A structure holding no
concentration, no claims and no unowned interfaces scores the same at every
size.

- **Rather than:** a flat price for concentration at every scale; headcount
  read everywhere.
- **Gains:** a founder deciding for a few dozen people scores well while the
  identical structure at conglomerate scale scores badly; a conformance suite
  pins each half of that claim.
- **Costs:** the band's edges are a modelling choice rather than a figure
  measured for any one organisation.

### Escalation priced at its resolution distance

An escalating team is priced at the population of the nearest enclosing unit
that holds a clean authority. A share of its workload lands on that
authority's queue; the prince band never forgives that share.

- **Rather than:** pricing every escalation at the whole organisation's size.
- **Gains:** an escalation across a desk is never priced at conglomerate
  scale; a saturated centre shows up as latency. A signal for centre
  escalation load makes it visible.
- **Costs:** one more mechanism to understand when reading a score.

### Dependency concentration prices itself

A team waiting on an upstream lands a share of the frame's workload on the
upstream's queue, whatever its authority. That share may never exceed the
escalation share; the parameters refuse it.

- **Rather than:** demand travelling only along escalation lines, under which
  a small team that dozens of teams wait on read as healthy.
- **Gains:** an empowered hub saturates exactly as a deciding centre does;
  waiting on a supplier never costs more than resolving through an
  authority.
- **Costs:** a light fan-out is free within the capacity headroom, so the cost
  begins only where a queue does.

### Any standing claim is contest

Every decision class already has a structural owner (the team or the line it
escalates to), so any further claim makes the team contested. Resolving in
favour of a claimant clears the claims outright.

- **Rather than:** counting the team's own authority as its only claimant.
  The sensitivity sweep falsified that: the matrix-overlay blunder read as
  positive on escalation-heavy archetypes.
- **Gains:** the overlay blunder stays a blunder at every scale.
- **Costs:** a claimant that is really only consulted must be downgraded to a
  priced dependency to stop counting as contest.

### Contest priced, not simulated

Contest cuts the team's capacity, counts it among teams that cannot decide
cleanly and divides the whole score per standing claim. Contest is never
attenuated by scale.

- **Rather than:** synthesising reconciliation traffic between claimants as
  dependency edges.
- **Gains:** no invented queues; contest costs strictly more than clean
  escalation at every scale.
- **Costs:** the traffic itself is not drawn on the map.

### Fragmentation is priced as well as concentration

A dependency between two clean sovereigns that share no enclosing unit is an
unowned interface: nobody can arbitrate its conflicts. It pushes both ends
toward the share of teams that cannot decide cleanly.

- **Rather than:** pricing concentration only, under which a large roofless
  network of sovereign teams read as healthy.
- **Gains:** a roofless network fragments at scale; any shared unit owns the
  edge.
- **Costs:** a federation whose real arbiter is not modelled reads as
  fragmented until a roof is drawn.

## Frames and the hierarchy

### Sections are played; the whole is an overview

A scope up to a playable size is scored and valued live. Above that the
board shows an overview to drill into.

- **Rather than:** scoring every scope live, which froze the interface while
  a large section scored.
- **Gains:** with scoring made linear, a whole division scores on a worker
  thread; the interface never blocks.
- **Costs:** a whole group or company cannot be played as one position.

### Higher levels play their children as single actors

Focusing a unit scores its children rolled into one node each. Moves made
there translate down to the real teams beneath.

- **Rather than:** offering moves only on teams.
- **Gains:** strong structural moves appear at every tier; a focused section
  is a handful of nodes, so it scores at once.
- **Costs:** a rolled node is synthetic: it carries no claims and never grows
  as one act.

### One projection rule for dependencies

An edge may join teams, whole units or both across levels. Each frame maps
each end to the node that stands for it; an edge inside one node vanishes and
one crossing the frame's edge drops.

- **Rather than:** expanding a unit-level edge into team-to-team edges; a
  separate interface object.
- **Gains:** an edge between units counts exactly where those units act,
  without inflating coupling with invented queues.
- **Costs:** an edge does not show in a frame that holds only one of its ends.

### Frames carry their roof

A focused frame keeps its enclosing units, so pricing inside a section
agrees with the whole organisation. The top level stays roofless and offers
no moves: nothing above it is modelled to make one.

- **Rather than:** dropping the enclosing units, which priced one fact two
  ways and showed dozens of phantom unowned interfaces in a fully roofed
  section.
- **Gains:** a section's score and the whole organisation's agree.
- **Costs:** "Play this level" at the top scores the root units but offers
  nothing to play there.

### The headline is the flat truth

The unfocused score is always the flat team-level score. The top level is
scored as one actor per root unit only when the player asks.

- **Rather than:** making the rolled-up top level the default view.
- **Gains:** dependencies between root units can be priced without changing
  what the headline means.
- **Costs:** two numbers for the top of the organisation.

### Every team sits in exactly one leaf frame

Teams held directly by a unit that also holds sub-units get a composable row
of their own, as do loose teams at the top level.

- **Rather than:** rolling only child units, which dropped such teams from
  every frame.
- **Gains:** every team's repairs reach the headline.
- **Costs:** an extra row in the guide for each mixed unit.

## Play and the guide

### Generated levels carry a reachable great move

A random organisation is a branching tree whose leaves are cloned from a
small pool of cluster templates. Each template is resampled until a great
move is reachable within a short greedy line, up to a capped number of tries.

- **Rather than:** demanding a great move available at once; building every
  leaf from scratch.
- **Gains:** the costly search runs a fixed number of times however large
  the organisation; a clone scores exactly as its template does.
- **Costs:** the great move is sought per cluster rather than proven; once
  the cap is reached the last sample is used as it is, so an unlucky draw
  could ship without one.

### A greedy guide

The guide repeatedly takes the strongest improving move and stops when none
gains enough to matter or the line reaches its length limit, like a chess
engine's principal variation. It plans at
the organisation's current size unless growth is switched on.

- **Rather than:** a search over move sequences.
- **Gains:** fast; every step can be explained.
- **Costs:** it never takes a weaker move first to open a stronger one.

### The guide plans every frame; only leaf lines compose

Every frame gets its own line. Sibling leaf frames are disjoint, so their
lines apply together to the real organisation and the headline is the real
score after all of them. Higher rows are shown as the view from that altitude
and never composed.

- **Rather than:** one plan for the whole organisation; adding up the higher
  rows too.
- **Gains:** an honest whole-organisation before and after; the higher rows
  show where value lives without counting it twice.
- **Costs:** higher rows can look worth more than they contribute.

### A leaf line composes only when it pays its way

Each line is priced against the composed position. The worst net-harmful
line is dropped, then the rest are priced again until every survivor helps.
A dropped line keeps its row, flagged with its cost.

- **Rather than:** judging a line by its worth applied alone. A line that
  costs on its own can help once its siblings have repaired their frames.
- **Gains:** a line that would cost the whole organisation never enters the
  headline; none that helps is dropped by mistake.
- **Costs:** composing repeats the pricing pass after each drop.

### Growth is priced where its edges are visible

Growth is off by default. Switched on, it adds a whole-organisation growth
line as the last composable row and offers growth to real teams standing in
higher frames. A frame that growth cannot improve says so.

- **Rather than:** growth only inside leaf frames, where the edges a split
  relieves have already been dropped.
- **Gains:** growth's worth shows where it is real.
- **Costs:** another planning pass when the toggle is used.

### Heavy guide pricing runs on worker processes

On an organisation above the playable size the guide's independent pricing
runs on a process pool, with one core left for the interface. Results are
gathered in order, so the guide is identical with or without the pool. A pool
that breaks falls back to pricing in-process.

- **Rather than:** threads, which the interpreter lock would serialise; a
  pool for every organisation.
- **Gains:** large organisations plan across every core; small ones skip a
  pool that would cost more to start than their whole build.
- **Costs:** the pool has never been run inside a packaged build; the
  fallback means the worst case is a slow guide.

### Every planning bar can cancel

A cancel request is checked at every step, valuation chunk and progress tick.
The pool waits in short slices so a cancel lands even while workers are
starting.

- **Rather than:** a bar that runs to completion.
- **Gains:** a machine without the cores is never trapped in a long build.
- **Costs:** every long loop has to consult the request.

### Moves are previewed on request

A magnifier beside each move opens a preview of before and after, built off
the interface thread. Hovering a move only shows its explanation.

- **Rather than:** previewing on hover, which rebuilt the organisation and
  redrew the map on every mouse movement until Windows reported the window as
  not responding.
- **Gains:** hovering is instant on any size of organisation.
- **Costs:** one more click to see a move's effect.

### Moves can be taken back

The session keeps a snapshot of each position played, so undo walks back to
the original organisation.

- **Rather than:** a one-way game.
- **Gains:** a move can be tried without commitment.
- **Costs:** none recorded.

## Saving and exporting

### The session is saved as a history and restored by replay

Every change writes the starting organisation, every move and the section in
focus. The next launch replays the moves, so undo works across runs and the
report can set earlier runs apart from the current one.

- **Rather than:** saving only the final organisation.
- **Gains:** nothing about the session is lost by closing the app.
- **Costs:** the whole history is replayed at every launch.

### A new organisation starts a new record

Replacing the organisation (a new random one, a fresh model, an import or an
edit) starts a fresh session.

- **Rather than:** carrying moves across organisations.
- **Gains:** the record always belongs to the organisation it was played on.
- **Costs:** an edit clears the moves played so far.

### An unreadable save is never written over

A save that will not read is moved aside under its own name and the app says
where it went. If it cannot be moved, nothing is saved at all.

- **Rather than:** starting afresh and saving over it within seconds.
- **Gains:** a whole organisation and its record are never silently lost.
- **Costs:** if the file cannot be moved, that session goes unsaved.

### Writes are atomic

Every file is written beside its target and then swapped into place.

- **Rather than:** writing in place.
- **Gains:** a crash mid-write never leaves half a file.
- **Costs:** none recorded.

### JSON, not CSV

Organisations and plans are stored as JSON. Older shapes are read at the JSON
boundary and brought up to date there.

- **Rather than:** CSV; keeping retired values alive in the model.
- **Gains:** matches the nested shape of an organisation and the moves played
  on it; the model carries no dead members.
- **Costs:** none recorded.

### The presentation goes to Downloads

The report is a self-contained HTML file written into Downloads under a name
that never overwrites an earlier one, then opened. Its controls stay disabled
until a move is played, with a red border and a tooltip saying why.

- **Rather than:** a save dialog each time; a control that produces an empty
  report.
- **Gains:** one press gives a report that stands alone and can be sent on.
- **Costs:** the location is fixed.

### Each move is judged twice in the report

A move is judged against the whole organisation. Where its targets sit
inside one unit it is also judged within that unit's own frame, scored
exactly as the board scores a drilled section.

- **Rather than:** a whole-organisation verdict alone, under which a good
  repair inside a section read as neutral.
- **Gains:** the plan's balance survives into the report.
- **Costs:** two verdicts to read per move.

## The interface

### Opens maximised, scaled to the screen

The interface is scaled once at start-up from the screen's height and the
window opens maximised.

- **Rather than:** a fixed pixel size; a window sized short of the screen,
  which truncated move labels.
- **Gains:** fits small laptop screens and large monitors alike.
- **Costs:** the scale is global, so nothing can draw at two scales.

### Two themes; contest in violet

Light and dark themes are switched from the header and remembered. The map
colours are weighted per theme. Contested ownership is violet.

- **Rather than:** red for contest.
- **Gains:** contest stays distinct from the green hover ring under red-green
  colour blindness.
- **Costs:** none recorded.

### One keyboard ring

Every control sits on one explicit focus ring, menus first. Right and Left
behave exactly as Tab and Shift+Tab; the map keeps its own arrow keys. A ring
appears only where the user put it; dialogs open with nothing focused.

- **Rather than:** the toolkit's own tab order and native menu cycling.
- **Gains:** the whole application works without a mouse; no control wears a
  ring uninvited.
- **Costs:** every new control needs its place in the ring.

### Long content reads itself

Help pages, the move list and other long surfaces scroll gently on their own,
hold at the end and rewind. Any manual scroll or focus suspends the cycle,
which resumes where the reader stopped. Every surface shares one pace.

- **Rather than:** static pages; a pace per dialog.
- **Gains:** long text can be read hands free; the pace is the same
  everywhere.
- **Costs:** none recorded.

### Three decimal places everywhere

Every score and move value shows three decimals.

- **Rather than:** rounded figures.
- **Gains:** a repair inside one unit moves a whole-organisation score by
  hundredths; rounding would hide it.
- **Costs:** busier numbers.

### Played moves are ringed

The nodes a move acted on are ringed on both maps. Where the complete picture
summarises them, the section holding them is ringed instead.

- **Rather than:** relying on the colours to show change.
- **Gains:** at whole-organisation scale the ring is what makes a played move
  visible at all.
- **Costs:** none recorded.

### One editor for every organisation

The editor is an explorer-style tree working on a draft. Any live
organisation, whatever its origin, converts back into a draft, so every
organisation can be edited. The quick-organisation wizard was retired.

- **Rather than:** separate paths for modelled, imported and generated
  organisations.
- **Gains:** one way to change anything; the wizard's ground is covered by
  the editor and generation.
- **Costs:** none recorded.

### Pick lists exist only while editing

The editor's dependency and claim tables hold plain rows. A pick list is
created only for the cell being edited.

- **Rather than:** a live pick list in every cell, which priced a
  thousand-row organisation at millions of list items.
- **Gains:** large organisations open at once.
- **Costs:** none recorded.

### Names are never blank

Every lead and owner gets a plausible name from one built-in pool, in the
editor and in generation.

- **Rather than:** blank fields to fill.
- **Gains:** a fresh organisation reads as an organisation; the names are
  overtyped in one motion.
- **Costs:** none recorded.

## Building and installing

### Nuitka on Windows and macOS; Flatpak from source

The Windows and macOS packages are compiled with Nuitka into standalone
applications. The Linux Flatpak runs from source, built offline from wheels
downloaded beforehand.

- **Rather than:** PyInstaller, which the project used before.
- **Gains:** one compiler for both desktop packages; no system Python needed.
- **Costs:** every file the app loads beside its code is listed in the build
  scripts by hand.

### The build tools are held to chosen versions

The linter is pinned to one release and the packaged builds refuse to start
on a compiler older than the one they are written against, saying which
version they found.

- **Rather than:** whatever release happens to be installed.
- **Gains:** a fresh setup lints and compiles exactly as the release did; a
  build never ships from a compiler nobody chose.
- **Costs:** moving to a newer linter or compiler is a deliberate piece of
  work, with its new findings cleared in the same change.

### Installed for one user, without administrator rights

On Windows the setup program installs into the user's own folders and
registry. Removing Fulcrum keeps the user's organisations and settings unless
they tick the box to remove them.

- **Rather than:** a machine-wide install.
- **Gains:** no administrator prompt; an uninstall never takes data by
  default.
- **Costs:** each account on a machine installs separately.

### A setup program of its own

Install, repair and removal are one bespoke program, layered like the app:
pure decisions, the exact command text, then the code that acts. It may not
import the application. It asks the user to close a running Fulcrum first.

- **Rather than:** a generic installer.
- **Gains:** its decisions are held at full coverage; the two binaries ship
  separately.
- **Costs:** the name of the state folder is written down twice; a test holds
  the two together, since an uninstaller clearing the wrong folder would
  report success either way.

### macOS builds are notarised or refused

Notarisation is required. An Apple account password given in the environment
is refused before any build work, since the notary service accepts only an
app-specific one; a missing or rejected keychain profile stops the build at
the notarisation step. Both the app and the disk image are stapled and
verified as an end user's machine would.

- **Rather than:** skipping notarisation when credentials were absent, which
  shipped disk images that would not open on any machine but the builder's.
- **Gains:** a published disk image opens, offline included.
- **Costs:** an Apple developer account; an explicit override is needed for
  an unreleasable local build.

### The Flatpak may reach the network and the home folder

The sandbox grants network access and the home folder.

- **Rather than:** a tighter sandbox.
- **Gains:** the update check can work; plans can be exported where the user
  chooses.
- **Costs:** the sandbox does not itself enforce that Fulcrum stays local.

### One version, read at run time

The version lives in one file. The app reads it when it runs and every
package carries the file. The website is stamped from it when a release is
prepared; only the Windows builds stamp as they build.

- **Rather than:** stamping from every build script.
- **Gains:** About is right on every platform; a macOS or Linux build never
  rewrites tracked files on a machine not making the release.
- **Costs:** the site must be stamped as a separate step.

### A website written by hand

The site is static pages with no generator.

- **Rather than:** a generator, which was retired once it had drifted to a
  single page while the live site had several.
- **Gains:** nothing can overwrite the pages.
- **Costs:** every page is maintained by hand.

### Two licences plus a commercial one

The model is GPL-3.0 and the interface LGPL-3.0. A commercial licence for
Fulcrum's own code is offered separately.

- **Rather than:** one licence for everything.
- **Gains:** the interface carries the same terms as Qt itself.
- **Costs:** two licence files to keep straight.

## Engineering

### Layers that point inward

The code is split into domain, application, infrastructure and interface.
The domain imports no I/O and no outer layer; the application never imports
infrastructure or the interface. Structural tests hold both. One composition
root builds the services and injects them.

- **Rather than:** convention alone; a dependency injection framework.
- **Gains:** the model can be tested with no disk, network, clock or screen.
- **Costs:** more modules and explicit wiring. The single composition root is
  held by convention rather than by a test.

### Complete coverage where the decisions are

Coverage must be total over the domain, the application, the infrastructure,
the shared text helpers and the installer's decision modules. The interface
is tested but not held to a figure.

- **Rather than:** one figure over everything, met only by testing Qt itself.
- **Gains:** anything short of complete in the gated layers is a decision
  nobody made.
- **Costs:** decisions that still live in the interface are invisible to the
  gate, so they are moved down a layer over time.

### Small modules

No module may exceed a fixed line cap, tests and the installer included.
The build scripts are exempt as linear recipes.

- **Rather than:** letting files grow.
- **Gains:** modules split at real seams.
- **Costs:** families of small files where one feature spans several.

### Tests with real parts

No mocking library. Infrastructure tests write real files in a temporary
folder; the guide's pool is tested live with real worker processes;
fakes are written by hand.

- **Rather than:** mocks.
- **Gains:** a passing test means the real thing works.
- **Costs:** fakes to write and keep.

### The analysis scripts sit in the suite

The sensitivity sweep, the calibration harness and the generator of the large
calibration case each have smoke tests. The sweep scales every coefficient
up and down one at a time, then moves them all at once across many seeded
draws.

- **Rather than:** scripts run by hand when remembered.
- **Gains:** the suite fails if a published conclusion stops holding or a
  calibration case leaves its band.
- **Costs:** a model change can fail the suite for a reason far from the
  code changed.

### Threads are owned

Background work runs on owned threads; a result is delivered to a method of
an object on the interface thread. Closing the window saves first, then stops
the analysis and generation work. An answer whose recipient has gone is
dropped rather than raised on a thread nobody watches.

- **Rather than:** fire-and-forget threads.
- **Gains:** quitting never pulls the ground from under work still running.
- **Costs:** more ceremony around background work.

### Lint rules widen one family at a time

Ruff runs at its default selection. A rule family is added only once it is
clear, in a commit of its own.

- **Rather than:** a wholesale automatic fix across the repository.
- **Gains:** every change is reviewable with the gate green.
- **Costs:** with every rule selected the repository still reports thousands
  of findings to work through.
