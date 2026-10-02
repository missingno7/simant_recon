cmake_minimum_required(VERSION 3.20)
project(simant_sdl3 LANGUAGES C)

find_package(SDL3 3.4 CONFIG REQUIRED)
file(GLOB_RECURSE SIMANT_NATIVE_SOURCES CONFIGURE_DEPENDS
    game/*.c render/*.c ui_model/*.c audio/*.c platform/*.c)
# Diagnostic source-reuse modules have not passed the production proof gate.
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/game/recovered/")
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/game/save/")
# Standalone diagnostic models are integrated only after caller review.
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/ui_model/windows/zoom[.]c$")
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/ui_model/windows/control_events[.]c$")
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/ui_model/windows/history_render[.]c$")
list(FILTER SIMANT_NATIVE_SOURCES EXCLUDE REGEX "/ui_model/dialogs/menu_quit[.]c$")
add_executable(simant-sdl3 main.c ${SIMANT_NATIVE_SOURCES})
target_compile_features(simant-sdl3 PRIVATE c_std_11)
set_target_properties(simant-sdl3 PROPERTIES C_EXTENSIONS OFF)
target_include_directories(simant-sdl3 PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(simant-sdl3 PRIVATE SDL3::SDL3)
if(MSVC)
    target_compile_options(simant-sdl3 PRIVATE /W4)
else()
    target_compile_options(simant-sdl3 PRIVATE -Wall -Wextra -Werror)
endif()
