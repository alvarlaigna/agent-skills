#include "raylib.h"

#if defined(PLATFORM_WEB)
#include <emscripten/emscripten.h>
#endif

static const int screenWidth = 800;
static const int screenHeight = 450;

static void UpdateDrawFrame(void)
{
    float dt = GetFrameTime();

    // Update
    // TODO: advance game state using dt

    // Draw
    BeginDrawing();
    ClearBackground(RAYWHITE);
    DrawText("{{PROJECT_NAME}}", 190, 200, 20, LIGHTGRAY);
    DrawFPS(10, 10);
    EndDrawing();
}

int main(void)
{
    InitWindow(screenWidth, screenHeight, "{{PROJECT_NAME}}");
    SetTargetFPS(60);

    // Load resources after InitWindow (OpenGL context required).
    // InitAudioDevice();
    // Sound fx = LoadSound("resources/coin.wav");

#if defined(PLATFORM_WEB)
    emscripten_set_main_loop(UpdateDrawFrame, 0, 1);
#else
    while (!WindowShouldClose())
    {
        UpdateDrawFrame();
    }
#endif

    // UnloadSound(fx);
    // CloseAudioDevice();
    CloseWindow();

    return 0;
}
