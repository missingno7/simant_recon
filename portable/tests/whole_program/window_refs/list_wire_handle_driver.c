#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "portable/whole_program/conversions/pointer_globals.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/window_list_refs.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/window_source_rects.h"

extern int16_t db_SetDataBase(char *name);
extern void db_CloseDataBase(void);
extern void win_LockInit(void);
extern void win_LockWin(int16_t window);
extern void win_UnlockWin(int16_t window);
extern int16_t win_IsWinLocked(int16_t window);
extern void win_LoadWindow(int16_t window);
extern char *win_ObjAddr(int16_t object);
extern void f_23E6_0266(int16_t object, char *text);
extern int16_t f_23E6_0109(int16_t object);
extern char *f_23E6_0132(int16_t object, int16_t line);
extern void f_23E6_0392(char *object);
extern int32_t f_171C_1C1C(char **handle);
extern char *f_171C_1B84(char **handle);
struct Pt { int16_t x, y; };
struct Rect fd_50F6_393C;
struct Pt fd_50F6_47DA;
int16_t g_5702[32];
int16_t fd_55B3_6262;


void Punt(char *format, ...)
{ fprintf(stderr, "source Punt: %s\n", format ? format : "(null)"); exit(90); }
int16_t WinPrintf(char *format, ...)
{ fprintf(stderr, "source WinPrintf: %s\n", format ? format : "(null)"); return 0; }
void f_24AB_02AD(int16_t font) { (void)font; }
void clip_KillWin(int16_t win) { (void)win; }
void clip_SetWin(int16_t win) { (void)win; }
void clip_Off(void) { }
void win_FlushEvents(void) { }
void clip_Push(void) { }
void clip_SubInclude(struct Rect *rect) { (void)rect; }
void clip_Pop(void) { }
int16_t f_24AB_030B(void) { return 10; }
void win_SetColorNum(int16_t color) { (void)color; }
void f_24AB_042B(struct Rect *rect, int16_t y, char *text)
{ (void)rect; (void)y; (void)text; }
void win_DrawObject(void *object) { (void)object; abort(); }
void win_DrawWindow(int16_t window) { (void)window; abort(); }
void win_DrawBitMapAtObjNum(int16_t obj, int16_t bitmap)
{ (void)obj; (void)bitmap; abort(); }
void win_SetColorFromObjNum(int16_t obj) { (void)obj; abort(); }
void win_GetObjSize(int16_t obj, struct Pt *size)
{ (void)obj; (void)size; abort(); }
struct Pt win_StringSize(char *text)
{ (void)text; Punt("unexpected auto-sized string"); return (struct Pt){0,0}; }
void f_208F_0419(struct Pt *size, int16_t id)
{ (void)size; (void)id; abort(); }
void font_InitFonts(void) { abort(); }
SimGraphicsDriver *sim_graphics_source_owner(void)
{ static SimGraphicsDriver unused; return &unused; }
void f_1F58_0090(void) { Punt("invalid geometry branch"); }
void f_1FD2_0883(int16_t a, int16_t b, int16_t c, int16_t d, int16_t e)
{ (void)a; (void)b; (void)c; (void)d; (void)e; abort(); }
void f_1FD2_03EB(char *obj, int16_t id) { (void)obj; (void)id; abort(); }
void f_1FD2_044F(char *window, int16_t id) { (void)window; (void)id; abort(); }
void f_1FD2_0438(int16_t id) { (void)id; abort(); }
void f_1FD2_049C(int16_t id) { (void)id; abort(); }
void f_218D_01EB(void) { abort(); }
void f_1B73_01E1(char *image, char *mask) { (void)image; (void)mask; abort(); }
void f_1B73_00D9(void) { abort(); }
void f_1E57_00B1(void) { abort(); }
void f_1E57_0052(void) { abort(); }
void f_24FA_0004(void) { abort(); }
void f_1F80_0081(void) { abort(); }
int16_t StillDown(void) { abort(); }
void f_21FA_0B4B(void) { abort(); }
void f_21FA_0AD2(void) { abort(); }
void f_24FA_00B5(void) { abort(); }
int8_t fd_55B3_360C;
int16_t fd_55B3_3612;
char *fd_55B3_360E;
char *fd_50F6_3B48;
typedef struct { uint16_t age; int16_t file, page; } TestEmsSlot;
TestEmsSlot **fd_50F6_3B4C;
int16_t f_195A_0260(void) { return 0; }
void f_195A_001D(void) { abort(); }
void f_195A_0035(void) { abort(); }
int16_t f_195A_004B(int16_t pages) { (void)pages; abort(); }
void f_195A_0062(int16_t a, int16_t b, int16_t c)
{ (void)a; (void)b; (void)c; abort(); }
void f_195A_007D(int16_t a) { (void)a; abort(); }
void f_195A_01CB(int16_t a, char *b) { (void)a; (void)b; abort(); }
int16_t win_DrawBitMap(int16_t x, int16_t y, int16_t id)
{ (void)x; (void)y; (void)id; abort(); }
SimGraphicsRectCallback g_9134;
void (*g_9188)(int16_t left, int16_t top, int16_t right, int16_t bottom,
               int16_t x, int16_t y);
static void ignore_rect(int16_t left, int16_t top, int16_t right,
                        int16_t bottom, int16_t color)
{ (void)left; (void)top; (void)right; (void)bottom; (void)color; }

int main(int argc, char **argv)
{
    const int16_t object = 0x1609;
    const char input[] = "Alpha\0Beta\0";
    char *obj;
    char ***slot;
    char *line;
    uint8_t before[56];
    uint8_t neighbor_before[4];
    char **objects;
    int16_t db;
    int16_t row_count;

    if (argc != 2 || dos_files_set_root(argv[1]) != 0) return 2;
    if (!sim_window_runtime_owner_init() ||
        sim_handles_global_configure(SIZE_MAX, 65536) != SIM_HANDLE_OK) return 3;
    db = db_SetDataBase("HCEGANT");
    if (db < 0 || db >= 4) return 4;
    win_LockInit();
    win_LockWin(0x1600);
    obj = win_ObjAddr(object);
    if (obj == NULL || (uint8_t)obj[0x21] != 4 ||
        sim_window_wire_read_i16(obj, 0x22) != 56) return 5;
    if (obj[0x34] || obj[0x35] || obj[0x36] || obj[0x37]) return 6;
    memcpy(before, obj, sizeof(before));
    objects = sim_window_ref_registry_objects_for_buffer(
        &sim_window_ref_registry, (char *)*win_handles[22]);
    if (objects == NULL || objects[10] == NULL) return 12;
    memcpy(neighbor_before, objects[10], sizeof(neighbor_before));
    g_9134 = ignore_rect;
    f_23E6_0266(object, (char *)input);
    obj = win_ObjAddr(object);
    objects = sim_window_ref_registry_objects_for_buffer(
        &sim_window_ref_registry, (char *)*win_handles[22]);
    slot = sim_window_list_text_slot(obj + 0x2a);
    if (slot == NULL || *slot == NULL) return 7;
    row_count = f_23E6_0109(object);
    if (row_count != 2) { fprintf(stderr, "unexpected list count: %d\n", row_count); return 8; }
    f_23E6_0392(obj);
    line = f_23E6_0132(object, 0);
    if (line == NULL || strcmp(line, "Alpha") != 0) {
        fprintf(stderr, "unexpected list line: ptr=%p text=%s count=%d handle=%p size=%" PRId32 "\n",
                (void *)line, line ? line : "(null)", row_count, (void *)*slot,
                f_171C_1C1C(*slot));
        return 9;
    }
    objects = sim_window_ref_registry_objects_for_buffer(
        &sim_window_ref_registry, (char *)*win_handles[22]);
    if (memcmp(obj + 0x34, before + 0x34, 4) != 0) return 10;
    if (objects == NULL || memcmp(objects[10], neighbor_before,
                                  sizeof(neighbor_before)) != 0) return 13;
    if (sim_window_list_text_slot(obj + 0x2a + 8) != NULL) return 11;
    printf("LIST,%u,%u,%d,%d,%s,%08x\n", (unsigned)object,
           (unsigned)(uint8_t)obj[0x21], row_count,
           (int)f_171C_1C1C(*slot), line,
           (unsigned)(uint8_t)obj[0x34] |
               ((unsigned)(uint8_t)obj[0x35] << 8) |
               ((unsigned)(uint8_t)obj[0x36] << 16) |
               ((unsigned)(uint8_t)obj[0x37] << 24));
    win_UnlockWin(0x1600);
    db_CloseDataBase();
    dos_files_close_all();
    return 0;
}
