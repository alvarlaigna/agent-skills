#include "raylib.h"
#include "screens.h"

bool onTransition = false;
static bool transFadeOut = false;
static int transFromScreen = -1;
static int transToScreen = -1;
static float transAlpha = 0.0f;

void TransitionToScreen(int screen)
{
    onTransition = true;
    transFadeOut = false;
    transFromScreen = currentScreen;
    transToScreen = screen;
    transAlpha = 0.0f;
}

void UpdateTransition(void)
{
    if (!transFadeOut)
    {
        transAlpha += 0.05f;
        if (transAlpha > 1.01f)
        {
            transAlpha = 1.0f;
            switch (transFromScreen)
            {
            case TITLE: UnloadTitleScreen(); break;
            case GAMEPLAY: UnloadGameplayScreen(); break;
            default: break;
            }
            switch (transToScreen)
            {
            case TITLE: InitTitleScreen(); break;
            case GAMEPLAY: InitGameplayScreen(); break;
            default: break;
            }
            currentScreen = transToScreen;
            transFadeOut = true;
        }
    }
    else
    {
        transAlpha -= 0.02f;
        if (transAlpha < -0.01f)
        {
            transAlpha = 0.0f;
            transFadeOut = false;
            onTransition = false;
            transFromScreen = -1;
            transToScreen = -1;
        }
    }
}

void DrawTransition(void)
{
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), Fade(BLACK, transAlpha));
}
