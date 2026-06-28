package main

import (
	"log"

	"github.com/hajimehoshi/ebiten/v2"

	"{{MODULE_PATH}}/internal/app"
	"{{MODULE_PATH}}/internal/assets"
	"{{MODULE_PATH}}/internal/game"
)

func main() {
	store, err := assets.Load()
	if err != nil {
		log.Fatalf("load assets: %v", err)
	}

	ebiten.SetWindowSize(1280, 720)
	ebiten.SetWindowTitle("{{PROJECT_NAME}}")
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)

	if err := ebiten.RunGame(app.New(game.NewState(), store)); err != nil {
		log.Fatalf("run game: %v", err)
	}
}
