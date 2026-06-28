# Raylib Architecture & Patterns

## Core Philosophy
Raylib is built on simplicity. It is a highly modular C library without external dependencies. It relies on the paradigm of "spartan programming", providing functions for multimedia without forcing a specific architecture, object-oriented model, or entity-component system (ECS).

## Modular Design
Raylib is organized into self-contained modules, but all functions are exposed via `raylib.h`:
1. `rcore`: Window, context, and input management.
2. `rlgl`: OpenGL wrapper (abstracts OpenGL 1.1, 2.1, 3.3, 4.3, ES 2.0).
3. `rtextures`: Texture and image loading/manipulation.
4. `rshapes`: 2D shapes drawing.
5. `rtext`: Font loading and text drawing.
6. `rmodels`: 3D model loading and drawing.
7. `raudio`: Audio device management and sound streaming.
8. `raymath`: Math module for Vector2/3, Matrix, and Quaternion.

## Basic Game Loop Structure
```c
#include "raylib.h"

int main(void) {
    // 1. Initialization
    InitWindow(800, 450, "My Raylib Game - by Alvar Laigna");
    SetTargetFPS(60); // Set desired framerate

    // Load resources here (textures, models, audio)
    // MUST call InitWindow before loading textures/models!

    // 2. Main Game Loop
    while (!WindowShouldClose()) { // Detect window close button or ESC key
        // 3. Update
        // Update variables, positions, states here
        // GetFrameTime() returns time elapsed since last frame

        // 4. Draw
        BeginDrawing();
            ClearBackground(RAYWHITE);
            
            // Draw 2D or 3D elements here
            
        EndDrawing();
    }

    // 5. De-Initialization
    // Unload resources here
    CloseWindow();
    return 0;
}
```

## Screen vs. World Coordinates
- **Camera2D / Camera3D**: Use `BeginMode2D(camera)` or `BeginMode3D(camera)` to apply transformations.
- `GetScreenToWorld2D()` / `GetWorldToScreen2D()` convert between screen space (pixels) and world space (camera view).

## Memory Management
- Most structures are passed by value if they are small (under 64 bytes, like `Vector2`, `Rectangle`, `Color`).
- Larger data is modified via reference (e.g., `UpdateCamera(&camera)`).
- **Rule of Thumb**: Always pair a `Load*` function with an `Unload*` function (e.g., `LoadTexture()` -> `UnloadTexture()`).

## Web/HTML5 Specifics
For WebAssembly (Emscripten) builds, the standard `while(!WindowShouldClose())` loop blocks the browser.
**Pattern for Web:**
Refactor the Update/Draw code into a single function (`UpdateDrawFrame()`) and use `emscripten_set_main_loop(UpdateDrawFrame, 0, 1);`.
