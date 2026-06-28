# Ebitengine Ecosystem Tooling

Ebitengine is intentionally small. Add libraries when they remove real complexity or match an existing project pattern. For prototypes and small games, prefer plain Go code plus Ebitengine APIs.

## Dependency Rule

Before adding a library:

1. Check whether the repository already has a preferred tool.
2. Confirm the feature is large enough to justify a dependency.
3. Prefer maintained libraries with examples, tags, and active issue history.
4. Keep third-party types at package boundaries so they can be replaced later.
5. Add focused tests around adapters, parsers, and data transformations.

## UI And Menus

Default: build simple HUDs and menus directly with Ebitengine drawing and input.

Use `ebitenui` when the project needs retained-mode widgets, complex menus, settings screens, inventories, scroll panes, or desktop-style controls.

Use `ebiten-imgui` for developer tooling, debug inspectors, editors, profiling panels, or internal builds. Avoid shipping immediate-mode debug UI as the main player-facing interface unless the project already does so.

Gotchas:

- Build widget trees during initialization, not each `Update`.
- Keep UI callbacks small; they should change app state or send commands, not implement large gameplay rules.
- For resolution-independent UI, centralize scaling and layout assumptions.

## Scenes And Screens

Default: use a small project-local `Scene` interface or enum state machine.

Use `stagehand` when the game has many screens, typed transitions, or shared transition state that would otherwise become repetitive.

Good scene boundaries:

- Title/menu
- Gameplay
- Pause/options
- Editor/tooling mode
- Game over/results

Keep long-lived services such as assets, audio, settings, saves, and telemetry outside individual scenes.

## Entity Systems

Default: use structs and slices.

Use `donburi` when entity composition and system iteration are central to the design, or when profiling shows many heterogeneous entities are hard to manage with plain structs.

Use a simpler ECS or project-local component model only if the codebase already uses one or the domain is small enough to keep it obvious.

Gotchas:

- Do not introduce ECS to solve a naming or package-organization problem.
- Hide ECS queries behind game package methods when rendering or input does not need to know the storage model.
- Use bulk creation APIs when spawning many homogeneous entities if the chosen ECS supports it.

## Collision And Physics

Default: use simple AABB, circle, grid, or tile collision implemented in pure Go.

Use `resolv` for deterministic arcade-style collision, spatial hashing, platformers, top-down games, and many axis-aligned objects.

Use a Chipmunk2D binding such as `cp` only when real rigid-body behavior matters: mass, elasticity, impulses, joints, friction, or complex body interactions.

Gotchas:

- Tune spatial cell sizes around average entity or tile dimensions.
- Keep physics units and screen pixels explicitly mapped.
- Test collision rules with table-driven Go tests.

## Tile Maps And Level Data

Default: parse the project's own JSON, CSV, or text format when levels are simple.

Use `ldtk-go` for LDtk projects with layers, entities, enums, and editor-authored metadata.

Use `go-tiled` for Tiled/TMX maps.

Gotchas:

- Convert editor data into runtime-friendly structs during loading.
- Composite static tile layers into offscreen images when they do not change.
- Keep collision data separate from visual tile layers.
- Validate map data at load time with useful errors for missing layers, unknown tiles, and invalid entity fields.

## Animation

Default: represent simple animations as frame indices, durations, and sprite-sheet rectangles.

Use `goaseprite` when the pipeline is built around Aseprite JSON, tags, slices, or animation events.

Use tweening libraries such as `gween` for value interpolation, UI easing, camera motion, and non-skeletal animation.

Gotchas:

- Advance animation by ticks or accumulated time in `Update`, not `Draw`.
- Keep animation state separate from immutable animation definitions.
- Prefer named animations and tags over hard-coded frame numbers in gameplay code.

## Particles And Effects

Default: write a small particle system with preallocated slices.

Use a library only when it matches the art pipeline or when designers need external authoring. For many games, particles are simple enough to own locally.

Gotchas:

- Avoid allocating particles with `append` in every frame after warm-up.
- Store particle state in compact structs.
- Batch draws by sprite and blend mode where possible.

## Debugging And Profiling

Use built-in Go tooling first:

```bash
go test ./...
go test -run TestName ./internal/game
go test -bench=. ./...
go test -cpuprofile cpu.out -memprofile mem.out ./...
```

Use Ebitengine debug overlays or project-local debug screens for FPS, TPS, entity counts, draw counts, and scene state.

Use `ebiten-imgui` or a custom debug console when runtime inspection meaningfully improves iteration.

## Asset Pipelines

Use source assets that are easy to edit and generated assets that are easy to load.

Recommended pattern:

- Store editable source files under `assets_src/` or tool-specific directories.
- Generate runtime atlases, JSON, or packed data into `assets/`.
- Embed only runtime assets.
- Document generation commands in `README.md`, `Makefile`, `Taskfile.yml`, or `justfile` if the project has one.

Gotchas:

- Generated assets should be deterministic.
- Do not require a proprietary editor at build time unless the project explicitly depends on it.
- Validate atlas frame names and map entity names during loading.
