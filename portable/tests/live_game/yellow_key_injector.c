/* Test-only SDL events for the recovered YellowCommandKey boundary. */
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;

static Uint32 SDLCALL inject_yellow_keys(void *context, SDL_TimerID id,
                                         Uint32 interval)
{
    SDL_Event event;
    (void)context;
    (void)id;
    (void)interval;
    SDL_zero(event);
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.scancode = SDL_SCANCODE_0;
    event.key.key = SDLK_0;
    event.key.down = true;
    if (SDL_PushEvent(&event)) ++pushed_events;
    event.type = SDL_EVENT_KEY_UP;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.down = false;
    if (SDL_PushEvent(&event)) ++pushed_events;
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.scancode = SDL_SCANCODE_TAB;
    event.key.key = SDLK_TAB;
    event.key.down = true;
    if (SDL_PushEvent(&event)) ++pushed_events;
    event.type = SDL_EVENT_KEY_UP;
    event.key.timestamp = SDL_GetTicksNS();
    event.key.down = false;
    if (SDL_PushEvent(&event)) ++pushed_events;
    return 0;
}

__attribute__((constructor)) static void start_test_event_timer(void)
{
    timer_id = SDL_AddTimer(500, inject_yellow_keys, NULL);
}

__attribute__((destructor)) static void stop_test_event_timer(void)
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
