# C++ architecture for agent-built games

Code an agent can write, review, test, and rebuild without opening graphs.

## Contents

- Module layout
- Reflection rules
- Constructors and the CDO
- Thin Blueprints, data in files
- Where state lives
- Events, timers, Tick
- UI from C++
- Input
- Logging
- Automation tests

## Module layout

```
Source/<Game>/
├── <Game>.Build.cs
├── Core/          # GameMode, GameState, PlayerController, Character, settings
├── Systems/       # subsystems: scoring, audio, save, director, spawning
├── Actors/        # interactables, props, slots, pickups
├── UI/            # HUD and widgets built from C++
├── Rules/         # plain C++: no UObject, no engine types where avoidable
└── Tests/         # automation tests (WITH_DEV_AUTOMATION_TESTS)
```

Keep game rules (scoring, turn resolution, puzzles, procedural generation) in plain C++ structs
and functions under `Rules/`. They compile in seconds, test without a world, and replay
deterministically from a seed. Some teams add a tiny standalone test runner for this folder
(a plain compiler, no Unreal) so rule tests run in two seconds instead of a full editor build.

Add module dependencies in `Build.cs` deliberately (`EnhancedInput`, `UMG`, `Slate`, `SlateCore`,
`Niagara`, `GameplayTags`) and only when used; each one is a restart cycle.

## Reflection rules

- Every `UObject` pointer a class holds is a `UPROPERTY()` (`TObjectPtr<>` in headers) so garbage
  collection sees it. A raw pointer to a `UObject` in a member is a dangling pointer later.
- `EditDefaultsOnly` for tuning on the class, `EditAnywhere` only for per-instance values,
  `BlueprintReadOnly` unless Blueprints must write it, `VisibleAnywhere` for components.
- Interfaces (`UINTERFACE`) for cross-cutting verbs (`IInteractable`, `IItemReceiver`). Avoid cast
  chains between unrelated classes.
- Gameplay Tags instead of `FName` keys or enums for states and categories: typo-proof, editable
  without a recompile, hierarchical matching.
- Any change to reflected declarations needs the restart cycle in
  [the editor loop](editor-loop.md#live-coding-versus-restart). Plan header changes in batches.

## Constructors and the CDO

The constructor runs for the class default object at load and during cooking, with no world.

- Only `CreateDefaultSubobject`, `ConstructorHelpers` lookups and default values belong there.
- No physics calls, no world queries, no spawning, no timers, no `GetWorld()` use. These pass in
  the editor and fail in the cook or crash the packaged game.
- Put runtime setup in `BeginPlay`, `PostInitializeComponents` or `OnConstruction`.

## Thin Blueprints, data in files

- C++ owns behaviour. A Blueprint subclass holds asset references (meshes, sounds, materials),
  tuning values, and nothing else. Re-parenting a thin Blueprint is cheap; rewriting a graph is not.
- Content data (levels of a puzzle, dialogue, item stats, critic rules) lives in CSV or JSON in the
  repo, imported into DataTables or read at startup. One source, diffable, editable by an agent.
- Prefer one explicit rule per C++ function over a generic data schema whose columns change
  meaning per row. A spreadsheet that reuses a column for different meanings breaks silently.
- Soft references (`TSoftObjectPtr`, `TSoftClassPtr`) in data assets for anything large, loaded
  through the Asset Manager. A hard reference loads the whole chain with its owner.

## Where state lives

| Scope | Class |
|---|---|
| One level's session (managers, pools, spatial grids) | `UWorldSubsystem` |
| Across levels (settings, progression, audio mix) | `UGameInstanceSubsystem` |
| Per local player (UI state, input) | `ULocalPlayerSubsystem` |
| Match rules | `AGameModeBase` (server only; hidden in game, so no visuals on it) |
| Replicated or readable match state | `AGameStateBase` |

The GameMode turns into a hub that every agent edits. Keep it a thin coordinator that calls
subsystems, so parallel work touches different files.

## Events, timers, Tick

- Default actors and components to `PrimaryActorTick.bCanEverTick = false`.
- Prefer delegates, timers (`FTimerManager`) and input events. A short repeating timer (0.05 s)
  is enough for most "watch a value" needs.
- When Tick is needed, say why in a comment and keep the work small.
- Cap the frame rate from the first build (`t.MaxFPS`, or `UGameUserSettings::SetFrameRateLimit`).
  An uncapped menu or idle scene can drive a GPU at full power for hours.

## UI from C++

- UMG: a `UUserWidget` subclass in C++ with `meta=(BindWidget)` members, and a thin widget
  Blueprint for layout; or build the widget tree in C++ entirely when the layout is simple. If
  building a widget Blueprint over MCP drags on, build the tree in C++.
- `UCanvas` / HUD text in a packaged build needs a real `UFont` asset. A composite font assembled
  at runtime from font files draws nothing, without an error, outside the editor.
- Measure text with the font it is drawn in. Uppercase titles in a wide display face overflow
  panels sized with the body font.
- Some brush and size setters are ignored depending on widget type (for example a desired-size
  override on a border brush). Verify by screenshot, not by reading the code.

## Input

- Enhanced Input: one `UInputAction` per verb, mapping contexts per mode (menu, play, inspect).
- Never delete and recreate an input action that a mapping context references; the mapping keeps
  a blank entry. Edit it in place.
- Template mapping contexts can claim keys first (A/D in side-scroller templates). Check the
  priority of every context added.
- Tests and self-play should inject input through the same actions a player uses
  (`UEnhancedInputLocalPlayerSubsystem::InjectInputForAction`), not call gameplay functions
  directly. A test that skips the input path proves nothing about input.

## Logging

```cpp
// MyGame.h
DECLARE_LOG_CATEGORY_EXTERN(LogMyGame, Log, All);
// MyGame.cpp
DEFINE_LOG_CATEGORY(LogMyGame);
// use
UE_LOG(LogMyGame, Display, TEXT("Scene %s scored %d"), *SceneId.ToString(), Score);
```

One category per module (or per system). Log checks, self-play reports and reviewers can then
filter the project's own lines out of engine noise.

## Automation tests

```cpp
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScoringBestCutTest, "MyGame.Scoring.BestCutScores100",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FScoringBestCutTest::RunTest(const FString& Parameters)
{
    const FCutResult Result = Scoring::Evaluate(Fixtures::BestCut());
    TestEqual(TEXT("best cut scores 100"), Result.Score, 100);
    return true;
}
#endif
```

- Name tests `<Game>.<Area>.<Case>` so one filter runs the project's suite.
- Run headless with `python scripts/ue.py test --project <dir> --filter <Game>`, or in the open
  editor with the console command `Automation RunTests <Game>`.
- Break the rule under test once on purpose and watch the test fail before trusting it.
- Exhaustive tests are often cheap: nine items have under a million orderings.
- Pin balance numbers (win rates of AI versus AI over N seeded games) in a test so a later change
  cannot shift difficulty unnoticed.
