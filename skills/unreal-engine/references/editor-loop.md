# The editor loop

How an agent works with a live Unreal Editor without losing work.

## Contents

- Channels and when to use each
- MCP etiquette
- Editor Python
- Save and verify
- Live Coding versus restart
- Ports, several editors, reconnecting
- Headless editor runs
- Seeing the editor and the game
- Version notes

## Channels and when to use each

| Channel | Good for | Weak at |
|---|---|---|
| MCP tools | Single structured edits, queries, PIE start/stop, captures, Live Coding | Bulk edits (one call per change), anything the toolsets do not cover |
| Editor Python (through an MCP Python tool or the Python console) | Bulk edits, imports, level layout, audits, anything repeatable | Blueprint graph surgery, modal UI |
| Headless editor (`UnrealEditor-Cmd -run=pythonscript`) | The same scripts with no GUI editor open: fixes, imports, audits at night | Anything that needs a viewport |
| C++ | All gameplay logic, systems, UI layout from code | Tuning values designers want to see |
| Computer use / a human | Viewport judgement, play feel, modal dialogs, sound | Anything that can be scripted |

## MCP etiquette

- **Discover once, write it down.** After the first `list_toolsets` and `describe_toolsets` calls,
  record the exact tool names, argument shapes and quirks in `docs/MCP_TOOLS.md`. Mark each needed
  capability as available or missing (actor spawn/transform/delete, save, console command,
  viewport capture, PIE start/stop, Python, import, asset-registry queries, DataTable import, UMG,
  materials, automation tests, Live Coding).
- **Read, change one thing, read back.** Get the current value, set it, get it again. Many tools
  return a status rather than throwing; anything that is not an explicit success is a stop.
- **Serialize mutations.** Calls that touch the same asset or level run one after another. Keep
  each change small enough to undo.
- **Mind PIE.** Asset creation and some edits behave differently while Play-in-Editor runs. Stop
  PIE before editing assets.
- **Results are not always JSON.** Some tools return bulleted text. Parse defensively and keep a
  test for the parser if a script depends on it.
- **Some tools need arguments they do not advertise as required.** Viewport capture tools, for
  example, may refuse an empty request and want a camera position. Note it in `MCP_TOOLS.md`.
- **Never edit asset files on disk.** `.uasset` and `.umap` change only through the editor.
- **Keep calls short.** Clients time out (Claude Code after about two minutes). Split long work, or
  send a `progressToken` for heartbeats.
- **One script for many edits.** Through `execute_python`, write one script for bulk edits instead
  of dozens of tool calls; imports at the top level only, no star imports; the last expression is
  the result and `print` goes to the Output Log. See [modern engine](modern-engine.md).
- **Project rules for every agent.** Put naming rules, protected folders and the test map in the
  project's MCP server instructions (Project Settings, Agentic Workflows, stored in
  `DefaultGame.ini`); every connecting agent receives them.

## Editor Python

Scripts live in the repository (`scripts/editor/*.py`) so any level or asset set can be rebuilt
from nothing.

- **Re-runnable.** Tag or label what the script creates (`GB_*` labels, a folder path, an actor
  tag) and delete those first, then rebuild. A second run must give the same result.
- **Data at the top.** Positions, sizes and colours in a table at the head of the file, with units
  and axes stated (`cm`, `+X north`, `Z up`). Sizes relative to what they stand on, not absolute
  guesses: a 25 m mast on a 2 km tower is invisible.
- **One transaction per logical edit** so a human can undo it:

```python
import unreal

with unreal.ScopedEditorTransaction("Place spawn"):
    actor.modify()  # marks the actor (and its external package) dirty
    actor.set_actor_location_and_rotation(
        unreal.Vector(-120, 330, 100), unreal.Rotator(0, 0, -81), False, False)
```

- **Importable without the editor.** Guard `import unreal` so the same file can be imported by a
  plain Python process (to render a plan, run unit checks on the data):

```python
try:
    import unreal
except ImportError:
    unreal = None
```

- **Avoid swapping a Blueprint's root component from Python.** It has crashed the editor in
  preview builds. Give the C++ base class the root component instead.

## Save and verify

Unsaved work looks correct in the editor and in PIE, then vanishes when the editor closes or
never reaches the packaged game.

1. Mark what you change (`actor.modify()`, `asset.modify()`), or use editor APIs that do.
2. Save explicitly: `unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)` for maps
   and content, or `unreal.EditorAssetLibrary.save_loaded_asset(asset)` for one asset. MCP graph
   tools that compile a Blueprint do not save it.
3. Verify: run `scripts/editor/save_and_verify.py` (reports anything still dirty), then check the
   disk. In a One File Per Actor level each actor is its own file under
   `Content/__ExternalActors__/...`; a moved actor must show up in `git status`.
4. Watch the status bar count of unsaved packages before closing the editor or handing it over.

## Live Coding versus restart

| Change | Path |
|---|---|
| Function bodies in `.cpp` only, editor open | Live Coding (MCP Live Coding tool or console `LiveCoding.Compile`). Read the result in the log |
| New or changed `UCLASS` / `USTRUCT` / `UENUM` / `UPROPERTY` / `UFUNCTION`, new source files, `Build.cs`, `Target.cs`, plugin changes | Full restart cycle (below) |
| Config `.ini` changes | Usually a restart; some console variables apply live |
| DataTable row struct changes | Restart, then re-import the tables |

Restart cycle:

1. Batch every pending reflection change.
2. Save everything and verify (above).
3. Close the editor and its Live Coding console. Do not kill it while it saves.
4. `python scripts/ue.py build --project <dir>`.
5. Reopen the editor; reconnect MCP.
6. `python scripts/check_log.py --project <dir>`: no `Can't find class descriptor`, no load errors.

If Live Coding has crashed the editor on a project, stop using it there; full builds are slower
but predictable.

## Ports, several editors, reconnecting

- The default MCP port is 8000. Give each editor its own: `-ModelContextProtocolPort=8011` on the
  command line, Server Port Number in Editor Preferences (Agentic Workflows, Model Context Protocol,
  in 5.9), or `ServerPortNumber` under `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]`
  in `Saved/Config/<Platform>Editor/EditorPerProjectUserSettings.ini`. Regenerate the client
  config after changing it (`ModelContextProtocol.GenerateClientConfig ClaudeCode`).
- With several editors running, confirm which process answers before any mutation (the server's
  instance metadata, or the process that owns the port).
- After an editor restart the client connection drops. Check the port is listening, then
  reconnect the client. A stdio proxy, where the engine ships one, keeps the client session alive
  across restarts.
- Agent toolsets may be off by default in new projects: enable `AllToolsets` (or the specific
  toolset plugins) once per project, restart, reconnect.

## Headless editor runs

The same editor Python scripts run with no GUI editor, which avoids waiting for a human to reopen
the editor:

```
python scripts/ue.py python --project ./MyGame --script scripts/editor/fix_spawn.py
```

This wraps `UnrealEditor-Cmd <uproject> -run=pythonscript -script=<file> -unattended -nosplash`.
The script must load the map it needs (`unreal.EditorLoadingAndSavingUtils.load_map(path)`) and
save what it changes. Do not run it while a GUI editor has the same project open.

## Seeing the editor and the game

- MCP viewport capture for the level view.
- `scripts/capture_window.ps1` (Windows) for the whole editor window, PIE, UMG and dialogs, even
  when another window covers it. It prints the PNG path; read that file.
- In the game: a screenshot mode the game triggers itself (see [testing](testing.md)), or the
  `HighResShot` console command.
- Read every screenshot at full size before judging it. Empty text, overlapping panels and
  wrong materials are visible only there. A sheet of eight small screenshots side by side is good
  for judging a sequence, not for judging detail.
- On a locked desktop, window captures and screen recordings get few or no frames. Record with
  the session unlocked.

## Version notes

- **UE 5.8:** Unreal MCP is Experimental. Calls run on the editor's game thread; treat it as
  single-writer even where concurrent requests are accepted.
- **UE 5.9 Preview:** MCP launches with the editor and has more toolsets (Blueprints, editor
  actions, MVVM, Slate inspection, performance, files, scene capture, console, Texture Graph,
  widget animation), but toolset plugins are off in new projects until enabled. Settings moved to
  Agentic Workflows; agents can also run inside the editor's Assistant panel. Test on a copy of
  a project rather than converting the main one.
