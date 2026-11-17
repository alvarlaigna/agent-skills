---
name: unreal-engine
description: Builds, debugs, tests, and ships Unreal Engine 5 games with a coding agent that drives the editor through Unreal MCP, editor Python, and the command line. Use for UE5 C++ gameplay code, UCLASS/UPROPERTY reflection, Blueprint and UMG work, levels and actors, asset imports, Live Coding versus full rebuilds, UnrealBuildTool and UAT packaging, cook errors, Windows and web (Wasm) builds, character animation (AnimGen, motion matching, retargeting), automation tests, PIE and self-play testing, multi-agent setups on one project, and game jams. Complements Epic's unreal-mcp skill, which covers MCP tool discovery.
compatibility: Agent Skills format. Scripts need Python 3.9+ and a local Unreal Engine 5 install; capture_window.ps1 is Windows-only. Written against UE 5.8 and the 5.9 Preview.
---

# Unreal Engine

An operating model for agent-driven Unreal work: which channel to use for what, the rules that
stop work from being lost, how to build and ship, and how to prove a change works. Tool discovery
over MCP (`list_toolsets`, `describe_toolset`, `call_tool`) belongs to Epic's `unreal-mcp` skill;
use it when installed. This skill does not repeat it.

## Pick the channel

| Need | Channel |
|---|---|
| Editor state: actors, assets, Blueprints, materials, widgets, PIE, settings | Unreal MCP, one call at a time, read before write |
| Five or more similar edits, imports, a level layout | An editor Python script in the repo (`scripts/editor/*.py`), re-runnable, run through MCP or headless |
| Gameplay rules and systems | C++. Blueprint and UMG assets stay thin subclasses that hold tuning and asset references |
| Build, package, run tests, headless Python | `scripts/ue.py` (wraps UnrealBuildTool, UAT and `UnrealEditor-Cmd`) |
| See the editor or the game | MCP viewport capture, `scripts/capture_window.ps1`, or the game's own screenshot mode |
| Feel, sound, taste, "does this read" | A human. Ask for a specific check and record the answer |

Text beats graphs: C++ over Blueprint graphs, Material Custom nodes over large node graphs, data
files over hand-placed values. Text is cheaper to write, diff, review, and rebuild from nothing.

## Start of every session

1. Read the project's `AGENTS.md` / `CLAUDE.md`. Run `git pull --rebase` and `git status`.
2. `python scripts/ue.py env --project <dir>`: engine root, `.uproject`, whether an editor is running.
3. `python scripts/check_log.py --project <dir>`: any `Can't find class descriptor` means the
   editor runs a stale game module. Save nothing from that editor; rebuild first.
4. Confirm which editor answers MCP before changing anything (project path, port). Keep the exact
   tool names and arguments that worked in `docs/MCP_TOOLS.md`; it saves the search next session.
5. Read the clock (`date` / `Get-Date`) before writing any time into a log. Never estimate it.

## Rules that prevent lost work

1. **Save, then prove it saved.** MCP graph tools compile a Blueprint but do not save it. A Python
   transform change on an actor in a One File Per Actor level does not always mark its external
   package dirty, so "save all" skips it and only PIE (which uses memory) looks right. Call
   `actor.modify()` before the change, save dirty packages, then confirm the file changed on disk
   (`git status`, mtime). See [the editor loop](references/editor-loop.md).
2. **Reflection changes need a closed editor.** New or changed `UCLASS`, `USTRUCT`, `UPROPERTY`,
   `UFUNCTION`, new files, or `Build.cs` edits: save all, close the editor, `ue.py build`, reopen,
   recheck the log. Live Coding is for function bodies only. Batch reflection changes so one
   restart covers them.
3. **Builds refuse to run beside a live game module.** "Unable to build while Live Coding is
   active" comes from any running editor or game of the project. Close it (and its Live Coding
   console) before building or packaging.
4. **One writer per editor.** A second agent gets its own worktree, its own editor, its own MCP
   port. Two agents on one editor need an explicit handoff. See [multi-agent](references/multi-agent.md).
5. **Never edit `.uasset` or `.umap` files on disk**, and never commit a binary asset that the
   editor held locked during a pull: restore it from `HEAD` after the editor closes.
6. **Do not delete and recreate a loaded asset under the same name.** It leaves broken references
   and can crash the editor and the game. Create under a new name, or delete with the editor closed.
7. **No modal dialogs mid-session.** A setting that asks "restart now?" blocks the editor's game
   thread and every MCP call behind it. Set such prerequisites in `.ini` files with the editor closed.
8. **Package a test build on day one**, then at every milestone. Cook-only failures (constructor
   side effects, missing scan rules, stale references the editor masks in memory) never show in PIE.
9. **Trust the screen over names.** Enum values, asset names and comments lie; a screenshot or a
   log line from the running game does not.
10. **Automated runs start from default settings and save none**, and every build has a frame-rate
    cap. Uncapped frame rates and leftover user settings both produce false results.

## Definition of done

A change is done when all of these hold, and the report says which ones were not checked:

1. It compiles with no new warnings from the project's modules.
2. Logic changes: the project's automation tests pass (`ue.py test --filter <Project>`).
3. Visual changes: a screenshot was read at full size and given a one-line verdict.
4. Gameplay changes: the changed step ran in PIE or a self-play run, through the real input path.
5. Every touched asset is saved and the change is visible in `git status`.
6. Committed with a short message; one line added to the devlog if the project keeps one.

## Reference routing

- [Editor loop](references/editor-loop.md): MCP etiquette, editor Python, save-and-verify, the
  Live Coding versus restart protocol, ports, headless runs, seeing the editor.
- [C++ architecture](references/cpp-architecture.md): module layout, reflection rules, thin
  Blueprints, subsystems, data-driven design, UI from C++, logging, automation tests.
- [Content pipeline](references/content-pipeline.md): folders and naming, imports (textures,
  audio, meshes), DataTables, redirectors, cook rules, dependency closure, external actors, licences.
- [Build and ship](references/build-and-ship.md): UBT and UAT commands, Shipping builds, size
  limits, cook-only failures, verifying the artifact, the web (Wasm) target.
- [Animation](references/animation.md): choosing between state machines, motion matching and
  AnimGen; AnimGen training, tuning and limits; retargeting; procedural layers; measuring motion.
- [Testing](references/testing.md): the testing ladder, self-play modes, shot runs, real input,
  measuring performance, human playtests.
- [Multi-agent](references/multi-agent.md): ownership, worktrees, shared hub files, reviewers,
  machine locks, when to stop parallel work.
- [Jam production](references/jam-production.md): pre-jam proof, gates, cut ladder, devlog,
  submission checklist.
- [Ecosystem](references/ecosystem.md): built-in plugins and open-source plugins worth knowing,
  with caveats.
- [In-game AI](references/in-game-ai.md): language-model characters and generated speech inside
  the game: the rules engine owns the facts, the model only acts.

## Scripts

Run these; do not read their source unless debugging the skill. Each prints `--help`.

- `scripts/ue.py env|build|package|test|python|running`: engine discovery and UBT/UAT/commandlet
  wrappers. Refuses to build or package while an editor of the project runs.
  - `python scripts/ue.py build --project ./MyGame`
  - `python scripts/ue.py package --project ./MyGame --platform Win64 --config Shipping --out ./Build`
  - `python scripts/ue.py test --project ./MyGame --filter MyGame`
  - `python scripts/ue.py python --project ./MyGame --script scripts/editor/fix_spawn.py`
- `scripts/check_log.py`: scans the newest editor, cook or UAT log for known blockers and prints
  what each one means. Exit code 1 when a blocker is found.
- `scripts/audit_source_assets.py`: checks source art and audio before import: non-power-of-two
  textures, clipped or silent WAVs, loop seams, stereo music, oversized files.
- `scripts/init_agent_files.py`: writes `AGENTS.md`, `CLAUDE.md`, `.gitignore` and `.gitattributes`
  (Git LFS) into a UE project from `templates/`. Refuses to overwrite.
- `scripts/capture_window.ps1` (Windows): screenshot of the editor or game window, even when
  covered, for the agent to read.
- `scripts/editor/dependency_closure.py` (runs inside the editor): lists every package a map pulls
  into the cook that lives outside the allowed content roots.
- `scripts/editor/save_and_verify.py` (runs inside the editor): saves dirty packages and reports
  anything still dirty, including external actor packages.

## Gotchas

- Agent toolset plugins enable GameFeatures, and the cook then fails on a missing scan rule for
  `GameFeatureData`. Add the scan rule or keep the toolsets editor-only. See
  [build and ship](references/build-and-ship.md#cook-only-failures).
- A component that renders (particles, lights, meshes) placed on the GameMode never shows: the
  GameMode actor is hidden in game. Put visuals on a world actor.
- A variable added to a Blueprint after its actor was placed may read 0 on the placed instance
  rather than the class default. Check the instance, not the class.
- In UE 5.9 hidden bones stop animating: meshes attached to a hidden head or hand bone jump every
  other frame. Call `SetAlwaysAnimateHiddenBones(true)`. Stills never show it; compare frames.
- Overlay materials do not draw on Nanite meshes. Use custom depth and stencil for outlines.
- A material used by Niagara mesh particles needs its "Used with Niagara Mesh Particles" flag,
  or it renders as the default material.
- Canvas text in a packaged build needs a real `UFont` asset; a font built in memory from TTF files
  draws nothing, with no error.
- Imported models that are a few centimetres long were authored in other units; check scale on
  import. Mirroring an axis in a converter flips triangle winding and makes the mesh look hollow.
- Non-power-of-two textures get no mips and do not stream. Fix them in the source or import with
  power-of-two padding or stretch.
- Looping audio needs the looping flag on the imported asset. Browsers keep audio muted until the
  first click or key press.
- The replay system records at a low rate by default (`demo.RecordHz`), and physics actors jitter
  on playback. Test a replay-based feature with real content on day one.
- MCP tool results can be bulleted text rather than JSON. Parse defensively and test the parser.
- The default MCP port (8000) collides with common dev servers. Give each editor its own port.
- Anything an agent session launches dies with that session. Start long-lived editors outside it.
