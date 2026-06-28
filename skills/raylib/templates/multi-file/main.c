#include "raylib.h"

#if defined(PLATFORM_WEB)
#include <emscripten/emscripten.h>
#endif

#include "screens.h"

static const int screenWidth = 800;
static const int screenHeight = 450;

GameScreen currentScreen = TITLE;

static void UpdateDrawFrame(void)
{
    if (!onTransition)
    {
        switch (currentScreen)
        {
        case TITLE:
            UpdateTitleScreen();
            if (FinishTitleScreen()) TransitionToScreen(GAMEPLAY);
            break;
        case GAMEPLAY:
            UpdateGameplayScreen();
            if (FinishGameplayScreen()) TransitionToScreen(TITLE);
            break;
        default:
            break;
        }
    }
    else
    {
        UpdateTransition();
    }

    BeginDrawing();
    ClearBackground(RAYWHITE);

    switch (currentScreen)
    {
    case TITLE: DrawTitleScreen(); break;
    case GAMEPLAY: DrawGameplayScreen(); break;
    default: break;
    }

    if (onTransition) DrawTransition();
    EndDrawing();
}

int main(void)
{
    InitWindow(screenWidth, screenHeight, "{{PROJECT_NAME}} - by Alvar Laigna");
    SetTargetFPS(60);

    InitTitleScreen();

#if defined(PLATFORM_WEB)
    emscripten_set_main_loop(UpdateDrawFrame, 0, 1);
#else
    while (!WindowShouldClose())
    {
        UpdateDrawFrame();
    }
#endif

    switch (currentScreen)
    {
    case TITLE: UnloadTitleScreen(); break;
    case GAMEPLAY: UnloadGameplayScreen(); break;
    default: break;
    }

    CloseWindow();
    return 0;
}
