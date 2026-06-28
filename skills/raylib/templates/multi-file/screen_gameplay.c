#include "raylib.h"
#include "screens.h"

static int finishScreen = 0;
static float playerX = 400.0f;

void InitGameplayScreen(void)
{
    finishScreen = 0;
    playerX = 400.0f;
}

void UpdateGameplayScreen(void)
{
    if (IsKeyDown(KEY_LEFT)) playerX -= 200.0f * GetFrameTime();
    if (IsKeyDown(KEY_RIGHT)) playerX += 200.0f * GetFrameTime();
    if (IsKeyPressed(KEY_ESCAPE)) finishScreen = 1;
}

void DrawGameplayScreen(void)
{
    DrawText("GAMEPLAY - ESC to title", 10, 10, 20, DARKGRAY);
    DrawCircle((int)playerX, 225, 20, MAROON);
}

void UnloadGameplayScreen(void) {}

int FinishGameplayScreen(void)
{
    int result = finishScreen;
    finishScreen = 0;
    return result;
}
