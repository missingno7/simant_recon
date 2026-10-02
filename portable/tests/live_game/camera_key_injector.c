/* Test-only SDL driver for one Control+numeric-keypad-right camera step. */
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;
static unsigned stage;

static int push_key(SDL_Keycode key, SDL_Scancode scan, int down,
                    SDL_Keymod modifiers)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.scancode = scan;
    event.key.key = key;
    event.key.mod = modifiers;
    event.key.down = down != 0;
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static Uint32 SDLCALL inject_camera_step(void *context, SDL_TimerID id,
                                         Uint32 interval)
{
    (void)context;
    (void)id;
    if (stage == 0) {
        stage = 1;
        if (!push_key(SDLK_LCTRL, SDL_SCANCODE_LCTRL, 1, SDL_KMOD_LCTRL) ||
            !push_key(SDLK_KP_6, SDL_SCANCODE_KP_6, 1, SDL_KMOD_LCTRL))
            return 0;
        return interval;
    }
    if (stage == 1) {
        stage = 2;
        if (!push_key(SDLK_KP_6, SDL_SCANCODE_KP_6, 0, SDL_KMOD_LCTRL) ||
            !push_key(SDLK_LCTRL, SDL_SCANCODE_LCTRL, 0, SDL_KMOD_NONE))
            return 0;
    }
    return 0;
}

__attribute__((constructor)) static void start_camera_timer(void)
{
    timer_id = SDL_AddTimer(250, inject_camera_step, NULL);
}

__attribute__((destructor)) static void stop_camera_timer(void)
{
    const char *path = getenv("SIMANT_LIVE_SMOKE_EVENT_REPORT");
    FILE *file;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (path == NULL || path[0] == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file, "%u\n", pushed_events);
    (void)fclose(file);
}
