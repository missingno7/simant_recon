#include "portable/whole_program/platform/sdl3/input_time_host.h"
#include "portable/whole_program/platform/sdl3/host_modes.h"
#include <SDL3/SDL.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>

static uint64_t cpu_ns(void)
{
    FILETIME created, exited, kernel, user;
    ULARGE_INTEGER k, u;
    assert(GetProcessTimes(GetCurrentProcess(), &created, &exited, &kernel, &user));
    k.LowPart = kernel.dwLowDateTime; k.HighPart = kernel.dwHighDateTime;
    u.LowPart = user.dwLowDateTime; u.HighPart = user.dwHighDateTime;
    return (k.QuadPart + u.QuadPart) * 100;
}

int native_windows_translate(SDL_Event *e) { (void)e; return 0; }
int native_windows_take_deferred(SDL_Event *e) { (void)e; return 0; }
int native_windows_filter_root(SDL_Event *e) { (void)e; return 0; }
int native_windows_pointer(float *x, float *y) { (void)x; (void)y; return 0; }
void native_windows_root_pointer(float *x, float *y) { (void)x; (void)y; }

static PortableInputTimeHost input;
static uint64_t injected_ns, handled_ns;
static unsigned received;
static int observe(void *unused, const HostEvent *event)
{
    (void)unused;
    if (event->kind == HOST_EVENT_KEY_DOWN || event->kind == HOST_EVENT_MOUSE_DOWN) {
        handled_ns = SDL_GetTicksNS();
        ++received;
    }
    return 1;
}
static void drain(void)
{
    HostEvent event;
    while (portable_input_time_host_poll_event(&input, &event) > 0) {}
}
static int refresh(void *unused, SimTimingClock *clock)
{
    (void)unused;
    assert(portable_input_time_host_refresh_from_sdl_monotonic(&input.monotonic_refresh, clock));
    while (portable_machine_clock_pace()) drain();
    drain();
    return 1;
}
static int inject(void *unused)
{
    SDL_Event event = {0};
    (void)unused;
    SDL_Delay(5);
    event.type = SDL_EVENT_KEY_DOWN;
    event.key.key = SDLK_A;
    event.key.scancode = SDL_SCANCODE_A;
    event.key.down = true;
    injected_ns = SDL_GetTicksNS();
    assert(SDL_PushEvent(&event));
    memset(&event, 0, sizeof(event));
    event.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    event.button.button = SDL_BUTTON_LEFT;
    event.button.x = 100; event.button.y = 100;
    assert(SDL_PushEvent(&event));
    return 0;
}
int main(int argc, char **argv)
{
    SimTimingClock clock;
    Host *host;
    SDL_Thread *thread = NULL;
    uint32_t tick = 0, previous = 0, sequence[4] = {0};
    unsigned calls = 0, n = 1;
    int spin = argc > 1 && !strcmp(argv[1], "--spin");
    uint64_t started, cpu_started;
    assert(SDL_SetHint(SDL_HINT_VIDEO_DRIVER, "dummy"));
    host = host_create_dimensions("idle poll fixture", 1, 640, 480);
    assert(host);
    if (spin) host_virtual_clock_configure(0);
    else portable_machine_clock_configure(0, 1000000);
    assert(sim_timing_clock_init_bios(&clock, 14318180, 12) == SIM_TIMING_OK);
    assert(portable_input_time_host_init(&input, host, &clock) == PORTABLE_INPUT_TIME_OK);
    portable_sdl_monotonic_clock_refresh_init(&input.monotonic_refresh);
    assert(portable_input_time_host_set_clock_refresh(&input, refresh, NULL) == PORTABLE_INPUT_TIME_OK);
    assert(portable_input_time_host_set_event_observer(&input, observe, NULL) == PORTABLE_INPUT_TIME_OK);
    assert(portable_input_time_host_bind(&input) == PORTABLE_INPUT_TIME_OK);
    if (!spin) thread = SDL_CreateThread(inject, "input wake", NULL);
    started = SDL_GetTicksNS();
    cpu_started = cpu_ns();
    /* Canonical BIOS deadline loop, using the actual bound public service. */
    while (tick < 3) {
        tick = timer_bios_tick_count();
        ++calls;
        if (tick != previous) { assert(n < 4); sequence[n++] = tick; previous = tick; }
    }
    assert(n == 4 && sequence[0] == 0 && sequence[1] == 1 && sequence[2] == 2 && sequence[3] == 3);
    if (spin) assert(calls > 1000);
    else {
        SDL_WaitThread(thread, NULL);
        assert(calls <= 165);
        assert(received == 2 && handled_ns >= injected_ns && handled_ns-injected_ns < 54925493);
        assert(SDL_GetTicksNS()-started >= 160000000);
        assert(cpu_ns()-cpu_started < 60000000); /* A busy delay fails this. */
    }
    printf("{\"mode\":\"%s\",\"calls\":%u,\"ticks\":[0,1,2,3],\"latency_ns\":%llu,\"wall_ns\":%llu,\"cpu_ns\":%llu}\n",
        spin ? "spin" : "paced", calls, (unsigned long long)(handled_ns-injected_ns),
        (unsigned long long)(SDL_GetTicksNS()-started), (unsigned long long)(cpu_ns()-cpu_started));
    portable_input_time_host_shutdown(&input);
    host_destroy(host);
    return 0;
}
