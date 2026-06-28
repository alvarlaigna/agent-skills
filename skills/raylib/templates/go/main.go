package main

import (
	rl "github.com/gen2brain/raylib-go/raylib"
)

// For web builds, standard raylib-go cannot target wasm via CGO.
// Use the Raylib-Go-Wasm fork and rl.SetMainLoop(update) instead of the loop below.
// See references/deployment_guide.md.

const (
	screenWidth  = 800
	screenHeight = 450
)

func updateDrawFrame() {
	dt := rl.GetFrameTime()
	_ = dt

	rl.BeginDrawing()
	rl.ClearBackground(rl.RayWhite)
	rl.DrawText("{{PROJECT_NAME}} - by Alvar Laigna", 190, 200, 20, rl.LightGray)
	rl.DrawFPS(10, 10)
	rl.EndDrawing()
}

func main() {
	rl.InitWindow(screenWidth, screenHeight, "{{PROJECT_NAME}} - by Alvar Laigna")
	defer rl.CloseWindow()

	rl.SetTargetFPS(60)

	for !rl.WindowShouldClose() {
		updateDrawFrame()
	}
}
