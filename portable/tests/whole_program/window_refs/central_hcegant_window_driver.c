#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "portable/whole_program/conversions/pointer_globals.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/window_refs.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/window_source_globals.h"
#include "portable/whole_program/window_source_rects.h"

extern int16_t db_SetDataBase(char *name);
extern void db_CloseDataBase(void);
extern void win_LockInit(void);
extern int16_t win_IsWinLocked(int16_t window);
extern void win_LockWin(int16_t window);
extern void win_UnlockWin(int16_t window);
extern int32_t f_171C_1C1C(char **handle);
extern void font_InitFonts(void);
struct Pt { int16_t x, y; };
extern void f_208F_0419(struct Pt *size, int16_t id);

typedef struct { uint16_t age; int16_t file, page; } TestEmsSlot;
int8_t fd_55B3_360C;
int16_t fd_55B3_3612;
char *fd_55B3_360E;
char *fd_50F6_3B48;
TestEmsSlot **fd_50F6_3B4C;
struct Rect fd_50F6_393C;
struct Pt fd_50F6_47DA;
int16_t g_5702[32];
int16_t fd_55B3_6262;

SimGraphicsDriver *sim_graphics_source_owner(void)
{
    static SimGraphicsDriver unused;
    return &unused;
}

void Punt(char *format, ...)
{
    fprintf(stderr, "source Punt: %s\n", format ? format : "(null)");
    exit(90);
}

int16_t WinPrintf(char *format, ...)
{
    fprintf(stderr, "source WinPrintf: %s\n", format ? format : "(null)");
    return 0;
}

void clip_KillWin(int16_t window) { (void)window; }
void clip_SetWin(int16_t window) { (void)window; }
void clip_Off(void) { }
void win_DrawWindow(int16_t window) { (void)window; }
void win_FlushEvents(void) { }
void f_1E57_00B1(void) { }
void f_1E57_0052(void) { }
void f_21FA_0B4B(void) { }
void f_21FA_0AD2(void) { }
void f_24FA_00B5(void) { }
void font_InitFonts(void) { }
void f_208F_0419(struct Pt *size, int16_t id)
{ (void)size; (void)id; }
void f_1B73_01E1(char *image, char *mask) { (void)image; (void)mask; }
void f_1B73_00D9(void) { }
struct Pt win_StringSize(char *text)
{ (void)text; Punt("unexpected auto-sized window string"); return (struct Pt){0,0}; }
void f_1F58_0090(void) { Punt("invalid source window geometry dependency"); }
void f_1FD2_0883(int16_t x, int16_t y, int16_t id, int16_t mode, int16_t flag)
{ (void)x; (void)y; (void)id; (void)mode; (void)flag; abort(); }
void f_1FD2_03EB(char *obj, int16_t id) { (void)obj; (void)id; abort(); }
void f_1FD2_044F(char *window, int16_t id) { (void)window; (void)id; abort(); }
void f_1FD2_0438(int16_t id) { (void)id; abort(); }
void f_1FD2_049C(int16_t id) { (void)id; abort(); }
void f_218D_01EB(void) { abort(); }

int16_t f_195A_0260(void) { return 0; }
void f_195A_001D(void) { abort(); }
void f_195A_0035(void) { abort(); }
int16_t f_195A_004B(int16_t pages) { (void)pages; abort(); }
void f_195A_0062(int16_t handle, int16_t logical, int16_t physical)
{ (void)handle; (void)logical; (void)physical; abort(); }
void f_195A_007D(int16_t handle) { (void)handle; abort(); }
void f_195A_01CB(int16_t handle, char *name)
{ (void)handle; (void)name; abort(); }

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

int main(int argc, char **argv)
{
    const uint16_t window_id = 0;
    char **handle;
    char **projected_handle;
    char **objects;
    uint8_t *wire;
    uint16_t count, i;
    int32_t payload_size;
    int16_t db;

    if (argc != 2 || dos_files_set_root(argv[1]) != 0) return 2;
    if (!sim_window_runtime_owner_init()) return 3;
    sim_window_source_set_profile(0);
    if (sim_handles_global_configure(SIZE_MAX, 65536) != SIM_HANDLE_OK) return 4;
    db = db_SetDataBase("HCEGANT");
    if (db < 0 || db >= SIM_SOURCE_DATABASE_COUNT) return 5;
    win_LockInit();
    win_LockWin((int16_t)(window_id << 8));

    handle = win_handles[window_id];
    if (handle == NULL || *handle == NULL || !win_IsWinLocked(0)) return 6;
    if (sim_window_ref_registry_handle(&sim_window_ref_registry, window_id) != handle)
        return 7;
    objects = sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, *handle);
    if (objects == NULL) return 8;
    wire = (uint8_t *)*handle;
    count = read_u16(wire + 0x0c);
    payload_size = f_171C_1C1C(handle);
    if (count == 0 || payload_size < (int32_t)(0x2c + (size_t)count * 4u))
        return 9;

    printf("WINDOW,%u,%u,%" PRId32 ",%d,%d\n", window_id, count, payload_size,
           win_IsWinLocked(0), db);
    for (i = 0; i < count; ++i) {
        ptrdiff_t offset = objects[i] - (char *)wire;
        int16_t size = sim_window_wire_read_i16(objects[i], 0x22);
        printf("OBJECT,%u,%td,%u,%d\n", i, offset,
               (unsigned)(uint8_t)objects[i][0x21], size);
    }

    win_UnlockWin(0);
    projected_handle = sim_window_ref_registry_handle(&sim_window_ref_registry,
                                                       window_id);
    printf("UNLOCK,%d,%d,%d\n", win_IsWinLocked(0),
           win_handles[window_id] != NULL, projected_handle != NULL);
    if (win_IsWinLocked(0)) return 11;
    db_CloseDataBase();
    dos_files_close_all();
    return 0;
}
