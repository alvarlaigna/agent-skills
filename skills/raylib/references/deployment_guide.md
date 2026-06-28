# Raylib Deployment & Build Guide

## Supported Platforms
Raylib supports Windows, Linux, macOS, FreeBSD, Raspberry Pi, Android, HTML5 (WebAssembly), and various retro consoles (Dreamcast, N64, PSP, PSVita).

## C/C++ Build Systems
Raylib provides robust Makefiles and CMake support. Prefer the bundled `templates/c/CMakeLists.txt` or run `scripts/build.sh` / `scripts/build.ps1` for a consistent desktop build.

### CMake Build (Recommended for Cross-Platform)
```cmake
cmake_minimum_required(VERSION 3.24)
project(MyRaylibGame)

include(FetchContent)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(RAYLIB_VERSION 6.0)

find_package(raylib ${RAYLIB_VERSION} QUIET)
if (NOT raylib_FOUND)
    FetchContent_Declare(
        raylib
        DOWNLOAD_EXTRACT_TIMESTAMP OFF
        URL https://github.com/raysan5/raylib/archive/refs/tags/${RAYLIB_VERSION}.tar.gz
        FIND_PACKAGE_ARGS ${RAYLIB_VERSION}
    )
    FetchContent_MakeAvailable(raylib)
endif()

add_executable(${PROJECT_NAME} main.c)
target_link_libraries(${PROJECT_NAME} PRIVATE raylib)

if ("${PLATFORM}" STREQUAL "Web")
    set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX ".html")
    target_link_options(${PROJECT_NAME} PUBLIC
        -sUSE_GLFW=3
        -sASYNCIFY
        -sGL_ENABLE_GET_PROC_ADDRESS=1
        -sFORCE_FILESYSTEM=1
        PUBLIC --preload-file resources)
endif()

if (APPLE)
    target_link_libraries(${PROJECT_NAME} PRIVATE
        "-framework IOKit" "-framework Cocoa" "-framework OpenGL")
endif()
```

Configure and build:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

For web via CMake:

```bash
emcmake cmake -S . -B build-web -DPLATFORM=Web
cmake --build build-web
```

## HTML5 / WebAssembly (Emscripten)
To compile for the web, use Emscripten (`emcc`). Refactor the game loop into `UpdateDrawFrame()` and register it with `emscripten_set_main_loop()`; see `templates/c/main.c`.

1. Install Emscripten SDK and activate it in the shell.
2. Build raylib for web (`-DPLATFORM=Web`) or use CMake with `-DPLATFORM=Web`.
3. Compile the game with the verified linker flags below, or run `scripts/build_web.sh` / `scripts/build_web.ps1`.

**Web Build Flags Example:**
```bash
emcc -o game.html main.c -Os -Wall /path/to/libraylib.web.a \
    -I/path/to/raylib/src \
    -sUSE_GLFW=3 -sASYNCIFY -sGL_ENABLE_GET_PROC_ADDRESS=1 \
    -sFORCE_FILESYSTEM=1 -sTOTAL_MEMORY=67108864 \
    --shell-file minshell.html \
    --preload-file resources
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

### WebAssembly (raylib-go)
Standard `raylib-go` uses CGO and **cannot** target `GOOS=js` directly. For web builds use the community [Raylib-Go-Wasm](https://github.com/BrownNPC/Raylib-Go-Wasm) fork:

1. Add `replace` directives in `go.mod` pointing at the wasm fork.
2. Refactor `main()` to call `rl.SetMainLoop(update)` instead of a blocking `for` loop.
3. Build with `GOOS=js GOARCH=wasm` using the fork's documented toolchain.

Do not assume a desktop `raylib-go` project builds to wasm without these changes.

### Cross-Compilation (Go)
**Windows from Linux:**
```bash
CGO_ENABLED=1 CC=x86_64-w64-mingw32-gcc GOOS=windows GOARCH=amd64 go build -ldflags "-s -w -H=windowsgui"
```
**macOS from Linux:**
```bash
CGO_ENABLED=1 CC=x86_64-apple-darwin21.1-clang GOOS=darwin GOARCH=amd64 go build -ldflags "-linkmode external -s -w '-extldflags=-mmacosx-version-min=10.15'"
```

Or run `scripts/cross_compile_go.sh` / `scripts/cross_compile_go.ps1` from the skill directory.

## Optimization
- Strip debug symbols for release builds (`-s -w` in Go, or `strip` command in C).
- Hide the console window on Windows: `-Wl,--subsystem,windows` in GCC, or `-H=windowsgui` in Go.
