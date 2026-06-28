# Ebitengine Architecture Patterns

Ebitengine gives you a small loop and few opinions. Good architecture comes from keeping rendering, platform input, asset loading, and game rules in separate Go packages.

## Recommended Package Layout

Start with ordinary Go packages. Rename directories to match the repository's conventions when working in an existing project.

```text
my-game/
├── cmd/game/
│   └── main.go              # Window setup, dependency wiring, ebiten.RunGame
├── internal/app/
│   └── game.go              # Implements ebiten.Game
├── internal/game/
│   ├── state.go             # Pure state and simulation rules
│   └── state_test.go        # Fast deterministic tests
├── internal/input/
│   └── mapper.go            # Hardware input to semantic intent
├── internal/render/
│   └── renderer.go          # Converts state snapshots to draw calls
├── internal/assets/
│   └── assets.go            # embed.FS, image/audio/font loaders
└── go.mod
```

Use `pkg/` only for packages meant to be imported by other modules. Keep game-specific code under `internal/`.

## Entry Point

`main` should configure the process and start the engine. It should not contain game rules.

```go
package main

import (
	"log"

	"github.com/hajimehoshi/ebiten/v2"

	"example.com/my-game/internal/app"
	"example.com/my-game/internal/assets"
	"example.com/my-game/internal/game"
)

func main() {
	store, err := assets.Load()
	if err != nil {
		log.Fatalf("load assets: %v", err)
	}

	ebiten.SetWindowSize(1280, 720)
	ebiten.SetWindowTitle("My Game")
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)

	if err := ebiten.RunGame(app.New(game.NewState(), store)); err != nil {
		log.Fatalf("run game: %v", err)
	}
}
```

## Engine Wrapper

The `ebiten.Game` implementation adapts platform concerns to pure game code.

```go
package app

import (
	"github.com/hajimehoshi/ebiten/v2"

	"example.com/my-game/internal/assets"
	"example.com/my-game/internal/game"
	"example.com/my-game/internal/input"
	"example.com/my-game/internal/render"
)

type Game struct {
	state    *game.State
	input    *input.Mapper
	renderer *render.Renderer
}

func New(state *game.State, store *assets.Store) *Game {
	return &Game{
		state:    state,
		input:    input.NewMapper(),
		renderer: render.NewRenderer(store),
	}
}

func (g *Game) Update() error {
	intent := g.input.Poll()
	g.state.Tick(intent)
	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	g.renderer.Draw(screen, g.state.Snapshot())
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return 640, 360
}
```

## Pure Game State

Keep core state free of Ebitengine imports. This makes game rules easy to test and reuse.

```go
package game

type Intent struct {
	MoveX  int
	MoveY  int
	Action bool
}

type State struct {
	playerX int
	playerY int
	score   int
}

func NewState() *State {
	return &State{playerX: 100, playerY: 100}
}

func (s *State) Tick(intent Intent) {
	s.playerX += intent.MoveX * 2
	s.playerY += intent.MoveY * 2
}

type Snapshot struct {
	PlayerX int
	PlayerY int
	Score   int
}

func (s *State) Snapshot() Snapshot {
	return Snapshot{PlayerX: s.playerX, PlayerY: s.playerY, Score: s.score}
}
```

## Scene And State Flow

Use a scene abstraction when the app has distinct modes such as title screen, gameplay, pause, editor, or results.

```go
type Scene interface {
	Update(input.Intent) (Scene, error)
	Draw(*ebiten.Image)
}
```

Return the next scene from `Update` when a transition happens. Keep shared resources, save data, and settings outside individual scenes so transitions do not duplicate ownership.

For very small games, a typed enum plus `switch` in `State.Tick` is often simpler than a full scene framework.

## Entity Modeling

Start with plain structs:

```go
type Enemy struct {
	Pos Vec2
	Vel Vec2
	HP  int
}
```

Prefer slices of concrete types for small and medium games. Introduce an ECS only when one of these is true:

- Many systems operate over thousands of entities.
- Entity composition changes often at runtime.
- Profiling shows struct traversal or branching is a real bottleneck.
- The project already uses an ECS consistently.

When using an ECS, hide it behind game package methods so rendering and input code do not depend on ECS internals.

## Fixed-Tick Simulation

Ebitengine calls `Update` at a fixed ticks-per-second rate by default. Use integer ticks or fixed-step math for gameplay, cooldowns, animation state, and deterministic systems.

Use variable delta time only for visual interpolation or when integrating with an external system that requires it. Do not mix variable timestep physics into fixed-tick gameplay without a clear reason.

## Input Boundary

Map keyboard, mouse, touch, and gamepad state to semantic intent:

```go
type Intent struct {
	MoveX int
	MoveY int
	Jump  bool
	Menu  bool
}
```

Gameplay code should ask whether the player wants to jump, not whether `Space` was pressed. This keeps controls remappable and allows multiple input devices.

## Rendering Boundary

Renderers should consume snapshots or read-only views of state. Avoid exposing mutable game state to drawing helpers.

Good renderer responsibilities:

- Choose sprite regions and draw options.
- Convert world coordinates to screen coordinates.
- Draw debug overlays when enabled.
- Sort draw commands if the game needs layering.

Avoid in renderers:

- Changing health, score, AI, inventory, or physics.
- Loading assets in `Draw`.
- Creating temporary images every frame.

## Testing Strategy

Write regular Go tests for pure packages:

- `Tick` state transitions and win/loss conditions.
- Collision resolution and spatial queries.
- Procedural generation with fixed seeds.
- Save/load migrations and validation.
- Map, sprite atlas, animation, and config parsing.

Example:

```go
func TestPlayerMovesRight(t *testing.T) {
	state := NewState()
	state.Tick(Intent{MoveX: 1})

	if got, want := state.Snapshot().PlayerX, 102; got != want {
		t.Fatalf("PlayerX = %d, want %d", got, want)
	}
}
```

Use Ebitengine-level smoke tests sparingly. Most confidence should come from pure logic tests plus target-platform builds.

## Performance Shape

Design around the hot path:

- Load and decode assets before gameplay or during explicit loading screens.
- Reuse `DrawImageOptions` values or allocate them outside tight loops when profiling shows pressure.
- Composite static tile layers, backgrounds, and generated art to offscreen images once.
- Keep particle systems and animations data-oriented when entity counts grow.
- Profile before adding complex abstractions.
