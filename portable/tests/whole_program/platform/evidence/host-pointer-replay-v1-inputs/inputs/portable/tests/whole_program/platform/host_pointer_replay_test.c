#include "portable/whole_program/platform/sdl3/host_modes.h"
#include <SDL3/SDL.h>
#include <assert.h>
#include <stdio.h>

static void check(Host *host, HostEventKind kind, uint8_t button, int16_t x, int16_t y)
{
    HostEvent input = {0}, output;
    int found = 0, result;
    input.kind = kind;
    input.button = button;
    input.x = x;
    input.y = y;
    assert(host_push_pointer_event(host, &input));
    while ((result = host_poll_event(host, &output)) != 0) {
        assert(result == 1);
        if (output.kind != kind) continue;
        assert(output.x == x && output.y == y && output.button == button);
        ++found;
    }
    assert(found == 1);
}

int main(void)
{
    Host *host;
    HostEvent invalid = {0};
    assert(SDL_SetHint(SDL_HINT_VIDEO_DRIVER, "dummy"));
    host = host_create_dimensions("Pointer replay control", 0, 640, 350);
    assert(host);
    assert(!host_push_pointer_event(host, &invalid));
    invalid.kind = HOST_EVENT_MOUSE_DOWN;
    invalid.button = 4;
    assert(!host_push_pointer_event(host, &invalid));
    check(host, HOST_EVENT_MOUSE_MOVE, 0, 344, 103);
    check(host, HOST_EVENT_MOUSE_DOWN, SDL_BUTTON_LEFT, 344, 103);
    check(host, HOST_EVENT_MOUSE_UP, SDL_BUTTON_LEFT, 344, 103);
    assert(host_set_logical_size(host, 640, 480));
    check(host, HOST_EVENT_MOUSE_MOVE, 0, 511, 420);
    check(host, HOST_EVENT_MOUSE_DOWN, SDL_BUTTON_RIGHT, 511, 420);
    check(host, HOST_EVENT_MOUSE_UP, SDL_BUTTON_RIGHT, 511, 420);
    host_destroy(host);
    puts("PASS EGA/VGA logical pointer round-trip and invalid-kind/button controls");
    return 0;
}
