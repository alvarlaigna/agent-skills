cmake_minimum_required(VERSION 3.24)
project({{PROJECT_NAME}})

include(FetchContent)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(RAYLIB_VERSION 6.0)

find_package(raylib ${RAYLIB_VERSION} QUIET)
if(NOT raylib_FOUND)
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

if("${PLATFORM}" STREQUAL "Web")
    set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX ".html")
    target_link_options(${PROJECT_NAME} PUBLIC
        -sUSE_GLFW=3
        -sASYNCIFY
        -sGL_ENABLE_GET_PROC_ADDRESS=1
        -sFORCE_FILESYSTEM=1
        PUBLIC --preload-file resources)
endif()

if(APPLE)
    target_link_libraries(${PROJECT_NAME} PRIVATE
        "-framework IOKit" "-framework Cocoa" "-framework OpenGL")
endif()
