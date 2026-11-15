#include "portable/tests/enhanced/workspace_disabled.inc"
#include "portable/whole_program/platform/sdl3/host_modes.h"
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"line %d: %s: %s\n",__LINE__,#x,SDL_GetError()); exit(71); } } while (0)
int native_windows_translate(SDL_Event *e) { (void)e; return 0; }
int native_windows_take_deferred(SDL_Event *e) { (void)e; return 0; }
int native_windows_filter_root(SDL_Event *e) { (void)e; return 0; }
int native_windows_pointer(float *x, float *y) { (void)x; (void)y; return 0; }
void native_windows_root_pointer(float *x, float *y) { (void)x; (void)y; }
static HostEvent drain(Host *h, HostEventKind kind)
{
    HostEvent e = {0}, result = {0};
    while (host_poll_event(h, &e) > 0) if (e.kind == kind) result=e;
    return result;
}
int main(int argc, char **argv)
{
    if (argc < 2 || strcmp(argv[1], "--windowed")) SDL_SetHint(SDL_HINT_VIDEO_DRIVER,"dummy");
    Host *h=host_create_dimensions("SimAnt desktop fixture",1,640,480); CHECK(h);
    SDL_Window *w=host_sdl_window(h);
    SDL_Renderer *r=SDL_GetRenderer(w);
    const int sizes[][2]={{320,240},{900,700},{1280,960},{1920,1080},{641,481}};
    host_virtual_clock_configure(1000000);
    for (unsigned n=0;n<SDL_arraysize(sizes);++n) {
        CHECK(SDL_SetWindowSize(w,sizes[n][0],sizes[n][1]));
        SDL_Delay(50); drain(h,HOST_EVENT_NONE);
        SDL_FRect rect; CHECK(SDL_GetRenderLogicalPresentationRect(r,&rect));
        int pw,ph;CHECK(SDL_GetWindowSizeInPixels(w,&pw,&ph));
        printf("size=%dx%d pixels=%dx%d viewport=%.2f,%.2f,%.2f,%.2f\n",sizes[n][0],sizes[n][1],pw,ph,rect.x,rect.y,rect.w,rect.h);fflush(stdout);
        CHECK(fabs(rect.w/rect.h-640.0/480.0)<.001);
        CHECK(rect.x>=0 && rect.y>=0 && rect.x+rect.w<=pw+.1 && rect.y+rect.h<=ph+.1);
        for (int y=0;y<480;y+=79) for (int x=0;x<640;x+=91) {
            HostEvent e={.kind=HOST_EVENT_MOUSE_MOVE,.x=(int16_t)x,.y=(int16_t)y};
            CHECK(host_push_pointer_event(h,&e));HostEvent actual=drain(h,HOST_EVENT_MOUSE_MOVE);
            CHECK(abs(actual.x-x)<=1 && abs(actual.y-y)<=1);
            /* A physical hit at a source pixel's centre must select that
             * exact pixel, including fractional downscaling and odd margins. */
            SDL_Event raw={0};raw.type=SDL_EVENT_MOUSE_MOTION;raw.motion.windowID=SDL_GetWindowID(w);
            CHECK(SDL_RenderCoordinatesToWindow(r,x+.5f,y+.5f,&raw.motion.x,&raw.motion.y));
            CHECK(SDL_PushEvent(&raw));actual=drain(h,HOST_EVENT_MOUSE_MOVE);
            CHECK(actual.x==x && actual.y==y);
        }
    }
    if (argc>1 && !strcmp(argv[1],"--windowed")) {
        int count=0;SDL_DisplayID *displays=SDL_GetDisplays(&count);CHECK(displays);
        printf("driver=%s displays=%d\n",SDL_GetCurrentVideoDriver(),count);
        for (int i=0;i<count;++i) {
            SDL_Rect bounds;CHECK(SDL_GetDisplayBounds(displays[i],&bounds));
            CHECK(SDL_SetWindowPosition(w,bounds.x+30,bounds.y+30));SDL_Delay(150);drain(h,HOST_EVENT_NONE);
            printf("display=%u bounds=%d,%d,%d,%d scale=%.2f window_scale=%.2f density=%.2f actual_display=%u\n",
                displays[i],bounds.x,bounds.y,bounds.w,bounds.h,SDL_GetDisplayContentScale(displays[i]),
                SDL_GetWindowDisplayScale(w),SDL_GetWindowPixelDensity(w),SDL_GetDisplayForWindow(w));
            CHECK(SDL_GetDisplayForWindow(w)==displays[i]);
            HostEvent point={.kind=HOST_EVENT_MOUSE_MOVE,.x=319,.y=239};
            CHECK(host_push_pointer_event(h,&point));HostEvent mapped=drain(h,HOST_EVENT_MOUSE_MOVE);
            CHECK(abs(mapped.x-point.x)<=1 && abs(mapped.y-point.y)<=1);
        }
        SDL_free(displays);
    }
    SDL_Event e={0};e.type=SDL_EVENT_KEY_DOWN;e.key.key=SDLK_Z;e.key.scancode=SDL_SCANCODE_Y;e.key.down=true;
    CHECK(SDL_PushEvent(&e));HostEvent key=drain(h,HOST_EVENT_KEY_DOWN);CHECK(key.key==0x1579);
    e.type=SDL_EVENT_TEXT_INPUT;e.text.text="composed text";
    CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_DOWN).kind==HOST_EVENT_NONE);
    const SDL_Scancode reserved[]={SDL_SCANCODE_TAB,SDL_SCANCODE_F4,SDL_SCANCODE_SPACE};
    for (unsigned i=0;i<SDL_arraysize(reserved);++i) {
        memset(&e,0,sizeof(e));e.type=SDL_EVENT_KEY_DOWN;e.key.scancode=reserved[i];e.key.mod=SDL_KMOD_ALT;
        CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_DOWN).kind==HOST_EVENT_NONE);
    }
    memset(&e,0,sizeof(e));e.type=SDL_EVENT_KEY_DOWN;e.key.scancode=SDL_SCANCODE_F10;
    CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_DOWN).key==0x4400);
    e.key.scancode=SDL_SCANCODE_LALT;e.key.mod=SDL_KMOD_LALT;
    CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_DOWN).key==0x3800);
    if (!SDL_GetKeyboardFocus()) {
        HostEvent down={.kind=HOST_EVENT_MOUSE_DOWN,.button=SDL_BUTTON_LEFT,.x=200,.y=200};
        CHECK(host_push_pointer_event(h,&down));CHECK(drain(h,HOST_EVENT_MOUSE_DOWN).kind==HOST_EVENT_MOUSE_DOWN);
        HostInputState state;CHECK(host_get_input_state(h,&state) && state.left_button_down);
        memset(&e,0,sizeof(e));e.type=SDL_EVENT_WINDOW_FOCUS_LOST;e.window.windowID=SDL_GetWindowID(w);
        CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_MOUSE_UP).kind==HOST_EVENT_MOUSE_UP);
        CHECK(host_get_input_state(h,&state) && !state.left_button_down);
    }
    /* A fullscreen shortcut is consumed on both edges, including repeat. */
    if (argc>1 && !strcmp(argv[1],"--windowed")) {
        for (int n=0;n<2;++n) {
            memset(&e,0,sizeof(e));e.type=SDL_EVENT_KEY_DOWN;e.key.scancode=SDL_SCANCODE_RETURN;e.key.mod=SDL_KMOD_ALT;
            CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_DOWN).kind==HOST_EVENT_NONE);
            SDL_Delay(100);drain(h,HOST_EVENT_NONE);
            CHECK(!!(SDL_GetWindowFlags(w)&SDL_WINDOW_FULLSCREEN)==!n);
            HostEvent point={.kind=HOST_EVENT_MOUSE_MOVE,.x=319,.y=239};
            CHECK(host_push_pointer_event(h,&point));HostEvent mapped=drain(h,HOST_EVENT_MOUSE_MOVE);
            CHECK(abs(mapped.x-point.x)<=1 && abs(mapped.y-point.y)<=1);
            e.type=SDL_EVENT_KEY_UP;CHECK(SDL_PushEvent(&e));CHECK(drain(h,HOST_EVENT_KEY_UP).kind==HOST_EVENT_NONE);
        }
    }
    CHECK(host_set_top_crop(h,17));SDL_Delay(50);drain(h,HOST_EVENT_NONE);
    HostEvent cropped={.kind=HOST_EVENT_MOUSE_MOVE,.x=200,.y=200};
    CHECK(host_push_pointer_event(h,&cropped));HostEvent mapped=drain(h,HOST_EVENT_MOUSE_MOVE);
    CHECK(abs(mapped.x-cropped.x)<=1 && abs(mapped.y-cropped.y)<=1);
    host_destroy(h);puts("PASS desktop mapping and physical key");return 0;
}
