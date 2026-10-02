#include "recovered_state.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void *Handle;
void f_00BA_0002(void);
void f_00BA_0211(void);
void f_00BA_0228(void);
void win_YardClosed(void);
void win_MapChanged(void);
void f_0250_05CB(void);
void f_0250_0E15(void);
void f_0250_0F2C(void);
void win_ModeControlClosed(void);
void win_CasteControlClosed(void);
void f_00BA_01C3(int16_t);
void f_0250_0EDA(int16_t);
void o12_384C_1035(int16_t);
void win_DrawHistoryWindow(int16_t);
void win_DrawModeWindow(int16_t);
void win_DrawCasteWindow(int16_t);
void win_DrawYardWindow(int16_t);
void win_DrawInfoWindow(int16_t);

int16_t fd_50F6_10D0;
void *fd_50F6_10CC;
void *fd_50F6_10DA;
int16_t fd_50F6_15C4[30][40];
int16_t source_g_19CE;

typedef void (*CloseHook)(void);
static CloseHook before_close_hook, after_close_hook;
static char events[256][128];
static size_t event_count;
static int16_t open_map, open_yard_cursor;
static struct Rect yard_cursor_rect = {100, 40, 130, 70};
static struct Rect map_rect = {7, 11, 90, 80};
static struct Rect edit_rect = {20, 30, 340, 230};
static int yard_anim, mode_anim, caste_anim;

static void event(const char *name, long a, long b, long c)
{
    if (event_count >= sizeof(events) / sizeof(events[0])) exit(20);
    (void)snprintf(events[event_count++], sizeof(events[0]), "%s:%ld:%ld:%ld",
                   name, a, b, c);
}

static const char *handle_name(Handle handle)
{
    if (handle == &yard_anim) return "yard";
    if (handle == &mode_anim) return "mode";
    if (handle == &caste_anim) return "caste";
    if (handle == NULL) return "null";
    return "other";
}

static const char *draw_hook_name(void (*hook)(int16_t))
{
    if (hook == f_0250_0EDA) return "edit";
    if (hook == o12_384C_1035) return "map";
    if (hook == win_DrawHistoryWindow) return "history";
    if (hook == win_DrawModeWindow) return "mode";
    if (hook == win_DrawCasteWindow) return "caste";
    if (hook == win_DrawYardWindow) return "yard";
    if (hook == win_DrawInfoWindow) return "info";
    return "unknown";
}

int16_t win_LoadAllWindows(void)
{ event("load_all_windows", 0, 0, 0); return 1; }
void win_SetWinDrawHook(int16_t window, void (*hook)(int16_t))
{ event("draw_hook", window, 0, 0); event(draw_hook_name(hook), 0, 0, 0); }
void f_20E8_088B(void (*hook)(void))
{
    after_close_hook = hook;
    event("register_after", hook == f_00BA_0228, 0, 0);
}
void f_20E8_08DB(void (*hook)(int16_t))
{ event("register_edit", hook == f_00BA_01C3, 0, 0); }
void f_20E8_089F(void (*hook)(void))
{
    before_close_hook = hook;
    event("register_before", hook == f_00BA_0211, 0, 0);
}
void f_22BF_0E83(int16_t a, int16_t b) { event("window_relationship", a, b, 0); }
void InitMapFunctions(void) { event("init_map_functions", 0, 0, 0); }
void f_0250_0EDA(int16_t flags) { (void)flags; }
void o12_384C_1035(int16_t flags) { (void)flags; }
void win_DrawHistoryWindow(int16_t flags) { (void)flags; }
void win_DrawModeWindow(int16_t flags) { (void)flags; }
void win_DrawCasteWindow(int16_t flags) { (void)flags; }
void win_DrawYardWindow(int16_t flags) { (void)flags; }
void win_DrawInfoWindow(int16_t flags) { (void)flags; }
void f_00BA_01C3(int16_t item) { (void)item; }

Handle f_171C_1A9E(int32_t size, int16_t flags, char *name)
{ (void)size; (void)flags; (void)name; event("unexpected_alloc", 0, 0, 0); return NULL; }
char *f_171C_1B84(Handle handle)
{ (void)handle; event("unexpected_lock", 0, 0, 0); return NULL; }
Handle f_171C_1BBA(Handle handle)
{ (void)handle; event("unexpected_unlock", 0, 0, 0); return NULL; }
void f_171C_1C0A(Handle handle) { (void)handle; event("unexpected_dispose", 0, 0, 0); }
long lseek(int16_t fd, int32_t offset, int16_t origin)
{ (void)fd; (void)offset; (void)origin; event("unexpected_lseek", 0, 0, 0); return -1; }
int16_t read(int16_t fd, void *buffer, uint16_t count)
{ (void)fd; (void)buffer; (void)count; event("unexpected_read", 0, 0, 0); return -1; }

void clip_Push(void) { event("clip_push", 0, 0, 0); }
void clip_SetWin(int16_t window) { event("clip_set", window, 0, 0); }
void clip_Pop(void) { event("clip_pop", 0, 0, 0); }
void hanim_RemoveAllAnimObjects(Handle handle)
{ event("anim_remove_all", handle_name(handle)[0], 0, 0); }
void hanim_RenderAnimSet(Handle handle)
{ event("anim_render", handle_name(handle)[0], 0, 0); }
void hanim_RemoveAnimSet(Handle handle)
{ event("anim_remove_set", handle_name(handle)[0], 0, 0); }
int16_t win_IsWinOpen(int16_t window)
{
    const int16_t result = window == 0x0100 ? open_map :
                           window == 0x1902 ? open_yard_cursor : 0;
    event("is_open", window, result, 0);
    return result;
}
void win_GetObjRect(int16_t object, struct Rect *rect)
{
    event("get_rect", object, 0, 0);
    if (object == 0x1902) *rect = yard_cursor_rect;
    else if (object == 0x0102) *rect = map_rect;
    else if (object == 4) *rect = edit_rect;
    else { event("bad_rect", object, 0, 0); memset(rect, 0, sizeof(*rect)); }
}
void EraseYardCursor(void) { event("erase_yard_cursor", 0, 0, 0); }
void EraseMapCursor(void) { event("erase_map_cursor", 0, 0, 0); }
void *_fmemset(void *dest, int16_t value, uint16_t count)
{
    event("cache_invalidate", value, count, 0);
    return memset(dest, (unsigned char)value, count);
}

static void invoke(RecoveredState *state, CloseHook hook)
{
    RecoveredBindingFrame frame;
    recovered_bind_begin(&frame, state);
    hook();
    recovered_bind_end(&frame, state);
}

static void run_case(int16_t initial_g19ce)
{
    RecoveredState state;
    size_t i, invalid = 0;
    int16_t close_front = 0x1900;
    recovered_state_init(&state);
    event("install_begin", 0, 0, 0);
    fd_50F6_10D0 = 0;
    invoke(&state, f_00BA_0002);
    if (before_close_hook == NULL || after_close_hook == NULL) exit(21);
    state.MapPlane = 2;
    state.fd_55B3_19BE = 16;
    state.fd_55B3_19C0 = 16;
    state.fd_50F6_0508[0] = 60;
    state.fd_50F6_0508[1] = 60;
    state.fd_50F6_37F6 = &mode_anim;
    state.fd_50F6_37F2 = &caste_anim;
    memset(fd_50F6_15C4, 0x2a, sizeof(fd_50F6_15C4));
    fd_50F6_10DA = &yard_anim;
    source_g_19CE = initial_g19ce;
    state.fd_55B3_29A2 = 0;
    open_map = open_yard_cursor = 1;
    event("before_hook", 0, 0, 0);
    invoke(&state, before_close_hook);
    event("win_close", close_front, 0, 0);
    event("after_hook", 0, 0, 0);
    invoke(&state, after_close_hook);
    for (i = 0; i < sizeof(fd_50F6_15C4) / sizeof(fd_50F6_15C4[0][0]); ++i)
        if (((int16_t *)fd_50F6_15C4)[i] == -1) ++invalid;
    printf("{\"events\":[");
    for (i = 0; i < event_count; ++i)
        printf("%s\"%s\"", i ? "," : "", events[i]);
    printf("],\"state\":{\"mode_anim_live\":%d,\"caste_anim_live\":%d,"
        "\"yard_anim_live\":%d,\"cursor_rect\":[%d,%d,%d,%d],"
        "\"edit_rect\":[%d,%d,%d,%d],\"edit_dims\":[%d,%d],"
        "\"camera\":[%d,%d],\"map_dirty\":%d,"
        "\"cache_invalid\":%zu,\"source_g_19CE\":%d,"
        "\"map_plane\":%d,\"tile_size\":[%d,%d]}}\n",
        state.fd_50F6_37F6 != NULL, state.fd_50F6_37F2 != NULL,
        fd_50F6_10DA != NULL,
        state.fd_50F6_10D2.left, state.fd_50F6_10D2.top,
        state.fd_50F6_10D2.right, state.fd_50F6_10D2.bottom,
        state.fd_50F6_110C.left, state.fd_50F6_110C.top,
        state.fd_50F6_110C.right, state.fd_50F6_110C.bottom,
        state.fd_50F6_10E0, state.fd_50F6_10DE,
        state.fd_50F6_0508[0], state.fd_50F6_0508[1],
        state.fd_55B3_29A2, invalid, source_g_19CE,
        state.MapPlane, state.fd_55B3_19BE, state.fd_55B3_19C0);
}

int main(int argc, char **argv)
{
    int16_t initial_g19ce;
    if (argc != 2 || (argv[1][0] != '0' && argv[1][0] != '1') || argv[1][1] != '\0')
        return 22;
    initial_g19ce = (int16_t)(argv[1][0] - '0');
    run_case(initial_g19ce);
    return 0;
}
