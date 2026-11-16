# Ecosystem

Engine features and open-source plugins that replace systems teams often build by hand. Check each
one against the engine version and target platforms before adopting it: third-party plugins lag
engine releases, and few are tested on the web target. Every plugin added to the build is also a
cook and size risk.

## Contents

- Built-in, often disabled
- Patterns
- Open-source plugins
- Editor tooling

## Built-in, often disabled

| Feature | Replaces | Notes |
|---|---|---|
| Game Features and Modular Gameplay | Monolithic Character and GameMode inheritance | Add components, abilities, input and UI to actors from data-only plugins. Enabling GameFeatures requires a `GameFeatureData` scan rule or the cook fails (see [build and ship](build-and-ship.md#cook-only-failures)) |
| StateTree | Behaviour trees bent into state machines, AnimBP state hacks | Hierarchical states with selectors and evaluators: AI, interactables, multi-stage bosses |
| Gameplay Ability System | Hand-rolled abilities, cooldowns, attributes, effects | Heavy to set up; worth it for combat with many abilities or multiplayer |
| Enhanced Input | Legacy input | Input actions and mapping contexts per mode; injectable for tests |
| CommonUI | Manual gamepad focus and input routing in menus | Input-method switching, focus, button icons |
| UMG Viewmodel (MVVM) | Widget bindings polled on tick | Beta plugin. Fires on change only |
| Mover | `UCharacterMovementComponent` for non-humanoid or networked custom movement | Experimental. Modular movement modes with network prediction |
| Mass Entity | Thousands of actors for crowds and traffic | Data-oriented; large setup cost |
| Data Validation | Manual asset checks | Write `UEditorValidatorBase` subclasses; runs on save and on demand |

`FInstancedStruct` (polymorphic structs by value in arrays and data assets) is part of
`CoreUObject` since UE 5.5; older versions need the StructUtils plugin. The Gameplay Message Router
(a tag-keyed pub/sub subsystem) ships with the Lyra sample as a project plugin, not with the engine:
copy it from Lyra.

## Patterns

- **Gameplay Tags over `FName` and enums** for states, categories and events: typo-proof,
  hierarchical (`Status.Debuff.Burn`), matchable by parent, editable without a recompile.
- **Soft references in primary data assets.** A hard `UPROPERTY` pointer loads its target and its
  whole chain with the owner. Hold `TSoftObjectPtr` / `TSoftClassPtr` in `UPrimaryDataAsset`
  subclasses and stream through `UAssetManager`.
- **Subsystems over singletons.** `UWorldSubsystem` per level, `UGameInstanceSubsystem` across
  levels, `ULocalPlayerSubsystem` per player (split screen works without refactoring).
- **Validation before polish.** An Editor Utility Widget or a Python script on a toolbar button
  that flags bad names, missing LODs, oversized textures and unreachable actors pays back on day one.

## Open-source plugins

Check licence, last commit and supported engine versions on each repository before adding.

| Plugin | What it does |
|---|---|
| FlowGraph (MothCocoon/FlowGraph) | Node graph for narrative, quests and level scripting, with node state and save support |
| SPUD (sinbad/SPUD) | Persistence across level streaming and save games with little boilerplate |
| SUDS (sinbad/SUDS) | Text-scripted dialogue; diffs cleanly, agent-friendly |
| Cog (arnaud-jamin/Cog) | Dear ImGui debug windows: attribute inspectors, plots, cheats, collision views |
| Subsystem Browser (aquanox/SubsystemBrowserPlugin) | Details-panel view of every live subsystem |
| PCG Extended Toolkit (PCGEx/PCGExtendedToolkit) | Graph, pathfinding, Voronoi and Delaunay nodes for PCG |
| KawaiiPhysics (pafuhana1213/KawaiiPhysics) | Light bone dynamics for hair, cloth and accessories |
| glTFRuntime (rdeioris/glTFRuntime) | Load glTF at runtime for user content and mods |
| RuntimeAudioImporter (gtreshchev/RuntimeAudioImporter) | Load audio files at runtime |
| UnrealSharp (UnrealSharp/UnrealSharp) | C# gameplay code with hot reload |

## Editor tooling

- Epic's Unreal MCP plugin and the `unreal-mcp` skill for agent access to the editor.
- Community MCP servers (Monolith, ue-mcp, Claireon and paid options) add actions the built-in
  toolsets lack. Add one only for a concrete gap; some listen on all interfaces and need a firewall
  rule, and Python-execution tools run arbitrary code in the editor.
- Blender driven by script (or through a Blender MCP) for meshes, unwraps and bakes, with the
  scripts in the repository.
