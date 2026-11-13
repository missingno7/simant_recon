#include "host_modes.h"
#include "native_windows.h"
#include <SDL3/SDL.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <inttypes.h>
#define SIMANT_TEST_OBSERVER_IMPLEMENTATION
#include "../input_time.h"

static FILE *test_clock_file, *test_input_file;
static int test_loaded, test_clock_done,test_window_source;
static uint64_t test_pumps;
static unsigned test_inputs,test_queued;
static uint64_t test_input_pump,test_input_reads;
static unsigned test_input_step, test_input_phase;
static char test_input_op[24],test_input_arg[40];
static int test_input_a,test_input_b,test_input_ready;
static Host *test_host;
/* Ordinal inputs join the normal host event boundary before SDL's end-of-poll
 * sentinel. SDL_PushEvent may defer an event to a later polling batch. */
static SDL_Event test_raw[128];
static unsigned test_raw_ids[128],test_raw_sequence;
static unsigned test_raw_head,test_raw_count;
static int test_injecting;
static int test_queue_raw(const SDL_Event *event)
{
    if (test_raw_count==128) abort();
    test_raw[(test_raw_head+test_raw_count)%128]=*event;
    test_raw_ids[(test_raw_head+test_raw_count)%128]=test_queued+1;
    ++test_raw_count;return 1;
}
static int test_take_raw(SDL_Event *event)
{
    test_raw_sequence=0;
    if (!test_raw_count) return 0;
    *event=test_raw[test_raw_head];test_raw_sequence=test_raw_ids[test_raw_head];
    test_raw_head=(test_raw_head+1)%128;--test_raw_count;return 1;
}
typedef struct TestRun { uint32_t value; uint64_t count; struct TestRun *next; } TestRun;
typedef struct TestStream {
    char kind,original_kind;
    int64_t pc;
    uint32_t original_pc;
    TestRun *head,*tail;
} TestStream;
static TestStream test_streams[256];
static unsigned test_stream_count;
static uint64_t test_reads,test_hash=UINT64_C(1469598103934665603),test_remaining;
static uint64_t test_control_read;

static void test_finish(void)
{
    if ((test_clock_file && (!test_clock_done || test_remaining)) || test_input_ready || test_raw_count || test_inputs!=test_queued) {
        fprintf(stderr,"Observer tape incomplete: clock=%" PRIu64 " input=%d pump=%" PRIu64 "\n",test_remaining,test_input_ready,test_pumps);
        abort();
    }
}
static int test_line(FILE *file,char *line,size_t size)
{
    while (fgets(line,(int)size,file)) if (line[0]!='#' && line[0]!='\n') return 1;
    if (ferror(file)) abort();
    return 0;
}
static void test_next_input(void)
{
    char line[240],extra;
    test_input_ready=0;
    if (!test_input_file || !test_line(test_input_file,line,sizeof(line))) return;
    if (sscanf(line,"%" SCNu64 " %" SCNu64 " %u %u %23s %39s %d %d %c",&test_input_pump,&test_input_reads,
            &test_input_step,&test_input_phase,test_input_op,test_input_arg,&test_input_a,&test_input_b,&extra)!=8) abort();
    test_input_ready=1;
}
static void test_load(void)
{
    const char *clock_path,*input_path;
    if (test_loaded) return;
    test_loaded=1;
    clock_path=getenv("SIMANT_TEST_FULL_CLOCK");input_path=getenv("SIMANT_TEST_PUMP_INPUT");
    if (getenv("SIMANT_TEST_PUMP_SOURCE")) {
        if (!strcmp(getenv("SIMANT_TEST_PUMP_SOURCE"),"window")) test_window_source=1;
        else if (!strcmp(getenv("SIMANT_TEST_PUMP_SOURCE"),"both")) test_window_source=2;
        else if (strcmp(getenv("SIMANT_TEST_PUMP_SOURCE"),"queue")) abort();
    }
    if (getenv("SIMANT_TEST_CLOCK_CONTROL_READ")) {
        char *end;test_control_read=strtoull(getenv("SIMANT_TEST_CLOCK_CONTROL_READ"),&end,10);
        if (*end || !test_control_read) abort();
    }
    if (clock_path && !(test_clock_file=fopen(clock_path,"r"))) abort();
    if (test_clock_file) {
        char line[200],kind,original_kind,extra;
        int64_t pc;uint32_t original_pc,value;uint64_t count;
        while (test_line(test_clock_file,line,sizeof(line))) {
            unsigned i;TestRun *run;
            if (!strcmp(line,"X\n")) { test_clock_done=1;break; }
            if (sscanf(line,"%c %" SCNd64 " %c %" SCNu32 " %" SCNu32 " %" SCNu64 " %c",
                    &kind,&pc,&original_kind,&original_pc,&value,&count,&extra)!=6 || !count) abort();
            for (i=0;i<test_stream_count && (test_streams[i].kind!=kind || test_streams[i].pc!=pc);++i) {}
            if (i==test_stream_count) {
                if (i==256) abort();
                test_streams[i].kind=kind;test_streams[i].pc=pc;
                test_streams[i].original_kind=original_kind;test_streams[i].original_pc=original_pc;
                ++test_stream_count;
            }
            if (test_streams[i].original_kind!=original_kind || test_streams[i].original_pc!=original_pc) abort();
            run=(TestRun *)malloc(sizeof(*run));if (!run) abort();
            run->value=value;run->count=count;run->next=NULL;
            if (test_streams[i].tail) test_streams[i].tail->next=run;else test_streams[i].head=run;
            test_streams[i].tail=run;test_remaining+=count;
        }
        if (!test_clock_done || !test_remaining) abort();
    }
    if (input_path && !(test_input_file=fopen(input_path,"r"))) abort();
    if ((clock_path || input_path) && atexit(test_finish)) abort();
    test_next_input();
}
uint32_t portable_test_clock_read(char kind,void *pc,uint32_t fallback)
{
    unsigned i;TestStream *stream;TestRun *run;uint32_t value;
    int64_t delta=pc ? (int64_t)(uintptr_t)pc-(int64_t)(uintptr_t)portable_test_clock_read : 0;
    test_load();
    if (!test_clock_file) return fallback;
    if (!test_remaining) exit(0);
    for (i=0;i<test_stream_count && (test_streams[i].kind!=kind || test_streams[i].pc!=delta);++i) {}
    if (i==test_stream_count || !test_streams[i].head) {
        fprintf(stderr,"Observer extra clock read: %c %" PRId64 " (%" PRIu64 " total reads left) pump=%" PRIu64 "\n",kind,delta,test_remaining,test_pumps);
        abort();
    }
    stream=&test_streams[i];run=stream->head;value=run->value;
    --test_remaining;++test_reads;
    if (test_reads==test_control_read) {
        fprintf(stderr,"Observer negative control read %" PRIu64 ": tape=%" PRIu32 " host=%" PRIu32 "\n",test_reads,value,fallback);
        value=fallback;
    }
    test_hash=(test_hash^((uint64_t)stream->original_pc^((uint64_t)(unsigned char)stream->original_kind<<32)^((uint64_t)value<<8)))*UINT64_C(1099511628211);
    if (!--run->count) { stream->head=run->next;free(run); }
    return value;
}
uint64_t portable_test_pump_ordinal(void) { return test_pumps; }
unsigned portable_test_input_count(void) { return test_inputs; }
__attribute__((noinline)) void portable_test_input_delivered(unsigned sequence) { (void)sequence; }

struct Host {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint8_t *rgba;
    int logical_width, logical_height;
    int integer_scaling;
    int window_scale;              /* global presentation scale (--scale) */
    int crop_top;                  /* rows above the main window (native menu bar) */
    HostInputState replay_state;
    HostPalette presented_palette;
    int frame_presented;
};
static int (*event_observer)(void *, const SDL_Event *);
static void *event_observer_context;
void host_set_event_observer(int (*observer)(void *, const SDL_Event *), void *context)
{
    event_observer = observer;
    event_observer_context = context;
}
int host_presented_palette(const Host *host, HostPalette *palette)
{
    if (!host || !palette || !host->frame_presented) return 0;
    *palette = host->presented_palette;
    return 1;
}
static uint64_t virtual_ns, virtual_quantum;
void host_virtual_clock_configure(uint64_t quantum_ns)
{
    virtual_ns = 0;
    virtual_quantum = quantum_ns;
}
int host_virtual_clock_enabled(void) { return virtual_quantum != 0; }
void host_virtual_clock_poll(void) { virtual_ns += virtual_quantum; }
uint64_t host_virtual_dos_elapsed_ms(void) { return virtual_ns / 1000000u; }
int host_virtual_dos_datetime(HostDosDateTime *value)
{
    static const unsigned month_days[12] = {31,28,31,30,31,30,31,31,30,31,30,31};
    uint64_t ms, days;
    unsigned year = 1992, month = 1, count;
    if (!value || !virtual_quantum) return 0;
    ms = virtual_ns / 1000000u + UINT64_C(43200000);
    days = ms / UINT64_C(86400000);
    value->weekday = (unsigned)((3u + days) % 7u);
    value->hundredth = (unsigned)(ms / 10u % 100u);
    value->second = (unsigned)(ms / 1000u % 60u);
    value->minute = (unsigned)(ms / 60000u % 60u);
    value->hour = (unsigned)(ms / 3600000u % 24u);
    for (;;) {
        int leap = year % 4u == 0 && (year % 100u != 0 || year % 400u == 0);
        count = month_days[month - 1] + (month == 2 && leap);
        if (days < count) break;
        days -= count;
        if (++month == 13) { month = 1; ++year; }
    }
    value->year = year; value->month = month; value->day = (unsigned)days + 1u;
    return 1;
}

/* Derived from the existing SDL presentation/input provider. This target
 * adds the original VGA geometry; the selected-module prototype is unchanged. */
static int valid_geometry(int width, int height)
{
    return width == 640 && (height == 350 || height == 480);
}

int host_set_logical_size(Host *host, int width, int height)
{
    SDL_Texture *texture;
    uint8_t *rgba;
    if (!host || !valid_geometry(width, height)) {
        SDL_SetError("Unsupported original SimAnt logical geometry");
        return 0;
    }
    if (host->logical_width == width && host->logical_height == height) return 1;
    rgba = calloc((size_t)width * (size_t)height, 4);
    if (!rgba) { SDL_SetError("SimAnt presentation allocation failed"); return 0; }
    texture = SDL_CreateTexture(host->renderer, SDL_PIXELFORMAT_RGBA32,
        SDL_TEXTUREACCESS_STREAMING, width, height);
    if (!texture || !SDL_SetTextureScaleMode(texture, SDL_SCALEMODE_NEAREST) ||
        !SDL_SetWindowSize(host->window, width * host->window_scale,
                           (height - host->crop_top) * host->window_scale) ||
        !SDL_SetRenderLogicalPresentation(host->renderer, width, height - host->crop_top,
            host->integer_scaling ? SDL_LOGICAL_PRESENTATION_INTEGER_SCALE :
            SDL_LOGICAL_PRESENTATION_LETTERBOX)) {
        SDL_DestroyTexture(texture);
        free(rgba);
        return 0;
    }
    SDL_DestroyTexture(host->texture);
    free(host->rgba);
    host->texture = texture;
    host->rgba = rgba;
    host->logical_width = width;
    host->logical_height = height;
    host->frame_presented = 0;
    return 1;
}

int host_get_logical_size(const Host *host, int *width, int *height)
{
    if (!host || !width || !height) return 0;
    *width = host->logical_width;
    *height = host->logical_height;
    return 1;
}

Host *host_create_dimensions(const char *title, int integer_scaling,
                             int width, int height)
{
    Host *host;
    if (!valid_geometry(width, height)) {
        SDL_SetError("Unsupported original SimAnt logical geometry");
        return NULL;
    }
    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)) return NULL;
    host = calloc(1, sizeof(*host));
    if (!host) { SDL_Quit(); return NULL; }
    host->integer_scaling = integer_scaling != 0;
    host->window_scale = 1;
    if (!SDL_CreateWindowAndRenderer(title, width, height, SDL_WINDOW_RESIZABLE,
            &host->window, &host->renderer) ||
        !host_set_logical_size(host, width, height)) {
        host_destroy(host);
        return NULL;
    }
    return host;
}

Host *host_create(const char *title, int integer_scaling)
{
    return host_create_dimensions(title, integer_scaling,
                                   HOST_LOGICAL_WIDTH, HOST_LOGICAL_HEIGHT);
}

void host_destroy(Host *host)
{
    if (host) {
        free(host->rgba);
        SDL_DestroyTexture(host->texture);
        SDL_DestroyRenderer(host->renderer);
        SDL_DestroyWindow(host->window);
        free(host);
    }
    SDL_Quit();
}

const char *host_error(void) { return SDL_GetError(); }
SDL_Window *host_sdl_window(Host *host) { return host ? host->window : NULL; }
int host_window_scale(const Host *host) { return host ? host->window_scale : 1; }
int host_set_window_scale(Host *host, int scale)
{
    if (!host || scale < 1 || scale > 8) return 0;
    host->window_scale = scale;
    return SDL_SetWindowSize(host->window, host->logical_width * scale,
                             (host->logical_height - host->crop_top) * scale);
}

/* Modern presentation: the game's own menu bar rows are replaced by a native
 * menu; the main window shows the logical screen below them. */
int host_set_top_crop(Host *host, int rows)
{
    if (!host || rows < 0 || rows >= host->logical_height) return 0;
    if (rows == host->crop_top) return 1;
    host->crop_top = rows;
    return SDL_SetRenderLogicalPresentation(host->renderer, host->logical_width,
               host->logical_height - rows,
               host->integer_scaling ? SDL_LOGICAL_PRESENTATION_INTEGER_SCALE :
                                       SDL_LOGICAL_PRESENTATION_LETTERBOX) &&
           SDL_SetWindowSize(host->window, host->logical_width * host->window_scale,
                             (host->logical_height - rows) * host->window_scale);
}
uint64_t host_time_ns(void) { return virtual_quantum ? virtual_ns : SDL_GetTicksNS(); }
void host_wait_ms(uint32_t milliseconds)
{
    if (!virtual_quantum) SDL_Delay(milliseconds);
}

/* Only keys with a direct source DOS representation are emitted. SDL text
 * composition is deliberately separate from this physical game-key boundary. */
static uint16_t dos_key(const SDL_KeyboardEvent *event)
{
    static const uint8_t letters[26] = {
        0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,
        0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c
    };
    SDL_Keycode key = event->key;
    uint16_t scan = 0, ascii = 0;
    if (key >= SDLK_A && key <= SDLK_Z) {
        scan = letters[key - SDLK_A];
        ascii = (uint16_t)('a' + key - SDLK_A);
        if (((event->mod & SDL_KMOD_SHIFT) != 0) !=
            ((event->mod & SDL_KMOD_CAPS) != 0)) ascii -= 32;
        if (event->mod & SDL_KMOD_CTRL) ascii = (uint16_t)(key - SDLK_A + 1);
    } else if (key >= SDLK_1 && key <= SDLK_9) {
        scan = (uint16_t)(key - SDLK_1 + 2); ascii = (uint16_t)key;
        if (event->mod & SDL_KMOD_SHIFT) ascii = (uint8_t)"!@#$%^&*("[key-SDLK_1];
    } else switch (key) {
        case SDLK_0: scan=0x0b; ascii=(event->mod & SDL_KMOD_SHIFT) ? ')':'0'; break;
        case SDLK_ESCAPE: scan=1; ascii=27; break;
        case SDLK_BACKSPACE: scan=0x0e; ascii=8; break;
        case SDLK_TAB: scan=0x0f; ascii=9; break;
        case SDLK_RETURN: scan=0x1c; ascii=13; break;
        case SDLK_SPACE: scan=0x39; ascii=32; break;
        case SDLK_MINUS: scan=0x0c; ascii=(event->mod & SDL_KMOD_SHIFT) ? '_':'-'; break;
        case SDLK_EQUALS: scan=0x0d; ascii=(event->mod & SDL_KMOD_SHIFT) ? '+':'='; break;
        case SDLK_LEFTBRACKET: scan=0x1a; ascii=(event->mod & SDL_KMOD_SHIFT) ? '{':'['; break;
        case SDLK_RIGHTBRACKET: scan=0x1b; ascii=(event->mod & SDL_KMOD_SHIFT) ? '}':']'; break;
        case SDLK_SEMICOLON: scan=0x27; ascii=(event->mod & SDL_KMOD_SHIFT) ? ':':';'; break;
        case SDLK_APOSTROPHE: scan=0x28; ascii=(event->mod & SDL_KMOD_SHIFT) ? '"':'\''; break;
        case SDLK_GRAVE: scan=0x29; ascii=(event->mod & SDL_KMOD_SHIFT) ? '~':'`'; break;
        case SDLK_BACKSLASH: scan=0x2b; ascii=(event->mod & SDL_KMOD_SHIFT) ? '|':'\\'; break;
        case SDLK_COMMA: scan=0x33; ascii=(event->mod & SDL_KMOD_SHIFT) ? '<':','; break;
        case SDLK_PERIOD: scan=0x34; ascii=(event->mod & SDL_KMOD_SHIFT) ? '>':'.'; break;
        case SDLK_SLASH: scan=0x35; ascii=(event->mod & SDL_KMOD_SHIFT) ? '?':'/'; break;
        case SDLK_UP: scan=0x48; break;
        case SDLK_DOWN: scan=0x50; break;
        case SDLK_LEFT: scan=0x4b; break;
        case SDLK_RIGHT: scan=0x4d; break;
        case SDLK_HOME: scan=0x47; break;
        case SDLK_END: scan=0x4f; break;
        case SDLK_PAGEUP: scan=0x49; break;
        case SDLK_PAGEDOWN: scan=0x51; break;
        case SDLK_INSERT: scan=0x52; break;
        case SDLK_DELETE: scan=0x53; break;
        /* The game clears NumLock while polling its DOS keyboard. Keep the
         * physical keypad directions available to the logical event model. */
        case SDLK_KP_7: scan=0x47; break;
        case SDLK_KP_8: scan=0x48; break;
        case SDLK_KP_9: scan=0x49; break;
        case SDLK_KP_4: scan=0x4b; break;
        case SDLK_KP_5: scan=0x4c; break;
        case SDLK_KP_6: scan=0x4d; break;
        case SDLK_KP_1: scan=0x4f; break;
        case SDLK_KP_2: scan=0x50; break;
        case SDLK_KP_3: scan=0x51; break;
        case SDLK_KP_0: scan=0x52; break;
        case SDLK_KP_PERIOD: scan=0x53; break;
        case SDLK_KP_PLUS: scan=0x4e; ascii='+'; break;
        case SDLK_KP_MINUS: scan=0x4a; ascii='-'; break;
        case SDLK_KP_ENTER: scan=0x1c; ascii=13; break;
        case SDLK_CAPSLOCK: scan=0x3a; break;
        case SDLK_NUMLOCKCLEAR: scan=0x45; break;
        case SDLK_SCROLLLOCK: scan=0x46; break;
        /* Modifier transitions update the host held-key model. They are
         * physical events, and do not enter the DOS logical key queue. */
        case SDLK_LCTRL: case SDLK_RCTRL: scan=0x1d; break;
        case SDLK_LSHIFT: scan=0x2a; break;
        case SDLK_RSHIFT: scan=0x36; break;
        case SDLK_LALT: case SDLK_RALT: scan=0x38; break;
        default:
            if (key >= SDLK_F1 && key <= SDLK_F10)
                scan = (uint16_t)(0x3b + key - SDLK_F1);
            break;
    }
    if (event->mod & SDL_KMOD_ALT) ascii=0;
    return (uint16_t)((scan << 8) | ascii);
}

static uint8_t dos_modifiers(SDL_Keymod modifiers)
{
    return (uint8_t)(((modifiers & SDL_KMOD_RSHIFT) ? 1 : 0) |
                     ((modifiers & SDL_KMOD_LSHIFT) ? 2 : 0) |
                     ((modifiers & SDL_KMOD_CTRL) ? 4 : 0) |
                     ((modifiers & SDL_KMOD_ALT) ? 8 : 0));
}

static float pointer_coordinate(float value, int extent)
{
    if (value < 0) return 0;
    if (value > (float)(extent - 1)) return (float)(extent - 1);
    return value;
}

int host_get_input_state(Host *host, HostInputState *state)
{
    float window_x, window_y, logical_x, logical_y;
    SDL_MouseButtonFlags buttons;
    if (host == NULL || state == NULL) return 0;
    if (virtual_quantum) { *state = host->replay_state; return 1; }
    buttons = SDL_GetMouseState(&window_x, &window_y);
    if (!native_windows_pointer(&logical_x, &logical_y)) {
        if (!SDL_RenderCoordinatesFromWindow(host->renderer, window_x, window_y,
                                             &logical_x, &logical_y))
            return 0;
        logical_y += (float)host->crop_top;
        native_windows_root_pointer(&logical_x, &logical_y);
    }
    state->x = (int16_t)pointer_coordinate(logical_x, host->logical_width);
    state->y = (int16_t)pointer_coordinate(logical_y, host->logical_height);
    state->left_button_down = (uint8_t)((buttons & SDL_BUTTON_LMASK) != 0);
    state->dos_modifiers = dos_modifiers(SDL_GetModState());
    return 1;
}

int host_warp_pointer(Host *host, int16_t logical_x, int16_t logical_y)
{
    float window_x, window_y;
    if (host == NULL) return 0;
    logical_x = (int16_t)pointer_coordinate(logical_x, host->logical_width);
    logical_y = (int16_t)pointer_coordinate(logical_y, host->logical_height);
    if (host && virtual_quantum) {
        host->replay_state.x = logical_x;
        host->replay_state.y = logical_y;
        return 1;
    }
    if (host == NULL || !SDL_RenderCoordinatesToWindow(host->renderer,
            (float)logical_x, (float)(logical_y - host->crop_top), &window_x, &window_y))
        return 0;
    SDL_WarpMouseInWindow(host->window, window_x, window_y);
    return 1;
}

int host_push_pointer_event(Host *host, const HostEvent *event)
{
    SDL_Event raw = {0};
    float x, y;
    if (!host || !event ||
        !SDL_RenderCoordinatesToWindow(host->renderer, (float)event->x,
                                       (float)(event->y - host->crop_top), &x, &y)) return 0;
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        raw.type = SDL_EVENT_MOUSE_MOTION;
        raw.motion.windowID = SDL_GetWindowID(host->window);
        raw.motion.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.motion.x = x;
        raw.motion.y = y;
    } else if ((event->kind == HOST_EVENT_MOUSE_DOWN ||
                event->kind == HOST_EVENT_MOUSE_UP) && event->button >= 1 &&
               event->button <= 3) {
        raw.type = event->kind == HOST_EVENT_MOUSE_DOWN ?
                   SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
        raw.button.windowID = SDL_GetWindowID(host->window);
        raw.button.timestamp = HOST_REPLAY_EVENT_TIMESTAMP;
        raw.button.button = event->button;
        raw.button.down = event->kind == HOST_EVENT_MOUSE_DOWN;
        raw.button.clicks = 1;
        raw.button.x = x;
        raw.button.y = y;
    } else return 0;
    return test_injecting ? test_queue_raw(&raw) : SDL_PushEvent(&raw);
}

void portable_test_pump(void)
{
    test_load();
    if (test_window_source==1) return;
    ++test_pumps;
    portable_test_before_poll();
}

void portable_test_window_pump(void)
{
    test_load();
    if (!test_window_source) return;
    ++test_pumps;
    portable_test_before_poll();
}

void portable_test_before_poll(void)
{
    test_load();
    while (test_input_ready && test_input_pump<=test_pumps && test_input_reads<=test_reads) {
        SDL_Event raw={0};
        if (!strcmp(test_input_op,"keydown") || !strcmp(test_input_op,"keyup")) {
            const char *name=!strcmp(test_input_arg,"enter")?"Return":
                !strcmp(test_input_arg,"kp_5")?"Keypad 5":test_input_arg;
            raw.type=!strcmp(test_input_op,"keydown")?SDL_EVENT_KEY_DOWN:SDL_EVENT_KEY_UP;
            raw.key.key=SDL_GetKeyFromName(name);
            raw.key.scancode=SDL_GetScancodeFromKey(raw.key.key,&raw.key.mod);
            raw.key.down=raw.type==SDL_EVENT_KEY_DOWN;
            raw.key.timestamp=HOST_REPLAY_EVENT_TIMESTAMP;
            if (!raw.key.key || !test_queue_raw(&raw)) abort();
        } else {
            HostInputState state;
            HostEvent event={0};
            if (!test_host || !host_get_input_state(test_host,&state)) abort();
            event.x=state.x;event.y=state.y;
            if (!strcmp(test_input_op,"mouse_move")) {
                int x=state.x+test_input_a/2,y=state.y+test_input_b/2;
                event.kind=HOST_EVENT_MOUSE_MOVE;
                event.x=(int16_t)(x<0?0:x>test_host->logical_width-4?test_host->logical_width-4:x);
                event.y=(int16_t)(y<0?0:y>test_host->logical_height-4?test_host->logical_height-4:y);
            } else if (!strcmp(test_input_op,"mouse_button")) {
                event.kind=!strcmp(test_input_arg,"down")?HOST_EVENT_MOUSE_DOWN:HOST_EVENT_MOUSE_UP;
                event.button=(uint8_t)(test_input_a==0?SDL_BUTTON_LEFT:test_input_a==1?SDL_BUTTON_RIGHT:SDL_BUTTON_MIDDLE);
            } else abort();
            test_injecting=1;
            if (!host_push_pointer_event(test_host,&event)) abort();
            test_injecting=0;
        }
        fprintf(stderr,"Observer queued input %u pump=%" PRIu64 " reads=%" PRIu64 " original=%" PRIu64 "/%" PRIu64 " step=%u phase=%u %s %s\n",
            ++test_queued,test_pumps,test_reads,test_input_pump,test_input_reads,test_input_step,test_input_phase,test_input_op,test_input_arg);
        test_next_input();
    }
}

int host_poll_event(Host *host, HostEvent *event)
{
    SDL_Event raw;
    int hosted;
    if (!host || !event) return 0;
    test_host=host;
    while (test_take_raw(&raw) || native_windows_take_deferred(&raw) || SDL_PollEvent(&raw)) {
        memset(event, 0, sizeof(*event));
        /* Modern mode: hosted windows convert to logical screen space. */
        hosted = native_windows_translate(&raw);
        if (hosted < 0) continue;
        if (!hosted && !SDL_ConvertEventToRenderCoordinates(host->renderer, &raw)) return -1;
        if (!hosted && raw.type == SDL_EVENT_MOUSE_MOTION) {
            raw.motion.y += (float)host->crop_top;
            native_windows_root_pointer(&raw.motion.x, &raw.motion.y);
        }
        if (!hosted && (raw.type == SDL_EVENT_MOUSE_BUTTON_DOWN || raw.type == SDL_EVENT_MOUSE_BUTTON_UP)) {
            raw.button.y += (float)host->crop_top;
            native_windows_root_pointer(&raw.button.x, &raw.button.y);
        }
        /* Report the visible logical screen, including captured/letterboxed
         * motion. The INT33 adapter subsequently applies the source's tighter
         * width-4/height-4 bounds. Diagnostics and replay state see this same
         * host boundary (VGA: 0..639 x 0..479), never a one-past coordinate. */
        if (raw.type == SDL_EVENT_MOUSE_MOTION) {
            raw.motion.x = pointer_coordinate(raw.motion.x, host->logical_width);
            raw.motion.y = pointer_coordinate(raw.motion.y, host->logical_height);
        } else if (raw.type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
                   raw.type == SDL_EVENT_MOUSE_BUTTON_UP) {
            raw.button.x = pointer_coordinate(raw.button.x, host->logical_width);
            raw.button.y = pointer_coordinate(raw.button.y, host->logical_height);
        }
        if (!hosted && native_windows_filter_root(&raw) < 0) continue;
        if (raw.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED &&
            raw.window.windowID == SDL_GetWindowID(host->window))
            raw.type = SDL_EVENT_QUIT; /* other visible windows keep SDL from quitting */
        if (event_observer && event_observer(event_observer_context, &raw)) continue;
        switch (raw.type) {
            case SDL_EVENT_QUIT: event->kind=HOST_EVENT_QUIT; break;
            case SDL_EVENT_MOUSE_MOTION:
                event->kind=HOST_EVENT_MOUSE_MOVE;
                event->x=(int16_t)raw.motion.x; event->y=(int16_t)raw.motion.y; break;
            case SDL_EVENT_MOUSE_BUTTON_DOWN:
            case SDL_EVENT_MOUSE_BUTTON_UP:
                event->kind=raw.type == SDL_EVENT_MOUSE_BUTTON_DOWN ?
                            HOST_EVENT_MOUSE_DOWN : HOST_EVENT_MOUSE_UP;
                event->x=(int16_t)raw.button.x; event->y=(int16_t)raw.button.y;
                event->button=raw.button.button; break;
            case SDL_EVENT_KEY_DOWN:
            case SDL_EVENT_KEY_UP:
                event->key=dos_key(&raw.key);
                event->kind=raw.type == SDL_EVENT_KEY_DOWN ?
                           HOST_EVENT_KEY_DOWN : HOST_EVENT_KEY_UP;
                event->modifiers=dos_modifiers(raw.key.mod);
                event->extended = raw.key.key == SDLK_RCTRL ||
                    raw.key.key == SDLK_RALT || raw.key.key == SDLK_KP_ENTER ||
                    raw.key.key == SDLK_UP || raw.key.key == SDLK_DOWN ||
                    raw.key.key == SDLK_LEFT || raw.key.key == SDLK_RIGHT ||
                    raw.key.key == SDLK_HOME || raw.key.key == SDLK_END ||
                    raw.key.key == SDLK_PAGEUP || raw.key.key == SDLK_PAGEDOWN ||
                    raw.key.key == SDLK_INSERT || raw.key.key == SDLK_DELETE;
                if (!event->key) continue;
                break;
            default: continue;
        }
        /* Caller attaches its source-derived logical clock. SDL timestamps
         * never advance game state or introduce a presentation-rate tick. */
        if (virtual_quantum) {
            if (event->kind == HOST_EVENT_MOUSE_MOVE ||
                event->kind == HOST_EVENT_MOUSE_DOWN || event->kind == HOST_EVENT_MOUSE_UP) {
                host->replay_state.x = event->x;
                host->replay_state.y = event->y;
                if (event->button == SDL_BUTTON_LEFT)
                    host->replay_state.left_button_down = event->kind == HOST_EVENT_MOUSE_DOWN;
            }
            if (event->kind == HOST_EVENT_KEY_DOWN || event->kind == HOST_EVENT_KEY_UP)
                host->replay_state.dos_modifiers = event->modifiers;
        }
        if (test_raw_sequence) {
            if (test_raw_sequence!=test_inputs+1) abort();
            ++test_inputs;
            fprintf(stderr,"Observer admitted input %u pump=%" PRIu64 " reads=%" PRIu64 "\n",test_inputs,test_pumps,test_reads);
            portable_test_input_delivered(test_inputs);
        }
        return 1;
    }
    return 0;
}

int host_present(Host *host, const uint8_t *pixels, size_t stride,
                 const HostPalette *palette)
{
    int x,y;
    SDL_FRect crop;
    if (!host || !pixels || !palette || stride < (size_t)host->logical_width) return 0;
    crop.x = 0; crop.y = (float)host->crop_top;
    crop.w = (float)host->logical_width; crop.h = (float)(host->logical_height - host->crop_top);
    for (y=0;y<host->logical_height;y++) for (x=0;x<host->logical_width;x++) {
        uint8_t index = pixels[y*stride+x];
        uint8_t *out = host->rgba + (y*host->logical_width+x)*4;
        if (index >= 16) { SDL_SetError("Palette index exceeds EGA domain"); return 0; }
        memcpy(out, palette->rgb[index], 3); out[3]=255;
    }
    if (!(SDL_UpdateTexture(host->texture, NULL, host->rgba,
                host->logical_width*4) &&
           SDL_SetRenderDrawColor(host->renderer,0,0,0,255) &&
           SDL_RenderClear(host->renderer) &&
           SDL_RenderTexture(host->renderer,host->texture,&crop,NULL) &&
           SDL_RenderPresent(host->renderer))) return 0;
    host->presented_palette = *palette;
    host->frame_presented = 1;
    return 1;
}

int host_save_frame(Host *host, const char *path)
{
    SDL_Surface *surface;
    int okay;
    if (!host || !path) return 0;
    surface = SDL_CreateSurfaceFrom(host->logical_width,host->logical_height,
                    SDL_PIXELFORMAT_RGBA32,host->rgba,host->logical_width*4);
    if (!surface) return 0;
    okay=SDL_SaveBMP(surface,path);
    SDL_DestroySurface(surface);
    return okay;
}
