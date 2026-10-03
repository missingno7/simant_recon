#include "host_modes.h"
#include <SDL3/SDL.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

struct Host {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Texture *texture;
    uint8_t *rgba;
    uint8_t dos_scan_down[256];
    int logical_width, logical_height;
    int integer_scaling;
};

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
        !SDL_SetRenderLogicalPresentation(host->renderer, width, height,
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
uint64_t host_time_ns(void) { return SDL_GetTicksNS(); }
void host_wait_ms(uint32_t milliseconds) { SDL_Delay(milliseconds); }

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

int host_get_input_state(Host *host, HostInputState *state)
{
    float window_x, window_y, logical_x, logical_y;
    SDL_MouseButtonFlags buttons;
    if (host == NULL || state == NULL) return 0;
    buttons = SDL_GetMouseState(&window_x, &window_y);
    if (!SDL_RenderCoordinatesFromWindow(host->renderer, window_x, window_y,
                                         &logical_x, &logical_y) ||
        logical_x < (float)INT16_MIN || logical_x > (float)INT16_MAX ||
        logical_y < (float)INT16_MIN || logical_y > (float)INT16_MAX)
        return 0;
    state->x = (int16_t)logical_x;
    state->y = (int16_t)logical_y;
    state->left_button_down = (uint8_t)((buttons & SDL_BUTTON_LMASK) != 0);
    state->dos_modifiers = dos_modifiers(SDL_GetModState());
    return 1;
}

int host_warp_pointer(Host *host, int16_t logical_x, int16_t logical_y)
{
    float window_x, window_y;
    if (host == NULL || !SDL_RenderCoordinatesToWindow(host->renderer,
            (float)logical_x, (float)logical_y, &window_x, &window_y))
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
                                       (float)event->y, &x, &y)) return 0;
    if (event->kind == HOST_EVENT_MOUSE_MOVE) {
        raw.type = SDL_EVENT_MOUSE_MOTION;
        raw.motion.windowID = SDL_GetWindowID(host->window);
        raw.motion.x = x;
        raw.motion.y = y;
    } else if ((event->kind == HOST_EVENT_MOUSE_DOWN ||
                event->kind == HOST_EVENT_MOUSE_UP) && event->button >= 1 &&
               event->button <= 3) {
        raw.type = event->kind == HOST_EVENT_MOUSE_DOWN ?
                   SDL_EVENT_MOUSE_BUTTON_DOWN : SDL_EVENT_MOUSE_BUTTON_UP;
        raw.button.windowID = SDL_GetWindowID(host->window);
        raw.button.button = event->button;
        raw.button.down = event->kind == HOST_EVENT_MOUSE_DOWN;
        raw.button.clicks = 1;
        raw.button.x = x;
        raw.button.y = y;
    } else return 0;
    return SDL_PushEvent(&raw);
}

int host_is_dos_scan_down(Host *host, uint8_t scan, int *down)
{
    if (host == NULL || down == NULL || scan == 0) return 0;
    *down = host->dos_scan_down[scan] != 0;
    return 1;
}

int host_poll_event(Host *host, HostEvent *event)
{
    SDL_Event raw;
    if (!host || !event) return 0;
    while (SDL_PollEvent(&raw)) {
        memset(event, 0, sizeof(*event));
        if (!SDL_ConvertEventToRenderCoordinates(host->renderer, &raw)) return -1;
        switch (raw.type) {
            case SDL_EVENT_QUIT: event->kind=HOST_EVENT_QUIT; break;
            case SDL_EVENT_WINDOW_FOCUS_LOST:
                memset(host->dos_scan_down, 0, sizeof(host->dos_scan_down));
                continue;
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
                if ((event->key >> 8) != 0)
                    host->dos_scan_down[event->key >> 8] =
                        (uint8_t)(raw.type == SDL_EVENT_KEY_DOWN);
                if (raw.key.repeat) continue;
                event->kind=raw.type == SDL_EVENT_KEY_DOWN ?
                           HOST_EVENT_KEY_DOWN : HOST_EVENT_KEY_UP;
                event->modifiers=dos_modifiers(raw.key.mod);
                if (!event->key) continue;
                break;
            default: continue;
        }
        /* Caller attaches its source-derived logical clock. SDL timestamps
         * never advance game state or introduce a presentation-rate tick. */
        return 1;
    }
    return 0;
}

int host_present(Host *host, const uint8_t *pixels, size_t stride,
                 const HostPalette *palette)
{
    int x,y;
    if (!host || !pixels || !palette || stride < (size_t)host->logical_width) return 0;
    for (y=0;y<host->logical_height;y++) for (x=0;x<host->logical_width;x++) {
        uint8_t index = pixels[y*stride+x];
        uint8_t *out = host->rgba + (y*host->logical_width+x)*4;
        if (index >= 16) { SDL_SetError("Palette index exceeds EGA domain"); return 0; }
        memcpy(out, palette->rgb[index], 3); out[3]=255;
    }
    return SDL_UpdateTexture(host->texture, NULL, host->rgba,
                host->logical_width*4) &&
           SDL_SetRenderDrawColor(host->renderer,0,0,0,255) &&
           SDL_RenderClear(host->renderer) &&
           SDL_RenderTexture(host->renderer,host->texture,NULL,NULL) &&
           SDL_RenderPresent(host->renderer);
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
