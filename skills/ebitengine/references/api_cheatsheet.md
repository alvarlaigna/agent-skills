# Ebitengine API Cheat Sheet

Use this file for common Ebitengine v2 APIs and gotchas. Prefer the project's existing wrappers when they exist.

## Game Loop

```go
import "github.com/hajimehoshi/ebiten/v2"

type Game struct{}

func (g *Game) Update() error {
	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return 640, 360
}
```

Configure the window before `ebiten.RunGame`:

```go
ebiten.SetWindowSize(1280, 720)
ebiten.SetWindowTitle("My Game")
ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)

if err := ebiten.RunGame(game); err != nil {
	return fmt.Errorf("run game: %w", err)
}
```

## Images And Drawing

```go
img := ebiten.NewImage(width, height)
img.Fill(color.RGBA{R: 20, G: 20, B: 24, A: 255})

op := &ebiten.DrawImageOptions{}
op.GeoM.Scale(scaleX, scaleY)
op.GeoM.Rotate(angleRadians)
op.GeoM.Translate(x, y)
screen.DrawImage(img, op)
```

Transform order matters. Ebitengine applies transforms in the order you call them. For sprite drawing, scale or rotate around the origin first, then translate into world or screen position.

Rotate around a sprite center:

```go
op := &ebiten.DrawImageOptions{}
op.GeoM.Translate(-float64(w)/2, -float64(h)/2)
op.GeoM.Rotate(angleRadians)
op.GeoM.Translate(x+float64(w)/2, y+float64(h)/2)
screen.DrawImage(sprite, op)
```

Use `SubImage` for sprite sheets:

```go
rect := image.Rect(frameX, frameY, frameX+frameW, frameY+frameH)
frame := spriteSheet.SubImage(rect).(*ebiten.Image)
screen.DrawImage(frame, op)
```

Gotchas:

- Avoid creating `ebiten.Image` values every frame.
- Avoid `Image.At` and frequent `ReplacePixels` during gameplay; they can synchronize CPU and GPU work.
- Reuse `DrawImageOptions` only after resetting it. A stale `GeoM`, `ColorScale`, filter, or composite mode causes subtle draw bugs.
- Draw static tile layers, large backgrounds, or generated visuals to an offscreen image once, then draw that image each frame.

## Vector Drawing

```go
import "github.com/hajimehoshi/ebiten/v2/vector"

vector.FillRect(screen, x, y, width, height, clr, false)
vector.StrokeRect(screen, x, y, width, height, strokeWidth, clr, false)
vector.FillCircle(screen, cx, cy, radius, clr, false)
vector.StrokeLine(screen, x1, y1, x2, y2, strokeWidth, clr, false)
```

Use vector drawing for UI, debug overlays, simple effects, and prototypes. For large repeated shapes, consider pre-rendering to an image.

## Input

```go
import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
)

leftHeld := ebiten.IsKeyPressed(ebiten.KeyArrowLeft)
jumpPressed := inpututil.IsKeyJustPressed(ebiten.KeySpace)
jumpReleased := inpututil.IsKeyJustReleased(ebiten.KeySpace)

mx, my := ebiten.CursorPosition()
mousePressed := inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft)
```

Use held-state APIs for continuous movement. Use `inpututil` for menus, actions, toggles, and single-fire events.

Gamepad patterns:

```go
ids := ebiten.AppendGamepadIDs(nil)
for _, id := range ids {
	if ebiten.IsGamepadButtonPressed(id, ebiten.GamepadButton0) {
		// Map to semantic intent.
	}
	x := ebiten.GamepadAxisValue(id, 0)
	_ = x
}
```

Add dead zones for analog sticks before applying movement.

## Text

Prefer `text/v2` for new code:

```go
import "github.com/hajimehoshi/ebiten/v2/text/v2"

op := &text.DrawOptions{}
op.GeoM.Translate(x, y)
op.ColorScale.ScaleWithColor(color.White)
text.Draw(screen, "Score: 100", face, op)
```

Use debug print only for temporary diagnostics:

```go
import "github.com/hajimehoshi/ebiten/v2/ebitenutil"

ebitenutil.DebugPrintAt(screen, "debug", 8, 8)
```

Keep font loading in asset setup, not in `Draw`.

## Embedded Assets

```go
package assets

import (
	"embed"
	"fmt"
	"image"
	_ "image/png"

	"github.com/hajimehoshi/ebiten/v2"
)

//go:embed images/*.png
var files embed.FS

func LoadImage(path string) (*ebiten.Image, error) {
	f, err := files.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	img, _, err := image.Decode(f)
	if err != nil {
		return nil, fmt.Errorf("decode %s: %w", path, err)
	}

	return ebiten.NewImageFromImage(img), nil
}
```

Gotchas:

- Blank-import image decoders (`_ "image/png"`, `_ "image/jpeg"`) required by the asset types.
- Return errors from loaders. Do not ignore failed opens or decodes.
- Asset paths in `embed.FS` use forward slashes.
- Embedded assets are usually best for WASM, mobile, and single-binary desktop releases.

## Audio

```go
import "github.com/hajimehoshi/ebiten/v2/audio"

const sampleRate = 44100

audioContext := audio.NewContext(sampleRate)
player := audioContext.NewPlayerFromBytes(soundBytes)
player.Play()
```

For short sound effects, keep encoded or decoded bytes in memory and create/reuse players deliberately. For music, stream through a decoder and loop it instead of loading a whole long track into memory.

Typical BGM shape:

```go
stream := audio.NewInfiniteLoop(decodedStream, decodedStream.Length())
player, err := audioContext.NewPlayer(stream)
if err != nil {
	return fmt.Errorf("create music player: %w", err)
}
player.Play()
```

Gotchas:

- Keep the `audio.Context` alive for the lifetime of the app.
- Keep music streams and players referenced; losing references can stop playback or prevent control.
- Browsers may require a user gesture before audio can start.
- Close players when they are no longer needed.

## Build Tags And Platform Checks

Use build tags to isolate platform-specific code:

```go
//go:build js && wasm

package platform
```

Keep platform files small. Put most behavior behind interfaces so gameplay code stays portable.
