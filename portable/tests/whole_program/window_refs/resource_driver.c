#include "portable/whole_program/window_refs.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct TestRect {
    int16_t left, top, right, bottom;
} TestRect;
typedef struct TestPoint { int16_t x, y; } TestPoint;

extern void win_LockInit(void);
extern void win_LockWin(int16_t win);
extern void win_UnlockWin(int16_t win);
extern int16_t win_IsWinLocked(int16_t win);
extern void win_LoadWindow(int16_t win);

char **win_handles[45];
TestRect win_offsets[45];
SimWindowRefRegistry sim_window_ref_registry;
int16_t win_numOfWindows, win_numOfColors, win_numOfGroups;
int16_t g_5702[32];
char g_3DB2, g_3DB4, g_5A97;
uint8_t fd_50F6_393C[8];
TestPoint fd_50F6_47DA;
char win_colors[45][6];
void (*win_drawHooks[45])(int16_t phase);

static uint8_t *g_payload;
static char *g_payload_handle;
static size_t g_payload_size;
static int16_t g_resource_id;
static int g_recalc_calls;
static int g_purge_calls;

void Punt(char *format, ...)
{
    fprintf(stderr, "source Punt: %s\n", format != NULL ? format : "(null)");
    abort();
}

int16_t WinPrintf(char *format, ...)
{
    (void)format;
    return 0;
}

void *_fmemset(void *dst, int16_t value, uint16_t count)
{
    return memset(dst, value, count);
}

void *_fmemcpy(void *dst, const void *src, uint16_t count)
{
    return memcpy(dst, src, count);
}

static void unexpected_unselected_service(void)
{
    Punt("unselected window service reached in wire-integration test");
}

uint16_t _fstrlen(char *text) { (void)text; unexpected_unselected_service(); return 0; }
TestPoint win_StringSize(char *text) { TestPoint p = {0, 0}; (void)text; unexpected_unselected_service(); return p; }
void f_208F_0419(TestPoint *size, int16_t id) { (void)size; (void)id; unexpected_unselected_service(); }
int16_t f_1F58_0090(void) { unexpected_unselected_service(); return 0; }
void f_1FD2_0883(int16_t x, int16_t y, int16_t id, int16_t mode, int16_t flag)
{ (void)x; (void)y; (void)id; (void)mode; (void)flag; unexpected_unselected_service(); }
void f_1FD2_03EB(void) { unexpected_unselected_service(); }
void f_1FD2_044F(void) { unexpected_unselected_service(); }
void f_1FD2_0438(void) { unexpected_unselected_service(); }
void f_1FD2_049C(void) { unexpected_unselected_service(); }
void f_218D_01EB(void) { unexpected_unselected_service(); }
void f_171C_1BBA(void *handle) { (void)handle; unexpected_unselected_service(); }
void f_24FA_00B5(void) { unexpected_unselected_service(); }
void font_InitFonts(void) { unexpected_unselected_service(); }
char **db_LoadObject(int16_t object, int16_t kind)
{ (void)object; (void)kind; unexpected_unselected_service(); return NULL; }
void db_PurgeObject(int16_t object, int16_t kind) { (void)object; (void)kind; unexpected_unselected_service(); }
void db_UnhookObject(void) { unexpected_unselected_service(); }
void clip_KillWin(int16_t win) { (void)win; unexpected_unselected_service(); }
void clip_SetWin(int16_t win) { (void)win; unexpected_unselected_service(); }
void clip_Off(void) { unexpected_unselected_service(); }
void win_DrawWindow(int16_t win) { (void)win; unexpected_unselected_service(); }
void win_FlushEvents(void) { unexpected_unselected_service(); }
void f_1E57_00B1(void) { unexpected_unselected_service(); }
void f_1E57_0052(void) { unexpected_unselected_service(); }
void f_21FA_0B4B(void) { unexpected_unselected_service(); }
void f_21FA_0AD2(void) { unexpected_unselected_service(); }

char **f_1A53_00F0(int16_t object, int16_t kind, int16_t type)
{
    if (object != g_resource_id || kind != 0 || type != 1)
        Punt("unexpected source window resource request");
    return &g_payload_handle;
}

int32_t f_171C_1C1C(char **handle)
{
    if (handle != &g_payload_handle || *handle != (char *)g_payload)
        Punt("unexpected source Handle extent query");
    return (int32_t)g_payload_size;
}

int16_t f_171C_1AD4(char **handle)
{
    (void)handle;
    return 0;
}

char *f_171C_1B84(char **handle)
{
    if (handle != &g_payload_handle) Punt("unexpected source data lock");
    return *handle;
}

char *f_171C_1D40(char **handle)
{
    return f_171C_1B84(handle);
}

void f_171C_1C0A(char **handle) { (void)handle; }
void f_171C_1E86(char **handle, int16_t flag) { (void)handle; (void)flag; }
int16_t f_171C_1686(void *handle) { (void)handle; return 0; }
void f_171C_13E4(char **handle) { (void)handle; }
void f_171C_2086(void *handle) { (void)handle; }
void f_171C_20E2(void *handle) { (void)handle; ++g_purge_calls; }

/* Recalc is an explicit renderer/geometry boundary for this test. All window
 * loading, manager locking/unlocking, and RepointObjects code is generated C. */
void win_Recalc(int16_t win)
{
    if ((uint16_t)win >> 8 != (uint16_t)g_resource_id)
        Punt("unexpected source recalculation window");
    ++g_recalc_calls;
}

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static int16_t read_i16(const uint8_t *p)
{
    return (int16_t)read_u16(p);
}

int main(int argc, char **argv)
{
    FILE *input, *output;
    long file_size;
    uint16_t i, count, id;
    char *end;
    char **objects;
    int16_t win;
    int locked, loaded, registry_bound;

    if (argc != 4) return 2;
    id = (uint16_t)strtoul(argv[1], &end, 10);
    if (*end != '\0' || id >= 45) return 3;
    g_resource_id = (int16_t)id;
    input = fopen(argv[2], "rb");
    if (input == NULL || fseek(input, 0, SEEK_END) != 0 ||
        (file_size = ftell(input)) <= 0 || fseek(input, 0, SEEK_SET) != 0)
        return 4;
    g_payload_size = (size_t)file_size;
    g_payload = (uint8_t *)malloc(g_payload_size);
    if (g_payload == NULL || fread(g_payload, 1, g_payload_size, input) != g_payload_size)
        return 5;
    fclose(input);
    g_payload_handle = (char *)g_payload;
    memset(&sim_window_ref_registry, 0, sizeof(sim_window_ref_registry));
    for (i = 0; i < 45; ++i) {
        win_offsets[i].left = (int16_t)0x8000;
        win_offsets[i].top = (int16_t)0x8000;
        win_offsets[i].right = (int16_t)0x8000;
        win_offsets[i].bottom = (int16_t)0x8000;
    }

    win_LockInit();
    win = (int16_t)(id << 8);
    win_LockWin(win);
    count = read_u16(g_payload + 0x0c);
    objects = sim_window_ref_registry_objects_for_buffer(
        &sim_window_ref_registry, (char *)g_payload);
    if (objects == NULL && count != 0) Punt("source lock left no object projection");
    locked = win_IsWinLocked(win);
    loaded = win_handles[id] != NULL;
    registry_bound = sim_window_ref_registry_handle(
        &sim_window_ref_registry, id) != NULL;
    printf("S,%u,%u,%d,%d,%d,%d,%d\n", id, count, locked, loaded,
           registry_bound, g_recalc_calls, g_purge_calls);
    for (i = 0; i < count; ++i) {
        ptrdiff_t offset = objects[i] - (char *)g_payload;
        uint8_t *object = (uint8_t *)objects[i];
        printf("O,%u,%u,%ld,%u,%d\n", id, i, (long)offset,
               object[0x21], (int)read_i16(object + 0x22));
    }

    win_UnlockWin(win);
    printf("U,%u,%d,%d,%d,%d\n", id, win_IsWinLocked(win),
           win_handles[id] != NULL,
           sim_window_ref_registry_handle(&sim_window_ref_registry, id) != NULL,
           g_purge_calls);
    output = fopen(argv[3], "wb");
    if (output == NULL || fwrite(g_payload, 1, g_payload_size, output) != g_payload_size)
        return 6;
    fclose(output);
    sim_window_ref_registry_detach(&sim_window_ref_registry, id);
    free(g_payload);
    return 0;
}
