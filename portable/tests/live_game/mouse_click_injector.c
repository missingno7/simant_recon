/* Test-only SDL driver for one unmodified press/release in Edit object 4. */
#include <SDL3/SDL.h>

#include <stdio.h>
#include <stdlib.h>

static SDL_TimerID timer_id;
static volatile unsigned pushed_events;
static unsigned stage;

static int push_button(int down)
{
    SDL_Event event;
    SDL_zero(event);
    event.type = down ? SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
    event.button.timestamp = SDL_GetTicksNS();
    event.button.button = SDL_BUTTON_LEFT;
    event.button.down = down != 0;
    event.button.x = 100.0f;
    event.button.y = 100.0f;
    if (!SDL_PushEvent(&event)) return 0;
    ++pushed_events;
    return 1;
}

static Uint32 SDLCALL inject_click(void *context, SDL_TimerID id,
                                   Uint32 interval)
{
    (void)context;
    (void)id;
    if (stage == 0) {
        stage = 1;
        return push_button(1) ? interval : 0;
    }
    if (stage == 1) {
        stage = 2;
        (void)push_button(0);
    }
    return 0;
}

__attribute__((constructor)) static void start_click_timer(void)
{
    timer_id = SDL_AddTimer(250, inject_click, NULL);
}

__attribute__((destructor)) static void stop_click_timer(void)
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
