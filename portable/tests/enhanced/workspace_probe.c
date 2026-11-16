/* Source-seam test: real native windows and ordinary messages, no game calls. */
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/sdl3/native_menu.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/enhanced/actions.h"
#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void);
static int phase, checks, failures,activation_iteration,activation_ready;
#define CHECK(c) do{++checks;if(!(c)){++failures;fprintf(stderr,"WORKSPACE_CHECK %d: %s\n",__LINE__,#c);}}while(0)
static HWND named(const char * name) {
    HWND h = NULL;
    while ((h = FindWindowExA(NULL, h, NULL, name))) {
        DWORD pid;
        GetWindowThreadProcessId(h, & pid);
        if (pid == GetCurrentProcessId()) return h;
    }
    return NULL;
}
static HWND main_window(void) {
    HWND h = NULL;
    while ((h = FindWindowExA(NULL, h, NULL, "SimAnt"))) {
        DWORD pid;
        GetWindowThreadProcessId(h, & pid);
        if (pid == GetCurrentProcessId() && GetMenu(h)) return h;
    }
    return NULL;
}
static void exercise(HWND main) {
    Workspace old = * native_workspace_layout();
    static EnhancedSnapshot before;
    before = * enhanced_snapshot();
    for (unsigned i = 0; i < 16; ++ i) CHECK(native_workspace_operation(i));
    CHECK(native_workspace_apply(& old));
    HWND game = named("SimAnt - Game"), ant = named("Map / Ant Control Panel"), yard = named("Yard Control Panel");
    CHECK(game && ant && yard);
    typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");RECT mr,gr;GetClientRect(named("Map"),&mr);GetClientRect(game,&gr);fprintf(stderr,"NATIVE_DPI main=%u game=%u map=%u map_client=%ld,%ld game_client=%ld,%ld\n",dpi?dpi(main):0,dpi?dpi(game):0,dpi?dpi(named("Map")):0,mr.right,mr.bottom,gr.right,gr.bottom);
    if (! game || ! ant || ! yard) return;
    CHECK(GetWindow(game, GW_OWNER) == main && GetWindow(ant, GW_OWNER) == main);
    CHECK((GetWindowLongPtr(game, GWL_STYLE) & (WS_THICKFRAME | WS_MAXIMIZEBOX)) == (WS_THICKFRAME | WS_MAXIMIZEBOX));
    CHECK(! (GetWindowLongPtr(game, GWL_STYLE) & WS_MINIMIZEBOX));
    CHECK(! (GetWindowLongPtr(ant, GWL_STYLE) & (WS_THICKFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX)));
    RECT prior;
    GetWindowRect(ant, & prior);
    SendMessage(ant, WM_ENTERSIZEMOVE, 0, 0);
    RECT client;
    GetClientRect(main, & client);
    MapWindowPoints(main, NULL, (POINT *) & client, 2);
    RECT r = {
        client.left + 2, client.top + 2, client.left + prior.right - prior.left + 2, client.top + prior.bottom - prior.top + 2
    };
    SendMessage(ant, WM_MOVING, WMSZ_TOPLEFT, (LPARAM) & r);
    SetWindowPos(ant, NULL, r.left, r.top, r.right - r.left, r.bottom - r.top, SWP_NOZORDER | SWP_NOACTIVATE);
    SendMessage(ant, WM_EXITSIZEMOVE, 0, 0);
    CHECK(native_workspace_layout()->panels [WS_ANT].edge == WS_TOP || native_workspace_layout()->panels [WS_ANT].edge == WS_LEFT);
    SendMessage(ant, WM_SYSCOMMAND, 0xe204, 0);
    CHECK(native_workspace_layout()->panels [WS_ANT].edge == WS_FLOAT);
    SendMessage(main,WM_COMMAND,0xe103,0);CHECK(IsWindowVisible(named("SimAnt - Red Nest")));SendMessage(named("SimAnt - Red Nest"),WM_CLOSE,0,0);CHECK(!IsWindowVisible(named("SimAnt - Red Nest")));
    int z = native_workspace_layout()->panels [WS_GAME].zoom;
    POINT at = {
        80, 80
    };
    ClientToScreen(game, & at);
    SendMessage(game, WM_MOUSEWHEEL, MAKEWPARAM(0, WHEEL_DELTA), MAKELPARAM(at.x, at.y));
    CHECK(native_workspace_layout()->panels [WS_GAME].zoom > z);
    SetFocus(game);
    SendMessage(game, WM_KEYDOWN, VK_F6, 0);
    CHECK(GetFocus() != game);
    CHECK(native_workspace_apply(& old));
    const char * path = getenv("SIMANT_WORKSPACE_LAYOUT");
    FILE * f = fopen(path, "r");
    Workspace disk;
    CHECK(f != NULL);
    if (f) {
        CHECK(ws_read(& disk, f));
        fclose(f);
        disk.revision = old.revision;
        CHECK(! memcmp(& disk, & old, sizeof (old)));
    }
    CHECK(! memcmp(& before, enhanced_snapshot(), sizeof (before)));
}
static void scene(int id, HWND main) {
    Workspace w = * native_workspace_layout();
    w.panels [WS_ANT].x = 24;
    w.panels [WS_ANT].y = 72;
    w.panels [WS_YARD_CONTROL].x = 24;
    w.panels [WS_YARD_CONTROL].y = 1200;
    w.panels [WS_GAME].x = 24;
    w.panels [WS_GAME].y = 300;
    w.panels [WS_GAME].w = 460;
    w.panels [WS_GAME].h = 350;
    w.panels [WS_MAP].x = 510;
    w.panels [WS_MAP].y = 300;
    w.panels [WS_BEHAVIOR].x = 24;
    w.panels [WS_BEHAVIOR].y = 660;
    w.panels [WS_CASTE].x = 284;
    w.panels [WS_CASTE].y = 660;
    w.panels [WS_BLACK].visible = 1;
    w.panels [WS_BLACK].x = 24;
    w.panels [WS_BLACK].y = 880;
    w.panels [WS_BLACK].w = 460;
    w.panels [WS_BLACK].h = 300;
    w.panels[WS_RED]=w.panels[WS_BLACK];w.panels[WS_RED].x=510;w.panels[WS_RED].visible=1;
    typedef UINT(WINAPI *Dpi)(HWND);Dpi get=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int dpi=get?get(main):96;
    SetWindowPos(main,NULL,12,12,MulDiv(1100,dpi,96),MulDiv(1400,dpi,96),SWP_NOZORDER|SWP_NOACTIVATE);
    if (id == 1) {
        ws_attach(& w, WS_ANT, WS_TOP, 0);
        ws_attach(& w, WS_YARD_CONTROL, WS_BOTTOM, 0);
        ws_attach(& w, WS_MAP, WS_RIGHT, 240);
    }
    if (id == 5) w.panels [WS_GAME].zoom = 300;
    if (id == 6) w.panels [WS_GAME].zoom = 50;
    CHECK(native_workspace_apply(& w));
    if(id==3||id==4){HWND target=named(id==3?"Map / Ant Control Panel":"Yard Control Panel");SetWindowPos(target,HWND_TOP,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE);}
    RedrawWindow(main, NULL, NULL, RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW);
}
static VOID CALLBACK menu_capture(HWND h, UINT message, UINT_PTR id, DWORD time) {
    (void) message;
    (void) time;
    KillTimer(h, id);
    const char * path = getenv("SIMANT_WORKSPACE_CAPTURE");
    if (path) CHECK(native_workspace_capture(path));
    PostMessage(h, WM_CANCELMODE, 0, 0);
    EndMenu();
}
void __wrap_enhanced_execute_next(void) {
    const EnhancedSnapshot * s = enhanced_snapshot();
    if (! s || s->panels.game_type < 0) {
        __real_enhanced_execute_next();
        return;
    }
    static int restored;
    if(!restored&&getenv("SIMANT_WORKSPACE_EXPECT_LAYOUT")){
        restored=1;Workspace expected;FILE *file=fopen(getenv("SIMANT_WORKSPACE_EXPECT_LAYOUT"),"r");int okay=file&&ws_read(&expected,file);if(file)fclose(file);
        if(okay){const Workspace *actual=native_workspace_layout();for(int p=0;p<WS_PANELS;++p){const WsPanel *a=&actual->panels[p],*e=&expected.panels[p];if(memcmp(a,e,7*sizeof(int))||a->zoom!=e->zoom||strcmp(a->monitor,e->monitor))okay=0;}}
        CHECK(okay);fprintf(stderr,"WORKSPACE_RESTORE {\"passed\":%s}\n",okay?"true":"false");
    }
    if (! phase && main_iteration_count > 20) {
        phase = 1;
        CHECK(enhanced_submit_event(0xfd26, 0, 0, 0) == ENHANCED_QUEUED);
        CHECK(enhanced_submit_event(0xfd41, 0, 0, 0) == ENHANCED_QUEUED);
    }
    if (phase == 1 && main_iteration_count > 45 && s->world.plane == 1 && s->panels.paused && ! s->dialogs.modal) {
        phase = 2;
        HWND main = main_window();
        CHECK(main != NULL);
        CHECK(native_workspace_active());
        if (! main) {
            __real_enhanced_execute_next();
            return;
        }
        static EnhancedSnapshot before;
        before = * s;
        exercise(main);
        int id = atoi(getenv("SIMANT_WORKSPACE_SCENE") ? getenv("SIMANT_WORKSPACE_SCENE") : "0");
        scene(id, main);
        CHECK(GetMenuItemCount(GetMenu(main)) == 5);
        const char * path = getenv("SIMANT_WORKSPACE_CAPTURE");
        if (id == 2) {
            SetTimer(main, 1, 100, menu_capture);
            RECT r;
            GetWindowRect(main, & r);
            TrackPopupMenu(GetSubMenu(GetMenu(main), 3), TPM_LEFTALIGN | TPM_LEFTBUTTON, r.left + 240, r.top + 50, 0, main, NULL);
        }
        else {
            HWND ant = named("Map / Ant Control Panel");
            if (id == 7) {
                RECT r;
                GetWindowRect(ant, & r);
                RECT m;
                GetClientRect(main, & m);
                MapWindowPoints(main, NULL, (POINT *) & m, 2);
                OffsetRect(& r, m.left - r.left + 2, m.top - r.top + 2);
                SendMessage(ant, WM_ENTERSIZEMOVE, 0, 0);
                SendMessage(ant, WM_MOVING, WMSZ_TOP, (LPARAM) & r);
                CHECK(IsWindowVisible(named("Edge attachment preview")));
            }
            if (id == 8) {
                HWND tip = FindWindowExA(NULL, NULL, TOOLTIPS_CLASSA, NULL);
                while (tip && GetWindow(tip, GW_OWNER) != ant) tip = FindWindowExA(NULL, tip, TOOLTIPS_CLASSA, NULL);
                CHECK(tip != NULL);
                if (tip) {
                    CHECK(SendMessage(tip,TTM_GETTOOLCOUNT,0,0)>0);
                    HWND button=GetDlgItem(ant,11);RECT bounds;GetWindowRect(button,&bounds);SetForegroundWindow(ant);SetFocus(button);SetCursorPos((bounds.left+bounds.right)/2,(bounds.top+bounds.bottom)/2);
                    SendMessage(button,WM_MOUSEHOVER,0,MAKELPARAM((bounds.right-bounds.left)/2,(bounds.bottom-bounds.top)/2));UpdateWindow(tip);
                    fprintf(stderr,"TOOLTIP_STATUS count=%lld visible=%d\n",(long long)SendMessage(tip,TTM_GETTOOLCOUNT,0,0),IsWindowVisible(tip));
                    CHECK(IsWindowVisible(tip));
                }
            }
            if (path) {
                CHECK(native_workspace_capture(path));
                if (id == 3 || id == 4) {
                    HWND target = named(id == 3 ? "Map / Ant Control Panel" : "Yard Control Panel");
                    RECT r;
                    GetWindowRect(target, & r);
                    RECT origin;
                    GetWindowRect(main, & origin);
                    OffsetRect(& r, - origin.left, - origin.top);
                    fprintf(stderr, "WORKSPACE_CROP %ld %ld %ld %ld\n", r.left, r.top, r.right, r.bottom);
                }
            }
            if (id == 7) SendMessage(ant, WM_EXITSIZEMOVE, 0, 0);
        }
        CHECK(! memcmp(& before, enhanced_snapshot(), sizeof (before)));
        fprintf(stderr, "WORKSPACE_UI {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"scene\":%d,\"generation\":%llu}\n", failures ? "false" : "true", checks, failures, id, (unsigned long long) s->generation);
        if(getenv("SIMANT_WORKSPACE_ACTIVATION")){
            activation_ready=s->panels.caste.automatic==1&&s->logical_order[0]!=0x1300;CHECK(activation_ready);
            HostEvent down={.kind=HOST_EVENT_MOUSE_DOWN,.button=SDL_BUTTON_LEFT,.x=28,.y=29},up=down;up.kind=HOST_EVENT_MOUSE_UP;
            CHECK(native_windows_push_pointer(0x1300,&down));CHECK(native_windows_push_pointer(0x1300,&up));activation_iteration=main_iteration_count;
        }

    }
    if(phase==2&&activation_iteration&&main_iteration_count>activation_iteration+4){phase=3;const EnhancedActionLedger *l=enhanced_action_ledger();int okay=activation_ready&&s->panels.caste.automatic==0&&l->last_event==0x1305&&l->prepared==1&&l->flush_completed==1;CHECK(okay);fprintf(stderr,"WORKSPACE_ACTIVATION {\"passed\":%s,\"manual\":%d,\"delivered\":%llu}\n",okay?"true":"false",s->panels.caste.automatic==0,(unsigned long long)l->delivered);}
    __real_enhanced_execute_next();
}
