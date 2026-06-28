---
name: ebitengine
description: Develop, refactor, test, and ship Go projects using Ebitengine/Ebiten. Use for 2D games, game loops, sprites, tile maps, input, audio, UI, simulations, visualizers, tools, WebAssembly builds, mobile or desktop releases, and architecture decisions around Ebitengine.
compatibility: Portable Agent Skills format for coding agents including Claude, Gemini, Grok, Codex, Manus, and other model-neutral clients.
---

# Ebitengine Development

Use this skill when the user asks about Ebitengine, Ebiten, Go game development, real-time 2D rendering, interactive simulations, visual tools, or cross-platform apps built on Ebitengine.

## Default Workflow

1. Inspect the existing Go module, package layout, build tags, assets, and tests before proposing changes.
2. Keep the `ebiten.Game` implementation thin: `Update` collects input and advances state, `Draw` renders current state, and `Layout` returns logical screen dimensions.
3. Put game rules, simulation, scoring, AI, collision math, and save data in ordinary Go packages that can be tested without opening a window.
4. Prefer simple structs, slices, and interfaces first. Add scene managers, ECS, physics libraries, or UI frameworks only when the project size or feature set justifies them.
5. Validate with `go test ./...`. For rendering, input, or deployment changes, also run the narrowest practical build or smoke test for the target platform.

## Must-Follow Ebitengine Rules

- Do not mutate game state in `Draw`. Rendering should be repeatable from the current state.
- Do not do file I/O, network I/O, image decoding, or audio decoding in the hot path unless the existing project already has a deliberate async loading system.
- Use `//go:embed` for assets that must work in desktop, WebAssembly, mobile, or single-binary releases.
- Treat `ebiten.Image` as a GPU resource. Avoid `At`, frequent `ReplacePixels`, and per-frame image creation in gameplay loops.
- Group draw calls by source image, blend mode, filter, and render target when practical so Ebitengine can batch them.
- Map hardware input to semantic intent before applying gameplay logic. Prefer `inpututil` for just-pressed and just-released events.
- Stream long music and keep short sound effects preloaded. Manage audio player lifetimes explicitly.
- Keep logical resolution separate from window size. Use `Layout` for stable coordinates and scale intentionally.
- Use fixed-tick logic unless the project has a clear reason for variable timestep behavior.
- Add tests around pure Go state transitions, collision rules, deterministic generation, save/load logic, and data parsers.

## Project Setup Defaults

For a new project, use a Go module and Ebitengine v2:

```bash
go mod init example.com/my-game
go get github.com/hajimehoshi/ebiten/v2
```

Prefer this package shape unless the existing repository has a stronger convention:

```text
cmd/game/              # main package, window setup, RunGame
internal/app/          # ebiten.Game wrapper and scene orchestration
internal/game/         # pure gameplay state and rules
internal/input/        # hardware-to-intent mapping
internal/render/       # drawing helpers and asset-backed renderers
internal/assets/       # embed.FS and loading functions
```

## Reference Routing

- Read [architecture patterns](references/architecture_patterns.md) when creating a new project, refactoring structure, adding scenes, separating logic from rendering, introducing ECS, or designing tests.
- Read [API cheat sheet](references/api_cheatsheet.md) when writing Ebitengine code for drawing, input, text, audio, assets, transforms, or common API calls.
- Read [ecosystem tooling](references/ecosystem_tooling.md) before adding UI, scene, ECS, collision, map, animation, particles, debugging, or asset-pipeline dependencies.
- Read [deployment guide](references/deployment_guide.md) when building for desktop, WebAssembly, mobile, Steam, release packaging, or platform-specific smoke tests.

## Templates and Scripts

Use bundled scaffolding instead of regenerating project layout or wasm packaging from memory.

- **Run** `scripts/new_project.py` when creating a new Ebitengine project. Prefer this over hand-assembling packages.
  - Example: `python scripts/new_project.py --out ./my-game --name "My Game" --module example.com/my-game`
- **Read** files under `templates/` when adding a missing package or matching the canonical layout (`cmd/game`, `internal/app`, `internal/game`, `internal/assets`, `internal/input`, `internal/render`).
- **Run** `scripts/build_wasm.sh` or `scripts/build_wasm.ps1` for WebAssembly builds. This copies `wasm_exec.js` from the correct Go toolchain path (Go 1.24+ uses `lib/wasm`).
- **Run** `scripts/release.sh` or `scripts/release.ps1` for multi-target desktop release builds.

On Windows, use the `.ps1` scripts. On Linux and macOS, use the `.sh` scripts. Run scripts from the skill directory or pass the user's project path as the first argument.

Do not read script source into context unless debugging the skill itself; execute scripts and use their output.

## Review Checklist

Before finalizing Ebitengine work, check:

- `Update`, `Draw`, and `Layout` responsibilities are separated.
- Hot paths avoid allocation, decoding, blocking I/O, and CPU/GPU synchronization.
- Asset loading returns useful errors and works from embedded files where portability matters.
- Input code supports the requested devices without leaking key names into gameplay rules.
- Tests cover pure logic and parsers; graphical behavior has at least a build or smoke-test path.
- New dependencies are justified by project complexity and documented in Go module files.
