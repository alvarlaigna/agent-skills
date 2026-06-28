# Simplified raylib Makefile for single-file projects.
# Requires a pre-built raylib library. Override RAYLIB_PATH, CC, or LDLIBS on the
# command line if your install or platform differs from the defaults below.

.PHONY: all clean web

PLATFORM ?= PLATFORM_DESKTOP
PROJECT_NAME ?= {{PROJECT_SLUG}}
BUILD_MODE ?= RELEASE

# Detect the host OS so desktop builds link the correct system libraries.
ifeq ($(OS),Windows_NT)
    DETECTED_OS = Windows
else
    DETECTED_OS = $(shell uname -s)
endif

# Per-platform raylib location and link libraries. All values are overridable.
ifeq ($(DETECTED_OS),Windows)
    RAYLIB_PATH ?= C:/raylib/raylib
    RAYLIB_INCLUDE_PATH ?= $(RAYLIB_PATH)/src
    RAYLIB_LIB_PATH ?= $(RAYLIB_PATH)/src
    LDLIBS ?= -lraylib -lopengl32 -lgdi32 -lwinmm
else ifeq ($(DETECTED_OS),Darwin)
    RAYLIB_PATH ?= /usr/local
    RAYLIB_INCLUDE_PATH ?= $(RAYLIB_PATH)/include
    RAYLIB_LIB_PATH ?= $(RAYLIB_PATH)/lib
    LDLIBS ?= -lraylib -framework CoreVideo -framework IOKit -framework Cocoa -framework GLUT -framework OpenGL
else
    RAYLIB_PATH ?= /usr/local
    RAYLIB_INCLUDE_PATH ?= $(RAYLIB_PATH)/include
    RAYLIB_LIB_PATH ?= $(RAYLIB_PATH)/lib
    LDLIBS ?= -lraylib -lGL -lm -lpthread -ldl -lrt -lX11
endif

BUILD_WEB_SHELL ?= web/minshell.html
BUILD_WEB_HEAP_SIZE ?= 128MB
BUILD_WEB_STACK_SIZE ?= 1MB
BUILD_WEB_RESOURCES ?= TRUE
BUILD_WEB_RESOURCES_PATH ?= resources

CC = gcc
CFLAGS = -Wall -std=c99 -I. -I$(RAYLIB_INCLUDE_PATH)
LDFLAGS = -L$(RAYLIB_LIB_PATH)
EXT =

ifeq ($(BUILD_MODE),RELEASE)
    CFLAGS += -O2
else
    CFLAGS += -g -D_DEBUG
endif

ifeq ($(PLATFORM),PLATFORM_WEB)
    CC = emcc
    CFLAGS = -Wall -std=gnu99 -I. -I$(RAYLIB_INCLUDE_PATH) -Os
    LDFLAGS = -sUSE_GLFW=3 -sASYNCIFY -sGL_ENABLE_GET_PROC_ADDRESS=1 \
              -sFORCE_FILESYSTEM=1 -sTOTAL_MEMORY=$(BUILD_WEB_HEAP_SIZE) \
              -sSTACK_SIZE=$(BUILD_WEB_STACK_SIZE) --shell-file $(BUILD_WEB_SHELL)
    ifeq ($(BUILD_WEB_RESOURCES),TRUE)
        LDFLAGS += --preload-file $(BUILD_WEB_RESOURCES_PATH)
    endif
    LDLIBS = $(RAYLIB_LIB_PATH)/libraylib.web.a
    EXT = .html
endif

all: $(PROJECT_NAME)$(EXT)

$(PROJECT_NAME)$(EXT): main.c
	$(CC) -o $@ $< $(CFLAGS) $(LDFLAGS) $(LDLIBS) -D$(PLATFORM)

web:
	$(MAKE) PLATFORM=PLATFORM_WEB

clean:
	rm -f $(PROJECT_NAME) $(PROJECT_NAME).html $(PROJECT_NAME).js $(PROJECT_NAME).wasm $(PROJECT_NAME).data *.o
