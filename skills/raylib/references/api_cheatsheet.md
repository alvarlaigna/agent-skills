# Raylib API Cheatsheet (v6.0)

## Window & Core
```c
void InitWindow(int width, int height, const char *title);
void CloseWindow(void);
bool WindowShouldClose(void);
void SetTargetFPS(int fps);
float GetFrameTime(void);
double GetTime(void);
void TakeScreenshot(const char *fileName);
void SetTraceLogLevel(int logLevel);
```

## Drawing
```c
void BeginDrawing(void);
void EndDrawing(void);
void ClearBackground(Color color);
void BeginMode2D(Camera2D camera);
void EndMode2D(void);
void BeginMode3D(Camera3D camera);
void EndMode3D(void);
```

## Input Handling
```c
bool IsKeyPressed(int key);    // Pressed once
bool IsKeyDown(int key);       // Held down
bool IsMouseButtonPressed(int button);
Vector2 GetMousePosition(void);
bool IsGamepadAvailable(int gamepad);
bool IsGamepadButtonPressed(int gamepad, int button);
float GetGamepadAxisMovement(int gamepad, int axis);
```

## 2D Shapes
```c
void DrawRectangle(int posX, int posY, int width, int height, Color color);
void DrawRectangleRec(Rectangle rec, Color color);
void DrawCircle(int centerX, int centerY, float radius, Color color);
void DrawLine(int startPosX, int startPosY, int endPosX, int endPosY, Color color);
```

## Textures & Images
```c
// NOTE: Must call InitWindow() before loading textures!
Texture2D LoadTexture(const char *fileName);
void UnloadTexture(Texture2D texture);
void DrawTexture(Texture2D texture, int posX, int posY, Color tint);
void DrawTextureRec(Texture2D texture, Rectangle source, Vector2 position, Color tint);
// To flip a texture, pass a negative width/height in the source Rectangle.
```

## Text & Fonts
```c
void DrawText(const char *text, int posX, int posY, int fontSize, Color color);
int MeasureText(const char *text, int fontSize);
Font LoadFont(const char *fileName);
void DrawTextEx(Font font, const char *text, Vector2 position, float fontSize, float spacing, Color tint);
```

## 3D Models
```c
Model LoadModel(const char *fileName);
void DrawModel(Model model, Vector3 position, float scale, Color tint);
void DrawModelEx(Model model, Vector3 position, Vector3 rotationAxis, float rotationAngle, Vector3 scale, Color tint);
void UpdateModelAnimation(Model model, ModelAnimation anim, int frame);
```

## Audio
```c
void InitAudioDevice(void);
void CloseAudioDevice(void);
Sound LoadSound(const char *fileName);
void PlaySound(Sound sound);
Music LoadMusicStream(const char *fileName);
void PlayMusicStream(Music music);
void UpdateMusicStream(Music music); // MUST be called every frame
```
