/* Ordinary owned windows and edge attachment. Callbacks only submit intents. */
#include "native_workspace.h"
#include "native_menu.h"
#include "native_windows.h"
#include "host_modes.h"
#include "../m1b73_event_enqueue.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/platform/window_hosting.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/world.h"
#include "portable/whole_program/enhanced/assets.h"
#include "portable/whole_program/enhanced/actions.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static int initial_ui_scale=-1;
int native_workspace_start_scale(const char *value){
    char *end;long n;if(!value||!*value)return 0;
    if(!strcmp(value,"auto")){initial_ui_scale=0;return 1;}
    n=strtol(value,&end,10);if(*end||n<100||n>300||!ws_ui_scale_valid((int)n))return 0;
    initial_ui_scale=(int)n;return 1;
}
#ifdef _WIN32
#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <shlobj.h>
enum {
    ATTACH_LEFT = 0xe200, DETACH = 0xe204, RESET = 0xe100, SHOW_BLACK = 0xe102, SHOW_RED = 0xe103
};
#define PAPER RGB(245,242,232)
#define INK RGB(36,43,33)
#define EARTH RGB(146,113,56)
#define RUST RGB(160,45,40)
typedef struct Native {
    HWND h, tooltip;
    SDL_Window *sdl;
    HFONT font;
    int dpi, monitor_dpi, client_w,client_h, external, moving, candidate, pan, gesture, gx, gy,card_id,card_scroll,card_max;
    uint8_t keys[256];
    uint8_t edit_dirty[3],syncing;
    UINT64 content_painted;
    unsigned link_count;
    struct { RECT rect; unsigned index; } links[128];
    RECT start;
    POINT pointer;
    int start_x, start_y;
} Native;
typedef struct Picture {
    int event, art, x, y, w, h;
} Picture;
static const Picture pictures [] = {
#include "portable/whole_program/enhanced/picture_controls.inc"
};
typedef struct Button {
    int panel, event, x, y, w, h;
    const char * name;
} Button;
/* Distinct source contexts, including map plane commands that clear scent. */
static const Button buttons [] = {
    {
        WS_ANT, 5, 8, 8, 72, 44, "Map / Minimap"
    }, {
        WS_ANT, 8, 88, 8, 72, 44, "Surface (world)"
    }, {
        WS_ANT, 9, 168, 8, 72, 44, "Black Nest (world)"
    }, {
        WS_ANT, 10, 248, 8, 72, 44, "Red Nest (world)"
    }, {
        WS_ANT, 11, 328, 8, 72, 44, "Go to Yellow Ant"
    }, {
        WS_ANT, 12, 408, 8, 72, 44, "Go to Spider"
    }, {
        WS_ANT, 13, 488, 8, 72, 44, "Go to Black Queen"
    }, {
        WS_ANT, 14, 568, 8, 72, 44, "Go to Red Queen"
    }, {
        WS_ANT, 15, 8, 56, 80, 30, "Pause / Unpause"
    }, {
        WS_ANT, 16, 204, 56, 80, 30, "World Scent"
    }, {
        WS_ANT, 7, 292, 56, 40, 30, "World Tools"
    }, {
        WS_ANT, 6, 340, 56, 40, 30, "World Help"
    }, {
        WS_ANT, 0x105, 8, 92, 52, 44, "Map: Yard"
    }, {
        WS_ANT, 0x106, 68, 92, 60, 44, "Map: Surface (clear scent)"
    }, {
        WS_ANT, 0x107, 144, 92, 44, 44, "Map: Black Nest (clear scent)"
    }, {
        WS_ANT, 0x108, 188, 92, 44, 44, "Map: Red Nest (clear scent)"
    }, {
        WS_ANT, 0x109, 240, 92, 48, 44, "Map: Black Nest Scent"
    }, {
        WS_ANT, 0x10a, 296, 92, 48, 44, "Map: Black Trail"
    }, {
        WS_ANT, 0x10b, 352, 92, 40, 44, "Map: Alarm"
    }, {
        WS_ANT, 0x10c, 400, 92, 48, 44, "Map: Red Nest Scent"
    }, {
        WS_ANT, 0x10d, 456, 92, 48, 44, "Map: Red Trail"
    }, {
        WS_ANT, 0x116, 512, 92, 40, 44, "Map Help"
    }, {
        WS_ANT, 0x117, 560, 92, 40, 44, "Map Tools"
    }, {
        WS_ANT, 0x10e, 608, 92, 40, 44, "Original map background toggle (%)"
    }, {
        WS_ANT, 0x10f, 8, 144, 40, 36, "Behavior"
    }, {
        WS_ANT, 0x111, 56, 144, 40, 36, "Caste"
    }, {
        WS_ANT, 0x113, 104, 144, 40, 36, "History"
    }, {
        WS_ANT, 0x115, 152, 144, 40, 36, "Info"
    }, {
        WS_ANT, 0x114, 200, 144, 40, 36, "Status"
    }, {
        WS_ANT, 0x112, 248, 144, 40, 36, "Mystery"
    }, {
        WS_ANT, 0x118, 296, 144, 124, 48, "Population"
    }, {
        WS_ANT, 0x110, 428, 144, 40, 36, "Map to Yellow Ant"
    }, {
        WS_YARD_CONTROL, 0x1907, 8, 8, 64, 44, "Patch"
    }, {
        WS_YARD_CONTROL, 0x1908, 80, 8, 64, 44, "Yard / House"
    }, {
        WS_YARD_CONTROL, 0xfd22, 152, 8, 64, 44, "House"
    }, {
        WS_YARD_CONTROL, 0x1909, 224, 8, 64, 44, "Strategic"
    }, {
        WS_YARD_CONTROL, 0x190a, 296, 8, 64, 44, "Graphic"
    }, {
        WS_YARD_CONTROL, 0x190b, 368, 8, 64, 44, "Mate (Full Game; requires breeders)"
    }, {
        WS_YARD_CONTROL, 0x1910, 440, 8, 64, 44, "Place Queen (requires a stored queen)"
    }, {
        WS_YARD_CONTROL, 0x1911, 512, 8, 40, 44, "Yard Help"
    }, {
        WS_YARD_CONTROL, 0x190d, 96, 56, 120, 28, "Automatic queen drop"
    }, {
        WS_YARD_CONTROL, 0x190e, 224, 56, 120, 28, "Manual queen drop"
    }
};
static struct {
    int active, applying, saving, focus, ready, source_plane, source_x, source_y,painting;
    int follow, follow_x, follow_y; /* smooth camera target set by a source view move */
    HWND root, preview;
    SDL_WindowID sdl_id;
    int dpi,info_popup,status_continue_pending,root_width,root_height,scaling;
    Workspace layout;
    Native windows [WS_PANELS];
    HostPalette palette;
    char path [2048], hint[160];
    UINT64 last_paint, modal_token;
} u;
static LRESULT CALLBACK window_proc(HWND, UINT, WPARAM, LPARAM);
static LRESULT CALLBACK managed_proc(HWND, UINT, WPARAM, LPARAM, UINT_PTR, DWORD_PTR);
static LRESULT CALLBACK root_proc(HWND, UINT, WPARAM, LPARAM, UINT_PTR, DWORD_PTR);
static LRESULT CALLBACK child_proc(HWND, UINT, WPARAM, LPARAM, UINT_PTR, DWORD_PTR);
static void arrange(void);
static void fixed_client(Native *,int,int);
static void save(void);
static int scale(int v, int dpi) {
    return MulDiv(v, dpi, 96);
}
static int dpi_of(HWND h) {
    typedef UINT(WINAPI * GetDpi)(HWND);
    GetDpi f = (GetDpi) GetProcAddress(GetModuleHandleA("user32.dll"), "GetDpiForWindow");
    return f ? (int) f(h) : 96;
}
static HFONT make_font(int dpi);
static int effective_dpi(int physical){return u.layout.ui_scale?MulDiv(u.layout.ui_scale,96,100):physical?physical:96;}
static int point_dpi(POINT at){
    if(u.layout.ui_scale)return effective_dpi(96);
    HMODULE lib=LoadLibraryA("shcore.dll");UINT x=96,y=96;
    if(lib){typedef HRESULT(WINAPI *GetDpi)(HMONITOR,int,UINT *,UINT *);GetDpi f=(GetDpi)GetProcAddress(lib,"GetDpiForMonitor");
        if(!f||FAILED(f(MonitorFromPoint(at,MONITOR_DEFAULTTONEAREST),0,&x,&y)))x=dpi_of(u.root);FreeLibrary(lib);}
    else x=dpi_of(u.root);return (int)x;
}
int native_workspace_ui_dpi(void *window){if(window)return effective_dpi(dpi_of((HWND)window));POINT at;GetCursorPos(&at);return point_dpi(at);}
static int metric(int what,int dpi){
    typedef int(WINAPI *Metric)(int,UINT);Metric f=(Metric)GetProcAddress(GetModuleHandleA("user32.dll"),"GetSystemMetricsForDpi");
    return f?f(what,dpi):MulDiv(GetSystemMetrics(what),dpi,96);
}
static int caption_extra(Native *n){
    DWORD ex=n->h?(DWORD)GetWindowLongPtr(n->h,GWL_EXSTYLE):WS_EX_TOOLWINDOW;
    return scale(26,n->dpi)-metric(ex&WS_EX_TOOLWINDOW?SM_CYSMCAPTION:SM_CYCAPTION,n->h?dpi_of(n->h):n->monitor_dpi);
}
static void resize_fonts(int p){
    Native *n=&u.windows[p];HFONT old=n->font;n->font=make_font(n->dpi);
    for(HWND c=GetWindow(n->h,GW_CHILD);c;c=GetWindow(c,GW_HWNDNEXT)){
        SendMessage(c,WM_SETFONT,(WPARAM)n->font,TRUE);
        int w=(int)(INT_PTR)GetPropA(c,"SimAntLogicalW"),h=(int)(INT_PTR)GetPropA(c,"SimAntLogicalH");
        if(w&&h){int x=(int)(INT_PTR)GetPropA(c,"SimAntLogicalX")-1,y=(int)(INT_PTR)GetPropA(c,"SimAntLogicalY")-1;
            MoveWindow(c,scale(x,n->dpi),scale(y,n->dpi),scale(w,n->dpi),scale(h,n->dpi),TRUE);}
    }
    if(n->tooltip){SendMessage(n->tooltip,WM_SETFONT,(WPARAM)n->font,TRUE);SendMessage(n->tooltip,TTM_SETMAXTIPWIDTH,0,scale(340,n->dpi));}
    if(old)DeleteObject(old);n->content_painted=0;
}
static RECT main_client(void) {
    RECT r;
    GetClientRect(u.root, & r);
    MapWindowPoints(u.root, NULL, (POINT *) & r, 2);
    return r;
}
static HFONT make_font(int dpi) {
    return CreateFontW(- scale(13, dpi), 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Tahoma");
}
static POINT native_cursor_point(void){
    POINT p={0,0};
    if(!GetCursorPos(&p)&&u.root){RECT r;GetWindowRect(u.root,&r);p=(POINT){(r.left+r.right)/2,(r.top+r.bottom)/2};}
    return p;
}
static void color_fill(HDC dc, RECT r, COLORREF color) {
    HBRUSH b = CreateSolidBrush(color);
    FillRect(dc, & r, b);
    DeleteObject(b);
}
static RECT attached(int p, RECT r, int edge, int offset) {
    (void) p;
    RECT m = main_client();
    int w = r.right - r.left, h = r.bottom - r.top, at = scale(offset, u.dpi);
    if (edge < 2) {
        r.left = edge == WS_LEFT ? m.left : m.right - w;
        r.top = m.top + at;
    }
    else {
        r.left = m.left + at;
        r.top = edge == WS_TOP ? m.top : m.bottom - h;
    }
    r.right = r.left + w;
    r.bottom = r.top + h;
    return r;
}
typedef struct MonitorFind {
    const char * name;
    HMONITOR found;
} MonitorFind;
static BOOL CALLBACK find_monitor(HMONITOR h, HDC dc, LPRECT r, LPARAM arg) {
    (void) dc;
    (void) r;
    MonitorFind * f = (MonitorFind *) arg;
    MONITORINFOEXA m = {
        .cbSize = sizeof (m)
    };
    GetMonitorInfoA(h, (MONITORINFO *) & m);
    if (! strcmp(m.szDevice, f->name)) f->found = h;
    return TRUE;
}
static RECT restored(int p) {
    WsPanel * v = & u.layout.panels [p];
    Native * n = & u.windows [p];
    MonitorFind find = {
        v->monitor, NULL
    };
    EnumDisplayMonitors(NULL, NULL, find_monitor, (LPARAM) & find);
    MONITORINFO m = {
        .cbSize = sizeof (m)
    };
    GetMonitorInfo(find.found ? find.found : MonitorFromWindow(u.root, MONITOR_DEFAULTTONEAREST), & m);
    int dpi = n->dpi ? n->dpi : u.dpi;
    RECT r = {
        m.rcWork.left + scale(v->x, dpi), m.rcWork.top + scale(v->y, dpi), 0, 0
    };
    int w = scale(v->w, dpi), h = scale(v->h, dpi);
    if(!ws_resizable(p)&&n->client_w){
        RECT frame,client;GetWindowRect(n->h,&frame);GetClientRect(n->h,&client);w=scale(n->client_w,dpi)+frame.right-frame.left-client.right;h=scale(n->client_h,dpi)+frame.bottom-frame.top-client.bottom;
    }
    /* Recover a caption without stretching a fixed client or losing saved bounds. */
    if (w <= m.rcWork.right - m.rcWork.left && r.left > m.rcWork.right - w) r.left = m.rcWork.right - w;
    else if (r.left > m.rcWork.right - scale(80, dpi)) r.left = m.rcWork.right - scale(80, dpi);
    if (r.left < m.rcWork.left) r.left = m.rcWork.left;
    if (h <= m.rcWork.bottom - m.rcWork.top && r.top > m.rcWork.bottom - h) r.top = m.rcWork.bottom - h;
    else if (r.top > m.rcWork.bottom - scale(32, dpi)) r.top = m.rcWork.bottom - scale(32, dpi);
    if (r.top < m.rcWork.top) r.top = m.rcWork.top;
    r.right = r.left + w;
    r.bottom = r.top + h;
    return v->edge >= 0 ? attached(p, r, v->edge, v->offset) : r;
}
static void root_size(int width,int height){
    MONITORINFO monitor={.cbSize=sizeof(monitor)};GetMonitorInfo(MonitorFromWindow(u.root,MONITOR_DEFAULTTONEAREST),&monitor);
    int maxw=monitor.rcWork.right-monitor.rcWork.left-scale(16,u.dpi),maxh=monitor.rcWork.bottom-monitor.rcWork.top-scale(64,u.dpi);
    if(width>maxw)width=maxw;if(height>maxh)height=maxh;if(width<320)width=320;if(height<240)height=240;
    SDL_Window *window=SDL_GetWindowFromID(u.sdl_id);int w,h;SDL_GetWindowSize(window,&w,&h);if(w!=width||h!=height)SDL_SetWindowSize(window,width,height);
}
static void save(void) {
    if (u.saving || ! u.path [0]) return;
    u.saving = 1;
    char tmp [2100];
    snprintf(tmp, sizeof (tmp), "%s.tmp", u.path);
    FILE * f = fopen(tmp, "w");
    if (f) {
        int okay = ws_write(& u.layout, f);
        if (fclose(f)) okay = 0;
        if (okay) MoveFileExA(tmp, u.path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
        else DeleteFileA(tmp);
    }
    u.saving = 0;
}
static void remember(int p) {
    Native * n = & u.windows [p];
    if (u.applying || ! n->h) return;
    RECT r;
    GetWindowRect(n->h, & r);
    WsPanel * v = & u.layout.panels [p];
    if (v->edge < 0) {
        MONITORINFOEXA m = {
            .cbSize = sizeof (m)
        };
        GetMonitorInfoA(MonitorFromWindow(n->h, MONITOR_DEFAULTTONEAREST), (MONITORINFO *) & m);
        int dpi = n->dpi ? n->dpi : u.dpi;
        v->x = MulDiv(r.left - m.rcWork.left, 96, dpi);
        v->y = MulDiv(r.top - m.rcWork.top, 96, dpi);
        v->w = MulDiv(r.right - r.left, 96, dpi);
        v->h = MulDiv(r.bottom - r.top, 96, dpi);
        snprintf(v->monitor, sizeof (v->monitor), "%s", m.szDevice);
    }
    ++ u.layout.revision;
    save();
}
static void outline(RECT r) {
    if (! u.preview) u.preview = CreateWindowExA(WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT, "STATIC", "Edge attachment preview", WS_POPUP | SS_BLACKRECT, 0, 0, 1, 1, u.root, NULL, GetModuleHandle(NULL), NULL);
    int w = r.right - r.left, h = r.bottom - r.top, t = scale(3, u.dpi);
    HRGN outer = CreateRectRgn(0, 0, w, h), inner = CreateRectRgn(t, t, w - t, h - t);
    CombineRgn(outer, outer, inner, RGN_DIFF);
    DeleteObject(inner);
    SetWindowRgn(u.preview, outer, FALSE);
    SetWindowPos(u.preview, HWND_TOP, r.left, r.top, w, h, SWP_SHOWWINDOW | SWP_NOACTIVATE);
}
static void moving(int p, RECT r) {
    Native * n = & u.windows [p];
    RECT m = main_client();
    int dist [4] = {
        abs(r.left - m.left), abs(r.right - m.right), abs(r.top - m.top), abs(r.bottom - m.bottom)
    }
    , best = - 1;
    for (int i = 0; i < 4; ++ i) if (dist [i] <= scale(28, u.dpi) && (best < 0 || dist [i] < dist [best])) best = i;
    if (r.right < m.left || r.left > m.right || r.bottom < m.top || r.top > m.bottom) best = - 1;
    n->candidate = best;
    if (best >= 0) {
        int offset = best < 2 ? MulDiv(r.top - m.top, 96, u.dpi) : MulDiv(r.left - m.left, 96, u.dpi);
        if (offset < 0) offset = 0;
        outline(attached(p, r, best, offset));
    }
    else if (u.preview) ShowWindow(u.preview, SW_HIDE);
}
static void end_move(int p) {
    Native * n = & u.windows [p];
    if (! n->moving) return;
    n->moving = 0;
    RECT r;
    GetWindowRect(n->h, & r);
    if (u.preview) ShowWindow(u.preview, SW_HIDE);
    if (EqualRect(& r, & n->start)) {
        n->candidate = - 1;
        return;
    }
    if (n->candidate >= 0) {
        RECT m = main_client();
        int offset = n->candidate < 2 ? MulDiv(r.top - m.top, 96, u.dpi) : MulDiv(r.left - m.left, 96, u.dpi);
        ws_attach(& u.layout, p, n->candidate, offset < 0 ? 0 : offset);
    }
    else {
        ws_detach(& u.layout, p);
        remember(p);
    }
    arrange();
    save();
}
static void system_entries(HWND h) {
    HMENU sys = GetSystemMenu(h, FALSE);
    if (! sys) return;
    AppendMenuA(sys, MF_SEPARATOR, 0, NULL);
    HMENU attach = CreatePopupMenu();
    const char * edge [] = {
        "Left", "Right", "Top", "Bottom"
    };
    for (int i = 0; i < 4; ++ i) AppendMenuA(attach, MF_STRING, ATTACH_LEFT + i, edge [i]);
    AppendMenuA(sys, MF_POPUP, (UINT_PTR) attach, "Attach to Edge");
    AppendMenuA(sys, MF_STRING, DETACH, "Detach");
}
static void layout_command(int p, int command) {
    if (p < 0 || p >= WS_PANELS) return;
    if (command >= ATTACH_LEFT && command < ATTACH_LEFT + 4) ws_attach(& u.layout, p, command - ATTACH_LEFT, 0);
    else if (command == DETACH) ws_detach(& u.layout, p);
    else return;
    arrange();
    save();
}
static void system_popup(HWND h, int p) {
    HMENU menu = CreatePopupMenu(), attach = CreatePopupMenu();
    const char * names [] = {
        "Left", "Right", "Top", "Bottom"
    };
    AppendMenuA(menu, MF_STRING, SC_MOVE, "Move");native_menu_theme_item(menu,0,"Move");
    for (int i = 0; i < 4; ++ i){AppendMenuA(attach, MF_STRING, ATTACH_LEFT + i, names [i]);native_menu_theme_item(attach,i,names[i]);}
    AppendMenuA(menu, MF_POPUP, (UINT_PTR) attach, "Attach to Edge");
    AppendMenuA(menu, MF_STRING, DETACH, "Detach");native_menu_theme_item(menu,1,"Attach to Edge");native_menu_theme_item(menu,2,"Detach");
    RECT r;
    GetWindowRect(h, & r);
    POINT at=native_cursor_point();
    int id = TrackPopupMenu(menu, TPM_RETURNCMD | TPM_LEFTBUTTON, at.x+scale(8,u.windows[p].dpi),at.y+scale(8,u.windows[p].dpi),0,h,NULL);
    DestroyMenu(menu);
    if (id == SC_MOVE) SendMessage(h, WM_SYSCOMMAND, SC_MOVE, 0);
    else layout_command(p, id);
}
int native_workspace_shortcut(unsigned msg, uintptr_t key) {
    if (! u.active || (msg != WM_KEYDOWN && msg != WM_SYSKEYDOWN)) return 0;
    if(key==VK_ESCAPE&&enhanced_submit_wait_dismiss())return 1;
    HWND f = GetFocus();
    char cls [32] = {
        0
    };
    GetClassNameA(f, cls, sizeof (cls));
    if (! strcmp(cls, "Edit") || ! strcmp(cls, "ComboBox")) return 0;
    int ctrl = GetKeyState(VK_CONTROL) < 0, shift = GetKeyState(VK_SHIFT) < 0;
    if (key == VK_F6) {
        int direction = shift ? - 1 : 1;
        for (int i = 1; i <= WS_PANELS; ++ i) {
            int p = (u.focus + WS_PANELS + direction * i) % WS_PANELS;
            HWND h = u.windows [p].h;
            if (h && IsWindowVisible(h)) {
                u.focus = p;
                SetForegroundWindow(h);
                SetFocus(h);
                break;
            }
        }
        return 1;
    }
    if(key==VK_F10&&msg==WM_KEYDOWN&&GetKeyState(VK_SHIFT)>=0){SetForegroundWindow(u.root);PostMessage(u.root,WM_SYSCOMMAND,SC_KEYMENU,0);return 1;}
    if(msg==WM_SYSKEYDOWN&&(key=='F'||key=='W'||key=='V'||key=='O'||key=='S')){SetForegroundWindow(u.root);PostMessage(u.root,WM_SYSCOMMAND,SC_KEYMENU,(LPARAM)(key+32));return 1;}
    const EnhancedSnapshot *snapshot=enhanced_snapshot();
    if(snapshot&&snapshot->dialogs.modal)return 0;
    if(key==VK_F1&&msg==WM_KEYDOWN){unsigned help=u.focus==WS_MAP?0x116:u.focus==WS_YARD||u.focus==WS_YARD_CONTROL?0x1911:u.focus==WS_BEHAVIOR?0x1203:u.focus==WS_CASTE?0x1303:u.focus==WS_HISTORY?0x150d:6;enhanced_submit_event(help,0,0,0);return 1;}
    unsigned event = 0;
    if (ctrl) {
        if (key >= '1' && key <= '7') event = 0xfd11 + (unsigned) key - '1';
        else if (key == 'N') event = 0xfd03;
        else if (key == 'O') event = 0xfd04;
        else if (key == 'S') event = shift ? 0xfd06 : 0xfd05;
        else if (key == VK_F4) {
            if (ws_closable(u.focus) && u.windows [u.focus].h) SendMessage(u.windows [u.focus].h, WM_CLOSE, 0, 0);
            return 1;
        }
    }
    else if (msg == WM_KEYDOWN) {
        if (key == 'P') event = 0xfd41;
        else if (key >= '1' && key <= '4') event = 0xfd43 + (unsigned) key - '1';
    }
    if (event) {
        native_menu_command(event);
        return 1;
    }
    return 0;
}
static HWND make_control(HWND parent, const char * cls, const char * name, DWORD style, int id) {
    HWND h = CreateWindowExA(0, cls, name, WS_CHILD | WS_VISIBLE | style, 0, 0, 1, 1, parent, (HMENU)(INT_PTR) id, GetModuleHandle(NULL), NULL);
    SendMessage(h, WM_SETFONT, (WPARAM) u.windows [parent == u.windows [WS_ANT].h ? WS_ANT : WS_YARD_CONTROL].font, TRUE);
    SetWindowSubclass(h, child_proc, 71, 0);
    return h;
}
static void add_tooltip(Native * n, HWND control, const char * text) {
    (void)n;(void)control;(void)text; /* One tracking tooltip only. */
}
static const Picture * picture(int event) {
    if (event == 0xfd22) event = 0x1908;
    for (unsigned i = 0; i < sizeof (pictures) / sizeof (pictures [0]); ++ i) if (pictures [i].event == event) return & pictures [i];
    return NULL;
}
static void panel_children(int p) {
    Native * n = & u.windows [p];
    n->tooltip = CreateWindowExA(WS_EX_TOPMOST, TOOLTIPS_CLASSA, NULL, WS_POPUP | TTS_ALWAYSTIP | TTS_NOPREFIX, 0, 0, 0, 0, n->h, NULL, GetModuleHandle(NULL), NULL);
    SendMessage(n->tooltip,WM_SETFONT,(WPARAM)n->font,TRUE);
    SendMessage(n->tooltip, TTM_SETMAXTIPWIDTH, 0, scale(340, n->dpi));
    TOOLINFOA tracking={.cbSize=sizeof(tracking),.uFlags=TTF_TRACK|TTF_ABSOLUTE,.hwnd=n->h,.uId=0x7fff,.lpszText=""};
    SendMessageA(n->tooltip,TTM_ADDTOOLA,0,(LPARAM)&tracking);
    for (unsigned i = 0; i < sizeof (buttons) / sizeof (buttons [0]); ++ i) {
        const Button * b = & buttons [i];
        if (b->panel != p) continue;
        HWND h = make_control(n->h, "BUTTON", b->name, WS_TABSTOP | BS_OWNERDRAW, b->event);
        add_tooltip(n, h, b->name);
    }
    if (p == WS_ANT) {
        HWND combo = make_control(n->h, "COMBOBOX", "Game speed", WS_TABSTOP | CBS_DROPDOWNLIST, 0xe300);
        const char * speeds [] = {
            "Slow", "Normal", "Fast", "Ultra"
        };
        for (int i = 0; i < 4; ++ i) SendMessageA(combo, CB_ADDSTRING, 0, (LPARAM) speeds [i]);
        add_tooltip(n, combo, "Game speed");
    }
    for (int i = 0; i < 2; ++ i) {
        HWND h = make_control(n->h, "BUTTON", i ? "Black warning threshold" : "Yellow warning threshold", WS_TABSTOP | BS_OWNERDRAW, 0xe310 + i);
        add_tooltip(n, h, i ? "Black health / warning threshold" : "Yellow health / warning threshold");
    }
}
static void size_children(int p) {
    Native * n = & u.windows [p];
    for (unsigned i = 0; i < sizeof (buttons) / sizeof (buttons [0]); ++ i) {
        const Button * b = & buttons [i];
        if (b->panel == p) MoveWindow(GetDlgItem(n->h, b->event), scale(b->x, n->dpi), scale(b->y, n->dpi), scale(b->w, n->dpi), scale(b->h, n->dpi), TRUE);
    }
    if (p == WS_ANT) {
        SendMessage(GetDlgItem(n->h, 0xe300), WM_SETFONT, (WPARAM) n->font, TRUE);
    }
    if (p == WS_ANT) MoveWindow(GetDlgItem(n->h, 0xe300), scale(96, n->dpi), scale(58, n->dpi), scale(100, n->dpi), scale(160, n->dpi), TRUE);
    for (int i = 0; i < 2; ++ i) MoveWindow(GetDlgItem(n->h, 0xe310 + i), scale(480 + i * 152, n->dpi), scale(p == WS_ANT ? 150 : 90, n->dpi), scale(144, n->dpi), scale(32, n->dpi), TRUE);
}
static void draw_indexed(HDC dc, RECT r, const uint8_t * indices, int w, int h) {
    uint32_t * rgb = malloc((size_t) w * h * 4);
    if (! rgb) return;
    int masked=0;
    for (int i = 0; i < w * h; ++ i) {
        const uint8_t * c = u.palette.rgb [indices [i] & 15];
        masked|=indices[i]==255;
        rgb [i] = indices [i] == 255 ? 0 : (c [0] << 16) | (c [1] << 8) | c [2];
    }
    BITMAPINFO info = {
        .bmiHeader = {
            .biSize = sizeof (BITMAPINFOHEADER),.biWidth = w,.biHeight = - h,.biPlanes = 1,.biBitCount = 32,.biCompression = BI_RGB
        }
    };
    SetStretchBltMode(dc, COLORONCOLOR);
    if(masked){
        uint32_t *mask=malloc((size_t)w*h*4);if(!mask){free(rgb);return;}
        for(int i=0;i<w*h;++i)mask[i]=indices[i]==255?0xffffff:0;
        StretchDIBits(dc,r.left,r.top,r.right-r.left,r.bottom-r.top,0,0,w,h,mask,&info,DIB_RGB_COLORS,SRCAND);
        free(mask);
    }
    StretchDIBits(dc, r.left, r.top, r.right - r.left, r.bottom - r.top, 0, 0, w, h, rgb, & info, DIB_RGB_COLORS, masked?SRCPAINT:SRCCOPY);
    free(rgb);
}
int native_workspace_art_paint(void *dc,int id,int x,int y){
    const EnhancedArt *a=enhanced_art(id);if(!a)return 0;
    draw_indexed((HDC)dc,(RECT){x,y,x+a->width,y+a->height},a->pixels,a->width,a->height);return 1;
}
static int selected(unsigned event, const EnhancedSnapshot * s) {
    if (! s) return 0;
    switch (event) {
        case 8 :
        case 9 :
        case 10 :
        return s->world.plane == (int) event - 7;
        case 15 :
        return s->panels.paused;
        case 0x190d :
        return s->overview.placement_auto;
        case 0x190e :
        return ! s->overview.placement_auto;
        case 0x106 :
        case 0x107 :
        case 0x108 :
        return s->world.plane == (int) event - 0x105 && s->overview.map_mode < 4;
        case 0x109 :
        return s->overview.map_mode == 4;
        case 0x10a :
        return s->overview.map_mode == 5;
        case 0x10b :
        return s->overview.map_mode == 8;
        case 0x10c :
        return s->overview.map_mode == 6;
        case 0x10d :
        return s->overview.map_mode == 7;
        case 0x1908 :
        return s->overview.yard_mode < 2;
        case 0xfd22 :
        return s->overview.yard_mode == 1;
        case 0x1909 :
        return s->overview.yard_mode == 2;
        case 0x190a :
        return s->overview.yard_mode == 3;
    }
    return 0;
}
static void text(HDC dc, RECT r, const char * s, int flags) {
    SetTextColor(dc, INK);
    SetBkMode(dc, TRANSPARENT);
    DrawTextA(dc, s, - 1, & r, flags);
}
/* DOS bevel: a dark outline, light leading edge and earth shadow. */
static void game_edge(HDC dc,RECT r,int down,int dpi){
    HBRUSH dark=CreateSolidBrush(RGB(85,44,4));FrameRect(dc,&r,dark);DeleteObject(dark);
    int t=scale(1,dpi);if(t<1)t=1;InflateRect(&r,-t,-t);
    color_fill(dc,(RECT){r.left,r.top,r.right,r.top+t},down?EARTH:RGB(255,255,255));
    color_fill(dc,(RECT){r.left,r.top,r.left+t,r.bottom},down?EARTH:RGB(255,255,255));
    color_fill(dc,(RECT){r.left,r.bottom-t,r.right,r.bottom},down?RGB(255,255,255):EARTH);
    color_fill(dc,(RECT){r.right-t,r.top,r.right,r.bottom},down?RGB(255,255,255):EARTH);
    if(down){InflateRect(&r,-t,-t);HBRUSH gold=CreateSolidBrush(RGB(255,243,4));FrameRect(dc,&r,gold);DeleteObject(gold);}
}
static void meter(HDC dc, RECT r, int value, int warning, COLORREF c, const char * label) {
    char s [80];
    snprintf(s, sizeof (s), "%s  %d", label, value);
    int marker=(r.bottom-r.top+5)/10;if(marker<1)marker=1;
    RECT t = r;
    t.bottom = t.top + (r.bottom - r.top) * 2 / 3;
    text(dc, t, s, DT_SINGLELINE | DT_LEFT);
    r.top = t.bottom;
    color_fill(dc, r, RGB(219, 214, 197));
    RECT bar = r;
    if (value < 0) value = 0;
    if (value > 100) value = 100;
    bar.right = r.left + MulDiv(r.right - r.left, value, 100);
    color_fill(dc, bar, c);
    FrameRect(dc, & r, GetStockObject(GRAY_BRUSH));
    if (warning >= 0) {
        int x = r.left + MulDiv(r.right - r.left, warning, 100);
        POINT triangle [] = {
            {
                x - marker, r.top - marker
            }, {
                x + marker, r.top - marker
            }, {
                x, r.top + marker-1
            }
        };
        HGDIOBJ old = SelectObject(dc, GetStockObject(BLACK_BRUSH));
        Polygon(dc, triangle, 3);
        SelectObject(dc, old);
    }
}
/* Native clients repaint periodically from the live snapshot. Painting through an
 * off-screen bitmap makes each refresh reach the screen as one copy, so the
 * background fill under the content is never visible (no flicker). */
static void buffered(HDC target, RECT r, int p, void (* draw)(HDC, RECT, int)) {
    int w = r.right - r.left, h = r.bottom - r.top;
    HDC mem = w > 0 && h > 0 ? CreateCompatibleDC(target) : NULL;
    HBITMAP bmp = mem ? CreateCompatibleBitmap(target, w, h) : NULL;
    if (! bmp) {
        if (mem) DeleteDC(mem);
        draw(target, r, p);
        return;
    }
    HGDIOBJ old = SelectObject(mem, bmp);
    SetWindowOrgEx(mem, r.left, r.top, NULL);
    draw(mem, r, p);
    SetWindowOrgEx(mem, 0, 0, NULL);
    BitBlt(target, r.left, r.top, w, h, mem, 0, 0, SRCCOPY);
    SelectObject(mem, old);
    DeleteObject(bmp);
    DeleteDC(mem);
}
static void draw_button_direct(DRAWITEMSTRUCT * d, int p);
static void draw_button(DRAWITEMSTRUCT * d, int p) {
    RECT r = d->rcItem;
    int w = r.right - r.left, h = r.bottom - r.top;
    HDC mem = w > 0 && h > 0 ? CreateCompatibleDC(d->hDC) : NULL;
    HBITMAP bmp = mem ? CreateCompatibleBitmap(d->hDC, w, h) : NULL;
    if (! bmp) {
        if (mem) DeleteDC(mem);
        draw_button_direct(d, p);
        return;
    }
    HGDIOBJ old = SelectObject(mem, bmp);
    DRAWITEMSTRUCT item = * d;
    item.hDC = mem;
    item.rcItem = (RECT) { 0, 0, w, h };
    draw_button_direct(& item, p);
    BitBlt(d->hDC, r.left, r.top, w, h, mem, 0, 0, SRCCOPY);
    SelectObject(mem, old);
    DeleteObject(bmp);
    DeleteDC(mem);
}
static void draw_button_direct(DRAWITEMSTRUCT * d, int p) {
    Native * n = & u.windows [p];
    const EnhancedSnapshot * s = enhanced_snapshot();
    RECT r = d->rcItem;
    if(p==WS_BEHAVIOR||p==WS_CASTE){
        const EnhancedAllocationSnapshot *a=s?(p==WS_BEHAVIOR?&s->panels.behavior:&s->panels.caste):NULL;
        int slot=(int)d->CtlID-(p==WS_BEHAVIOR?0x1203:0x1303);
        int on=(d->itemState&ODS_SELECTED)||(a&&slot>=0&&slot<6&&(a->control_flags[slot]&4));
        color_fill(d->hDC,r,on?RUST:PAPER);game_edge(d->hDC,r,on,n->dpi);
        SelectObject(d->hDC,n->font);SetTextColor(d->hDC,on?RGB(255,255,255):INK);SetBkMode(d->hDC,TRANSPARENT);
        char label[80];GetWindowTextA(d->hwndItem,label,sizeof(label));DrawTextA(d->hDC,label,-1,&r,DT_CENTER|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX);
        if(d->itemState&ODS_FOCUS){InflateRect(&r,-3,-3);DrawFocusRect(d->hDC,&r);}return;
    }
    int on = selected(d->CtlID, s) || (d->itemState & ODS_SELECTED);
    if(p==WS_HISTORY&&s)for(int i=0;i<4;++i)on|=s->history.shown[i]==(int)d->CtlID-0x1503;
    color_fill(d->hDC, r, on ? RGB(219, 214, 197) : RGB(232,226,206));
    game_edge(d->hDC,r,on,n->dpi);
    SelectObject(d->hDC, n->font);
    if (d->CtlID == 0xe310 || d->CtlID == 0xe311) {
        int black = d->CtlID == 0xe311;
        InflateRect(& r, - 2, - 1);
        if (s) meter(d->hDC, r, black ? s->panels.health_black : s->panels.health_yellow, black ? s->panels.warning_black : s->panels.warning_yellow, black ? INK : EARTH, black ? "Black" : "Yellow");
    }
    else {
        Picture tool = {
            0, 5107, 0, 0, 0, 0
        };
        const Picture * pic = picture(d->CtlID);
        if(d->CtlID==0x115 || d->CtlID==0x112)pic=NULL; /* The DOS sheet leaves this slot blank. */
        if (d->CtlID == 7 || d->CtlID == 0x117) {
            tool.art=s&&s->panels.game_type==3?5100+s->panels.experiment_tool:5107;
            const EnhancedArt * icon = enhanced_art(tool.art);
            if (icon) {
                tool.w = icon->width;
                tool.h = icon->height;
                pic = & tool;
            }
        }
        const char *caption=NULL;
        switch(d->CtlID){case 8:case 0x106:caption="Surface";break;case 9:case 0x107:caption="Black Nest";break;case 10:case 0x108:caption="Red Nest";break;
        case 11:case 0x110:caption="Yellow";break;case 12:caption="Spider";break;case 13:caption="B. Queen";break;case 14:caption="R. Queen";break;
        case 0x105:caption="Yard";break;case 0x109:case 0x10c:caption="Nest scent";break;case 0x10a:case 0x10d:caption="Trail";break;case 0x10b:caption="Alarm";break;
        case 0x1907:caption="Patch";break;case 0x1908:caption="Yard";break;case 0xfd22:caption="House";break;case 0x1909:caption="Strategic";break;case 0x190a:caption="Graphic";break;case 0x190b:caption="Mate";break;case 0x1910:caption="Queen";break;}
        RECT art_rect=r;
        if(caption){art_rect.bottom-=scale(12,n->dpi);RECT label=r;label.top=art_rect.bottom;HFONT small=CreateFontA(-scale(10,n->dpi),0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,"Tahoma");HGDIOBJ old=SelectObject(d->hDC,small);text(d->hDC,label,caption,DT_CENTER|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX);SelectObject(d->hDC,old);DeleteObject(small);}
        const EnhancedArt * a = pic ? enhanced_art(pic->art) : NULL;
        if (a && pic->x >= 0 && pic->y >= 0 && pic->x + pic->w <= a->width && pic->y + pic->h <= a->height) {
            int factor=2;
            int available_w=MulDiv(art_rect.right-scale(6,n->dpi),96,n->dpi),available_h=MulDiv(art_rect.bottom-scale(4,n->dpi),96,n->dpi);
            while(factor>1&&(pic->w*factor>available_w||pic->h*factor>available_h))--factor;
            int width=scale(pic->w*factor,n->dpi),height=scale(pic->h*factor,n->dpi);
            int maxw=art_rect.right-scale(6,n->dpi),maxh=art_rect.bottom-scale(4,n->dpi);
            if(width>maxw){height=MulDiv(height,maxw,width);width=maxw;}if(height>maxh){width=MulDiv(width,maxh,height);height=maxh;}
            uint8_t * crop = malloc((size_t) pic->w * pic->h);
            if (crop) {
                for (int y = 0; y < pic->h; ++ y) memcpy(crop + y * pic->w, a->pixels + (pic->y + y) * a->width + pic->x, pic->w);
                RECT dst = {
                    (r.right - width) / 2, (art_rect.bottom - height) / 2, (r.right + width) / 2, (art_rect.bottom + height) / 2
                };
                draw_indexed(d->hDC, dst, crop, pic->w, pic->h);
                free(crop);
            }
        }
        else if(d->CtlID==0x115 || d->CtlID==0x112){
            SetBkMode(d->hDC,TRANSPARENT);SetTextColor(d->hDC,INK);
            DrawTextW(d->hDC,d->CtlID==0x115?L"\x2139":L"?",-1,&r,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        }
        else {
            char label [100];
            GetWindowTextA(d->hwndItem, label, sizeof (label));
            text(d->hDC, r, label, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
        }
    }
    if (d->itemState & ODS_DISABLED) {
        int saved = SaveDC(d->hDC);
        IntersectClipRect(d->hDC, r.left, r.top, r.right, r.bottom);
        HPEN pen = CreatePen(PS_SOLID, 1, RGB(185,185,180));
        SelectObject(d->hDC, pen);
        int height = r.bottom - r.top;
        for (int x = r.left - height; x < r.right; x += 6) {
            MoveToEx(d->hDC, x, r.bottom, NULL);
            LineTo(d->hDC, x + height, r.top);
        }
        RestoreDC(d->hDC, saved);
        DeleteObject(pen);
    }
    if (d->itemState & ODS_FOCUS) {
        InflateRect(& r, - 3, - 3);
        DrawFocusRect(d->hDC, & r);
    }
}
static void draw_panel(HDC dc, RECT r, int p) {
    Native * n = & u.windows [p];
    const EnhancedSnapshot * s = enhanced_snapshot();
    color_fill(dc,r,RGB(219,214,197));
    RECT rim=r;game_edge(dc,rim,0,n->dpi);
    if(p==WS_ANT){
        RECT groups[]={{4,4,652,88},{4,88,652,140},{4,140,472,196},{654,4,940,140},{472,144,936,196}};
        for(unsigned i=0;i<sizeof(groups)/sizeof(groups[0]);++i){RECT box={scale(groups[i].left,n->dpi),scale(groups[i].top,n->dpi),scale(groups[i].right,n->dpi),scale(groups[i].bottom,n->dpi)};color_fill(dc,box,PAPER);game_edge(dc,box,1,n->dpi);}
    }else{
        RECT groups[]={{4,4,558,56},{4,56,352,86},{568,4,940,86},{472,86,936,130}};
        for(unsigned i=0;i<sizeof(groups)/sizeof(groups[0]);++i){RECT box={scale(groups[i].left,n->dpi),scale(groups[i].top,n->dpi),scale(groups[i].right,n->dpi),scale(groups[i].bottom,n->dpi)};color_fill(dc,box,PAPER);game_edge(dc,box,1,n->dpi);}
    }
    SelectObject(dc, n->font);
    if (! s) return;
    int y = p == WS_ANT ? 150 : 90;
    RECT red = {
        scale(784, n->dpi), scale(y, n->dpi), scale(928, n->dpi), scale(y + 32, n->dpi)
    };
    meter(dc, red, s->panels.health_red, - 1, RUST, "Red");
    char label [200];
    RECT stats;
    if (p == WS_ANT) {
        stats = (RECT) {
            scale(660, n->dpi), scale(8, n->dpi), scale(940, n->dpi), scale(48, n->dpi)
        };
        snprintf(label, sizeof (label), "Population  Black %d   Red %d", s->panels.population_black, s->panels.population_red);
    }
    else {
        stats = (RECT) {
            scale(580, n->dpi), scale(8, n->dpi), scale(936, n->dpi), scale(28, n->dpi)
        };
        snprintf(label, sizeof (label), "Stored Queens %d", s->overview.stored_queens);
        text(dc, stats, label, DT_SINGLELINE);
        stats.top = scale(32, n->dpi);
        stats.bottom = scale(72, n->dpi);
        snprintf(label, sizeof (label), "%s%s", s->panels.game_type != 2 ? "Mate: Full Game only. " : "", s->overview.stored_queens <= 0 ? "Place Queen: no stored queen." : "");
        text(dc, stats, label, DT_WORDBREAK);
        RECT drop = {
            scale(8, n->dpi), scale(60, n->dpi), scale(90, n->dpi), scale(80, n->dpi)
        };
        text(dc, drop, "Queen drop", DT_SINGLELINE);
        stats = (RECT) {
            scale(8, n->dpi), scale(96, n->dpi), scale(460, n->dpi), scale(130, n->dpi)
        };
        snprintf(label, sizeof (label), "Colonies: Black %d / Red %d\nPopulation: Black %d / Red %d", s->overview.colonies_black, s->overview.colonies_red, s->panels.population_black, s->panels.population_red);
    }
    text(dc, stats, label, DT_WORDBREAK);
    int max = s->panels.population_black > s->panels.population_red ? s->panels.population_black : s->panels.population_red;
    if (max < 1) max = 1;
    for (int i = 0; i < 2; ++ i) {
        int x = p == WS_ANT ? 660 + i * 140 : 8 + i * 140, by = p == WS_ANT ? 56 : 136;
        RECT bar = {
            scale(x, n->dpi), scale(by, n->dpi), scale(x + 132, n->dpi), scale(by + 8, n->dpi)
        };
        color_fill(dc, bar, RGB(219, 214, 197));
        RECT fill = bar;
        fill.right = fill.left + MulDiv(fill.right - fill.left, i ? s->panels.population_red : s->panels.population_black, max);
        color_fill(dc, fill, i ? RUST : INK);
    }
}
/* Source strings use literal backslash-n separators. */
static void native_text(char *out,size_t size,const char *in){size_t n=0;while(*in&&n+1<size){if(in[0]=='\\'&&in[1]=='n'){out[n++]='\n';in+=2;}else out[n++]=*in++;}out[n]=0;}
static void draw_world(HDC dc, RECT r, int p) {
    const EnhancedSnapshot * s = enhanced_snapshot();
    color_fill(dc, r, RGB(85, 44, 4));
    if (! s || s->panels.game_type < 0) return;
    WsPanel * v = & u.layout.panels [p];
    Native * n = & u.windows [p];
    int plane = p == WS_GAME ? s->world.plane : p == WS_BLACK ? 2 : 3;
    int width = plane < 2 ? 2048 : 1024, height = 1024;
    uint8_t * indexed = calloc((size_t) width, height);
    if (! indexed) return;
    for (int x = 0; x < width / 16; ++ x) for (int y = 0; y < 64; ++ y) {
        ModernCell c;
        uint8_t tile [256];
        enhanced_world_cell(& s->world, plane, x, y, & c);
        if (enhanced_asset_cell(s->world.terrain_set, c.ground, c.life, tile)) for (int yy = 0; yy < 16; ++ yy) memcpy(indexed + (size_t)(y * 16 + yy) * width + x * 16, tile + yy * 16, 16);
    }
    if (plane == s->world.plane) {
        static EnhancedWorldSnapshot local;
        local = s->world;
        local.overlays.balloon_count = 0;
        enhanced_world_draw(& local, indexed, width, height, width);
    }
    if (v->camera_x < 0) v->camera_x = s->world.origin.x * 16;
    if (v->camera_y < 0) v->camera_y = s->world.origin.y * 16;
    double zoom = v->zoom / 100.0 * n->dpi / 96.0;
    int sx = v->camera_x, sy = v->camera_y, sw = (int)((r.right - r.left) / zoom) + 1, sh = (int)((r.bottom - r.top) / zoom) + 1;
    if (sx > width - 1) sx = width - 1;
    if (sy > height - 1) sy = height - 1;
    if (sw > width - sx) sw = width - sx;
    if (sh > height - sy) sh = height - sy;
    uint8_t * crop = malloc((size_t) sw * sh);
    if (crop) {
        for (int y = 0; y < sh; ++ y) memcpy(crop + y * sw, indexed + (sy + y) * width + sx, sw);
        RECT dst = {
            r.left, r.top, r.left + (int)(sw * zoom), r.top + (int)(sh * zoom)
        };
        draw_indexed(dc, dst, crop, sw, sh);
        free(crop);
    }
    free(indexed);
    SelectObject(dc, n->font);
    if(p==WS_GAME&&s->world.status[0]&&
       !(s->panels.paused&&!strcmp(s->world.status,"Game Paused"))){char message[160];native_text(message,sizeof(message),s->world.status);RECT status={r.left+8,r.bottom-scale(44,n->dpi),r.right-8,r.bottom-4};SetBkColor(dc,PAPER);SetBkMode(dc,OPAQUE);SetTextColor(dc,INK);DrawTextA(dc,message,-1,&status,DT_CENTER|DT_WORDBREAK);}
    if (p == WS_GAME && s->panels.paused) {
        RECT t = {
            r.left + 8, r.top + 4, r.right - 8, r.top + scale(24, n->dpi)
        };
        SetBkColor(dc, PAPER);
        SetBkMode(dc, OPAQUE);
        SetTextColor(dc, INK);
        DrawTextA(dc, "Game Paused", - 1, & t, DT_CENTER | DT_SINGLELINE);
    }
    if (plane == s->world.plane) for (unsigned i = 0; i < s->world.overlays.balloon_count; ++ i) {
        const EnhancedBalloon * b = & s->world.overlays.balloons [i];
        RECT t = {
            (int)((b->anchor.x - sx) * zoom), (int)((b->anchor.y - sy) * zoom), 0, 0
        };
        t.right = t.left + scale(240, n->dpi);
        t.bottom = t.top + scale(80, n->dpi);
        color_fill(dc, t, PAPER);
        char message[300];native_text(message,sizeof(message),b->text);text(dc, t, message, DT_WORDBREAK);
    }
}
#include "native_content.inc"

static void zoom(int p, int delta, POINT at) {
    if (! ws_resizable(p)) return;
    WsPanel * v = & u.layout.panels [p];
    int old = v->zoom, now = delta > 0 ? (old * 9 + 7) / 8 : old * 8 / 9;
    if (now < 25) now = 25;
    if (now > 800) now = 800;
    double before = old / 100.0 * u.windows [p].dpi / 96.0, after = now / 100.0 * u.windows [p].dpi / 96.0;
    v->camera_x += (int)(at.x / before - at.x / after);
    v->camera_y += (int)(at.y / before - at.y / after);
    v->zoom = now;
    if (p == WS_GAME) u.follow = 0;
    if (v->camera_x < 0) v->camera_x = 0;
    if (v->camera_y < 0) v->camera_y = 0;
    if (v->camera_x > 2047) v->camera_x = 2047;
    if (v->camera_y > 1023) v->camera_y = 1023;
    InvalidateRect(u.windows [p].h, NULL, FALSE);
    save();
}
static void warning_command(int id, int percent) {
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    enhanced_submit_event(id == 0xe310 ? 17 : 18, percent, -1, 0);
}
static int minimap_origin_down;
static void panel_command(int p, int id) {
    POINT at=native_cursor_point();native_workspace_anchor(at.x,at.y);
    if (id == 0xe300) {
        int speed = SendMessage(GetDlgItem(u.windows [p].h, id), CB_GETCURSEL, 0, 0);
        if (speed >= 0 && speed < 4) enhanced_submit_event(0xfd43 + speed, 0, 0, 0);
        return;
    }
    if (id == 0xe310 || id == 0xe311) {
        const EnhancedSnapshot *s = enhanced_snapshot();
        if (s) warning_command(id, id == 0xe310 ? s->panels.warning_yellow : s->panels.warning_black);
        return;
    }
    enhanced_submit_event(id, 0, 0, 0);
}
static LRESULT CALLBACK child_proc(HWND h, UINT msg, WPARAM wp, LPARAM lp, UINT_PTR id, DWORD_PTR data) {
    (void) id;
    (void) data;
    Native *parent=NULL;for(int p=WS_ANT;p<=WS_YARD_CONTROL;++p)if(u.windows[p].h==GetParent(h))parent=&u.windows[p];
    if(parent){
        TOOLINFOA tool={.cbSize=sizeof(tool),.uFlags=TTF_TRACK|TTF_ABSOLUTE,.hwnd=parent->h,.uId=0x7fff,.lpszText=u.hint};
        if(msg==WM_MOUSEMOVE){TRACKMOUSEEVENT track={sizeof(track),TME_HOVER|TME_LEAVE,h,400};TrackMouseEvent(&track);}
        if(msg==WM_MOUSEHOVER){GetWindowTextA(h,u.hint,sizeof(u.hint));POINT at={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};ClientToScreen(h,&at);SendMessageA(parent->tooltip,TTM_UPDATETIPTEXTA,0,(LPARAM)&tool);SendMessageA(parent->tooltip,TTM_TRACKACTIVATE,TRUE,(LPARAM)&tool);SendMessage(parent->tooltip,TTM_TRACKPOSITION,0,MAKELPARAM(at.x+12,at.y+20));}
        if(msg==WM_MOUSELEAVE||msg==WM_LBUTTONDOWN||msg==WM_KEYDOWN)SendMessageA(parent->tooltip,TTM_TRACKACTIVATE,FALSE,(LPARAM)&tool);
    }
    int control = GetDlgCtrlID(h);
    if(parent&&control==5){
        if(msg==WM_LBUTTONDOWN){minimap_origin_down=1;SetFocus(h);POINT at={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};ClientToScreen(h,&at);native_workspace_anchor(at.x,at.y);enhanced_submit_event(5,0,0,0);return 0;}
        if(msg==WM_LBUTTONUP){minimap_origin_down=0;return 0;}
    }
    int allocation_panel=-1;for(int p=WS_BEHAVIOR;p<=WS_CASTE;++p)if(u.windows[p].h==GetParent(h))allocation_panel=p;
    if(allocation_panel>=0){
        if(msg==BM_GETCHECK&&control>=content_owner(allocation_panel)+3&&control<=content_owner(allocation_panel)+8){
            const EnhancedSnapshot *s=enhanced_snapshot();const EnhancedAllocationSnapshot *a=s?(allocation_panel==WS_BEHAVIOR?&s->panels.behavior:&s->panels.caste):NULL;
            return a&&(a->control_flags[control-content_owner(allocation_panel)-3]&4)?BST_CHECKED:BST_UNCHECKED;
        }
        if(control>=0xe520&&control<=0xe522){
            if(msg==WM_GETDLGCODE)return DefSubclassProc(h,msg,wp,lp)|DLGC_WANTALLKEYS;
            if(msg==WM_KEYDOWN&&(wp==VK_RETURN||wp==VK_ESCAPE)){
                if(wp==VK_RETURN)content_edit_commit(allocation_panel,control-0xe520);
                else {u.windows[allocation_panel].edit_dirty[control-0xe520]=0;content_sync(allocation_panel);}
                SendMessage(h,EM_SETSEL,0,-1);return 0;
            }
            if(msg==WM_CHAR&&(wp==VK_RETURN||wp==VK_ESCAPE))return 0;
        }
    }
    if (control == 0xe310 || control == 0xe311) {
        if (msg == WM_GETDLGCODE) return DLGC_WANTARROWS;
        if (msg == WM_LBUTTONDOWN) {
            SetFocus(h);
            SetCapture(h);
            return 0;
        }
        if (msg == WM_LBUTTONUP && GetCapture() == h) {
            RECT r;
            GetClientRect(h, &r);
            ReleaseCapture();
            warning_command(control, MulDiv(GET_X_LPARAM(lp), 100, r.right ? r.right : 1));
            return 0;
        }
        if (msg == WM_KEYDOWN) {
            const EnhancedSnapshot *s = enhanced_snapshot();
            if (s) {
                int value = control == 0xe310 ? s->panels.warning_yellow : s->panels.warning_black;
                if (wp == VK_HOME) value = 0;
                else if (wp == VK_END) value = 100;
                else if (wp == VK_LEFT || wp == VK_DOWN) value -= 5;
                else if (wp == VK_RIGHT || wp == VK_UP) value += 5;
                else if (wp >= '0' && wp <= '9') value = (int)(wp - '0') * 10;
                else if (wp != VK_SPACE) goto ordinary_key;
                warning_command(control, value);
                return 0;
            }
        }
    }
ordinary_key:
    if (native_workspace_shortcut(msg, wp)) return 0;
    if (msg == WM_KEYDOWN && wp == VK_TAB) {
        HWND current=h,parent=GetParent(h);char cls[32];GetClassNameA(parent,cls,sizeof(cls));if(!strcmp(cls,"ComboBox")){current=parent;parent=GetParent(parent);}
        HWND next = GetNextDlgTabItem(parent, current, GetKeyState(VK_SHIFT) < 0);
        if (next) SetFocus(next);
        return 0;
    }
    return DefSubclassProc(h, msg, wp, lp);
}
static int common(HWND h, int p, UINT msg, WPARAM wp, LPARAM lp, LRESULT * result) {
    Native * n = & u.windows [p];
    * result = 0;
    if(native_menu_theme_message(h,msg,lp)){*result=TRUE;return 1;}
    if (native_workspace_shortcut(msg, wp)) return 1;
    if(msg==WM_NCCALCSIZE && wp && n->h){
        *result=DefWindowProc(h,msg,wp,lp);
        ((NCCALCSIZE_PARAMS *)lp)->rgrc[0].top+=caption_extra(n);return 1;
    }
    if(msg==WM_NCPAINT||msg==WM_NCACTIVATE){
        *result=n->external?DefSubclassProc(h,msg,wp,lp):DefWindowProc(h,msg,wp,lp);
        RECT frame,client;GetWindowRect(h,&frame);GetClientRect(h,&client);POINT at={0,0};ClientToScreen(h,&at);
        int border=at.x-frame.left,top=at.y-frame.top;
        HDC dc=GetWindowDC(h);if(dc&&top>border){RECT r={border,border,frame.right-frame.left-border,top};
            int active=u.focus==p;color_fill(dc,r,active?RGB(85,44,4):RGB(219,214,197));
            SelectObject(dc,n->font);SetTextColor(dc,active?PAPER:INK);SetBkMode(dc,TRANSPARENT);
            int button=scale(26,n->dpi),right=r.right;
            if(n->external?(GetWindowLongPtr(h,GWL_STYLE)&WS_SYSMENU)!=0:ws_closable(p)){RECT b={right-button,r.top,right,r.bottom};DrawTextW(dc,L"\x00d7",-1,&b,DT_CENTER|DT_VCENTER|DT_SINGLELINE);right-=button;}
            if(ws_resizable(p)){RECT b={right-button,r.top,right,r.bottom};DrawTextW(dc,IsZoomed(h)?L"\x25a3":L"\x25a1",-1,&b,DT_CENTER|DT_VCENTER|DT_SINGLELINE);right-=button;}
            r.left+=scale(6,n->dpi);r.right=right;char title[160];GetWindowTextA(h,title,sizeof(title));DrawTextA(dc,title,-1,&r,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
        }if(dc)ReleaseDC(h,dc);return 1;
    }
    if(msg==WM_NCHITTEST){
        RECT frame;GetWindowRect(h,&frame);int x=GET_X_LPARAM(lp)-frame.left,y=GET_Y_LPARAM(lp)-frame.top;
        POINT origin={0,0};ClientToScreen(h,&origin);int top=origin.y-frame.top,border=origin.x-frame.left;
        int right=frame.right-frame.left-border,button=scale(26,n->dpi);
        if(y>=border&&y<top&&x>=border&&x<right){
            if((n->external?(GetWindowLongPtr(h,GWL_STYLE)&WS_SYSMENU)!=0:ws_closable(p))&&x>=right-button){*result=HTCLOSE;return 1;}
            if(n->external?(GetWindowLongPtr(h,GWL_STYLE)&WS_SYSMENU)!=0:ws_closable(p))right-=button;
            if(ws_resizable(p)&&x>=right-button){*result=HTMAXBUTTON;return 1;}
            *result=HTCAPTION;return 1;
        }
    }
    if (msg == WM_MOUSEACTIVATE) {
        * result = MA_ACTIVATE;
        return 1;
    }
    if (msg == WM_SETFOCUS || (msg == WM_ACTIVATE && LOWORD(wp)!=WA_INACTIVE)) {
        u.focus=p;for(int i=0;i<WS_PANELS;++i)if(u.windows[i].h)RedrawWindow(u.windows[i].h,NULL,NULL,RDW_FRAME|RDW_INVALIDATE);
    }
    if (msg == WM_SYSCOMMAND && wp >= ATTACH_LEFT && wp <= DETACH) {
        layout_command(p, (int) wp);
        return 1;
    }
    if (msg == WM_SYSKEYDOWN && wp == VK_SPACE) {
        system_popup(h, p);
        return 1;
    }
    if (msg == WM_ENTERSIZEMOVE) {
        n->moving = 1;
        n->candidate = - 1;
        GetWindowRect(h, & n->start);
    }
    if (msg == WM_MOVING) moving(p, * (RECT *) lp);
    if (msg == WM_EXITSIZEMOVE) end_move(p);
    if (msg == WM_DPICHANGED) {
        n->monitor_dpi=HIWORD(wp);n->dpi=effective_dpi(n->monitor_dpi);resize_fonts(p);
        SetWindowPos(h,NULL,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);
        if (p==WS_ANT||p==WS_YARD_CONTROL)size_children(p);
        arrange();
    }
    return 0;
}
static LRESULT CALLBACK managed_proc(HWND h, UINT msg, WPARAM wp, LPARAM lp, UINT_PTR id, DWORD_PTR data) {
    (void) id;
    LRESULT result;
    int p=(int)data;
    if (common(h,p,msg,wp,lp,&result)) return result;
    if(content_panel(p) && (p==WS_STATUS||enhanced_compatibility_owner()!=content_owner(p))){
        if(msg==WM_DRAWITEM){draw_button((DRAWITEMSTRUCT *)lp,p);return TRUE;}
        if(msg==WM_CTLCOLOREDIT){SetTextColor((HDC)wp,INK);SetBkColor((HDC)wp,RGB(255,255,255));return (LRESULT)GetStockObject(WHITE_BRUSH);}
        if(p==WS_INFO&&(msg==WM_MOUSEWHEEL||msg==WM_VSCROLL)){
            Native *n=&u.windows[p];int value=n->card_scroll;
            if(msg==WM_MOUSEWHEEL)value+=GET_WHEEL_DELTA_WPARAM(wp)>0?-32:32;
            else {SCROLLINFO si={.cbSize=sizeof(si),.fMask=SIF_TRACKPOS};GetScrollInfo(h,SB_VERT,&si);
                switch(LOWORD(wp)){case SB_LINEUP:value-=16;break;case SB_LINEDOWN:value+=16;break;case SB_PAGEUP:value-=128;break;case SB_PAGEDOWN:value+=128;break;case SB_THUMBTRACK:case SB_THUMBPOSITION:value=si.nTrackPos;break;}}
            if(value<0)value=0;if(value>n->card_max)value=n->card_max;n->card_scroll=value;InvalidateRect(h,NULL,FALSE);return 0;
        }
        if(msg==WM_PAINT||msg==WM_PRINTCLIENT){PAINTSTRUCT paint;HDC dc=msg==WM_PAINT?BeginPaint(h,&paint):(HDC)wp;RECT r;GetClientRect(h,&r);if(msg==WM_PAINT)buffered(dc,r,p,content_draw);else content_draw(dc,r,p);if(msg==WM_PAINT){EndPaint(h,&paint);u.windows[p].content_painted=SDL_GetTicksNS();}return 0;}
        if(msg==WM_ERASEBKGND)return 1;
        if(msg==WM_COMMAND&&LOWORD(wp)>=0xe520&&LOWORD(wp)<=0xe522){
            int axis=LOWORD(wp)-0xe520;
            if(HIWORD(wp)==EN_CHANGE&&!u.windows[p].syncing)u.windows[p].edit_dirty[axis]=1;
            if(HIWORD(wp)==EN_KILLFOCUS)content_edit_commit(p,axis);
            return 0;
        }
        if(msg==WM_COMMAND && HIWORD(wp)==BN_CLICKED){content_command(p,LOWORD(wp));return 0;}
        if(content_mouse(h,p,msg,wp,lp))return 0;
    }
    return DefSubclassProc(h,msg,wp,lp);
}
/* Original keyboard device path for the owned GDI worlds. Consumed workspace
 * accelerators never leak a later unmatched key-up into the game. */
static int forward_world_key(Native *n,UINT msg,WPARAM key){
    if(msg==WM_SYSKEYDOWN)msg=WM_KEYDOWN;else if(msg==WM_SYSKEYUP)msg=WM_KEYUP;
    if(msg!=WM_KEYDOWN && msg!=WM_KEYUP)return 0;
    if(key>255)return 0;
    SDL_Scancode scan=SDL_SCANCODE_UNKNOWN;
    if(key>='A'&&key<='Z')scan=SDL_SCANCODE_A+key-'A';
    else if(key>='1'&&key<='9')scan=SDL_SCANCODE_1+key-'1';
    else switch(key){
        case '0':scan=SDL_SCANCODE_0;break;case VK_SPACE:scan=SDL_SCANCODE_SPACE;break;
        case VK_RETURN:scan=SDL_SCANCODE_RETURN;break;case VK_ESCAPE:scan=SDL_SCANCODE_ESCAPE;break;
        case VK_TAB:scan=SDL_SCANCODE_TAB;break;case VK_SHIFT:scan=SDL_SCANCODE_LSHIFT;break;case VK_CONTROL:scan=SDL_SCANCODE_LCTRL;break;case VK_MENU:scan=SDL_SCANCODE_LALT;break;case VK_BACK:scan=SDL_SCANCODE_BACKSPACE;break;
        case VK_LEFT:scan=SDL_SCANCODE_LEFT;break;case VK_RIGHT:scan=SDL_SCANCODE_RIGHT;break;
        case VK_UP:scan=SDL_SCANCODE_UP;break;case VK_DOWN:scan=SDL_SCANCODE_DOWN;break;
        case VK_HOME:scan=SDL_SCANCODE_HOME;break;case VK_END:scan=SDL_SCANCODE_END;break;
        case VK_INSERT:scan=SDL_SCANCODE_INSERT;break;case VK_DELETE:scan=SDL_SCANCODE_DELETE;break;
    }
    if(scan==SDL_SCANCODE_UNKNOWN)return 0;
    if(msg==WM_KEYDOWN && key!=VK_SHIFT && key!=VK_CONTROL && key!=VK_MENU){POINT at=native_cursor_point();native_workspace_activate_point(at.x,at.y);}
    if(msg==WM_KEYUP&&!n->keys[key])return 1;
    n->keys[key]=msg==WM_KEYDOWN;
    SDL_Event event={0};event.type=msg==WM_KEYDOWN?SDL_EVENT_KEY_DOWN:SDL_EVENT_KEY_UP;
    event.key.scancode=scan;event.key.down=msg==WM_KEYDOWN;event.key.windowID=0;
    event.key.mod=(GetKeyState(VK_SHIFT)<0?SDL_KMOD_LSHIFT:0)|(GetKeyState(VK_CONTROL)<0?SDL_KMOD_LCTRL:0)|(GetKeyState(VK_MENU)<0?SDL_KMOD_LALT:0);
    return SDL_PushEvent(&event);
}
static LRESULT CALLBACK window_proc(HWND h, UINT msg, WPARAM wp, LPARAM lp) {
    int p = (int) GetWindowLongPtr(h, GWLP_USERDATA);
    if (msg == WM_NCCREATE) {
        p = (int)(INT_PTR)((CREATESTRUCT *) lp)->lpCreateParams;
        SetWindowLongPtr(h, GWLP_USERDATA, p);
        return DefWindowProc(h, msg, wp, lp);
    }
    if (p < 0 || p >= WS_PANELS) return DefWindowProc(h, msg, wp, lp);
    Native * n = & u.windows [p];
    LRESULT result;
    if (common(h, p, msg, wp, lp, & result)) return result;
    if (msg == WM_CLOSE) {
        if (ws_closable(p)) {
            u.layout.panels [p].visible = 0;
            ShowWindow(h, SW_HIDE);
            save();
        }
        return 0;
    }
    if (msg == WM_GETMINMAXINFO && ws_resizable(p)) {
        MINMAXINFO * m = (MINMAXINFO *) lp;
        m->ptMinTrackSize = (POINT) {
            scale(240, n->dpi), scale(180, n->dpi)
        };
        return 0;
    }
    if (msg == WM_COMMAND) {
        if (HIWORD(wp) == BN_CLICKED || HIWORD(wp) == CBN_SELCHANGE) panel_command(p, LOWORD(wp));
        return 0;
    }
    if (msg == WM_DRAWITEM) {
        draw_button((DRAWITEMSTRUCT *) lp, p);
        return TRUE;
    }
    if (msg == WM_PAINT || msg == WM_PRINTCLIENT) {
        PAINTSTRUCT paint;
        HDC dc = msg == WM_PAINT ? BeginPaint(h, & paint) : (HDC) wp;
        RECT r;
        GetClientRect(h, & r);
        if (msg == WM_PAINT) buffered(dc, r, p, ws_resizable(p) ? draw_world : draw_panel);
        else if (ws_resizable(p)) draw_world(dc, r, p);
        else draw_panel(dc, r, p);
        if (msg == WM_PAINT) EndPaint(h, & paint);
        return 0;
    }
    if (msg == WM_ERASEBKGND) return 1;
    if (ws_resizable(p)) {
        WsPanel * v = & u.layout.panels [p];
        if (msg == WM_MOUSEWHEEL) {
            POINT at = {
                GET_X_LPARAM(lp), GET_Y_LPARAM(lp)
            };
            ScreenToClient(h, & at);
            if (GET_KEYSTATE_WPARAM(wp) & MK_SHIFT) {
                int delta = GET_WHEEL_DELTA_WPARAM(wp) > 0 ? - 2 : 2;
                if (p == WS_GAME) enhanced_submit_pan(0, delta);
                else {
                    v->camera_y += delta * 16;
                    if (v->camera_y < 0) v->camera_y = 0;
                    if (v->camera_y > 1023) v->camera_y = 1023;
                }
            }
            else zoom(p, GET_WHEEL_DELTA_WPARAM(wp), at);
            return 0;
        }
        if(p==WS_GAME && (msg==WM_LBUTTONDOWN||msg==WM_LBUTTONDBLCLK||msg==WM_LBUTTONUP||msg==WM_RBUTTONDOWN||msg==WM_RBUTTONDBLCLK||msg==WM_RBUTTONUP||msg==WM_MOUSEMOVE||msg==WM_CAPTURECHANGED)){
            double z=v->zoom/100.0*n->dpi/96.0;
            int x=v->camera_x+(int)(GET_X_LPARAM(lp)/z),y=v->camera_y+(int)(GET_Y_LPARAM(lp)/z);
            if(msg==WM_LBUTTONDOWN||msg==WM_LBUTTONDBLCLK||msg==WM_RBUTTONDOWN||msg==WM_RBUTTONDBLCLK){
                int mods=msg==WM_LBUTTONDBLCLK?0x2000:msg==WM_RBUTTONDBLCLK?0x4000:msg==WM_RBUTTONDOWN?0x800:0x200;
                POINT screen={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};ClientToScreen(h,&screen);native_workspace_anchor(screen.x,screen.y);if(enhanced_submit_pointer(4,x,y,mods)==ENHANCED_QUEUED){n->gesture=1;n->gx=x;n->gy=y;SetCapture(h);SetFocus(h);}return 0;
            }
            if(n->gesture){if(msg==WM_CAPTURECHANGED){x=n->gx;y=n->gy;}n->gx=x;n->gy=y;int down=msg==WM_MOUSEMOVE;enhanced_pointer_update(x,y,down);if(!down){n->gesture=0;ReleaseCapture();}return 0;}
        }
        if (msg == WM_MBUTTONDOWN || (p!=WS_GAME && msg == WM_LBUTTONDOWN)) {
            const EnhancedSnapshot * s = enhanced_snapshot();
            if (p == WS_GAME && s && (s->dialogs.modal || s->panels.tool != - 1)) return 0;
            n->pan = 1;
            if (p == WS_GAME) u.follow = 0;
            n->pointer = (POINT) {
                GET_X_LPARAM(lp), GET_Y_LPARAM(lp)
            };
            n->start_x = v->camera_x;
            n->start_y = v->camera_y;
            SetCapture(h);
            SetFocus(h);
            return 0;
        }
        if (msg == WM_MOUSEMOVE && n->pan) {
            double z = v->zoom / 100.0 * n->dpi / 96.0;
            v->camera_x = n->start_x - (int)((GET_X_LPARAM(lp) - n->pointer.x) / z);
            v->camera_y = n->start_y - (int)((GET_Y_LPARAM(lp) - n->pointer.y) / z);
            int width = p == WS_GAME && u.source_plane == 1 ? 2048 : 1024;
            if (v->camera_x < 0) v->camera_x = 0;
            if (v->camera_y < 0) v->camera_y = 0;
            if (v->camera_x >= width) v->camera_x = width - 1;
            if (v->camera_y > 1023) v->camera_y = 1023;
            InvalidateRect(h, NULL, FALSE);
            return 0;
        }
        if ((msg == WM_MBUTTONUP || msg == WM_LBUTTONUP || msg == WM_CAPTURECHANGED) && n->pan) {
            n->pan = 0;
            ReleaseCapture();
            if (p == WS_GAME) {
                int dx = (v->camera_x - n->start_x) / 16, dy = (v->camera_y - n->start_y) / 16;
                if (dx || dy) enhanced_submit_pan(dx, dy);
            }
            save();
            return 0;
        }
        if (msg == WM_KEYDOWN && GetKeyState(VK_CONTROL) < 0 && (wp == VK_OEM_PLUS || wp == VK_ADD || wp == VK_OEM_MINUS || wp == VK_SUBTRACT || wp == '0')) {
            RECT r;
            GetClientRect(h, & r);
            POINT center = {
                r.right / 2, r.bottom / 2
            };
            if (wp == '0') {
                v->zoom = 100;
                InvalidateRect(h, NULL, FALSE);
                save();
            }
            else zoom(p, wp == VK_OEM_PLUS || wp == VK_ADD ? 1 : - 1, center);
            return 0;
        }
    }
    if(ws_resizable(p)&&msg==WM_KILLFOCUS)for(unsigned key=0;key<256;++key)if(n->keys[key])forward_world_key(n,WM_KEYUP,key);
    if(ws_resizable(p)&&forward_world_key(n,msg,wp))return 0;
    return DefWindowProc(h, msg, wp, lp);
}
static void arrange(void) {
    if (! u.active || u.applying) return;
    u.applying = 1;
    for (int p = 0; p < WS_PANELS; ++ p) {
        Native * n = & u.windows [p];
        if (! n->h) continue;
        if(!ws_resizable(p)&&n->client_w)fixed_client(n,n->client_w,n->client_h);
        RECT r = restored(p);
        RECT now,client;GetWindowRect(n->h,&now);GetClientRect(n->h,&client);
        if(!EqualRect(&r,&now))SetWindowPos(n->h, HWND_TOP, r.left, r.top, r.right - r.left, r.bottom - r.top, SWP_NOACTIVATE | SWP_NOOWNERZORDER | (ws_resizable(p)?0:SWP_NOSIZE));
        if (! n->external){
            int show=u.ready&&u.layout.panels[p].visible,was=IsWindowVisible(n->h);
            ShowWindow(n->h,show?SW_SHOWNOACTIVATE:SW_HIDE);
            if(show&&!was)RedrawWindow(n->h,NULL,NULL,RDW_INVALIDATE|RDW_ALLCHILDREN|RDW_UPDATENOW);
        }
    }
    u.applying = 0;
}
#include "native_proximity.inc"
#include "native_minimap.inc"
int native_workspace_set_ui_scale(int percent){
    if(!u.active||!ws_ui_scale_valid(percent))return 0;
    if(u.layout.ui_scale==percent)return 1;
    /* Snapshot the old DIP bounds before switching units. */
    for(int p=0;p<WS_PANELS;++p)if(u.windows[p].h)remember(p);
    u.scaling=1;
    u.layout.ui_scale=percent;u.dpi=effective_dpi(dpi_of(u.root));
    u.applying=1;root_size(scale(u.root_width,u.dpi),scale(u.root_height,u.dpi));
    for(int p=0;p<WS_PANELS;++p){Native *n=&u.windows[p];if(!n->h)continue;
        n->dpi=effective_dpi(n->monitor_dpi);resize_fonts(p);
        SetWindowPos(n->h,NULL,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);
        if(p==WS_ANT||p==WS_YARD_CONTROL)size_children(p);
    }
    u.applying=0;command_tool=-1;arrange();
    for(int p=0;p<WS_PANELS;++p)if(u.windows[p].h)RedrawWindow(u.windows[p].h,NULL,NULL,RDW_FRAME|RDW_INVALIDATE|RDW_ALLCHILDREN|RDW_UPDATENOW);
    ++u.layout.revision;save();DrawMenuBar(u.root);u.scaling=0;return 1;
}
static LRESULT CALLBACK root_proc(HWND h, UINT msg, WPARAM wp, LPARAM lp, UINT_PTR id, DWORD_PTR data) {
    (void) id;
    (void) data;
    if(proximity_message(msg,lp))return TRUE;
    if (native_workspace_shortcut(msg, wp)) return 0;
    if(msg==WM_LBUTTONDOWN && enhanced_submit_wait_dismiss())return 0;
    if (msg == WM_CLOSE && u.ready) {
        enhanced_submit_event(0xfd08, 0, 0, 0);
        return 0;
    }
    if (msg == WM_COMMAND && HIWORD(wp) == 0) {
        int command = LOWORD(wp);
        if (command == RESET) {
            Workspace next;
            ws_reset(& next);
            for (int p = 0; p < WS_PANELS; ++ p) next.panels [p].visible = u.layout.panels [p].visible;
            next.ui_scale=u.layout.ui_scale;
            u.layout = next;
            arrange();
            save();
            return 0;
        }
        if (command == SHOW_BLACK || command == SHOW_RED) {
            int p = command == SHOW_BLACK ? WS_BLACK : WS_RED;
            u.layout.panels [p].visible = 1;
            arrange();
            SetForegroundWindow(u.windows [p].h);
            save();
            return 0;
        }
    }
    if (msg == WM_MOVE || msg == WM_SIZE) {
        LRESULT r = DefSubclassProc(h, msg, wp, lp);
        if(msg==WM_SIZE&&wp!=SIZE_MINIMIZED&&!u.applying&&!u.scaling){RECT client;GetClientRect(h,&client);if(client.right>0&&client.bottom>0){u.root_width=MulDiv(client.right,96,u.dpi);u.root_height=MulDiv(client.bottom,96,u.dpi);}}
        arrange();
        return r;
    }
    if (msg == WM_DPICHANGED) {
        u.dpi = effective_dpi(HIWORD(wp));
        RECT * r = (RECT *) lp;
        SetWindowPos(h, NULL, r->left, r->top, r->right - r->left, r->bottom - r->top, SWP_NOZORDER | SWP_NOACTIVATE);
        arrange();
        return 0;
    }
    if (msg == WM_DISPLAYCHANGE) {
        arrange();
        return 0;
    }
    if (msg == WM_PAINT) {
        PAINTSTRUCT p;
        BeginPaint(h, & p);
        color_fill(p.hdc, p.rcPaint, RGB(166, 164, 145));
        EndPaint(h, & p);
        return 0;
    }
    if (msg == WM_ERASEBKGND) return 1;
    if (msg == WM_KEYDOWN || msg == WM_KEYUP || msg == WM_CHAR || msg == WM_MOUSEMOVE || msg == WM_LBUTTONDOWN || msg == WM_LBUTTONUP) return 0;
    return DefSubclassProc(h, msg, wp, lp);
}
int native_workspace_init(SDL_Window * root) {
    const char * enabled = getenv("SIMANT_ENHANCED_WORKSPACE");
    if (! enhanced_world_enabled() || (enabled && ! strcmp(enabled, "0"))) return 0;
    HWND h = SDL_GetPointerProperty(SDL_GetWindowProperties(root), SDL_PROP_WINDOW_WIN32_HWND_POINTER, NULL);
    if (! h) return 0;
    memset(& u, 0, sizeof (u));
    u.root = h;
    u.sdl_id = SDL_GetWindowID(root);
    u.dpi = dpi_of(h);
    if (! u.dpi) u.dpi = 96;
    ws_reset(& u.layout);
    INITCOMMONCONTROLSEX controls = {
        sizeof (controls), ICC_WIN95_CLASSES
    };
    InitCommonControlsEx(& controls);
    WNDCLASSEXA cls = {
        .cbSize = sizeof (cls),.style=CS_DBLCLKS,.lpfnWndProc = window_proc,.hInstance = GetModuleHandle(NULL),.hCursor = LoadCursor(NULL, IDC_ARROW),.lpszClassName = "SimAntGameWindow"
    };
    RegisterClassExA(& cls);
    const char * path = getenv("SIMANT_WORKSPACE_LAYOUT");
    if (path) snprintf(u.path, sizeof (u.path), "%s", path);
    else {
        char local [MAX_PATH];
        if (SUCCEEDED(SHGetFolderPathA(NULL, CSIDL_LOCAL_APPDATA, NULL, SHGFP_TYPE_CURRENT, local))) {
            snprintf(u.path, sizeof (u.path), "%s\\SimAnt", local);
            CreateDirectoryA(u.path, NULL);
            strcat(u.path, "\\windows-v2.txt");
        }
    }
    FILE * f = u.path [0] ? fopen(u.path, "r") : NULL;
    if (f) {
        int okay = ws_read(& u.layout, f);
        fclose(f);
        if (! okay) {
            char bad [2100];
            snprintf(bad, sizeof (bad), "%s.rejected-%llu", u.path, (unsigned long long) GetTickCount64());
            CopyFileA(u.path, bad, TRUE);
            ws_reset(& u.layout);
        }
    }
    if(initial_ui_scale>=0)u.layout.ui_scale=initial_ui_scale;
    u.dpi=effective_dpi(dpi_of(h));
    u.active = 1;
    native_menu_init(root);
    SetWindowSubclass(h, root_proc, 29, 0);
    SetWindowTextA(h, "SimAnt");
    u.root_width=1040;u.root_height=760;u.scaling=1;root_size(scale(u.root_width,u.dpi),scale(u.root_height,u.dpi));u.scaling=0;
    SetWindowPos(h, NULL, scale(8, u.dpi), scale(8, u.dpi), 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
    for (int p = 0; p <= WS_YARD_CONTROL; ++ p) {
        if (p == WS_RESERVED) continue;
        Native * n = & u.windows [p];
        n->monitor_dpi=dpi_of(h);n->dpi = u.dpi;
        if(!ws_resizable(p))ws_fixed_content(p,&n->client_w,&n->client_h);
        n->font = make_font(n->dpi);
        DWORD style = WS_POPUP | WS_CAPTION | WS_CLIPCHILDREN;
        if (ws_resizable(p)) style |= WS_THICKFRAME | WS_SYSMENU | WS_MAXIMIZEBOX;
        else style |= WS_BORDER;
        RECT r = {
            0, 0, scale(p == WS_ANT || p == WS_YARD_CONTROL ? 944 : 440, n->dpi), scale(p == WS_ANT ? 184 : p == WS_YARD_CONTROL ? 152 : 340, n->dpi)
        };
        AdjustWindowRectEx(& r, style, FALSE, WS_EX_TOOLWINDOW);
        if (! ws_resizable(p)) {
            u.layout.panels [p].w = MulDiv(r.right - r.left, 96, n->dpi);
            u.layout.panels [p].h = MulDiv(r.bottom - r.top, 96, n->dpi);
        }
        n->h = CreateWindowExA((ws_resizable(p) ? 0 : WS_EX_TOOLWINDOW) | WS_EX_CONTROLPARENT, "SimAntGameWindow", ws_name(p), style, 0, 0, r.right - r.left, r.bottom - r.top, h, NULL, GetModuleHandle(NULL), (void *)(INT_PTR) p);
        SetWindowTextA(n->h, ws_name(p));
        system_entries(n->h);
        SetWindowPos(n->h,NULL,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);
        if (p == WS_ANT || p == WS_YARD_CONTROL) {
            panel_children(p);
            size_children(p);
        }
    }
    arrange();
    if(initial_ui_scale>=0)save();
    return 1;
}
int native_workspace_active(void) {
    return u.active;
}
void native_workspace_reveal_game(void) {
    if (u.active) {
        u.layout.panels [WS_GAME].visible = 1;
        arrange();
        save();
    }
}
static int panel_for_logical(int id) {
    switch (id) {
        case 0x100 :
        return WS_MAP;
        case 0x1900 :
        return WS_YARD;
        case 0x1200 :
        return WS_BEHAVIOR;
        case 0x1300 :
        return WS_CASTE;
        case 0x1500 :
        return WS_HISTORY;
        case 0x500 :
        return WS_INFO;
        case 0x1800 :
        return WS_STATUS;
    }
    /* Compatibility owners are not workspace slots. Indexing 16+(id>>8)
     * exceeded u.windows and corrupted adjacent state for modal windows. */
    return -1;
}
static void fixed_client(Native *n,int width,int height){
    if(n->moving||width<1||height<1)return;
    n->client_w=width;n->client_h=height;
    RECT client;GetClientRect(n->h,&client);int w=scale(width,n->dpi),h=scale(height,n->dpi);
    if(client.right==w&&client.bottom==h)return;
    if(n->sdl){
        /* SDL also owns WM_WINDOWPOSCHANGING. Size through its API and
         * compensate the native caption/scrollbar inset, including fractional
         * DPI rounding. Stop as soon as the actual client is exact. */
        int request_w=w,request_h=h+caption_extra(n);
        for(int attempt=0;attempt<4;++attempt){
            SDL_SetWindowSize(n->sdl,request_w,request_h);SDL_SyncWindow(n->sdl);
            GetClientRect(n->h,&client);if(client.right==w&&client.bottom==h)break;
            request_w+=w-client.right;request_h+=h-client.bottom;
        }
    }else{
        RECT frame;GetWindowRect(n->h,&frame);
        SetWindowPos(n->h,NULL,0,0,frame.right-frame.left+w-client.right,frame.bottom-frame.top+h-client.bottom,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);
    }


}
static LRESULT CALLBACK compatibility_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp,UINT_PTR id,DWORD_PTR logical){
    (void)id;
    if(msg==WM_KEYDOWN&&wp==VK_ESCAPE&&enhanced_submit_wait_dismiss())return 0;
    if(msg==WM_LBUTTONDOWN){RECT r;GetClientRect(h,&r);POINT p={GET_X_LPARAM(lp),GET_Y_LPARAM(lp)};if(!PtInRect(&r,p)&&enhanced_submit_wait_dismiss())return 0;}
    if(logical==0x1f00&&((msg==WM_KEYDOWN&&wp==VK_ESCAPE)||msg==WM_CLOSE||msg==WM_LBUTTONDOWN)){
        if(enhanced_cancel_credits())return 0;
    }
    if(msg==WM_NCDESTROY)RemoveWindowSubclass(h,compatibility_proc,74);
    return DefSubclassProc(h,msg,wp,lp);
}
void native_workspace_manage_window(SDL_Window *window,int logical,int width,int height){
    if(!u.active)return;int p=panel_for_logical(logical);if(p<0){
        HWND h=SDL_GetPointerProperty(SDL_GetWindowProperties(window),SDL_PROP_WINDOW_WIN32_HWND_POINTER,NULL);
        if(h){
            int d=point_dpi(prompt_anchor()),w=scale(width*2,d),he=scale(height*2,d);RECT r;GetClientRect(h,&r);
            MONITORINFO m={.cbSize=sizeof(m)};GetMonitorInfo(MonitorFromPoint(prompt_anchor(),MONITOR_DEFAULTTONEAREST),&m);
            int mw=m.rcWork.right-m.rcWork.left-16,mh=m.rcWork.bottom-m.rcWork.top-64;
            if(w>mw){he=MulDiv(he,mw,w);w=mw;}if(he>mh){w=MulDiv(w,mh,he);he=mh;}
            if(r.right!=w||r.bottom!=he)SDL_SetWindowSize(window,w,he);
            SetWindowSubclass(h,compatibility_proc,74,(DWORD_PTR)logical);if(logical==0x1f00)sync_text(h,"About SimAnt - Esc or click closes");if(logical==0x1700)sync_text(h,"Population - Esc or click outside closes");}
        return;
    }Native *n=&u.windows[p];
    if(content_panel(p))content_size(p,&width,&height);
    /* Runs every frame: Info and Yard captions belong to content_sync, the rest change only when different. */
    if(n->h){fixed_client(n,width,height);if(content_panel(p)){if(p!=WS_INFO&&p!=WS_YARD)sync_text(n->h,ws_name(p));content_sync(p);}return;}
    SDL_SetWindowBordered(window,true);
    HWND h=SDL_GetPointerProperty(SDL_GetWindowProperties(window),SDL_PROP_WINDOW_WIN32_HWND_POINTER,NULL);if(!h)return;
    SetClassLongPtr(h,GCL_STYLE,GetClassLongPtr(h,GCL_STYLE)|CS_DBLCLKS);
    n->h=h;n->sdl=window;n->external=1;n->monitor_dpi=dpi_of(h);n->dpi=effective_dpi(n->monitor_dpi);n->font=make_font(n->dpi);SetWindowLongPtr(h,GWLP_HWNDPARENT,(LONG_PTR)u.root);
    LONG_PTR style=GetWindowLongPtr(h,GWL_STYLE)|WS_CLIPCHILDREN;style&=~(WS_THICKFRAME|WS_MINIMIZEBOX|WS_MAXIMIZEBOX);style|=WS_CAPTION;
    if(!(enhanced_window_flags((int16_t)logical)&4))style&=~WS_SYSMENU;else style|=WS_SYSMENU;
    SetWindowLongPtr(h,GWL_STYLE,style);SetWindowLongPtr(h,GWL_EXSTYLE,GetWindowLongPtr(h,GWL_EXSTYLE)|WS_EX_TOOLWINDOW);
    SetWindowPos(h,NULL,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);
    SetWindowSubclass(h,managed_proc,73,p);SetWindowPos(h,NULL,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE|SWP_FRAMECHANGED);fixed_client(n,width,height);if(content_panel(p)){SetWindowTextA(h,ws_name(p));content_children(p);content_sync(p);}system_entries(h);arrange();
}
int native_workspace_content_paint(void *window,void *output,int frame){
    if(!u.active)return 0;
    for(int p=WS_MAP;p<=WS_STATUS;++p)if(u.windows[p].h==(HWND)window){
        if(p!=WS_STATUS&&enhanced_compatibility_owner()==content_owner(p))return 0;
        content_sync(p);
        /* The present path also visits these clients between WM_PAINT refreshes.
         * Keep input polling cheap; readbacks and first show always draw now. */
        if(!output&&IsWindowVisible((HWND)window)&&u.windows[p].content_painted&&SDL_GetTicksNS()-u.windows[p].content_painted<50000000)return 1;
        HDC dc=(HDC)output;int own=!dc;if(own)dc=GetDC((HWND)window);int saved=SaveDC(dc);
        if(frame){RECT r;GetWindowRect((HWND)window,&r);POINT at={0,0};ClientToScreen((HWND)window,&at);SetViewportOrgEx(dc,at.x-r.left,at.y-r.top,NULL);}
        RECT r;GetClientRect((HWND)window,&r);
        /* PrintWindow has already drawn native children; repaint only their parent. */
        for(HWND child=GetWindow((HWND)window,GW_CHILD);child;child=GetWindow(child,GW_HWNDNEXT))if(IsWindowVisible(child)){
            RECT cr;GetWindowRect(child,&cr);MapWindowPoints(NULL,(HWND)window,(POINT *)&cr,2);ExcludeClipRect(dc,cr.left,cr.top,cr.right,cr.bottom);
        }
        /* Called every frame from the present loop (own DC): draw off-screen and copy once. */
        if(own)buffered(dc,r,p,content_draw);else content_draw(dc,r,p);RestoreDC(dc,saved);
        if(own){ReleaseDC((HWND)window,dc);u.windows[p].content_painted=SDL_GetTicksNS();}return 1;
    }return 0;
}
int native_workspace_popup_paint(void *window,void *output,int frame){
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(!u.active||!u.info_popup||!s||s->dialogs.owner!=0x500)return 0;
    /* Only source save-under popup windows have no native caption. */
    if(GetWindowLongPtr((HWND)window,GWL_STYLE)&WS_CAPTION)return 0;
    size_t size;const uint8_t *bytes=enhanced_resource(u.info_popup,10,&size);if(!bytes)return 0;
    char *message=malloc(size+1);if(!message)return 0;size_t n=0;
    for(size_t i=0;i<size;++i)if(bytes[i])message[n++]=bytes[i]=='\r'?'\n':bytes[i];message[n]=0;
    HDC dc=(HDC)output;int own=!dc;if(own)dc=GetDC((HWND)window);HDC screen=dc;HDC mem=NULL;HBITMAP bmp=NULL;HGDIOBJ old=NULL;
    RECT r;GetClientRect((HWND)window,&r);RECT full=r;
    /* Per-frame path: draw off-screen and copy once, so the paper fill is never visible. */
    if(own&&r.right>0&&r.bottom>0&&(mem=CreateCompatibleDC(screen))!=NULL){if((bmp=CreateCompatibleBitmap(screen,r.right,r.bottom))!=NULL){old=SelectObject(mem,bmp);dc=mem;}else{DeleteDC(mem);mem=NULL;}}
    int saved=SaveDC(dc);if(frame){RECT wr;GetWindowRect((HWND)window,&wr);POINT pt={0,0};ClientToScreen((HWND)window,&pt);SetViewportOrgEx(dc,pt.x-wr.left,pt.y-wr.top,NULL);}
    color_fill(dc,r,PAPER);FrameRect(dc,&r,GetStockObject(BLACK_BRUSH));InflateRect(&r,-8,-6);SelectObject(dc,u.windows[WS_INFO].font);wchar_t *wide=malloc((n+1)*sizeof(wchar_t));if(wide&&MultiByteToWideChar(10000,0,message,-1,wide,(int)n+1)){SetTextColor(dc,INK);SetBkMode(dc,TRANSPARENT);DrawTextW(dc,wide,-1,&r,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);}free(wide);
    RestoreDC(dc,saved);if(bmp){BitBlt(screen,0,0,full.right,full.bottom,mem,0,0,SRCCOPY);SelectObject(mem,old);DeleteObject(bmp);DeleteDC(mem);}if(own)ReleaseDC((HWND)window,screen);free(message);return 1;
}
void native_workspace_present(const HostPalette * palette) {
    if (! u.active) return;
    u.palette = * palette;
    for(int p=WS_MAP;p<=WS_STATUS;++p)if(u.windows[p].h)content_sync(p);
    native_menu_sync();
    /* A window can become visible inside source win_Open, before its source
     * front/flush transaction returns. Retain an early Continue click until
     * that same ScoreDialog owns the source queue; never lose first-frame input. */
    if(u.status_continue_pending){
        SimHostedWindowView view;int open=0;for(unsigned i=0;i<sim_window_hosting_count();++i)if(sim_window_hosting_view(i,&view)&&view.id==0x1800){open=view.open;break;}
        if(!open)u.status_continue_pending=0;
        else if(sim_window_hosting_top()==0x1800){
            const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[0x18];
            if(entry->bound&&entry->view.count>12){const uint8_t *rect=entry->view.object_table[12];
                /* A ScoreDialog click is a pointer transaction, including its
                 * semantic position and current/previous window events. Use
                 * the same hosted input path as the retained source client. */
                int strip=view.drag_bottom>view.drag_top&&view.drag_top>=view.top_y&&view.drag_bottom<view.bottom?view.drag_bottom-view.top_y:0;
                HostEvent down={.kind=HOST_EVENT_MOUSE_DOWN,.button=SDL_BUTTON_LEFT,
                    .x=(sim_window_wire_read_i16(rect,0)+sim_window_wire_read_i16(rect,4))/2-view.left,
                    .y=(sim_window_wire_read_i16(rect,2)+sim_window_wire_read_i16(rect,6))/2-view.top_y-strip},up=down;
                up.kind=HOST_EVENT_MOUSE_UP;
                if(native_windows_push_pointer(0x1800,&down)&&native_windows_push_pointer(0x1800,&up))u.status_continue_pending=0;
            }
        }
    }
    const EnhancedSnapshot * s = enhanced_snapshot();
    int ready = s && s->panels.world_ready;
    command_prompt_sync(s);
    if (ready != u.ready) {
        u.ready = ready;
        arrange();
    }
    if (s && ready) {
        WsPanel * v = & u.layout.panels [WS_GAME];
        /* The game moved its view (AutoTrack, edge, Map click, pan release): keep the
         * source viewport centred in the native view, which is usually larger and
         * zoomed, and glide there instead of snapping its top-left corner. */
        if ((! u.source_plane || u.source_plane != s->world.plane || u.source_x != s->world.origin.x || u.source_y != s->world.origin.y) && ! u.windows [WS_GAME].pan) {
            Native * g = & u.windows [WS_GAME];
            RECT cr = { 0, 0, 0, 0 };
            if (g->h) GetClientRect(g->h, & cr);
            double z = v->zoom / 100.0 * (g->dpi ? g->dpi : 96) / 96.0;
            const EnhancedRect * sv = & s->world.hidden_viewport;
            int tx = s->world.origin.x * 16 + (sv->right - sv->left) / 2 - (int)(cr.right / z) / 2;
            int ty = s->world.origin.y * 16 + (sv->bottom - sv->top) / 2 - (int)(cr.bottom / z) / 2;
            if (tx < 0) tx = 0;
            if (ty < 0) ty = 0;
            int jump = ! u.source_plane || u.source_plane != s->world.plane || v->camera_x < 0 || v->camera_y < 0;
            if (jump) { v->camera_x = tx; v->camera_y = ty; u.follow = 0; }
            else { u.follow = 1; u.follow_x = tx; u.follow_y = ty; }
        }
        if (u.follow && ! u.windows [WS_GAME].pan) {
            int dx = u.follow_x - v->camera_x, dy = u.follow_y - v->camera_y;
            int sx = dx / 4, sy = dy / 4;
            if (! sx && dx) sx = dx > 0 ? 1 : - 1;
            if (! sy && dy) sy = dy > 0 ? 1 : - 1;
            v->camera_x += sx;
            v->camera_y += sy;
            if (v->camera_x == u.follow_x && v->camera_y == u.follow_y) u.follow = 0;
        }
        u.source_plane = s->world.plane;
        u.source_x = s->world.origin.x;
        u.source_y = s->world.origin.y;
        for (int p = WS_ANT; p <= WS_YARD_CONTROL; ++ p) {
            Native * n = & u.windows [p];
            int okay = ! s->dialogs.modal && s->panels.tool == - 1;
            for (unsigned i = 0; i < sizeof (buttons) / sizeof (buttons [0]); ++ i) {
                const Button * b = & buttons [i];
                if (b->panel != p) continue;
                int available = okay;
                if (b->event == 0x1910) available &= s->overview.stored_queens > 0;
                if (b->event == 0x190b) available &= s->panels.game_type == 2;
                EnableWindow(GetDlgItem(n->h, b->event), available);
            }
            EnableWindow(GetDlgItem(n->h, 0xe310), okay);
            EnableWindow(GetDlgItem(n->h, 0xe311), okay);
            if (p == WS_ANT) {
                HWND combo = GetDlgItem(n->h, 0xe300);
                EnableWindow(combo, okay);
                if (GetFocus() != combo && SendMessage(combo, CB_GETCURSEL, 0, 0) != s->panels.speed) SendMessage(combo, CB_SETCURSEL, s->panels.speed, 0);
            }
        }
    }
    if(s){int modal=s->dialogs.modal,owner=modal?panel_for_logical(s->dialogs.owner):-1;
        /* Compatibility dialogs can follow a proximity choice synchronously.
         * Preserve its origin again before their native client takes focus. */
        if(modal&&!source_modal_focus)proximity_preserve_focus();
        source_modal_focus=modal;
        /* Transfer a held world gesture to its source-owned context/tracker
         * window without inventing a release. Its real SDL button-up ends it. */
        if(modal)for(int p=0;p<=WS_INFO;++p){Native *n=&u.windows[p];int source=ws_resizable(p)?0:content_owner(p);
            if(n->gesture&&s->dialogs.owner!=source&&GetCapture()==n->h){n->gesture=0;ReleaseCapture();}
        }
        for(int p=0;p<WS_PANELS;++p)if(u.windows[p].h)EnableWindow(u.windows[p].h,!modal||p==owner);
        if(modal&&owner>=0&&u.windows[owner].h&&u.modal_token!=s->dialogs.task_token){u.modal_token=s->dialogs.task_token;SetForegroundWindow(u.windows[owner].h);SetFocus(u.windows[owner].h);}
        if(!modal)u.modal_token=0;
    }
    proximity_restore_focus(s);
    UINT64 now = SDL_GetTicksNS();
    if (u.painting || now - u.last_paint < 50000000) return;
    u.painting=1;
    /* Refresh live clients and the owner-drawn picture buttons and meters (both
     * double-buffered). Standard child controls are left alone: content_sync and
     * the panel loop above update them only when their value changes. */
    for (int p = 0; p <= WS_STATUS; ++ p) if (u.windows [p].h && IsWindowVisible(u.windows [p].h)) {
        for (HWND c = GetWindow(u.windows [p].h, GW_CHILD); c; c = GetWindow(c, GW_HWNDNEXT)) {
            char cls [16];
            if (GetClassNameA(c, cls, sizeof (cls)) && ! lstrcmpiA(cls, "Button") && (GetWindowLong(c, GWL_STYLE) & BS_TYPEMASK) == BS_OWNERDRAW) InvalidateRect(c, NULL, FALSE);
        }
        RedrawWindow(u.windows [p].h, NULL, NULL, RDW_INVALIDATE | RDW_NOCHILDREN);
        RedrawWindow(u.windows [p].h, NULL, NULL, RDW_UPDATENOW | RDW_ALLCHILDREN);
    }
    /* Slow GDI work must not make the following source poll immediately due
     * for another full refresh. Source time/input advances between paints. */
    u.last_paint=SDL_GetTicksNS();u.painting=0;
}
int native_workspace_filter(const SDL_Event * e) {
    if (! u.active) return 0;
    if(enhanced_compatibility_owner()>=0)return 0;
    if(e->type==SDL_EVENT_MOUSE_MOTION||e->type==SDL_EVENT_MOUSE_BUTTON_DOWN||e->type==SDL_EVENT_MOUSE_BUTTON_UP){
        SDL_WindowID id=e->type==SDL_EVENT_MOUSE_MOTION?e->motion.windowID:e->button.windowID;
        for(int p=WS_MAP;p<=WS_INFO;++p)if(u.windows[p].sdl&&SDL_GetWindowID(u.windows[p].sdl)==id && e->common.timestamp!=HOST_REPLAY_EVENT_TIMESTAMP)return 1;
    }
    if (e->type == SDL_EVENT_KEY_DOWN || e->type == SDL_EVENT_KEY_UP) return e->key.windowID == u.sdl_id;
    if (e->type == SDL_EVENT_MOUSE_MOTION) return e->motion.windowID == u.sdl_id;
    if (e->type == SDL_EVENT_MOUSE_WHEEL) return e->wheel.windowID == u.sdl_id;
    if (e->type == SDL_EVENT_MOUSE_BUTTON_DOWN || e->type == SDL_EVENT_MOUSE_BUTTON_UP) return e->button.windowID == u.sdl_id;
    return e->type == SDL_EVENT_TEXT_INPUT && e->text.windowID == u.sdl_id;
}
int native_workspace_input(HostInputState * s) {
    if (! u.active) return 0;
    if(enhanced_compatibility_owner()>=0)return 0;
    const EnhancedSnapshot *frame=enhanced_snapshot();
    if(frame && (frame->dialogs.modal || (frame->dialogs.owner!=0 && frame->dialogs.owner!=0x100 && frame->dialogs.owner!=0x1900 && frame->dialogs.owner!=0x500 && frame->dialogs.owner!=0x1200 && frame->dialogs.owner!=0x1300 && frame->dialogs.owner!=0x1500)) && (frame->dialogs.owner!=0x1800))return 0;
    memset(s, 0, sizeof (* s));
    s->x = 320;
    s->y = 240;
    return 1;
}
int native_workspace_operation(unsigned step) {
    if (! u.active) return 0;
    ws_exercise(& u.layout, step);
    arrange();
    save();
    return ws_validate(& u.layout);
}
const Workspace * native_workspace_layout(void) {
    return u.active ? & u.layout : NULL;
}
int native_workspace_apply(const Workspace * w) {
    if (! u.active || ! ws_validate(w)) return 0;
    int old=u.layout.ui_scale;u.layout.ui_scale=old;
    if(old!=w->ui_scale)native_workspace_set_ui_scale(w->ui_scale);
    u.layout = * w;
    arrange();
    save();
    return 1;
}
typedef struct Capture {
    HWND windows [80];
    int count;
    RECT bounds;
} Capture;
static BOOL CALLBACK capture_window(HWND h, LPARAM arg) {
    Capture * c = (Capture *) arg;
    DWORD pid;
    GetWindowThreadProcessId(h, & pid);
    if (pid != GetCurrentProcessId() || ! IsWindowVisible(h) || IsIconic(h) || c->count >= 80) return TRUE;
    RECT r;
    GetWindowRect(h, & r);
    if (r.right - r.left < 8 || r.bottom - r.top < 8) return TRUE;
    char title [120], cls [80];
    GetWindowTextA(h, title, sizeof (title));
    GetClassNameA(h, cls, sizeof (cls));
    if (h != u.root && h != u.preview && strcmp(cls, "SimAntGameWindow") && strcmp(cls, "SDL_app") && strcmp(cls, TOOLTIPS_CLASSA) && strcmp(cls, "#32768") && strcmp(cls,"SimAntCommandPrompt") && strcmp(cls,"SimAntMinimapPopup")) return TRUE;
    c->windows [c->count ++] = h;
    UnionRect(& c->bounds, & c->bounds, & r);
    return TRUE;
}
int native_workspace_capture(const char * path) {
    if (! u.active) return 0;
    for(int p=WS_MAP;p<=WS_STATUS;++p)if(u.windows[p].h){content_sync(p);RedrawWindow(u.windows[p].h,NULL,NULL,RDW_INVALIDATE|RDW_ALLCHILDREN|RDW_UPDATENOW);}
    Capture c = {
        0
    };
    GetWindowRect(u.root, & c.bounds);
    EnumWindows(capture_window, (LPARAM) & c);
    int width = c.bounds.right - c.bounds.left, height = c.bounds.bottom - c.bounds.top;
    if (width > 12000 || height > 12000) return 0;
    HDC screen = GetDC(NULL), dc = CreateCompatibleDC(screen);
    HBITMAP bmp = CreateCompatibleBitmap(screen, width, height);
    HGDIOBJ old = SelectObject(dc, bmp);
    color_fill(dc, (RECT) {
        0, 0, width, height
    }
    , RGB(166, 164, 145));
    for (int i = c.count; i >= 0; -- i) {
        HWND h = i == c.count ? u.root : c.windows [i];
        if (i != c.count && h == u.root) continue;
        RECT r;
        GetWindowRect(h, & r);
        int w = r.right - r.left, he = r.bottom - r.top;
        HDC temp = CreateCompatibleDC(screen);
        HBITMAP b = CreateCompatibleBitmap(screen, w, he);
        HGDIOBJ prev = SelectObject(temp, b);
        int print_state=SaveDC(temp);PrintWindow(h, temp, 0);RestoreDC(temp,print_state);
        print_state=SaveDC(temp);
        if(!native_workspace_content_paint(h,temp,1)&&!native_workspace_popup_paint(h,temp,1))native_windows_capture_client(h,temp);
        RestoreDC(temp,print_state);
        int saved = SaveDC(dc);
        HRGN region = CreateRectRgn(0, 0, 0, 0);
        if (GetWindowRgn(h, region) != ERROR) {
            OffsetRgn(region, r.left - c.bounds.left, r.top - c.bounds.top);
            SelectClipRgn(dc, region);
        }
        BitBlt(dc, r.left - c.bounds.left, r.top - c.bounds.top, w, he, temp, 0, 0, SRCCOPY);
        RestoreDC(dc, saved);
        DeleteObject(region);
        SelectObject(temp, prev);
        DeleteObject(b);
        DeleteDC(temp);
    }
    BITMAPINFO info = {
        .bmiHeader = {
            .biSize = sizeof (BITMAPINFOHEADER),.biWidth = width,.biHeight = - height,.biPlanes = 1,.biBitCount = 32,.biCompression = BI_RGB
        }
    };
    void * pixels = malloc((size_t) width * height * 4);
    SelectObject(dc, old);
    int okay = pixels && GetDIBits(dc, bmp, 0, height, pixels, & info, DIB_RGB_COLORS);
    FILE * f = okay ? fopen(path, "wb") : NULL;
    if (f) {
        BITMAPFILEHEADER header = {
            .bfType = 0x4d42,.bfSize = 54 + width * height * 4,.bfOffBits = 54
        };
        okay = fwrite(& header, 14, 1, f) == 1 && fwrite(& info.bmiHeader, 40, 1, f) == 1 && fwrite(pixels, 4, width * height, f) == (size_t) width * height;
        if (fclose(f)) okay = 0;
    }
    else okay = 0;
    free(pixels);
    DeleteObject(bmp);
    DeleteDC(dc);
    ReleaseDC(NULL, screen);
    return okay != 0;
}
void native_workspace_shutdown(void) {
    if (! u.active) return;
    save();
    RemoveWindowSubclass(u.root, root_proc, 29);
    for (int p = 0; p < WS_PANELS; ++ p) {
        Native * n = & u.windows [p];
        if (n->h) {
            if (n->external) RemoveWindowSubclass(n->h, managed_proc, 73);
            else DestroyWindow(n->h);
        }
        if (n->font) DeleteObject(n->font);
    }
    if (u.preview) DestroyWindow(u.preview);
    if(command_prompt)DestroyWindow(command_prompt);command_prompt=NULL;command_tool=-1;
    proximity_return_focus=NULL;
    memset(& u, 0, sizeof (u));
}
#else
int native_workspace_set_ui_scale(int percent){(void)percent;return 0;}
int native_workspace_ui_dpi(void *window){(void)window;return 96;}
int native_workspace_minimap(const EnhancedRect *r,const EnhancedRect *c,EnhancedPoint *p){(void)r;(void)c;(void)p;return 0;}
int native_workspace_art_paint(void *dc,int id,int x,int y){(void)dc;(void)id;(void)x;(void)y;return 0;}
void native_workspace_activate_point(int x,int y){(void)x;(void)y;}
void native_workspace_request_point(int *x,int *y){*x=*y=0;}
int native_workspace_proximity_modifiers(void){return 0;}
int native_workspace_proximity(const EnhancedDialogsSnapshot *menu){return menu?menu->owner+1:-1;}
void native_workspace_anchor(int x,int y){(void)x;(void)y;}
void native_workspace_place_prompt(SDL_Window *w){(void)w;}
int native_workspace_popup_paint(void *w,void *d,int f){(void)w;(void)d;(void)f;return 0;}
int native_workspace_content_paint(void *w,void *d,int f){(void)w;(void)d;(void)f;return 0;}
int native_workspace_init(SDL_Window * root) {
    (void) root;
    return 0;
}
int native_workspace_active(void) {
    return 0;
}
void native_workspace_reveal_game(void) {
}
void native_workspace_shutdown(void) {
}
void native_workspace_present(const HostPalette * p) {
    (void) p;
}
int native_workspace_filter(const SDL_Event * e) {
    (void) e;
    return 0;
}
int native_workspace_input(HostInputState * s) {
    (void) s;
    return 0;
}
int native_workspace_operation(unsigned step) {
    (void) step;
    return 0;
}
int native_workspace_capture(const char * path) {
    (void) path;
    return 0;
}
const Workspace * native_workspace_layout(void) {
    return NULL;
}
int native_workspace_apply(const Workspace * w) {
    (void) w;
    return 0;
}
void native_workspace_manage_window(SDL_Window *window,int logical,int width,int height){(void)window;(void)logical;(void)width;(void)height;}
int native_workspace_shortcut(unsigned message, uintptr_t key) {
    (void) message;
    (void) key;
    return 0;
}
#endif
