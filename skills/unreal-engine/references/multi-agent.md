# Several agents on one Unreal project

Parallel agents multiply output and conflicts. Unreal adds two constraints of its own: binary
assets do not merge, and an editor takes one writer at a time.

## Contents

- Default shape
- Lanes
- Shared files
- Integration and review
- Coordination
- Machine limits
- When to stop running in parallel

## Default shape

One main session owns the editor and the MCP connection. Other agents do work that needs no
editor: C++ in files they own, data files, Blender or texture scripts, audio processing, docs,
research, reviews. They hand results back; the main session integrates and tests.

## Lanes

When several agents must build and run the game in parallel:

- **A contract first.** The main session writes which paths each lane owns. Every path has exactly
  one owner. Binary assets have one writer, always.
- **One worktree per lane** (`git worktree add`), cut from the same commit. Each lane builds,
  runs its own tests and reads its own screenshots.
- **One editor per lane, on its own MCP port** (`-ModelContextProtocolPort=80NN`), with helper
  scripts that refuse to talk to the wrong port. Editors hold several GB of memory each; know how
  many fit.
- **Stubs before lanes.** Interfaces, structs and the few functions every lane would need from
  the others are written first by the main session, so lanes compile without waiting.
- **Briefs** name the files owned, the points the lane answers, the shared functions it may touch,
  how it proves its result without seeing the whole game, and sizes relative to what things stand
  on. Cheaper models handle well-specified lanes; keep the hardest, most coupled work on the
  strongest model.

## Shared files

Some files are hubs everyone needs (GameMode, a constants header, a registry).

- Change them only by exact string replacement, never by rewriting the file.
- Only inside the functions the brief names; new behaviour goes in new functions.
- Commit with explicit paths, never `git add -A` in a shared tree.

## Integration and review

- Merge lane patches through a three-way merge. Textual conflicts are the easy kind; the hard
  kind is semantic: two lanes each built the same system (two fire effects on one wreck, two ways
  to recover a vehicle). Read merged features where lanes meet.
- One integration pass plays from the title screen through the game after every merge.
- A cold reviewer, ideally on a stronger model, reads the merged code with one question: what
  breaks for a player where two agents' work meets. Run it again after fixes.
- A lane's "fixed" is a claim until the integration pass or the human confirms it.

## Coordination

- **Reports go in files.** Messages between sessions get lost when sessions restart; an inbox
  file per session survives.
- **One planner.** A session that keeps the plan, counts remaining hours against remaining work,
  and proposes cuts sees mismatches the working sessions do not.
- **One place for the human to decide.** Twenty sessions asking twenty questions is too many.
  Route decisions through one session and a short list.
- **Sandboxes** (UE 5.8+, Experimental) hold an agent's editor changes apart until a human or the
  main session persists them; one sandbox per editor. See [modern engine](modern-engine.md#sandboxes).
- **Two agents sharing one editor** hand it over explicitly: save, verify nothing is dirty, write
  the handoff note, then the other side starts.
- **Claims against ledgers.** Credits, store text and jam declarations go stale as tools change.
  Before anything is public, check every claim against the asset and cost ledgers.

## Machine limits

- A build train: one session builds for everyone at fixed cut-off times; a branch that does not
  merge cleanly or fails tests within a time box is left out and named.
- Locks for heavy work (see [build and ship](build-and-ship.md#shared-machines)).
- Agent clients themselves use memory. Twenty sessions can hold tens of GB.
- A session that crashed or restarted forgets what it promised. Keep decision logs on disk so a
  summarised or restarted session can continue.

## When to stop running in parallel

Parallel lanes pay off for code, data and generated content with clear owners. They hurt on polish
of look and feel, where every change touches shared levels and the judgement is the human's. Teams
that ran dozens of lanes switched, near the end, to one editor, one agent and one human pointing at
one thing at a time. Plan that switch.
