#ifndef SCREENS_H
#define SCREENS_H

typedef enum GameScreen { UNKNOWN = -1, TITLE = 0, GAMEPLAY } GameScreen;

extern GameScreen currentScreen;

#ifdef __cplusplus
extern "C" {
#endif

void InitTitleScreen(void);
void UpdateTitleScreen(void);
void DrawTitleScreen(void);
void UnloadTitleScreen(void);
int FinishTitleScreen(void);

void InitGameplayScreen(void);
void UpdateGameplayScreen(void);
void DrawGameplayScreen(void);
void UnloadGameplayScreen(void);
int FinishGameplayScreen(void);

void TransitionToScreen(int screen);
void UpdateTransition(void);
void DrawTransition(void);

extern bool onTransition;

#ifdef __cplusplus
}
#endif

#endif
