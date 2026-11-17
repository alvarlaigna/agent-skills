# Testing

An agent cannot hold a controller, watch motion, or hear. Testing makes the game prove itself in
numbers, pictures and logs, and saves human attention for what only a human can judge.

## Contents

- The ladder
- Self-play mode
- Shot runs and pictures
- Real input
- Determinism
- Measuring performance
- How tests lie
- Human playtests

## The ladder

| Level | What | Cost |
|---|---|---|
| 1 | Plain C++ rule tests (no engine) | Seconds |
| 2 | Automation tests in the editor or headless (`ue.py test`) | A minute |
| 3 | Data validation: counts, references, reachability, ranges (a validator script or commandlet) | Seconds |
| 4 | Scripted PIE through the real input path | Minutes |
| 5 | Self-play in the packaged build: state log, screenshots, timings | Minutes |
| 6 | Packaged web build in a headless browser, at several core counts | Minutes |
| 7 | Human playtest of the packaged build | A person's time |

Each level catches what the one below cannot. A build reaches a human only after levels 1 to 6
pass on that build.

## Self-play mode

Give the game a command-line switch that makes it play itself:

```cpp
const bool bAutoPlay = FParse::Param(FCommandLine::Get(), TEXT("AutoPlay"));
int32 Seed = 1;
FParse::Value(FCommandLine::Get(), TEXT("Seed="), Seed);
```

In that mode the game:

- starts from default settings and saves none (a leftover resolution or quality choice changes
  results);
- answers its own menus, plays a fixed script or a simple autopilot from a seed;
- writes one log line per event with a fixed prefix (`AUTOPLAY PASS <name>` / `AUTOPLAY FAIL <name>
  <reason>`), and fails the run on any failure;
- saves a screenshot at named moments (`FScreenshotRequest::RequestScreenshot`) and records frame
  times;
- quits when done (`FGenericPlatformMisc::RequestExit(false)`).

Run it in the packaged build at a fixed window size (`-windowed -ResX=1920 -ResY=1080`).
A Development build can also host the MCP server with its runtime tools (input, console, scene
capture, performance), so an agent can drive the packaged game directly; never in a release build
(see [modern engine](modern-engine.md#testing-and-validation)). It also
records trailer footage and covers for when the PC is locked or nobody is at the desk.

A test that flies with the autopilot also tests the autopilot. When the autopilot changes, a
"pass" may only mean it now avoids the case under test (a crash test whose autopilot learned to
brake). Keep tests that need a specific situation scripted, not autopiloted.

## Shot runs and pictures

- A "shot run" flies a camera to a fixed list of views, saves a picture at each, and quits. Run it
  before and after a visual change and compare.
- Read each picture at full size and write a one-line verdict. Empty text, overlap, wrong
  material, z-fighting and missing lights are only visible there.
- Look at the source files of generated assets, not only renders: a texture atlas made of
  hundreds of tiny islands looks fine in a small render and smeared up close.
- Stills cannot show anything that alternates between frames (a bone that jumps every other
  frame, flicker, popping). Capture short frame sequences and compare consecutive frames, or count
  pixels that flip and flip back.

## Real input

- Inject input through the same input actions a player uses. Calling the gameplay function
  directly skips mapping contexts, focus, UI capture and key conflicts.
- Click into the game window in browser builds; keyboard focus is not automatic.
- At least once per build, a human presses every key the tutorial mentions.

## Determinism

- Fix the physics step (for example 1/60 s substepping) and apply every gameplay input that
  affects physics on the physics step, not on a game frame. A brake released on a frame boundary
  shifts a run by centimetres at a different frame rate.
- Physics is not bit-exact across frame rates. Design pass/fail rules with margin (no goal 7 cm
  from an edge) and test each solution at several frame rates.
- Gate releases on a repeat check: the same solution, 20 runs, the same player-visible result.

## Measuring performance

- Measure before fixing. Add timing lines around suspect systems and read the worst frames, not
  the average: creating thousands of physics bodies in one frame, spawning on chunk boundaries,
  synchronous loads.
- `stat unit`, `stat gpu`, Unreal Insights or the CSV profiler for detail; self-play frame-time
  logs for trends across builds.
- Cap the frame rate in every build. An uncapped game can drive a GPU at full power until the
  driver resets the device; with a cap the same scene ran cool for days.
- Measure on a quiet machine. Eight game instances on one GPU measure nothing.
- When the GPU or the game crashes, open the crash dump or the GPU crash report before theorising.

## How tests lie

Every one of these passed while the game was broken:

- **The test set the state itself.** The bot set a flag or a start time directly, so it never
  went through the step a player depends on (a hint clock that never started in real play; items
  reachable only by a route the bot skipped).
- **A cheap signal stood in for the real one.** A cursor flag for a visible cursor, a still for
  motion, a render for a texture atlas, "compiled" for "linked and ran".
- **A fallback was a normal outcome.** "No matching voice clip, show text" was allowed, so a data
  file that shrank from 1,200 entries to 23 silenced the town with every test green. Count
  fallbacks and fail above a threshold; guard data counts in the validator.
- **"Load flake."** A failure that passes alone was labelled flaky twice, and twice it was a real
  defect in the test (a clock not reset between tests, a time cap in game seconds at high time
  dilation). Explain every flake before shipping past it.
- **The check never failed.** Break the rule once on purpose and watch the test go red.
- **Nothing checked reachability.** NPCs stacked on one spot, inside buildings or under the floor.
  Add validator rules: every interactable reachable on foot and visible from its camera.
- **AI testers follow the hints.** Agent players and reviewers missed most of what a first-time
  human hit in minutes (too much on screen, a right click opening the browser menu, an empty view
  behind the set). Turn each human finding into a new check.

## Human playtests

- Ask for specific things: "press every key on the first screen", "turn the camera all the way
  round", "listen to the menu music level".
- Record every note as a numbered row with an owner. A note is fixed when the person who reported
  it sees it fixed, from the same spot and camera, in a packaged build.
- A note about one spot is about that spot. Do not turn it into a world-wide sweep; sweeps break
  things that worked.
- Audio, feel, readability and fun are human judgements. Say plainly which results are machine
  measurements only.
