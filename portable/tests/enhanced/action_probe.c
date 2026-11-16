/* Independent control-path comparator, linked only by action_equivalence.py.
 * Baseline replays original events at the same source seam; native lanes use HWNDs. */
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/platform/window_hosting.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
char action_observer_anchor;
extern int32_t main_iteration_count;
extern int16_t clip_window_z_order [];
extern void __real_enhanced_execute_next(void), __real_enhanced_source_poll(void);
extern int16_t edit_scroll_and_redraw(int16_t,int16_t);
extern int16_t win_IsWinOpen(int16_t);
extern void win_ToTop(int16_t), win_Open(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t);
extern void OpenModeWindow(void), OpenCasteWindow(void), OpenHistoryWindow(void), MapToYard(void), YardToMap(void);
static int phase, number, started, modal_inputs;
static HWND named(const char * name) {
    HWND h = NULL;
    while ((h = FindWindowExA(NULL, h, NULL, name))) {
        DWORD pid;
        GetWindowThreadProcessId(h, & pid);
        if (pid == GetCurrentProcessId()) return h;
    }
    return NULL;
}
static void dump(int slot) {
    const char * path = getenv("SIMANT_ACTION_CONFIG");
    FILE * config = fopen(path, "r");
    if (! config) abort();
    char base [2048];
    unsigned count;
    if (fscanf(config, "%2047s%u", base, & count) != 2) abort();
    char output [2100];
    snprintf(output, sizeof (output), "%s.%d", base, slot);
    FILE * out = fopen(output, "wb");
    if (! out) abort();
    for (unsigned i = 0; i < count; ++ i) {
        unsigned slices;
        if (fscanf(config, "%u", & slices) != 1) abort();
        for (unsigned j = 0; j < slices; ++ j) {
            long long offset;
            unsigned size;
            if (fscanf(config, "%lld%u", & offset, & size) != 2) abort();
            fwrite(& action_observer_anchor + offset, 1, size, out);
        }
    }
    fclose(config);
    fclose(out);
}
static void original(unsigned event) {
    if(event==0xe400){edit_scroll_and_redraw(2,0);return;}
    int h = 0, v = 0;
    if (event == 0xe310 || event == 0xe311) {
        event = event == 0xe310 ? 17 : 18;
        const SimWindowRefEntry * e = & sim_window_ref_registry.entries [0];
        const uint8_t * b = (const uint8_t *) e->view.object_table [event];
        h=sim_window_wire_read_i16(b,0);v=sim_window_wire_read_i16(b,6)-(sim_window_wire_read_i16(b,6)-sim_window_wire_read_i16(b,2))/2;
    }
    int16_t owner = event >= 0xfd00 ? INT16_MIN : (int16_t)(event & 0xff00);
    if (owner != INT16_MIN) {
        if (owner == 0x1200) OpenModeWindow();
        else if (owner == 0x1300) OpenCasteWindow();
        else if (owner == 0x1500) OpenHistoryWindow();
        else {
            if (owner == 0x100 && !win_IsWinOpen(0x100)) YardToMap();
            if (owner == 0x1900) MapToYard();
            win_ToTop(owner);
            win_Open(owner, 0, 0, 0, 0, 0);
        }
    }
    if (! portable_m1b73_try_enqueue_command((int16_t) event, 0, 0, h, v)) abort();
}
void __wrap_enhanced_source_poll(void) {
    __real_enhanced_source_poll();
    const EnhancedSnapshot * s = enhanced_snapshot();
    if (phase != 2 || ! s || ! s->dialogs.modal || modal_inputs > 8) return;
    /* Retained source tasks are answered through ordinary SDL keyboard events. */
    static uint64_t token;
    if (token == s->dialogs.task_token) return;
    token = s->dialogs.task_token;
    ++ modal_inputs;
    if(s->dialogs.owner==0x1800){
        /* ScoreDialog accepts a real click; 180C is its source Continue text.
         * Escape is deliberately not substituted for this original outcome. */
        for(unsigned i=0;i<s->dialogs.object_count;++i)if(s->dialogs.objects[i].id==0x180c){
            const EnhancedRect *r=&s->dialogs.objects[i].rect;
            for(unsigned j=0;j<sim_window_hosting_count();++j){SimHostedWindowView view;if(sim_window_hosting_view(j,&view)&&view.id==0x1800){
                int strip=view.drag_bottom>view.drag_top&&view.drag_top>=view.top_y&&view.drag_bottom<view.bottom?view.drag_bottom-view.top_y:0;
                HostEvent down={.kind=HOST_EVENT_MOUSE_DOWN,.button=SDL_BUTTON_LEFT,.x=(r->left+r->right)/2-view.left,.y=(r->top+r->bottom)/2-view.top_y-strip},up=down;up.kind=HOST_EVENT_MOUSE_UP;
                native_windows_push_pointer(0x1800,&down);native_windows_push_pointer(0x1800,&up);return;
            }}
        }
        return;
    }
    SDL_Event down = {
        .type = SDL_EVENT_KEY_DOWN
    }
    , up = {
        .type = SDL_EVENT_KEY_UP
    };
    down.key.scancode = SDL_SCANCODE_ESCAPE;
    down.key.key = SDLK_ESCAPE;
    down.key.down = 1;
    up.key = down.key;
    up.type = SDL_EVENT_KEY_UP;
    up.key.down = 0;
    SDL_PushEvent(& down);
    SDL_PushEvent(& up);
}
void __wrap_enhanced_execute_next(void) {
    const EnhancedSnapshot * s = enhanced_snapshot();
    if (! s || s->panels.game_type < 0) {
        __real_enhanced_execute_next();
        return;
    }
    if (! phase && main_iteration_count > 20) {
        phase = 1;
        enhanced_submit_event(0xfd41, 0, 0, 0);
    }
    if (phase == 1 && main_iteration_count > 70 && s->panels.paused && ! s->dialogs.modal) {
        number = (int) strtol(getenv("SIMANT_ACTION_EVENT"), NULL, 0);
        const char * mode = getenv("SIMANT_ACTION_MODE");
        phase = 2;
        started = main_iteration_count;
        dump(0);
        if (! strcmp(mode, "original")) original(number);
        else if (! strcmp(mode, "menu")) {
            HWND main = NULL;
            while ((main = FindWindowExA(NULL, main, NULL, "SimAnt"))) {
                DWORD pid;
                GetWindowThreadProcessId(main, & pid);
                if (pid == GetCurrentProcessId() && GetMenu(main)) break;
            }
            if (! main) abort();
            SendMessage(main, WM_COMMAND, (WPARAM) number, 0);
        }
        else if (number == 0xe400) {
            HWND game=named("SimAnt - Game");
            typedef UINT(WINAPI *Dpi)(HWND);
            Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");
            int delta=MulDiv(32,dpi?dpi(game):96,96);
            SendMessage(game,WM_MBUTTONDOWN,MK_MBUTTON,MAKELPARAM(150,120));
            SendMessage(game,WM_MOUSEMOVE,MK_MBUTTON,MAKELPARAM(150-delta,120));
            SendMessage(game,WM_MBUTTONUP,0,MAKELPARAM(150-delta,120));
        }
        else if (number >= 0xfd43 && number <= 0xfd46) {
            HWND h = named("Map / Ant Control Panel");
            if (! strcmp(mode, "keyboard")) {
                SetFocus(h);
                SendMessage(h, WM_KEYDOWN, '1' + number - 0xfd43, 0);
            }
            else {
                SendMessage(GetDlgItem(h, 0xe300), CB_SETCURSEL, number - 0xfd43, 0);
                SendMessage(h, WM_COMMAND, MAKEWPARAM(0xe300, CBN_SELCHANGE), (LPARAM) GetDlgItem(h, 0xe300));
            }
        }
        else {
            int panel = atoi(getenv("SIMANT_ACTION_PANEL"));
            HWND h = named(panel == 4 ? "Map / Ant Control Panel" : "Yard Control Panel");
            HWND b = GetDlgItem(h, number);
            if (! h || ! b) {
                fprintf(stderr, "ACTION_MISSING_CONTROL %x\n", number);
                exit(71);
            }
            if (number == 0xe310 || number == 0xe311) {
                RECT r;
                GetClientRect(b, & r);
                if (!strcmp(mode, "keyboard")) {
                    SetFocus(b);
                    SendMessage(b, WM_KEYDOWN, '5', 0);
                } else {
                    SendMessage(b, WM_LBUTTONDOWN, MK_LBUTTON, MAKELPARAM(r.right / 2, r.bottom / 2));
                    SendMessage(b, WM_LBUTTONUP, 0, MAKELPARAM(r.right / 2, r.bottom / 2));
                }
            }
            else if (! strcmp(mode, "keyboard")) {
                SetFocus(b);
                SendMessage(b, WM_KEYDOWN, VK_SPACE, 0);
                SendMessage(b, WM_KEYUP, VK_SPACE, 0);
            }
            else SendMessage(b, BM_CLICK, 0, 0);
        }
    }
    else if (phase == 2 && main_iteration_count > started + 4 && ! s->dialogs.modal) {
        phase = 3;
        dump(1);
        const EnhancedActionLedger * l = enhanced_action_ledger();
        fprintf(stderr, "ACTION_RESULT {\"event\":%d,\"before_iteration\":%d,\"after_iteration\":%ld,\"delivered\":%llu,\"modal_inputs\":%d}\n", number, started, (long) main_iteration_count, (unsigned long long) l->delivered, modal_inputs);
    }
    __real_enhanced_execute_next();
}
