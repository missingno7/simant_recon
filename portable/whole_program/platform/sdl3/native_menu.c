#include "native_menu.h"
#include "portable/whole_program/menu_globals.h"
#include "../m1b73_event_enqueue.h"

#include <stdio.h>
#include <string.h>

/* Win16 SimAnt shows the game's kind-6 menu resource as a native menu bar
 * (InitMenu) and sends WM_COMMAND 0xFDxx to DoMenuEntry. The DOS pull-down
 * (S10 o10_35F5_0384) posts the same command space as a game event:
 * code = (menu << 4) + item - 0x2FF. Item state bytes (byte 0 of each title
 * and item string: 0x10 check, 0x20 none, | 0x80 disabled) stay owned by the
 * game (SetMenuItemState); the native menu only mirrors them. */

enum { MENU_TITLES = 16, MENU_ITEMS = 16, COMMAND_QUEUE = 16 };

static int commands[COMMAND_QUEUE];
static unsigned command_count;

/* A menu choice (native WM_COMMAND, or replay `menu FDxx`). */
int native_menu_command(int code)
{
    if ((code & 0xff00) != 0xfd00 || command_count == COMMAND_QUEUE) return 0;
    commands[command_count++] = code;
    return 1;
}

void native_menu_pump(void)
{
    unsigned i;
    for (i = 0; i < command_count; ++i)
        portable_m1b73_event_enqueue_four_word_command((int16_t)(uint16_t)commands[i], 0, 0, 0);
    command_count = 0;
}

#ifdef _WIN32
#include <windows.h>

static struct {
    HWND hwnd;
    WNDPROC original;
    HMENU bar;
    char ***built;                 /* g_6054 the bar was built from */
} m;

static UINT command_of(int menu, int item) { return 0xFD01u + ((unsigned)menu << 4) + (unsigned)item; }

static void label(char *out, size_t size, const char *text)
{
    size_t length;
    snprintf(out, size, "%s", text && text[0] ? text + 1 : "");
    length = strlen(out);
    while (length && out[length - 1] == ' ') out[--length] = 0;
    while (out[0] == ' ') memmove(out, out + 1, strlen(out));
}

static void refresh(HMENU popup, int menu)
{
    char **items = g_6054 ? g_6054[menu + 1] : NULL;
    int k;
    for (k = 0; items && items[k] && k < MENU_ITEMS; ++k) {
        unsigned char state = (unsigned char)items[k][0];
        if (items[k][1] == '-') continue;
        CheckMenuItem(popup, command_of(menu, k),
                      MF_BYCOMMAND | (((state & 0x7f) == 0x10) ? MF_CHECKED : MF_UNCHECKED));
        EnableMenuItem(popup, command_of(menu, k),
                       MF_BYCOMMAND | ((state & 0x80) ? MF_GRAYED : MF_ENABLED));
    }
}

static LRESULT CALLBACK menu_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
    if (msg == WM_COMMAND && HIWORD(wparam) == 0 && (LOWORD(wparam) & 0xff00) == 0xfd00) {
        native_menu_command(LOWORD(wparam));
        return 0;
    }
    if (msg == WM_INITMENUPOPUP && !HIWORD(lparam) && m.bar) {
        int menu = LOWORD(lparam);
        if ((HMENU)wparam == GetSubMenu(m.bar, menu)) refresh((HMENU)wparam, menu);
    }
    return CallWindowProc(m.original, hwnd, msg, wparam, lparam);
}

static void build(void)
{
    char **titles = g_6054[0];
    char text[64];
    int menu, k;
    HMENU bar = CreateMenu();
    for (menu = 0; titles[menu] && menu < MENU_TITLES; ++menu) {
        char **items = g_6054[menu + 1];
        HMENU popup = CreatePopupMenu();
        for (k = 0; items && items[k] && k < MENU_ITEMS; ++k) {
            if (items[k][1] == '-') AppendMenuA(popup, MF_SEPARATOR, 0, NULL);
            else {
                label(text, sizeof(text), items[k]);
                AppendMenuA(popup, MF_STRING, command_of(menu, k), text);
                fprintf(stderr, "Native menu %04X: %s\n", command_of(menu, k), text);
            }
        }
        label(text, sizeof(text), titles[menu]);
        AppendMenuA(bar, MF_POPUP | (((unsigned char)titles[menu][0] & 0x80) ? MF_GRAYED : 0),
                    (UINT_PTR)popup, text);
    }
    SetMenu(m.hwnd, bar);
    if (m.bar) DestroyMenu(m.bar);
    m.bar = bar;
    m.built = g_6054;
    DrawMenuBar(m.hwnd);
    fprintf(stderr, "Native menu bar: %d menus from the game's menu resource\n", menu);
}

int native_menu_init(SDL_Window *root)
{
    memset(&m, 0, sizeof(m));
    m.hwnd = (HWND)SDL_GetPointerProperty(SDL_GetWindowProperties(root),
                                          SDL_PROP_WINDOW_WIN32_HWND_POINTER, NULL);
    if (m.hwnd == NULL) return 0;            /* headless: no native menu */
    m.original = (WNDPROC)SetWindowLongPtr(m.hwnd, GWLP_WNDPROC, (LONG_PTR)menu_proc);
    return m.original != NULL;
}

int native_menu_sync(void)
{
    if (m.hwnd == NULL || g_6054 == NULL || g_6054 == m.built) return m.bar != NULL;
    build();
    return 1;
}

#else
int native_menu_init(SDL_Window *root) { (void)root; return 0; }
int native_menu_sync(void) { return 0; }
#endif
