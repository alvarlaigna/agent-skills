#include "raylib.h"
#include "screens.h"

static int finishScreen = 0;

void InitTitleScreen(void)
{
    finishScreen = 0;
}

void UpdateTitleScreen(void)
{
    if (IsKeyPressed(KEY_ENTER))
    {
        finishScreen = 1;
    }
}

void DrawTitleScreen(void)
{
    DrawText("{{PROJECT_NAME}}", 260, 180, 40, DARKGRAY);
    DrawText("PRESS ENTER to start", 280, 240, 20, GRAY);
}

void UnloadTitleScreen(void) {}

int FinishTitleScreen(void)
{
    int result = finishScreen;
    finishScreen = 0;
    return result;
}
