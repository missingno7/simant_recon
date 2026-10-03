#include "portable/whole_program/menu_globals.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/platform/graphics_source_clip.h"
#include "portable/whole_program/platform/m1b73_queue_source.h"
#include "portable/whole_program/window_source_rects.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Event { int16_t what, message, x4, modifiers, h, v, code, xE; };
struct Pt { int16_t x, y; };

extern int16_t db_SetDataBase(char *name);
extern void db_CloseDataBase(void);
extern int16_t o17_384C_0039(int16_t id);
extern int16_t o10_35F5_0384(char *selection, char **items);
extern void f_171C_030C(char *where);
extern void SetMenuItemState(int16_t id, char state);
extern int16_t f_1FD2_0663(int16_t draw);
extern int16_t *fd_50F6_46A8, *fd_50F6_46BC;
extern int16_t fd_55B3_5AA0[2];
extern int16_t g_604C, g_6050;
extern void (*g_9130)(void);
extern void (*g_9128)(int16_t, int16_t, int16_t);

int16_t fd_55B3_5AA0[2] = {640, 350};
_Static_assert(sizeof(sim_source_screen_clip_list) == 2 * sizeof(struct Rect),
               "source graphics clip owner must retain its two-Rect list");
static int16_t geometry_x[16], geometry_width[16];
int16_t *fd_50F6_46A8 = geometry_x, *fd_50F6_46BC = geometry_width;

static SimGraphicsDriver graphics_owner;
static int16_t title_calls;
static int16_t title_ids[16];
static int16_t title_left[16];
static int16_t title_width[16];
static char drawn_rows[16][128];
static size_t drawn_row_count;
static const int16_t expected_x[5] = {0, 64, 144, 208, 296};
/* The actual root f_1FD2_0663 computes byte lengths from the real source
 * strings. The earlier DOS S17 receipt controlled this helper and recorded
 * its injected arguments, so that receipt is not reused as an oracle here. */
static const int16_t expected_len[5] = {5, 7, 5, 8, 6};
static int16_t reserve_count;
int16_t g_9122, g_9124;

static void source_driver3(int16_t a, int16_t b, int16_t c)
{ (void)a; (void)b; (void)c; }
static void source_tick(void) { }
void (*g_9130)(void) = source_tick;
void (*g_9128)(int16_t, int16_t, int16_t) = source_driver3;
int8_t fd_55B3_360C;
int16_t fd_55B3_3612;
char *fd_55B3_360E;
char *fd_50F6_3B48;
struct TestEmsSlot { uint16_t age; int16_t file, page; };
struct TestEmsSlot **fd_50F6_3B4C;
int16_t fd_55B3_6262;

SimGraphicsDriver *sim_graphics_source_owner(void) { return &graphics_owner; }
int sim_source_runtime_reserve_menu_titles(size_t count)
{
    if (count > 16) return 0;
    reserve_count = (int16_t)count;
    return 1;
}
struct Rect *sim_source_menu_bar_rect(void)
{
    static struct Rect r = {0, 0, 640, 350};
    return &r;
}
PortableM1B73Queue *portable_m1b73_queue_slot(uint8_t slot)
{ (void)slot; return NULL; }
uint8_t portable_m1b73_g9120_low_byte(void) { return 0; }
void f_1B73_0D4B(void) { }
void f_1B73_0B5B(int16_t ticks, PortableM1B73Queue *slot)
{ (void)ticks; (void)slot; }
void f_1B73_0B00(struct Timer *timer, PortableM1B73Queue *slot)
{ (void)timer; (void)slot; }
void f_1B73_0AC3(struct Timer *timer, PortableM1B73Queue *slot)
{ (void)timer; (void)slot; }
void f_1B73_0BC5(int16_t ticks, PortableM1B73Queue *slot)
{ (void)ticks; (void)slot; }
int16_t f_1B73_0C42(int16_t id, PortableM1B73Queue *slot,
                    PortableM1B73Rect *out_rect)
{ (void)id; (void)slot; (void)out_rect; return 0; }
int16_t f_1B73_0A30(int16_t key) { (void)key; return 0; }
uint32_t TickCount(void) { return 0; }
void win_FlushEvents(void) { }
void win_GetEvent(struct Event *event) { (void)event; }
int16_t f_208F_0419(void) { return 0; }
void f_1CE2_0951(struct Rect *rect, int16_t fore, int16_t back)
{ (void)rect; (void)fore; (void)back; }
void Punt(char *format, ...)
{
    fprintf(stderr, "source Punt: %s\n", format != NULL ? format : "(null)");
    abort();
}
int16_t WinPrintf(char *format, ...)
{ (void)format; return 0; }
int16_t f_195A_0260(void) { return 0; }
void f_195A_001D(void) { abort(); }
void f_195A_0035(void) { abort(); }
int16_t f_195A_004B(int16_t pages) { (void)pages; abort(); }
void f_195A_0062(int16_t a, int16_t b, int16_t c)
{ (void)a; (void)b; (void)c; abort(); }
void f_195A_007D(int16_t a) { (void)a; abort(); }
void f_195A_01CB(int16_t a, char *b) { (void)a; (void)b; abort(); }
void f_1B73_01E1(char *image, char *mask) { (void)image; (void)mask; abort(); }
void f_1B73_00D9(void) { abort(); }
void f_1B73_0046(void) { abort(); }
void f_1B73_0235(void) { abort(); }
void f_1B73_0AA3(void) { abort(); }
void f_1B73_0218(int16_t a, int16_t b) { (void)a; (void)b; abort(); }

void f_1FBD_0000(int16_t x, int16_t y, char *text)
{
    (void)x; (void)y;
    if (drawn_row_count < 16) {
        strncpy(drawn_rows[drawn_row_count], text,
                sizeof(drawn_rows[drawn_row_count]) - 1);
        ++drawn_row_count;
    }
}
void f_1B4E_0110(int16_t x, int16_t y, int16_t c)
{ (void)x; (void)y; (void)c; }
void f_1B73_030F(int16_t a, int16_t b, int16_t c, int16_t d, int16_t e)
{ (void)a; (void)b; (void)c; (void)d; (void)e; }
void f_1B73_032E(struct Event *event) { (void)event; }
void f_1B73_0C80(int16_t a) { (void)a; }
void portable_m1b73_event_enqueue_four_word_command(int16_t a,int16_t b,int16_t c,int16_t d)
{ (void)a; (void)b; (void)c; (void)d; }

/* The actual root renderer calls through source graphics/window boundaries. */
struct Rect *f_1CE2_000C(void)
{
    static struct Rect r = {0, 0, 640, 350};
    return &r;
}
void f_1CE2_046D(struct Rect *rect, int16_t color) { (void)rect; (void)color; }
void f_1CE2_044D(struct Rect *rect, int16_t mode) { (void)rect; (void)mode; }
char *GSaveRect(struct Rect *rect) { (void)rect; static char save[1]; return save; }
void f_1F80_0081(int16_t a) { (void)a; }
void f_1B73_0A40(void) { }
int16_t f_1B73_032A(void) { return 0; }
int16_t f_1F58_0038(void) { return 1; }
int16_t f_1F58_0090(void) { return 13; }
char f_1F58_005A(void) { return 0; }
void f_1F58_007F(int16_t c) { (void)c; }
void f_1B73_0A6C(void) { }
void f_1CE2_056C(struct Rect *rect, char *buffer) { (void)rect; (void)buffer; }
void f_1B73_09E9(int16_t x, int16_t y) { (void)x; (void)y; }

void f_1FD2_03EB_unused(struct Rect *rect, int16_t ticks)
{ (void)rect; (void)ticks; }

static void assert_borrowed(const uint8_t *payload, size_t size, const char *text)
{
    uintptr_t begin = (uintptr_t)payload;
    uintptr_t address = (uintptr_t)text;
    assert(address >= begin && address - begin < size);
    assert(memchr(text, 0, size - (size_t)(address - begin)) != NULL);
}

int main(int argc, char **argv)
{
    int16_t db;
    char selection = 0;
    char **handle;
    size_t i;
    uint16_t final_table_count;
    char old_state;

    if (argc != 2 || dos_files_set_root(argv[1]) != 0) return 2;
    graphics_owner.g_3DDE = 8;
    graphics_owner.g_3DDC = 14;
    graphics_owner.g_3DE2 = 1;
    graphics_owner.g_3DE4 = 0;
    graphics_owner.g_3DB2 = 640;
    if (sim_handles_global_configure(SIZE_MAX, 65536) != SIM_HANDLE_OK) return 3;
    portable_menu_source_record_view_init(&g_menu_view);
    fprintf(stderr, "stage-db-open\n"); fflush(stderr);
    db = db_SetDataBase("SHARED");
    if (db < 0) return 4;

    /* Load actual SHARED kind-6 through generated S17, whose real source
     * call invokes the actual generated root geometry consumer. */
    fprintf(stderr, "stage-s17\n"); fflush(stderr);
    assert(o17_384C_0039(0) == 1);
    handle = g_menu_view.handle_owner;
    assert(handle != NULL && *handle != NULL);
    assert(f_171C_1C1C(handle) == 514 && g_menu_view.payload_size == 514);
    assert(g_menu_view.payload_data == (const uint8_t *)(const void *)*handle);
    assert(g_menu_view.table_count == 6 && fd_55B3_6054 != NULL);
    assert(title_calls == 0); /* Geometry source calls use root f_1FD2_0008. */
    fprintf(stderr, "stage-root-layout\n"); fflush(stderr);
    assert(f_1FD2_0663(0) == 1);
    assert(g_604C == 5 && reserve_count == 5);
    for (i = 0; i < 5; ++i) {
        if (fd_50F6_46A8[i] != expected_x[i] ||
            fd_50F6_46BC[i] != expected_len[i]) {
            fprintf(stderr, "geometry[%u]=(%d,%d) expected=(%d,%d) title=<%s>\n",
                    (unsigned)i, fd_50F6_46A8[i], fd_50F6_46BC[i],
                    expected_x[i], expected_len[i], fd_55B3_6054[0][i]);
            return 10;
        }
        assert_borrowed((const uint8_t *)(const void *)*handle, 514,
                        fd_55B3_6054[0][i]);
    }
    assert(strcmp(fd_55B3_6054[0][4], " Speed") == 0);
    assert(strcmp(fd_55B3_6054[5][0], " Pause  ") == 0);

    /* The actual root state setter must mutate the exact item table that S17
     * installed, proving both translation units share one owner. */
    old_state = fd_55B3_6054[5][0][0];
    fprintf(stderr, "stage-set-state\n"); fflush(stderr);
    SetMenuItemState(0x40, (char)0x20);
    assert(fd_55B3_6054[5][0][0] == 0x20);
    fd_55B3_6054[5][0][0] = old_state;

    /* S10's real generated dropdown still walks the loaded source item table. */
    assert(f_171C_1C1C(handle) == 514 && *handle != NULL);
    fprintf(stderr, "stage-s10\n"); fflush(stderr);
    assert(o10_35F5_0384(&selection, fd_55B3_6054[5]) == 0);
    assert(drawn_row_count > 0);
    {
        int found_pause = 0;
        for (i = 0; i < drawn_row_count; ++i)
            if (strstr(drawn_rows[i], "Pause") != NULL) found_pause = 1;
        assert(found_pause);
    }
    assert(g_menu_view.handle_owner == handle && *handle != NULL);

    final_table_count = g_menu_view.table_count;
    sim_menu_globals_release();
    db_CloseDataBase();
    dos_files_close_all();
    printf("{\"status\":\"PASS\",\"db\":%d,\"menu_count\":%d,\"table_count\":%u,\"dropdown_rows\":%u}\n",
           db, g_604C, (unsigned)final_table_count,
           (unsigned)drawn_row_count);
    return 0;
}
