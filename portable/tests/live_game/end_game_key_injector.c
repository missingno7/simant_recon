/* Opt-in SDL event source for the synchronous EndGame modal smoke only. */
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;

static int push_key(SDL_EventType type, bool down)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = type;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.scancode = SDL_SCANCODE_ESCAPE;
    event.key.key = SDLK_ESCAPE;
    event.key.mod = SDL_KMOD_NONE;
    event.key.down = down;
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static Uint32 SDLCALL inject_end_game_key(void *context, SDL_TimerID id,
                                          Uint32 interval)
{
    (void)context;
    (void)id;
    (void)interval;
    if (!push_key(SDL_EVENT_KEY_DOWN, true) ||
        !push_key(SDL_EVENT_KEY_UP, false))
        return 0;
    return 0;
}

__attribute__((constructor)) static void start_end_game_key_timer(void)
{
    timer_id = SDL_AddTimer(350, inject_end_game_key, NULL);
}

__attribute__((destructor)) static void stop_end_game_key_timer(void)
{
    const char *path = getenv("SIMANT_LIVE_SMOKE_EVENT_REPORT");
    FILE *file;
    if (timer_id != 0) (void)SDL_RemoveTimer(timer_id);
    if (path == NULL || path[0] == '\0') return;
    file = fopen(path, "wb");
    if (file == NULL) return;
    (void)fprintf(file, "{\"pushed_event_count\":%u}\n", pushed_events);
    (void)fclose(file);
}
