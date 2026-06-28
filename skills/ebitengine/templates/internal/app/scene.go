package app

import (
	"github.com/hajimehoshi/ebiten/v2"

	"{{MODULE_PATH}}/internal/game"
	"{{MODULE_PATH}}/internal/input"
)

// Scene is an optional abstraction for distinct app modes.
type Scene interface {
	Update(game.Intent) (Scene, error)
	Draw(*ebiten.Image)
}

// SceneGame wraps the default single-scene flow when a full scene manager is not needed yet.
type SceneGame struct {
	state *game.State
	input *input.Mapper
}

func NewSceneGame(state *game.State) *SceneGame {
	return &SceneGame{state: state, input: input.NewMapper()}
}

func (s *SceneGame) Update() game.Intent {
	return s.input.Poll()
}

func (s *SceneGame) Tick(intent game.Intent) {
	s.state.Tick(intent)
}

func (s *SceneGame) Snapshot() game.Snapshot {
	return s.state.Snapshot()
}
