package app

import (
	"github.com/hajimehoshi/ebiten/v2"

	"{{MODULE_PATH}}/internal/assets"
	"{{MODULE_PATH}}/internal/game"
	"{{MODULE_PATH}}/internal/render"
)

// Scene is an optional abstraction for distinct app modes.
type Scene interface {
	Update(game.Intent) (Scene, error)
	Draw(*ebiten.Image)
}

// SceneGame wraps the default single-scene flow when a full scene manager is not needed yet.
type SceneGame struct {
	state    *game.State
	renderer *render.Renderer
}

// Compile-time check that *SceneGame satisfies the Scene interface.
var _ Scene = (*SceneGame)(nil)

func NewSceneGame(state *game.State, store *assets.Store) *SceneGame {
	return &SceneGame{state: state, renderer: render.NewRenderer(store)}
}

// Update advances the game state with the given intent and returns the next scene.
// The default flow stays on the same scene.
func (s *SceneGame) Update(intent game.Intent) (Scene, error) {
	s.state.Tick(intent)
	return s, nil
}

// Draw renders the current game state to the screen.
func (s *SceneGame) Draw(screen *ebiten.Image) {
	s.renderer.Draw(screen, s.state.Snapshot())
}
