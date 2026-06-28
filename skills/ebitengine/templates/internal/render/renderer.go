package render

import (
	"fmt"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"

	"{{MODULE_PATH}}/internal/assets"
	"{{MODULE_PATH}}/internal/game"
)

type Renderer struct {
	store *assets.Store
}

func NewRenderer(store *assets.Store) *Renderer {
	return &Renderer{store: store}
}

func (r *Renderer) Draw(screen *ebiten.Image, snap game.Snapshot) {
	_ = r.store

	ebitenutil.DrawCircle(screen, float64(snap.PlayerX), float64(snap.PlayerY), 12, color.RGBA{R: 180, G: 60, B: 60, A: 255})
	ebitenutil.DebugPrint(screen, fmt.Sprintf("{{PROJECT_NAME}}  score: %d", snap.Score))
}
