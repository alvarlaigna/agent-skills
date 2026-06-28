# Raylib Deployment & Build Guide

## Supported Platforms
Raylib supports Windows, Linux, macOS, FreeBSD, Raspberry Pi, Android, HTML5 (WebAssembly), and various retro consoles (Dreamcast, N64, PSP, PSVita).

## C/C++ Build Systems
Raylib provides robust Makefiles and CMake support.

### CMake Build (Recommended for Cross-Platform)
```cmake
cmake_minimum_required(VERSION 3.11)
project(MyRaylibGame)

# Find or fetch Raylib
find_package(raylib 5.5 QUIET)
if (NOT raylib_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        raylib
        GIT_REPOSITORY https://github.com/raysan5/raylib.git
        GIT_TAG master
    )
    FetchContent_MakeAvailable(raylib)
endif()

add_executable(${PROJECT_NAME} main.c)
target_link_libraries(${PROJECT_NAME} PRIVATE raylib)
```

## HTML5 / WebAssembly (Emscripten)
To compile for the web, use Emscripten (`emcc`).

1. Install Emscripten SDK.
2. Compile Raylib library with `-DPLATFORM_WEB`.
3. Compile the game using `emcc`.

**Web Build Flags Example:**
```bash
emcc -o game.html main.c -Os -Wall /path/to/libraylib.a \
    -I/path/to/raylib/src \
    -s USE_GLFW=3 -s ASYNCIFY -s TOTAL_MEMORY=67108864 \
    --preload-file assets
```

## Go Bindings (raylib-go)
Raylib is extremely popular in Go via `gen2brain/raylib-go`.

### Installation
```bash
go get -v -u github.com/gen2brain/raylib-go/raylib
```

### Build Tags
- `-tags sdl` : Use SDL backend instead of GLFW.
- `-tags opengl21` : Force OpenGL 2.1.
- `-tags wayland` : Force Wayland on Linux.

### Cross-Compilation (Go)
**Windows from Linux:**
```bash
CGO_ENABLED=1 CC=x86_64-w64-mingw32-gcc GOOS=windows GOARCH=amd64 go build -ldflags "-s -w -H=windowsgui"
```
**macOS from Linux:**
```bash
CGO_ENABLED=1 CC=x86_64-apple-darwin21.1-clang GOOS=darwin GOARCH=amd64 go build -ldflags "-linkmode external -s -w '-extldflags=-mmacosx-version-min=10.15'"
```

## Optimization
- Strip debug symbols for release builds (`-s -w` in Go, or `strip` command in C).
- Hide the console window on Windows: `-Wl,--subsystem,windows` in GCC, or `-H=windowsgui` in Go.
