package app

import (
	"github.com/hajimehoshi/ebiten/v2"

	"{{MODULE_PATH}}/internal/assets"
	"{{MODULE_PATH}}/internal/game"
	"{{MODULE_PATH}}/internal/input"
	"{{MODULE_PATH}}/internal/render"
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
