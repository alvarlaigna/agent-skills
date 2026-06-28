# Ebitengine Deployment Guide

Use this guide when preparing Ebitengine apps for desktop, WebAssembly, mobile, Steam, or packaged releases.

## Release Defaults

For most releases:

- Build from a clean working tree or CI job.
- Run `go test ./...` before packaging.
- Embed required runtime assets with `//go:embed` unless the project intentionally supports external mod files.
- Include license files, credits, third-party notices, and platform metadata.
- Smoke test the packaged artifact, not only `go run`.
- Keep debug overlays, profiling servers, and editor-only tools behind build tags or runtime flags.

Common flags:

```bash
go build -trimpath -ldflags="-s -w" ./cmd/game
```

Use `-trimpath` for reproducible paths and `-ldflags="-s -w"` to reduce binary size. Do not strip symbols when debugging crash reports unless the project has another symbol strategy.

## Desktop Builds

Set target OS and architecture explicitly:

```bash
GOOS=windows GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o dist/mygame.exe ./cmd/game
GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o dist/mygame ./cmd/game
GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o dist/mygame ./cmd/game
```

Safe defaults:

- Prefer `CGO_ENABLED=0` when the project and target platform support it.
- Test the binary from its packaged location to catch working-directory and asset assumptions.
- Keep save files and config outside the install directory.
- Log errors to a user-writable location or visible crash report path.

Advanced notes:

- Some integrations, GPU preference helpers, native dialogs, or platform SDKs require Cgo.
- Do not force pure-Go builds if the project depends on native libraries.
- Cross-compiling graphics/audio stacks can expose platform-specific dependencies; CI should build the real targets.

## Windows

Build GUI apps without a console window:

```bash
GOOS=windows GOARCH=amd64 go build -trimpath -ldflags="-s -w -H=windowsgui" -o dist/mygame.exe ./cmd/game
```

Windows checklist:

- Verify window icon, version metadata, and installer metadata if the project ships an installer.
- Test paths with spaces and non-ASCII usernames.
- Keep saves under a user data directory, not beside the executable.
- If using Steamworks or other native DLLs, package the required DLLs beside the executable or in the documented search path.

For Steamworks builds, test launched through Steam, not only by double-clicking the executable.

## macOS

Ship a `.app` bundle for user-facing releases. Minimal layout:

```text
MyGame.app/
└── Contents/
    ├── Info.plist
    ├── MacOS/
    │   └── MyGame
    └── Resources/
        └── AppIcon.icns
```

Universal binary pattern:

```bash
GOOS=darwin GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o build/mygame_amd64 ./cmd/game
GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o build/mygame_arm64 ./cmd/game
lipo -create build/mygame_amd64 build/mygame_arm64 -output MyGame.app/Contents/MacOS/MyGame
```

macOS checklist:

- Include a valid `Info.plist`.
- Code sign release bundles with the appropriate Developer ID.
- Notarize distributed builds when shipping outside the App Store.
- Package notarized apps with `ditto`, not Finder compression, to preserve metadata:

```bash
ditto -c -k --sequesterRsrc --keepParent MyGame.app MyGame_macOS.zip
```

## Linux And Steam Deck

Build and test on a runtime close to the target distribution. For Steam, target the current Valve Steam Runtime used by Steam Deck and Linux Steam clients.

Linux checklist:

- Prefer `linux/amd64` unless the project has a clear reason for additional architectures.
- Test on a clean machine or container with only expected runtime libraries.
- Verify audio works with PulseAudio/PipeWire environments and any ALSA fallback requirements.
- Package `.desktop` files, icons, and launch scripts when distributing outside Steam.
- Avoid assuming case-insensitive file paths.

## WebAssembly

Build:

```bash
GOOS=js GOARCH=wasm go build -trimpath -o dist/main.wasm ./cmd/game
```

Copy the matching `wasm_exec.js` from the Go toolchain. The path depends on the Go version (Go 1.24+ moved support files to `lib/wasm`):

```bash
# Go 1.24 and newer
cp "$(go env GOROOT)/lib/wasm/wasm_exec.js" dist/

# Go 1.23 and older
cp "$(go env GOROOT)/misc/wasm/wasm_exec.js" dist/
```

On Windows PowerShell:

```powershell
$goroot = go env GOROOT
# Go 1.24 and newer
Copy-Item "$goroot\lib\wasm\wasm_exec.js" dist\
# Go 1.23 and older
# Copy-Item "$goroot\misc\wasm\wasm_exec.js" dist\
```

Prefer running `scripts/build_wasm.sh` or `scripts/build_wasm.ps1`, which selects the correct path automatically.

WASM checklist:

- Serve with correct MIME type: `application/wasm`.
- Load assets through `embed.FS` or browser-compatible fetch paths.
- Start audio after a user gesture; browsers often block autoplay.
- Avoid blocking calls that assume a desktop process model.
- Keep download size in mind; compress assets and strip debug data.
- Test in the target browsers, not only a local dev server.

Use build tags for browser-only behavior:

```go
//go:build js && wasm
```

## Mobile

Use Ebitengine's mobile tooling and follow platform store requirements. Mobile builds have stricter constraints around lifecycle, orientation, input, audio focus, permissions, and asset size.

Mobile checklist:

- Treat touch as a first-class input path, not mouse emulation only.
- Handle pause/resume and audio focus changes.
- Keep memory usage lower than desktop targets.
- Test on real devices for performance, thermal behavior, and screen scaling.
- Keep platform-specific code behind build tags or small adapter packages.

## Steam

Steam checklist:

- Launch and test the game through the Steam client.
- Verify overlay, achievements, cloud saves, controller configuration, and language settings if used.
- Test a clean install from `steamapps/common`.
- Keep Steam App ID handling out of pure game logic.
- Package platform-specific native libraries exactly as Steamworks expects.

If using a restart-through-Steam helper, call it early in `main` before initializing game systems.

## Save Data And Config

Do not write saves into embedded assets or installation directories. Use OS-appropriate user data paths. Keep save serialization in pure Go packages so migrations can be tested.

Validate:

- New save creation.
- Loading old saves.
- Corrupt save handling.
- Permission errors.
- Cloud-sync conflict behavior when applicable.

## Release Smoke Test

For each target artifact:

1. Install or unpack the artifact into a fresh directory.
2. Start the app using the same launcher users will use.
3. Reach the main menu or first interactive screen.
4. Verify input, audio, window/fullscreen behavior, and a representative asset-heavy scene.
5. Create and reload save data if the app supports saves.
6. Close and restart the app.
7. Capture logs or crash reports if anything fails.

Document target-specific commands in the repository's existing build script, `Makefile`, `Taskfile.yml`, `justfile`, or CI configuration.
