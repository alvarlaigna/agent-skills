# Build and ship

Compiling, cooking, packaging and verifying what players will run.

## Contents

- The commands
- Configurations
- Package on day one
- Cook-only failures
- Size
- Verify the artifact, not the project
- Windows from another OS
- The web target (Wasm)
- Shared machines
- Version notes

## The commands

`scripts/ue.py` wraps these; the raw forms are here for debugging. Use absolute paths everywhere.

```
# Editor target (after reflection changes, editor closed)
<Engine>/Build/BatchFiles/Build.bat <Game>Editor Win64 Development -Project="<abs>.uproject" -WaitMutex
<Engine>/Build/BatchFiles/Mac/Build.sh <Game>Editor Mac Development -Project="<abs>.uproject" -WaitMutex
<Engine>/Build/BatchFiles/Linux/Build.sh <Game>Editor Linux Development -Project="<abs>.uproject" -WaitMutex

# Build, cook, stage, package, archive
<Engine>/Build/BatchFiles/RunUAT.bat BuildCookRun -project="<abs>.uproject" -noP4 -utf8output
    -platform=Win64 -clientconfig=Shipping -build -cook -stage -pak -archive
    -archivedirectory="<abs>/Build" -prereqs -nodebuginfo

# Automation tests, headless
<Engine>/Binaries/Win64/UnrealEditor-Cmd.exe "<abs>.uproject" -ExecCmds="Automation RunTests <Filter>"
    -TestExit="Automation Test Queue Empty" -unattended -nullrhi -nosplash -nosound -log

# Editor Python, headless
<Engine>/Binaries/Win64/UnrealEditor-Cmd.exe "<abs>.uproject" -run=pythonscript -script="<abs>.py"
    -unattended -nosplash
```

The most reliable way to get a platform's exact packaging command: package once from the editor's
Platforms menu, then copy the `RunUAT ... BuildCookRun ...` line the editor prints in its Output
Log into a project script. Every flag is then the one the engine actually uses.

`-prereqs` stages the Visual C++ runtime installer next to the game. Without it, some players'
PCs fail to start the game with a missing DLL.

## Configurations

| Config | Use |
|---|---|
| Development | Diagnosis: console, logs, stats. Large |
| Shipping | Release and size checks. No console; smaller and faster |
| Test | Shipping performance with some diagnostics |

Ship Shipping. Check that anything the game's own test or screenshot modes depend on still works in
Shipping before relying on it there (command-line parsing, log files, file paths).

## Package on day one

Package an empty or near-empty project before writing game code, and again at every milestone.
The cook and the packaged runtime enforce rules the editor does not, and each failure costs minutes
early and hours on the last night.

After each package:

1. Launch the packaged build, not the editor. Look at it (a screenshot), check the log.
2. Weigh the zip, not the folder.
3. If the game has a self-play mode, run it in the packaged build.

## Cook-only failures

| Symptom | Cause | Fix |
|---|---|---|
| Cook fails: Asset Manager has no entry for assets of type `GameFeatureData` | Agent toolset plugins enable GameFeatures | Add a scan rule (below), or enable the toolsets only for editor sessions and keep them out of the packaged target |
| Works in editor, crashes or fails in cook | Physics, world or spawn calls in a constructor | Move to `BeginPlay` / `PostInitializeComponents` |
| Untextured or missing assets only in the package | Stale references after a rename; editor had the new asset in memory | Fix up redirectors, re-save referencers, package again |
| Assets missing at runtime | Loaded only by path; cook never saw them | Reference them, add a primary asset rule, or `DirectoriesToAlwaysCook` |
| Template sample level in the build | No `MapsToCook` list | List every shipping map |
| Duplicate primary asset ID | A copied folder duplicated a label | Delete the duplicate label |
| Stale content after an incremental package | Staging reused (`-NoCleanStage` and similar) | Clean staging for release builds |
| Text missing in the package | Runtime-built fonts | Use real `UFont` assets |

Scan rule for the GameFeatures case, in `Config/DefaultGame.ini` under
`[/Script/Engine.AssetManagerSettings]`:

```ini
+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",AssetBaseClass="/Script/GameFeatures.GameFeatureData",bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/Game/Unused")),SpecificAssets=,Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
```

Run `python scripts/check_log.py --log <cook or UAT log>` after any failed package; it names these
patterns and the first real error.

## Size

- Weigh the zip. Typical limits: itch.io web upload 1 GB per file (larger files through `butler`),
  browser games about 500 MB total and 200 MB per file. Jams often cap the download at 1 GB.
- Biggest wins: Shipping config, `MapsToCook`, never-cook directories for template and sample
  content, texture `LODGroup` and max sizes, mono audio, removing unused plugins from the target.
- Photoreal packs (scanned foliage, high-resolution megascans) can add gigabytes. Decide early.
- If a file must exceed an upload limit, split the zip and ship a join script, and test that the
  join reproduces a byte-identical zip.

## Verify the artifact, not the project

1. Unzip the release zip into an empty folder on the same machine and run it from there.
2. Clone the repository fresh, build and package from the clone. This proves the repository holds
   everything (LFS files, generated assets, config) and nothing depends on local leftovers.
3. Test on a second machine if at all possible, ideally the platform judges or players will use.
4. Keep every release zip with its commit hash and a line in a build log.

## Windows from another OS

Most players run Windows. If development happens on macOS or Linux, build Windows early on a real
Windows machine. MSVC rejects code other compilers accept (a local variable shadowing a member is
an error under Unreal's warning settings; some template and macro forms fail to parse), and an old
Visual C++ runtime on the build machine stops the cook at the end. Package, launch, and play a few
minutes on Windows before the final day.

## The web target (Wasm)

The web platform (WebAssembly and WebGPU, mobile renderer) arrived as Experimental in the UE 5.9
Preview. What held during that preview:

- **Requirements.** A C++ project (a Blueprint project can add one empty C++ class). Emscripten
  through emsdk at the exact version the engine pins in `Engine/Platforms/Wasm/Config/Wasm_SDK.json`,
  with `WASM_EMSDK_ROOT` pointing at the emsdk root; restart the editor and refresh platform status
  in SDK Management. Mac and Linux launcher builds lacked some support files; a source build worked.
- **Look.** The mobile renderer: no Lumen-dependent look, no hardware ray tracing. Put grain,
  vignette and grading in post-process or UI overlays, and check with the editor's mobile preview.
- **Memory.** Tabs crashed above about 2 GB of Wasm memory. Ship Shipping, cut content, and measure
  the page's memory over several minutes of play, not at load.
- **Threads and frame pacing.** A small fixed worker pool froze the page when the engine needed a
  new worker after load; the automatic pool still started workers late on low-core machines. Test
  with the browser limited to 4 and 8 cores. Shipping builds ignored the engine's frame limit on the
  web, and frames arrived in uneven pairs; a frame limiter in the page script slightly above the
  display rate removed the judder.
- **Leaks.** A skinned mesh exposed per-frame upload buffers that the web graphics layer never
  freed (gigabytes in minutes). Measure GPU-process memory with the feature on and off.
- **Textures.** BC/DXT does not run on most phones. Cook ASTC as well when mobile browsers matter
  (`-cookflavor=ASTC` with an added texture set).
- **Hosting.** Opening `index.html` from `file://` fails. Use the generated `Play_*` launcher or a
  local web server. Put `index.html` at the zip root for itch.io. Bink video is unsupported.
- **Saves.** Launcher-engine web builds lost save games on reload until `-project=` was added to
  the page arguments.
- **Audio.** Starts after the first user gesture (see [content pipeline](content-pipeline.md#audio)).
- **Tests.** Drive the packaged web build in a headless browser (Playwright or Chrome DevTools):
  load, first interaction, one full solution of a level, console errors, memory after several
  minutes. Gate every build a human sees on that sweep passing.

## Shared machines

- One heavy job (build, cook, package, GPU test run) at a time unless the machine has clear
  headroom. A lock that cannot be half-taken works: create a lock folder with the owner's name in
  the same command, and let anyone remove a nameless lock after a few minutes.
- Cap parallel compile actions (`-MaxParallelActions=N` on UnrealBuildTool) and shader compiler
  workers when other work shares the machine. Memory, not CPU, is usually what runs out.
- Run long builds in the background and read the log when they exit. A notice that a background
  job was stopped is not proof it did not run; the log is.

## Version notes

- **UE 5.8:** some MSVC toolset versions are rejected by UnrealBuildTool; update Visual Studio to
  the version the release notes name. The .NET Framework SDK is required for the first C++ build.
- **UE 5.9 Preview:** the web target, more MCP toolsets, and a short QA pass. Work on a copy of
  the project, keep the 5.8 version runnable if plugins you need (for example DLSS) are only
  published for 5.8, and keep Target.cs Wasm SIMD and allocator settings at defaults with a
  launcher engine.
