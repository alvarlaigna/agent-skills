---
name: unity
description: Builds, architects, tests, and ships Unity 6 games in C# with the Universal Render Pipeline (URP), the Input System, Assembly Definitions, and the Unity Test Framework. Use when writing or refactoring Unity C# (MonoBehaviour, ScriptableObject, Awaitable), structuring .asmdef assemblies, fixing GC allocations or frame spikes in Update and FixedUpdate, configuring URP render graph passes, shaders, physics layers, Rigidbody or CharacterController movement, Input System actions and rebinding, writing EditMode or PlayMode tests, running batchmode test and build commands, migrating legacy Input or other deprecated APIs, or driving the Unity Editor through Unity MCP.
compatibility: Agent Skills format. Written against Unity 6.3 LTS (6000.3) and applies to later 6000.x releases. Command examples use macOS editor paths; the arguments are the same on Windows and Linux.
---

# Unity

An operating model for agent-driven Unity 6 work: where code lives, the frame and allocation
rules that keep it fast, what is banned, and how to prove a change works without a human pressing
Play. It assumes C# and Unity fundamentals and adds only conventions and failure modes.

## Baseline

| Concern | Default |
|---|---|
| Engine | Unity 6 LTS. Read the exact version from `ProjectSettings/ProjectVersion.txt`; never assume it |
| Rendering | URP with the render graph, Forward+, SRP Batcher on |
| Input | `com.unity.inputsystem`; Active Input Handling set to Input System Package |
| UI | UI Toolkit for menus and HUD; uGUI with TextMeshPro where world-space UI needs it |
| Async | `Awaitable` with `destroyCancellationToken` |
| Data | `ScriptableObject` assets for configuration; direct references or Addressables for loading |
| Tests | Unity Test Framework: EditMode for rules, PlayMode for lifecycle, physics and input |

## Pick the layer

| Need | Where it goes |
|---|---|
| Rules, state machines, combat math, inventory, scoring, AI decisions | Pure C# in `Game.Domain` (no `UnityEngine`), tested in EditMode |
| Lifecycle, physics callbacks, transforms, animation, audio, VFX | Thin `MonoBehaviour` adapters in `Game.Runtime` |
| Tuning values, item definitions, event channels | `ScriptableObject` assets under `Assets/_Project/Data/` |
| Build scripts, validators, importers, menu items | `Game.Editor` |
| Hierarchy, console and prefab inspection in a live editor | Unity MCP |
| Full test passes and player builds | The editor in batch mode (commands below) |

An adapter reads input and engine state, calls the domain, and writes the result back to the
engine. It holds no rules. If a branch in a `MonoBehaviour` decides a game outcome, move it into
`Game.Domain` and test it there.

## Project layout

```text
Assets/_Project/
├── Art/  Audio/  Prefabs/  Scenes/
├── Data/                  # ScriptableObject assets: configs, definitions, channels
├── Settings/              # URP assets, Input Actions, Build Profiles
└── Scripts/
    ├── Domain/            # Game.Domain.asmdef        noEngineReferences: true
    ├── Runtime/           # Game.Runtime.asmdef       references Game.Domain
    ├── Editor/            # Game.Editor.asmdef        Editor platform only
    └── Tests/
        ├── EditMode/      # Game.Tests.EditMode.asmdef
        └── PlayMode/      # Game.Tests.PlayMode.asmdef
```

`Game.Runtime`, `Game.Editor`, `Game.Tests.EditMode` and `Game.Tests.PlayMode` are required.
`Game.Domain` with `noEngineReferences` makes the compiler enforce the boundary: domain code that
reaches for `UnityEngine` does not build. In a small prototype the domain may live in
`Scripts/Runtime/Domain/` instead; it still must not use `UnityEngine`. Templates are in
[architecture and C#](references/architecture-and-csharp.md#assemblies).

## Start of every session

1. Read the project's `AGENTS.md` / `CLAUDE.md`, then `ProjectSettings/ProjectVersion.txt` and
   `Packages/manifest.json`. API advice depends on the editor and package versions.
2. Check whether an editor has the project open (`pgrep -fl 'Unity.app/Contents/MacOS/Unity'`).
   A batch-mode run cannot open a project an editor holds: work through MCP, or close the editor.
3. If Unity MCP is connected, read the console before changing anything. Record the exact tool
   names and arguments that worked in `docs/MCP_TOOLS.md`.
4. Search for the banned APIs below before writing code next to them. New code does not copy old
   patterns; touched code is migrated.

## Frame discipline

| Callback | Does | Never |
|---|---|---|
| `Awake` | Cache own components, build the domain object | Read other objects' state |
| `OnEnable` / `OnDisable` | Subscribe and unsubscribe events and `InputAction` callbacks, symmetrically | Leave a subscription without its matching removal |
| `Start` | Read other objects initialized in their `Awake` | Heavy loading (use an `Awaitable` flow) |
| `FixedUpdate` | Forces, `Rigidbody` velocity, `MovePosition`, the fixed domain tick | Read "this frame" input edges |
| `Update` | Sample input, latch edges, drive animation parameters, UI and visual state | Write `Rigidbody` state |
| `LateUpdate` | Camera follow, final visual interpolation | Gameplay rules |

Input edges (`WasPressedThisFrame`) are latched into a field in `Update` and consumed, then
cleared, in `FixedUpdate`. Zero or several fixed steps can run in one frame.

## Zero allocations in Update, FixedUpdate and LateUpdate

Steady-state frames allocate 0 B of managed memory. Allocate in `Awake`, on load, or from a pool.

| Allocates or searches | Use instead |
|---|---|
| `GetComponent<T>()` every frame | Cache in `Awake`; `TryGetComponent` when absence is valid |
| `GameObject.Find*`, `FindObjectOfType`, `FindObjectsByType` at runtime | Serialized references, a composition root, a `ScriptableObject` runtime set |
| LINQ, capturing lambdas, `foreach` over an interface type | `for` over `List<T>` or arrays; delegates cached in `Awake` |
| String concatenation, interpolation, `ToString()` for UI | `TMP_Text.SetText("{0:0}", value)`; update text only when the value changes |
| `tag == "Player"` | `CompareTag("Player")` |
| `Physics.RaycastAll`, `Physics.OverlapSphere` | `RaycastNonAlloc`, `OverlapSphereNonAlloc` into a preallocated buffer |
| `collision.contacts`, `mesh.vertices`, `renderer.materials` | `GetContacts(buffer)`, `GetVertices(list)`, `GetSharedMaterials(list)` |
| `Instantiate` / `Destroy` for projectiles, VFX, enemies | `UnityEngine.Pool.ObjectPool<T>` |
| `yield return new WaitForSeconds(t)` | `await Awaitable.WaitForSecondsAsync(t, destroyCancellationToken)` |
| `animator.SetFloat("Speed", v)`, `material.SetColor("_BaseColor", c)` | `static readonly int` IDs from `Animator.StringToHash` / `Shader.PropertyToID` |

Prove it with `Assert.That(() => sut.Tick(dt), Is.Not.AllocatingGCMemory())` in an EditMode test
or the Profiler's GC Alloc column in a development player. See
[testing, CLI and MCP](references/testing-cli-and-mcp.md#allocation-tests).

## Banned APIs

| Banned | Replacement |
|---|---|
| `UnityEngine.Input`, Input Manager axes | `UnityEngine.InputSystem` actions |
| `GameObject.Find`, `FindWithTag`, `FindObjectOfType`, `FindObjectsOfType` in runtime code | Serialized references, composition root, runtime sets |
| `Resources.Load` for game content | Direct references or Addressables (`com.unity.addressables`) |
| `WWW` | `UnityWebRequest`, awaited |
| `SendMessage`, `BroadcastMessage`, `PlayerInput` in Send Messages mode | C# events, interfaces, event channels |
| `Rigidbody.velocity`, `.drag`, `.angularDrag` | `linearVelocity`, `linearDamping`, `angularDamping` |
| Static mutable singletons holding game state | Scene-owned instances wired by a composition root |
| Public fields for inspector data | `[SerializeField] private` fields |
| URP passes that only override `Execute` (Compatibility Mode) | `RecordRenderGraph` |
| `Task.Result`, `.Wait()` on the main thread | `await` |

`Find*` is acceptable in Editor code and tests.

## Serialization and .meta safety

- An asset's identity is the GUID in its `.meta` file. Never delete, regenerate or hand-edit a
  `.meta`. Move and rename assets in the editor or through MCP; with `git mv`, move the `.meta` too.
- A `MonoBehaviour` or `ScriptableObject` class name matches its file name. Rename class and file
  together and keep the `.meta`, or every reference to the script breaks.
- Renaming a serialized field drops saved values unless the new field carries
  `[FormerlySerializedAs("oldName")]`. Keep it until every affected prefab and scene is re-saved.
- `[field: SerializeField]` stores `<Name>k__BackingField`; renaming the property is a field rename.
- Renaming or moving a type held by `[SerializeReference]`, including its namespace or assembly,
  needs `[MovedFrom]`.
- Never hand-edit scene or prefab YAML that the editor has open; its next save overwrites the edit.
- Projects use Force Text serialization and Visible Meta Files, with binary art in Git LFS.

Details and migration recipes: [architecture and C#](references/architecture-and-csharp.md#serialization-and-renames).

## Async

- Multi-frame flows are `async Awaitable` methods, not coroutines. Pass `destroyCancellationToken`
  to every wait; the `OperationCanceledException` ends the flow when the object is destroyed.
- Never await the same `Awaitable` instance twice: instances are pooled and reused.
- CPU work: `await Awaitable.BackgroundThreadAsync()`, then `await Awaitable.MainThreadAsync()`
  before touching any Unity object.

## Definition of done

A change is done when all of these hold. The report names the ones that were not checked.

1. The project compiles with no errors and no new warnings (MCP console, or the batch log).
2. EditMode tests pass. New domain rules arrived with tests.
3. PlayMode tests pass when lifecycle, physics, input or scene wiring changed.
4. Hot-path changes have an allocation test or a 0 B GC Alloc reading.
5. Serialized-field changes keep `.meta` GUIDs and saved values (`git diff` shows no GUID churn and
   no reset values in prefabs or scenes).
6. Visual changes: a Game view screenshot was read at full size and given a one-line verdict.

## Headless commands

```bash
# Editor binary for the project's pinned version (macOS, Unity Hub default install location)
UNITY="/Applications/Unity/Hub/Editor/$(awk '/m_EditorVersion:/ {print $2}' ProjectSettings/ProjectVersion.txt)/Unity.app/Contents/MacOS/Unity"

# EditMode tests
"$UNITY" -batchmode -nographics -projectPath "$PWD" -runTests -testPlatform EditMode \
  -testResults "$PWD/Logs/TestResults-EditMode.xml" -logFile -

# PlayMode tests (drop -nographics for tests that render or read back from the GPU)
"$UNITY" -batchmode -nographics -projectPath "$PWD" -runTests -testPlatform PlayMode \
  -testResults "$PWD/Logs/TestResults-PlayMode.xml" -logFile -

# Player build through the project's build entry point
"$UNITY" -batchmode -nographics -quit -projectPath "$PWD" -buildTarget StandaloneOSX \
  -executeMethod Game.Editor.BuildCommand.Run -buildOutput "$PWD/Builds/macOS/Game.app" \
  -logFile "$PWD/Logs/build-macos.log"
```

- Never pass `-quit` with `-runTests`. The runner exits by itself; `-quit` is not supported while
  tests run.
- Judge a run by the `<test-run>` element of the result XML (`result`, `total`, `failed`), not the
  exit code alone. A filter that matched nothing reports `total="0"`.
- One build target per invocation. Switching the target reimports and recompiles.

The build script, test filters, result parsing, coverage and CI are in
[testing, CLI and MCP](references/testing-cli-and-mcp.md).

## Reference routing

- [Architecture and C#](references/architecture-and-csharp.md): `.asmdef` templates, the
  domain/adapter pattern, composition root, `ScriptableObject` configs, event channels and runtime
  sets, state machines, fixed-tick determinism, allocation-free C#, pooling, `Awaitable` patterns,
  serialization renames, editor code.
- [Rendering, physics and input](references/rendering-physics-and-input.md): URP settings, render
  graph passes, SRP Batcher-compatible shaders, runtime materials, physics layers and queries,
  Rigidbody versus CharacterController movement, Input System setup, latching, rebinding, UI input,
  cameras.
- [Testing, CLI and MCP](references/testing-cli-and-mcp.md): the testing ladder, test assemblies,
  EditMode, allocation and PlayMode templates, input simulation, command-line runs and filters,
  result parsing, in-editor runs, the build script, CI, Unity MCP setup and the verification loop.

## Gotchas

- `obj?.Foo()` and `obj ?? fallback` bypass Unity's destroyed-object check, so a destroyed
  component passes as non-null. Use `if (obj)` or `obj != null` for anything derived from
  `UnityEngine.Object`.
- `GetComponent<T>()` that finds nothing allocates in the Editor but not in a player. Profile
  allocations in a development player, and use `TryGetComponent`.
- With Enter Play Mode Options and domain reload off, static fields and static event subscribers
  survive between Play sessions. Reset them in a
  `[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]` method.
- Writing to a `ScriptableObject` asset at runtime in the Editor persists into the asset, and the
  build behaves differently. Keep runtime state in plain C# objects.
- A raycast after moving a `Transform` in the same step sees the old pose: auto-sync transforms is
  off. Move through the `Rigidbody`, or call `Physics.SyncTransforms()` before the query.
- `NonAlloc` query results are unsorted, and a full buffer means hits were dropped.
- Setting `transform.position` on an enabled `CharacterController` is overwritten by its next
  `Move`. Disable it, teleport, re-enable.
- A `MaterialPropertyBlock` takes that renderer out of the SRP Batcher; `renderer.material` clones
  the material and leaks unless destroyed.
- Active Input Handling "Both" is a migration bridge. Third-party code that polls
  `UnityEngine.Input` throws `InvalidOperationException` once only the Input System is active.
- A generated Input Actions class must be disabled in `OnDisable` and disposed in `OnDestroy`.
- An unexpected `Debug.LogError` or exception fails a test. Use `LogAssert.Expect` when the error
  is the behaviour under test.
- `Time.time`, `UnityEngine.Random` and `DateTime.Now` inside domain code break determinism and
  tests. Pass the tick and a seeded RNG in.
- Unity MCP tools stay unavailable until the client is accepted under Project Settings > AI > Unity
  MCP, and some clients do not expand `~` in the relay path.
- An editor in the background may not import changed scripts until a refresh. Trigger one through
  MCP and wait for compilation before reading the console or running tests.
