# Testing, CLI and MCP

How a Unity change proves itself: the testing ladder, test templates, headless runs, builds, CI,
and working against a live editor through Unity MCP.

## Contents

- The ladder
- Test assemblies
- EditMode tests
- Allocation tests
- PlayMode tests
- Simulating input
- Running tests from the command line
- Reading results
- Running tests in a live editor
- Builds
- CI
- Unity MCP
- The verification loop

## The ladder

| Level | What | Mode | Cost |
|---|---|---|---|
| 1 | Domain rules, state machines, math (pure C#) | EditMode | Milliseconds |
| 2 | Allocation tests on hot paths | EditMode | Milliseconds |
| 3 | Data validation: config ranges, missing references, scene lists | EditMode or a batch validator | Seconds |
| 4 | Components built in code: lifecycle, physics stepping, input | PlayMode | Seconds |
| 5 | Scene smoke tests: load, run N frames, no errors | PlayMode | Seconds to a minute |
| 6 | Development player build running a self-play mode | Player | Minutes |
| 7 | Human playtest of a player build | A person | A person's time |

Each level catches what the one below cannot. Push logic down the ladder: a rule tested at level 1
does not need a scene.

## Test assemblies

`Assets/_Project/Scripts/Tests/EditMode/Game.Tests.EditMode.asmdef`

```json
{
  "name": "Game.Tests.EditMode",
  "rootNamespace": "Game.Tests",
  "references": [
    "Game.Domain",
    "Game.Runtime",
    "Game.Editor",
    "UnityEngine.TestRunner",
    "UnityEditor.TestRunner"
  ],
  "includePlatforms": ["Editor"],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": true,
  "precompiledReferences": ["nunit.framework.dll"],
  "autoReferenced": false,
  "defineConstraints": ["UNITY_INCLUDE_TESTS"],
  "versionDefines": [],
  "noEngineReferences": false
}
```

`Assets/_Project/Scripts/Tests/PlayMode/Game.Tests.PlayMode.asmdef`

```json
{
  "name": "Game.Tests.PlayMode",
  "rootNamespace": "Game.Tests",
  "references": [
    "Game.Domain",
    "Game.Runtime",
    "Unity.InputSystem",
    "Unity.InputSystem.TestFramework",
    "UnityEngine.TestRunner"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": true,
  "precompiledReferences": ["nunit.framework.dll"],
  "autoReferenced": false,
  "defineConstraints": ["UNITY_INCLUDE_TESTS"],
  "versionDefines": [],
  "noEngineReferences": false
}
```

- The PlayMode assembly has no `UnityEditor` references, so the same tests run on a player
  (`-testPlatform StandaloneOSX`).
- `Unity.InputSystem.TestFramework` resolves only when `Packages/manifest.json` lists the package
  as testable: `"testables": ["com.unity.inputsystem"]`.
- `UNITY_INCLUDE_TESTS` keeps test assemblies out of normal player builds.

## EditMode tests

```csharp
using System;
using Game.Domain.Movement;
using NUnit.Framework;
using NVector2 = System.Numerics.Vector2;

namespace Game.Tests
{
    public sealed class DashMotorTests
    {
        static readonly DashConfig Config = new(speed: 18f, duration: 0.15f, cooldown: 0.6f);
        const float Dt = 1f / 50f;
        const float Walk = 5f;

        [Test]
        public void Dash_MovesAtDashSpeed()
        {
            var motor = new DashMotor(Config);
            NVector2 v = motor.Tick(Dt, NVector2.UnitX, Walk, dashRequested: true);
            Assert.That(v.X, Is.EqualTo(18f).Within(1e-4f));
            Assert.That(motor.IsDashing, Is.True);
        }

        // Tick counts straddle the boundary on purpose: 30 x 0.02f is not exactly 0.6f
        [TestCase(29, false)]
        [TestCase(31, true)]
        public void Dash_RespectsCooldown(int ticksAfterDash, bool expectDash)
        {
            var motor = new DashMotor(Config);
            motor.Tick(Dt, NVector2.UnitX, Walk, dashRequested: true);
            for (int i = 1; i < ticksAfterDash; i++) motor.Tick(Dt, NVector2.UnitX, Walk, dashRequested: false);
            motor.Tick(Dt, NVector2.UnitX, Walk, dashRequested: true);
            Assert.That(motor.IsDashing, Is.EqualTo(expectDash));
        }

        [Test]
        public void SameInputs_GiveIdenticalOutputs()
        {
            float[] RunOnce()
            {
                var motor = new DashMotor(Config);
                var xs = new float[200];
                for (int i = 0; i < xs.Length; i++)
                    xs[i] = motor.Tick(Dt, new NVector2(MathF.Sin(i * 0.1f), 1f), Walk, i % 37 == 0).X;
                return xs;
            }
            Assert.That(RunOnce(), Is.EqualTo(RunOnce())); // bitwise, not Within
        }
    }
}
```

Name tests `Subject_Behaviour`, one behaviour per test, no shared mutable state between tests.

## Allocation tests

```csharp
using Game.Domain.Movement;
using NUnit.Framework;
using UnityEngine.TestTools.Constraints;
using Is = UnityEngine.TestTools.Constraints.Is; // Unity's Is extends NUnit's
using NVector2 = System.Numerics.Vector2;

namespace Game.Tests
{
    public sealed class HotPathAllocationTests
    {
        [Test]
        public void DashMotorTick_DoesNotAllocate()
        {
            var motor = new DashMotor(new DashConfig(18f, 0.15f, 0.6f));
            motor.Tick(0.02f, NVector2.UnitX, 5f, true); // warm-up: first-call costs are excluded

            Assert.That(() => motor.Tick(0.02f, NVector2.UnitX, 5f, false), Is.Not.AllocatingGCMemory());
        }
    }
}
```

- Warm up first: static initialisation and first-call JIT allocate once and are not the hot path.
- The constraint measures managed allocations on the calling thread in the Editor's Mono runtime.
  Confirm adapter code in a development player with the Profiler (GC Alloc column, or the Memory
  Profiler package) because some Unity APIs allocate only in the Editor.
- Performance budgets: `com.unity.test-framework.performance` with
  `Measure.Method(() => ...).WarmupCount(5).MeasurementCount(20).GC().Run()` on a
  `[Test, Performance]` method.

## PlayMode tests

Build objects in code; load scenes only in smoke tests.

```csharp
using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    public sealed class FallingCrateTests
    {
        SimulationMode _previousMode;
        GameObject _crate;

        [SetUp]
        public void SetUp()
        {
            _previousMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script; // the test owns time
            _crate = GameObject.CreatePrimitive(PrimitiveType.Cube);
            _crate.AddComponent<Rigidbody>();
        }

        [TearDown]
        public void TearDown()
        {
            Object.Destroy(_crate);
            Physics.simulationMode = _previousMode;
        }

        [UnityTest]
        public IEnumerator Crate_FallsUnderGravity()
        {
            yield return null; // let Awake/Start run
            var body = _crate.GetComponent<Rigidbody>();
            for (int i = 0; i < 50; i++) Physics.Simulate(0.02f);
            Assert.That(body.position.y, Is.LessThan(-4f)); // 1 s of free fall is about -4.9 m
        }
    }
}
```

Scene smoke test:

```csharp
[UnityTest]
public IEnumerator Gameplay_LoadsAndRunsTwoSeconds_WithoutErrors()
{
    Time.captureDeltaTime = 1f / 60f; // fixed frame time regardless of machine speed
    yield return UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Gameplay");
    for (int i = 0; i < 120; i++) yield return null;
    Time.captureDeltaTime = 0f;
    LogAssert.NoUnexpectedReceived();
}
```

- The scene must be in the build profile's scene list.
- `[Test] public async Task ...` tests are supported and can `await` an `Awaitable`; use them for
  flows written with `Awaitable`, `[UnityTest]` with `IEnumerator` for frame-by-frame stepping.
- Destroy everything a test creates in `[TearDown]` (or `[UnityTearDown]`). Leftover objects make
  the next test's result depend on order; `-randomOrderSeed` exposes this.
- `LogAssert.Expect(LogType.Error, new Regex("Missing MovementConfig"))` when the error is the
  expected behaviour.
- Adapters expose `internal void Construct(...)` for tests, with `InternalsVisibleTo` for the test
  assembly, rather than tests setting private serialized fields by reflection.

## Simulating input

Tests drive the real Input System path with `InputTestFixture`, which isolates devices and state
per test:

```csharp
using NUnit.Framework;
using UnityEngine.InputSystem;

namespace Game.Tests
{
    public sealed class JumpInputTests : InputTestFixture
    {
        [Test]
        public void SpacePress_IsSeenAsPressedThisFrame()
        {
            var keyboard = InputSystem.AddDevice<Keyboard>();
            var jump = new InputAction("Jump", binding: "<Keyboard>/space");
            jump.Enable();

            Press(keyboard.spaceKey);

            Assert.That(jump.WasPressedThisFrame(), Is.True);
            jump.Disable();
        }
    }
}
```

For adapter tests, create the action as above, pass `InputActionReference.Create(jump)` through
the adapter's `Construct` method, then step frames with `[UnityTest]` and assert on the
`Rigidbody` or domain state. Test the latch: press and release within one frame and confirm the
next fixed step still sees the jump.

## Running tests from the command line

```bash
UNITY="/Applications/Unity/Hub/Editor/$(awk '/m_EditorVersion:/ {print $2}' ProjectSettings/ProjectVersion.txt)/Unity.app/Contents/MacOS/Unity"

"$UNITY" -batchmode -nographics -projectPath "$PWD" -runTests -testPlatform EditMode \
  -testResults "$PWD/Logs/TestResults-EditMode.xml" -logFile -
```

| Argument | Use |
|---|---|
| `-testPlatform EditMode` / `PlayMode` / a `BuildTarget` name | Which tests run, and where. A build target builds a player and runs PlayMode tests on it |
| `-testFilter "Game.Tests.DashMotorTests"` | Semicolon-separated names or a regex on full names; `!` negates |
| `-testCategory "Smoke;!Slow"` | Categories from `[Category("Smoke")]` |
| `-assemblyNames "Game.Tests.EditMode"` | Restrict to assemblies |
| `-runSynchronously` | EditMode only, one editor update; filters out `[UnityTest]` and `[UnitySetUp]` tests |
| `-randomOrderSeed 42` | Shuffle order to expose test coupling |
| `-retry 2`, `-repeat 20` | Retry failures, or repeat passes to hunt flakes. Report retries; never hide them |
| `-testSettingsFile path` | `TestSettings.json` for player runs (scripting backend, architecture) |

- `-quit` is not supported while tests run; omit it.
- A batch run cannot open a project that an editor has open. Close the editor, or run the tests
  inside it (next sections).
- PlayMode under `-nographics` has no GPU device. Tests that render, capture the screen, or read
  back textures need a run without it.
- Code coverage (`com.unity.testtools.codecoverage`): add
  `-debugCodeOptimization -enableCodeCoverage -coverageResultsPath "$PWD/CodeCoverage"
  -coverageOptions "generateHtmlReport;assemblyFilters:+Game.*"`.

## Reading results

The XML is NUnit 3 format. The exit code is not a documented contract; read the file.

```bash
python3 - "$PWD/Logs/TestResults-EditMode.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
run = ET.parse(sys.argv[1]).getroot()  # <test-run>
total, failed = int(run.get("total", 0)), int(run.get("failed", 0))
print(f"{run.get('result')} total={total} passed={run.get('passed')} failed={failed} skipped={run.get('skipped')}")
for case in run.iter("test-case"):
    if case.get("result") == "Failed":
        message = case.findtext("./failure/message") or ""
        print("FAIL", case.get("fullname"), "|", message.strip().splitlines()[0] if message.strip() else "")
sys.exit(0 if total > 0 and failed == 0 else 1)
PY
```

`total == 0` is a failure: the filter or assembly name matched nothing. When the XML is missing,
the run never started; read the log for compile errors or a held project lock.

## Running tests in a live editor

When the editor stays open (MCP sessions), run tests in it through `TestRunnerApi` and read the
results from the console:

```csharp
// Scripts/Editor/AgentTestRunner.cs
using UnityEditor;
using UnityEditor.TestTools.TestRunner.Api;
using UnityEngine;

namespace Game.Editor
{
    public static class AgentTestRunner
    {
        [MenuItem("Tools/Agent/Refresh")]
        public static void Refresh() => AssetDatabase.Refresh();

        [MenuItem("Tools/Agent/Run EditMode Tests")]
        public static void RunEditMode() => Run(TestMode.EditMode);

        [MenuItem("Tools/Agent/Run PlayMode Tests")]
        public static void RunPlayMode() => Run(TestMode.PlayMode);

        static void Run(TestMode mode)
        {
            var api = ScriptableObject.CreateInstance<TestRunnerApi>();
            api.RegisterCallbacks(new Reporter());
            api.Execute(new ExecutionSettings(new Filter { testMode = mode }));
        }

        sealed class Reporter : ICallbacks
        {
            public void RunStarted(ITestAdaptor testsToRun) { }
            public void TestStarted(ITestAdaptor test) { }

            public void TestFinished(ITestResultAdaptor result)
            {
                if (!result.HasChildren && result.TestStatus == TestStatus.Failed)
                    Debug.LogError($"AGENT FAIL {result.FullName}: {result.Message}");
            }

            public void RunFinished(ITestResultAdaptor result) =>
                Debug.Log($"AGENT TESTS {result.TestStatus} passed={result.PassCount} failed={result.FailCount} skipped={result.SkipCount}");
        }
    }
}
```

- Trigger the menu item through MCP (or ask the human to), then read the console for the
  `AGENT TESTS` line. Absence of the line means the run has not finished or did not start.
- PlayMode runs reload the domain unless Enter Play Mode Options disable it. Callbacks registered
  on a temporary instance can be lost across that reload; register them from an
  `[InitializeOnLoad]` static constructor when PlayMode reporting goes missing.

## Builds

`Scripts/Editor/BuildCommand.cs`, the single entry point for player builds:

```csharp
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Game.Editor
{
    public static class BuildCommand
    {
        public static void Run()
        {
            string output = Arg("-buildOutput") ?? $"Builds/{EditorUserBuildSettings.activeBuildTarget}/Game";
            BuildProfile profile = BuildProfile.GetActiveBuildProfile(); // null when a platform profile is active

            BuildReport report = profile != null
                ? BuildPipeline.BuildPlayer(new BuildPlayerWithProfileOptions
                {
                    buildProfile = profile,
                    locationPathName = output,
                    options = BuildOptions.None,
                })
                : BuildPipeline.BuildPlayer(new BuildPlayerOptions
                {
                    scenes = EnabledScenes(),
                    target = EditorUserBuildSettings.activeBuildTarget,
                    locationPathName = output,
                    options = BuildOptions.None,
                });

            BuildSummary s = report.summary;
            Debug.Log($"BUILD {s.result} errors={s.totalErrors} warnings={s.totalWarnings} " +
                      $"size={s.totalSize} time={s.totalTime} path={s.outputPath}");
            if (Application.isBatchMode) EditorApplication.Exit(s.result == BuildResult.Succeeded ? 0 : 1);
        }

        static string[] EnabledScenes()
        {
            var scenes = new List<string>();
            foreach (EditorBuildSettingsScene scene in EditorBuildSettings.scenes)
                if (scene.enabled) scenes.Add(scene.path);
            return scenes.ToArray();
        }

        static string Arg(string name)
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
                if (args[i] == name) return args[i + 1];
            return null;
        }
    }
}
```

```bash
# With a saved build profile
"$UNITY" -batchmode -nographics -quit -projectPath "$PWD" \
  -activeBuildProfile "Assets/_Project/Settings/Build Profiles/macOS.asset" \
  -executeMethod Game.Editor.BuildCommand.Run -buildOutput "$PWD/Builds/macOS/Game.app" \
  -logFile "$PWD/Logs/build-macos.log"

# With a platform target only
"$UNITY" -batchmode -nographics -quit -projectPath "$PWD" -buildTarget StandaloneWindows64 \
  -executeMethod Game.Editor.BuildCommand.Run -buildOutput "$PWD/Builds/Win64/Game.exe" \
  -logFile "$PWD/Logs/build-win64.log"
```

- Always pass `-activeBuildProfile` or `-buildTarget` on the command line. Switching the target
  from inside the script recompiles assemblies mid-run, and `#if` code compiles for the old target.
- One target per invocation. Script defines from `-activeBuildProfile` apply before
  `-executeMethod` runs.
- `-build` with `-buildTarget` or `-activeBuildProfile` builds without a script, like the Build
  button. Prefer the script: it sets the output path and fails the process on a failed build.
- IL2CPP strips unused code. Types reached only through reflection or `[SerializeReference]` need
  `[Preserve]` or a `link.xml` entry, or the player throws where the editor worked.
- Profile builds: `BuildOptions.Development | BuildOptions.ConnectWithProfiler`. Never ship them.
- A packaged build is part of the first milestone and every milestone after. Stripping, missing
  scene-list entries and shader variants fail only in players.

## CI

- GitHub Actions: GameCI (`game-ci/unity-test-runner`, `game-ci/unity-builder`) on Linux runners
  for tests and non-Apple targets; a self-hosted macOS runner for macOS and iOS builds.
- License activation is a secret (serial, or a license file); never commit it.
- Cache `Library/` keyed on `ProjectSettings/ProjectVersion.txt` and `Packages/packages-lock.json`;
  a cold import dominates CI time.
- Order: compile, EditMode, data validator, PlayMode, build, then a smoke run of the built player
  with a self-play argument (`Game.app/Contents/MacOS/Game -batchmode -autoplay -seed 1 -logFile -`)
  that the game parses with `Environment.GetCommandLineArgs()` and exits non-zero on failure.

## Unity MCP

Unity's official MCP server ships in the AI Assistant package. It needs Unity 6, the
`com.unity.ai.assistant` package, a project linked to Unity Cloud, and Unity AI access on the
account.

1. Project Settings > AI > Unity MCP: Unity Bridge shows Running (start it if stopped). On startup
   Unity installs the relay to `~/.unity/relay/`.
2. Configure the client. The Integrations section of that settings page can do it; manually, for
   Claude Code on Apple silicon (`.mcp.json` in the project root):

   ```json
   {
     "mcpServers": {
       "unity-mcp": {
         "command": "/Users/<user>/.unity/relay/relay_mac_arm64.app/Contents/MacOS/relay_mac_arm64",
         "args": ["--mcp", "--project-path", "/Users/<user>/Projects/<Game>"]
       }
     }
   }
   ```

   Write the absolute home path; clients may not expand `~`. Intel Macs use
   `relay_mac_x64.app/Contents/MacOS/relay_mac_x64`; Windows `%USERPROFILE%\.unity\relay\relay_win.exe`;
   Linux `~/.unity/relay/relay_linux`. `--project-path` (or `--instance-id <pid>`) pins the relay
   to one editor when several are open; without it, it connects to the first it finds.
3. Accept the client under Pending Connections on the same settings page. Tools are unavailable
   until then; approved clients reconnect automatically.
4. Check: list the tools, then read the console (`Unity_ReadConsole`). Scene and object work go
   through tools such as `Unity_ManageScene` and `Unity_ManageGameObject`.

Record every tool name, argument shape and quirk that worked in `docs/MCP_TOOLS.md`, marking each
needed capability as available or missing: console read, asset refresh and compile, scene open and
save, hierarchy query, component get and set, prefab edit, menu item execution, Play Mode start and
stop, screenshot, test run. A community Unity MCP server follows the same workflow with different
tool names.

| Situation | Channel |
|---|---|
| Editor open, iterative change | MCP: refresh, console, tests through a tool or the `Tools/Agent` menu items, hierarchy checks |
| Editor closed, full pass, CI | Batch mode CLI |
| Player build | Batch mode CLI with the editor closed |
| Scene or prefab edit | MCP tools, or an editor script run as a menu item; never YAML on disk while the editor has it open |
| Feel, readability, audio | A human, asked a specific question |

MCP etiquette:

- Read, change one thing, read back. Anything that is not an explicit success is a stop.
- Serialize mutations to the same scene or asset; keep each change small enough to undo.
- Stop Play Mode before editing assets; edits made in Play Mode to scene objects are discarded.
- Results may be text rather than JSON. Parse defensively.
- One writer per editor. A second agent gets its own clone and its own editor.
- After a script change the domain reloads and the bridge may drop calls for a few seconds. Retry
  once the console shows compilation finished.

## The verification loop

For each change against a live editor:

1. Edit C# on disk.
2. Refresh: an MCP refresh or compile tool, or a `Tools/Agent/Refresh` menu item that calls
   `AssetDatabase.Refresh()`. Wait for compilation to finish.
3. Console: zero errors; compare warnings with the session's starting baseline.
4. Tests: EditMode through the `Tools/Agent` menu item; PlayMode as well when lifecycle, physics,
   input or wiring changed. Read the `AGENT TESTS` line.
5. Scene changes: query the hierarchy and the changed component values; confirm by reading back.
6. Visual changes: capture the Game view and read the image at full size.
7. Save scenes and prefabs; confirm with `git status` that the expected files changed and no
   `.meta` GUID did.

Without MCP the loop is the same with the editor closed: batch EditMode run, batch PlayMode run,
result parsing, and the build for anything that touches content or stripping.
