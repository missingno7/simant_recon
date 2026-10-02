/* Test-only SDL event driver for source-table speed and pause shortcuts. */
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;
static unsigned sequence_index;
static uint64_t pause_started_ns;
static uint64_t pause_hold_ns;

static SDL_Scancode scancode_for(SDL_Keycode key)
{
    switch (key) {
    case SDLK_1: return SDL_SCANCODE_1;
    case SDLK_2: return SDL_SCANCODE_2;
    case SDLK_3: return SDL_SCANCODE_3;
    case SDLK_4: return SDL_SCANCODE_4;
    default: return SDL_SCANCODE_0;
    }
}

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

static Uint32 SDLCALL inject_shortcut(void *context, SDL_TimerID id,
                                      Uint32 interval)
{
    static const SDL_Keycode speeds[] = {
        SDLK_1, SDLK_2, SDLK_3, SDLK_4, SDLK_1
    };
    size_t i;
    (void)context;
    (void)id;
    (void)interval;
    if (sequence_index == 0) {
        for (i = 0; i < sizeof(speeds) / sizeof(speeds[0]); ++i) {
            SDL_Keycode key = speeds[i];
            ++sequence_index;
            if (!push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 1, SDL_KMOD_LSHIFT) ||
                !push_key(key, scancode_for(key), 1, SDL_KMOD_LSHIFT) ||
                !push_key(key, scancode_for(key), 0, SDL_KMOD_LSHIFT) ||
                !push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 0, SDL_KMOD_NONE))
                return 0;
        }
        ++sequence_index;
        if (!push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 1, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_0, SDL_SCANCODE_0, 1, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_0, SDL_SCANCODE_0, 0, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 0, SDL_KMOD_NONE))
            return 0;
        pause_started_ns = SDL_GetTicksNS();
        return interval;
    }
    if (sequence_index == 6) {
        ++sequence_index;
        if (!push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 1, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_0, SDL_SCANCODE_0, 1, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_0, SDL_SCANCODE_0, 0, SDL_KMOD_LSHIFT) ||
            !push_key(SDLK_LSHIFT, SDL_SCANCODE_LSHIFT, 0, SDL_KMOD_NONE))
            return 0;
        pause_hold_ns = SDL_GetTicksNS() - pause_started_ns;
        return 0;
    }
    return 0;
}

__attribute__((constructor)) static void start_menu_key_timer(void)
{
    timer_id = SDL_AddTimer(250, inject_shortcut, NULL);
}

__attribute__((destructor)) static void stop_menu_key_timer(void)
{
    const char *path = getenv("SIMANT_LIVE_SMOKE_EVENT_REPORT");
    FILE *file;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (path == NULL || path[0] == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file, "{\"pushed_event_count\":%u,\"pause_hold_ns\":%llu}\n",
                  pushed_events, (unsigned long long)pause_hold_ns);
    (void)fclose(file);
}
