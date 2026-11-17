# Modern engine features (UE 5.8 and later)

What UE 5.8 and the 5.9 Preview added that changes how an agent should work, and which features
are worth reaching for. Most of these are Experimental: test on a copy of the project, and expect
names and settings to move between versions. Check the engine version before relying on any of it.

## Contents

- Agent tooling: MCP, Python, skills, the Assistant panel
- Blueprints and graphs as text
- Sandboxes
- PCG with an agent
- Rendering choices
- World building
- Characters and crowds
- Gameplay systems
- Testing and validation
- Unreal Canvas
- Sources

## Agent tooling: MCP, Python, skills, the Assistant panel

**Discovery.** With tool search on (the default), `tools/list` returns four meta-tools:
`list_toolsets`, `describe_toolsets` (pass `include_schemas: true` for schemas), `describe_tools`
(full schemas by `Toolset.Tool` name) and `call_tool`. Toolset names are qualified:
`<Plugin>.<Class>` for C++ toolsets, the module path for Python ones.

**Settings moved.** In 5.9 the MCP settings live under Editor Preferences, Agentic Workflows,
Model Context Protocol (port, URL path, auto-start, tool search, allowed origins, Dump Media To
Disk, instructions, client config generation). Project Settings has the same category for
project-wide instructions.

**Server instructions.** Text in Project Settings, Agentic Workflows, Model Context Protocol,
Instructions is sent to every agent that connects, and is stored in `DefaultGame.ini`. Put the
project's naming rules, protected folders and test map there; it reaches agents that never read
`AGENTS.md`. Clients must reconnect to see changes.

**One call at a time.** The server runs tool calls one at a time on the game thread; never send
overlapping calls.

**Long calls.** Clients give up after a timeout (Claude Code after about two minutes). Split long
work (Live Coding builds, big scripts, asset scans, automation runs) into shorter calls, or send a
`progressToken` to receive progress heartbeats.

**Python through MCP.** The PythonScriptingTools toolset's `execute_python`:
- rejects scripts with imports below the top level or star imports;
- returns the value of the script's last expression; `print` goes to the Output Log
  (`LogPython`), not to the tool result;
- can call other tools with `await call_tool("<Toolset.Tool>", **args)`;
- comes with `search_symbols`, `get_symbol` and `grep_stubs` for looking up the Python API.

For many similar edits (a widget tree, dozens of material instances), write one script rather
than many tool calls. Use single calls for inspection, screenshots and compile errors.

**Imports and restarts through tools.** The `ImportFile` tools (sounds, textures, meshes, data
tables, curve and string tables) default to `bReplaceExisting = false` and `bSave = false`: pass
both or the import is not saved. `EditorAppToolset.ExitEditor` closes the editor (with an option
to discard unsaved changes); clients must reconnect after a restart.

**Which editor answered.** The `initialize` result carries instance metadata (process ID, engine
version, project name and folders) under `_meta["com.epicgames.unrealengine/instance"]`. Check it
before any change when several editors run. Each editor needs its own port and its own named
entry in `.mcp.json`; `GenerateClientConfig` only writes the `unreal-mcp` entry.

**Seeing what tools returned.** Dump Media To Disk writes every image and audio block sent over
MCP to `Saved/ModelContextProtocol/`.

**Agent skills inside the engine.** The editor's skill registry loads Markdown skills: any folder
with a `SKILL.md` (frontmatter `name` and `description`) under `<Project>/Skills/`,
`<Plugin>/Skills/`, or `Engine/Extras/AgentTools/Skills/`. Agents fetch them with
`AgentSkillToolset.GetSkills`, and relative links are rewritten to absolute paths. Installing this
skill into `<Project>/Skills/` (`scripts/init_agent_files.py --install-skill`) makes it available
to any agent connected to that editor, including the in-editor Assistant. Engine plugins ship
their own skills (PCG, editor actions); load them before working in their area.

**Python toolsets.** A class deriving from `unreal.ToolsetDefinition` with `@unreal.uclass()`,
each tool marked `@toolset_registry.tool_call(mode=unreal.ToolAccessMode.READ|WRITE|EXECUTE)` and
`@staticmethod`; type hints become the JSON schema, Google-style docstrings the descriptions;
raise exceptions for errors; `async def` for long work. Register from the plugin's
`init_unreal.py`, then run `ModelContextProtocol.RefreshTools`. Set an access mode on every tool;
the default is Execute. A project-specific toolset (spawn this game's pickups, validate this
game's levels) is often better than teaching an agent the same steps every session.

**The Unreal Assistant panel.** In 5.9 the editor can run Claude Code, Codex, Cursor, OpenCode or
any Agent Client Protocol agent inside its Assistant panel, connected to its own MCP server with
no config file. Claude Code needs the `claude-agent-acp` adapter (npm) and a signed-in CLI. On
macOS start the editor from a terminal so it finds Node.js and the adapter. Approvals are stored
per user, project and command. The panel connects to one editor at a time; a terminal agent can
connect to several.

**Security.** The server has no authentication. Any local process, and any page served from an
allowed origin, can call every tool. Keep it on loopback, keep the allowed-origins list short, and
do not run untrusted local web pages while it is up.

## Blueprints and graphs as text

- The experimental EditorToolset exposes Blueprint graphs as an S-expression language:
  `BlueprintTools.read_graph_dsl(graph)` and `write_graph_dsl(graph, code)`, plus additive
  `create_node` and `connect_pins`. Writes are transactional: a failed write leaves the graph as
  it was.
- The round trip is not lossless in 5.8. Nodes with several data outputs, where a later output is
  used, bind to the wrong pin on write; branches that merge after a Switch, Cast or IsValid lose
  the shared chain on read. Use `read_graph_dsl` to inspect, edit such graphs with `create_node`
  and `connect_pins`, then compile and read back.
- 5.9 adds scripting functions to create and edit Blueprints, graphs, nodes and variables from
  Python or Editor Utility Blueprints; StateTrees, Chooser tables and Dataflow graphs become
  editable from script; and GraphDsl, a text language for authoring graph assets.
- Even with these, C++ stays the better home for logic: graphs edited as text are still graphs to
  review. After every graph write: compile, read the compile result, save, verify.

## Sandboxes

An Experimental 5.8 feature: while a sandbox is active, every file the editor adds, changes or
deletes under a mount point (`/Game`, `/Engine`, plugin mounts) goes to
`Intermediate/Sandboxes/<name>/` instead, with a `Manifest.json` listing the changes. Persisting
copies the changes over the originals; otherwise the project files stay as they were.

- Start a sandbox before letting an agent run a large or risky edit, review the changes, then
  persist or discard. It is the editor-side equivalent of a git branch for binary assets.
- Only one sandbox is active at a time per editor.
- Changes inside a sandbox do not appear in `git status` until persisted. While a sandbox is
  active, verify saves against the sandbox's change list, not the working tree.
- With a locking version control system, files are checked out only when the changes persist.
- `Intermediate/` is not version-controlled. A sandbox is not a backup; persist or export what
  matters.

## PCG with an agent

- Enable the PCG toolset and load the engine's PCG graph-generation skill at the start of every
  PCG session; without it agents misuse nodes and overbuild.
- Point the agent at reference graphs (the PCG plugin's sample content, the project's own graphs)
  and ask it to reuse or duplicate one before building from scratch.
- Select the assets or actors in question yourself and then ask; discovery by script is slower and
  costs context.
- Ask for a plan (which nodes, which references) before large edits, execute in steps, and stop it
  early when it goes wrong.
- Inspect point data and attributes through the toolset's Dataview, not by dumping points.
- Further engine skills cover shape grammars (facades, corridors), Mesh Terrain, instancing on
  meshes and biomes.

## Rendering choices

| Feature | Status | Use it for |
|---|---|---|
| Lumen Lite | 5.8 | Dynamic GI at about half the cost of Lumen High Quality; Switch 2 and PC |
| MegaLights | Production-ready in 5.8 | Many shadowed dynamic lights |
| Toon Shader (Substrate) | Experimental, 5.8 | Cartoon, anime and 2D looks on every platform |
| Fog Screen Space Scattering | Experimental, 5.8 | Dense fog, smoke and dust that blur and blend |
| Order-independent transparency (AVBOIT) | 5.9 | Overlapping glass, smoke and particles without sorting pops |
| Dynamic Wind for Nanite foliage | Experimental, 5.9 | GPU-simulated plant motion, local gusts |
| Shadow debug views | 5.9 | Virtual shadow map overview, cascade and far-shadow views |

The web target uses the mobile renderer: Lumen, MegaLights and hardware ray tracing do not apply
there. Pick the look for the weakest target first.

## World building

- **Mesh Terrain** (Experimental, 5.8): 3D mesh terrain with overhangs, tunnels and floating
  islands, non-destructive modifiers, World Partition and One File Per Actor streaming, PCG
  interop.
- **PCG**: manual edits on top of generated results without breaking regeneration; arrays,
  structs, sets and maps as attributes; embedded subgraphs that expose only the parameters artists
  need.
- **Procedural Vegetation Editor** (Experimental): grows Nanite-ready trees, imports DCC meshes,
  takes sketches and photos as input.
- **Fast Geometry Streaming** (Experimental): fast loading of static, non-gameplay geometry in
  large open worlds.

## Characters and crowds

- **MetaHuman Collections** (Experimental, 5.8): crowds of MetaHumans with Mass, switching between
  full actors and instanced skinned meshes by distance.
- **Mesh to MetaHuman** now conforms bodies as well as heads. **MetaHuman Animator** captures face
  and body from a single webcam with the Markerless Motion Capture plugin (Windows).
- **Control Rig Physics** (Beta) for cinematic ragdoll and secondary motion; **Control Rig
  Dynamics** for runtime; **Direct Mesh Controls** (Experimental) for animating on the surface.
- 5.9: IK Retargeter gains Proximity IK, Pelvis Volume and Limb Twist; the Unreal Animation
  Framework (UAF) expands, including AnimGen inside UAF; AnimGenOffline generates animation in
  Sequencer, and an NVIDIA Kimodo plugin adds text-and-trajectory-driven animation. See
  [animation](animation.md).

## Gameplay systems

- StateTrees are editable from Blueprint and Python in 5.9 (tasks, considerations, evaluators,
  global tasks), so an agent can build behaviour without graph surgery.
- Mass Characters (5.9) adds Mass traits for character interpolation, visualization and
  selective pawn replication.
- Navigation meshes can build progressively, a set number of tiles per tick.
- Mover works with AnimGen as well as Character Movement.

## Testing and validation

- **Cooked builds can host the MCP server** (`-ModelContextProtocolStartServer`, or
  `IModelContextProtocolModule::StartServer()`), exposing only tools tagged `AIRuntimeCallable`.
  Engine toolsets with runtime tools include Input, Console, Scene Capture, Widget Finder,
  NavMesh and Perf, so an agent can drive and measure a packaged Development build directly.
  Never enable it in a release build: there is no authentication, and cooked games are not
  read-only.
- 5.9 adds a Modular Test Framework for scoped plugin tests, a Map Check subsystem with Blueprint
  logging, Data Validation updates, and a source-control option to validate soft dependencies.
- Python toolsets can carry unit tests that appear in the Session Frontend under an automation path.

## Unreal Canvas

An Experimental 5.9 workspace where people and agents generate and refine text, images, video and
meshes with a chosen generation service, with plugins that expose Movie Render Graph renders to it
and place annotations in the 3D scene. Treat its output like any generated asset: record the tool
and the licence in the credits ledger.

## Sources

- Unreal MCP (5.9): https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- Using Python with AI agents: https://dev.epicgames.com/documentation/unreal-engine/using-python-with-ai-agents-in-unreal-engine
- External agents in the Assistant panel: https://dev.epicgames.com/documentation/unreal-engine/run-external-ai-agents-in-the-unreal-assistant-panel-in-unreal-engine
- PCG with LLMs: https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine
- UE 5.9 release notes: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-9-release-notes
- UE 5.8 announcement: https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available
- File sandbox API: https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/FileSandboxCore/ISandboxManager
- Graph DSL round-trip reports: https://forums.unrealengine.com/t/blueprinttools-read-graph-dsl-output-is-not-round-trippable-through-write-graph-dsl-for-nodes-with-multiple-data-outputs-single-bind-emitted-for-a-non-first-output-write-binds-it-to-the-wrong-pin/2734654 and https://forums.unrealengine.com/t/blueprinttools-read-graph-dsl-drops-shared-exec-chains-when-switch-cases-multi-output-node-branches-merge-into-one-chain/2747184
