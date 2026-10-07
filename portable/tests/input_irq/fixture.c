/* Hardware-boundary controls; the event ring, scan, descriptor, cursor and
 * BIOS FIFO code under test is the actual native platform implementation. */
#include "portable/whole_program/platform/m1b73_queue_runtime.h"
#include "portable/whole_program/platform/m1b73_main_input.h"
#include "portable/whole_program/platform/m1b73_mouse_state.h"
#include "canonical_mouse_input_data.h"
#include "portable/whole_program/types/input_queue.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#undef assert
#define assert(condition) do { if (!(condition)) { \
    fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#condition); exit(1); } } while (0)

/* Controlled source C owner views. ASM cells/queues come from the builder's
 * canonical_mouse_data.c, emitted from actual symbolic source directives. */
uint16_t g_9120;
int16_t g_9122, g_9124, g_5FF0 = 7;
struct Event input_queue[7];
struct InputQueueDescriptor g_5FF2;
extern uint8_t g_4362, g_4363, g_4364, g_4368, g_4369;
struct Host { int unused; };
static struct Host host;
static HostEvent pending[32];
static unsigned pending_head, pending_count, warps, renders, hits;
static uint16_t hit_query;
static PortableInputTimeHost input;
static PortableM1B73Events events;
static PortableM1B73MouseProvider mouse;
static PortableM1B73QueueRuntime runtime;
static SimTimingClock game_clock, bios_clock;
static int16_t width = 640, height = 480;
static const uint8_t image[4] = { 1, 0, 1, 0 };
static const uint8_t *cursor_image = image, *cursor_mask = image;

uint64_t host_time_ns(void) { return 0; }
/* The fixture drives wall-clock (non-virtual) host mode. */
int host_virtual_clock_enabled(void) { return 0; }
void host_wait_ms(uint32_t ms) { (void)ms; assert(0 && "test unexpectedly blocked"); }
int host_poll_event(Host *h, HostEvent *e)
{
    (void)h;
    if (pending_head == pending_count) return 0;
    *e = pending[pending_head++];
    return 1;
}
int host_warp_pointer(Host *h, int16_t x, int16_t y)
{ (void)h; (void)x; (void)y; ++warps; return 1; }
int host_get_input_state(Host *h, HostInputState *s)
{ (void)h; memset(s, 0, sizeof(*s)); return 1; }

static int identity(void *ctx, int16_t x, int16_t y, int16_t *ox, int16_t *oy)
{ (void)ctx; *ox=x; *oy=y; return 1; }
static int header(void *ctx, const uint8_t *a, const uint8_t *b, uint16_t *w, uint16_t *h)
{ (void)ctx; (void)a; (void)b; *w=*h=1; return 1; }
static int hit(void *ctx, int16_t x, int16_t y, uint16_t query, uint32_t *token)
{ (void)ctx; (void)x; (void)y; ++hits; hit_query=query; *token=0; return 0; }
static int render(void *ctx, PortableM1B73CursorAction a, const uint8_t *im,
                  const uint8_t *ma, uint16_t w, uint16_t h, int16_t x, int16_t y)
{ (void)ctx; (void)a; (void)im; (void)ma; (void)w; (void)h; (void)x; (void)y; ++renders; return 1; }
static int cursor_mode_callback(void *ctx, uint8_t mode, int16_t *ax)
{ (void)ctx; (void)mode; *ax=0; return 1; }
static int dispatch(void *ctx, uint16_t status)
{
    (void)ctx;
    if (!((status >> 8) & ((uint16_t)g_5FF2.r.bottom >> 8))) return 1;
    return portable_m1b73_queue_dispatch() == PORTABLE_M1B73_QUEUE_OK;
}
static int observe(void *ctx, const HostEvent *event)
{
    (void)ctx;
    return portable_m1b73_queue_runtime_scan_transition(&runtime, event) >= 0;
}
static void clear_ring(void)
{
    unsigned i;
    g_5FF2.r.left = g_5FF2.r.top = g_5FF2.r.right = 0;
    memset(input_queue, 0, sizeof(input_queue));
    for (i=0;i<7;++i) input_queue[i].what = (int16_t)0x5a5a;
}
static void reset(void)
{
    clear_ring();
    f_1B73_0A6C();
    kbd_last_scan=last_shift=shift_state=0;
    tick_phase=0; timer_busy=mouse_busy=0;
    g_4362=g_4363=g_4364=g_4368=g_4369=0;
    g_4331=g_4332=g_4333=g_4365=g_4366=0;
    g_9120=0; g_9122=260; g_9124=330;
    input.bios_keyboard_flags=input.bios_keyboard_flags_hi=0;
    input.key_head=input.key_count=input.event_head=input.event_count=0;
    input.suppress_bios_key=0;
    mouse.driver_buttons=0;
    g_4DA4=2;
    mouse.event_pump_active=1; mouse.event_mask=0x7f;
    pending_head=pending_count=warps=renders=hits=0;
    f_1B73_0AA3();
}
static void record(unsigned i, uint16_t ax, uint16_t cx, uint16_t dx,
                   uint16_t bx, uint16_t es, uint16_t message)
{
    const struct Event *e=&input_queue[i];
    assert((uint16_t)e->what == 0x5a5a);
    assert((uint16_t)e->message == message);
    assert((uint16_t)e->x4 == 0x1234);
    assert((uint8_t)e->modLo == (uint8_t)ax && (uint8_t)e->modHi == (uint8_t)(ax>>8));
    assert((uint16_t)e->h == cx && (uint16_t)e->v == dx);
    assert((uint16_t)e->code == bx && (uint16_t)e->xE == es);
}
static int scan(uint8_t raw)
{ return portable_m1b73_queue_runtime_scan_byte(&runtime,raw,0x0300,0x5c2d); }
static void add_key(HostEventKind kind, uint16_t key, uint8_t mods)
{
    HostEvent *e=&pending[pending_count++];
    memset(e,0,sizeof(*e)); e->kind=kind; e->key=key; e->modifiers=mods;
}
static void button_timer(void)
{
    struct Timer t = {{0,0,639,479},(void (*)(void))f_1B73_030F,(int16_t)0xff00,1,1,0,0x1f};
    f_1B73_0AC3(&t,&portable_m1b73_queue_set.queues[0]);
}
static void test_keys(void)
{
    static const struct { uint8_t scan, flags, command; } commands[] = {
        {0x19,4,1},{0x4e,4,2},{0x4a,4,3},{0x13,4,4},{0x2c,4,5},
        {0x4e,0,6},{0x4a,0,7}
    };
    unsigned i;
    reset();
    assert(scan(0x1e)==1); record(0,0,0x0302,0x5c2d,0xfa1e,0,0);
    assert(f_1B73_0A30(0x1e)==0x80);
    assert(scan(0x1e)==0 && g_5FF2.r.left==1); /* repeat suppressed/BIOS flushed */
    assert(scan(0x9e)==1 && g_53CD[0x1e]==0x80 && g_5FF2.r.left==1);
    assert(scan(0x2a)==1 && shift_state==2 && g_53CD[0x2a]==0x80);
    assert(f_1B73_0A30(0x2a)==0); /* held normal Shift leaves source cell up */
    shift_state |= 0x80;
    assert(scan(0xaa)==1 && shift_state==0); /* masks bit7 even on break */
    assert(scan(0xe0)==0); assert(scan(0x2a)==1);
    record(1,0,0x0300,0x5c2d,0xfa2a,0,0); /* E0 fake shift -> table */
    reset();
    input.bios_keyboard_flags=4; input.bios_keyboard_flags_hi=1;
    assert(scan(0x19)==1 && g_5FF2.r.left==2);
    record(0,0,0x0302,0x5c2d,0xfa19,0,0x0104);
    record(1,0x8081,4,0x5c2d,0xf081,0,0x0104);
    assert(scan(0x99)==1 && g_5FF2.r.left==2);
    reset(); assert(scan(0x4e)==1);
    record(1,0x8086,0,0x5c2d,0xf086,0,0);
    reset(); input.bios_keyboard_flags=2; assert(scan(0x4e)==1 && g_5FF2.r.left==1);
    reset(); assert(scan(0x3b)==1 && shift_state==0x80 && warps==1);
    assert(scan(0xbb)==1 && shift_state==0x80 && warps==2);
    /* Successful mouse press clears latch after recording message|1. */
    button_timer(); assert(scan(0x39)==0 && shift_state==0);
    record(1,0,0x0302,0x5c2d,0xfa39,0,1);
    record(2,0x0201,260,330,0xff00,0x0101,1);
    for (i=0;i<sizeof(commands)/sizeof(commands[0]);++i) {
        uint8_t s=commands[i].scan, f=commands[i].flags, c=commands[i].command;
        reset(); input.bios_keyboard_flags=f;
        assert(scan(s)==1 && g_5FF2.r.left==2);
        record(0,0,0x0302,0x5c2d,(uint16_t)(0xfa00|s),0,f);
        record(1,(uint16_t)(0x8080|c),f,0x5c2d,(uint16_t)(0xf080|c),0,f);
        assert(scan((uint8_t)(s|0x80))==1 && g_5FF2.r.left==2);
        reset(); input.bios_keyboard_flags=(uint8_t)(f|8);
        assert(scan(s)==1 && g_5FF2.r.left==1); /* Alt negative control */
    }
}
static void test_mouse(void)
{
    HostEvent e = {0};
    reset(); f_1B73_0046();
    assert(g_9120==0x0100 && g_9122==240 && g_9124==320 && g_4331==1);
    assert(g_435A==1 && warps==1 && g_5FF2.r.left==0);
    g_9120=0x0203; f_1B73_0046();
    assert(g_9120==0x0103 && mouse.driver_buttons==0); /* 09F7 takes source BL */
    reset(); button_timer();
    assert(scan(0x39)==0 && g_5FF2.r.left==2 && g_9120==0x0201);
    record(0,0,0x0302,0x5c2d,0xfa39,0,0);
    record(1,0x0201,260,330,0xff00,0x0101,0);
    assert(scan(0xb9)==0 && g_9120==0x0400 && g_5FF2.r.left==3);
    record(2,0x0400,260,330,0xff00,0x0101,0);
    reset(); button_timer();
    e.kind=HOST_EVENT_MOUSE_DOWN; e.button=1; e.x=260; e.y=330;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    record(0,0x0201,260,330,0xff00,0x0101,0);
    e.kind=HOST_EVENT_MOUSE_UP;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    record(1,0x0400,260,330,0xff00,0x0101,0);
    e.kind=HOST_EVENT_MOUSE_DOWN; e.button=3;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    record(2,0x0802,260,330,0xff00,0x0101,0);
    e.kind=HOST_EVENT_MOUSE_UP;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    record(3,0x1000,260,330,0xff00,0x0101,0);
    e.kind=HOST_EVENT_MOUSE_DOWN; e.button=2;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    assert(g_9120==0x2004 && g_5FF2.r.left==4); /* global callback mask1F excludes middle */
    e.kind=HOST_EVENT_MOUSE_UP;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    assert(g_9120==0x4000 && g_5FF2.r.left==4);
    e.kind=HOST_EVENT_MOUSE_DOWN;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    /* Physical driver BL replaces emulated left, not ORed with it. */
    assert(scan(0x39)==0); e.kind=HOST_EVENT_MOUSE_MOVE;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    assert(g_9120==0x0104);
    reset(); button_timer(); e.kind=HOST_EVENT_MOUSE_MOVE; e.x=261; e.y=331;
    assert(portable_m1b73_mouse_consume_event(&mouse,&e)==PORTABLE_M1B73_MOUSE_OK);
    record(0,0x0100,261,331,0xff00,0x0101,0);
    reset(); g_4365=1; g_4333=1;
    assert(portable_m1b73_mouse_callback(&mouse,1,0,10,20)==PORTABLE_M1B73_MOUSE_OK);
    assert(g_4331==1 && !renders && !hits);
    g_4333=0; g_4331=0;
    assert(portable_m1b73_mouse_callback(&mouse,1,0,10,20)==PORTABLE_M1B73_MOUSE_OK);
    assert(renders==2 && hits==1 && hit_query==0x0100 && g_4331==0);
    mouse_busy=1;
    assert(portable_m1b73_mouse_callback(&mouse,2,1,40,50)==PORTABLE_M1B73_MOUSE_OK);
    assert(g_9120==0x0100 && g_9122==10 && mouse_busy==1); mouse_busy=0;
    /* Queue0 declares five storage rows but capacity four. At the admitted
     * full count, its final usable row must dispatch. Never expand capacity. */
    reset();
    {
        struct Timer t = {{0,0,639,479},(void (*)(void))f_1B73_030F,
                          (int16_t)0xff00,1,1,0,0};
        unsigned i;
        for(i=0;i<3;++i) f_1B73_0AC3(&t,&portable_m1b73_queue_set.queues[0]);
        t.d=0x1f;
        f_1B73_0AC3(&t,&portable_m1b73_queue_set.queues[0]);
        assert(*portable_m1b73_queue_set.queues[0].count==4);
        assert(portable_m1b73_mouse_callback(&mouse,2,1,260,330)==PORTABLE_M1B73_MOUSE_OK);
        record(0,0x0201,260,330,0xff00,0x0101,0);
    }
}
static void test_cursor(void)
{
    unsigned i;
    reset(); g_4365=1; g_4366=1;
    assert(scan(0x4d)==0 && g_4362==5 && !warps);
    for (i=0;i<3;++i) assert(portable_m1b73_queue_runtime_cursor_tick(&runtime));
    assert(g_9122==275 && g_4364==0 && tick_phase==3);
    assert(portable_m1b73_queue_runtime_cursor_tick(&runtime));
    assert(g_9122==285 && g_4364==1 && tick_phase==4);
    assert(scan(0xcd)==0 && !g_4362 && !tick_phase && !g_4364);
    input.bios_keyboard_flags=4; assert(scan(0x48)==1 && !g_4363);
    assert(scan(0xc8)==0 && !g_4363);
    reset(); assert(scan(0x4c)==0 && g_9122==320 && g_9124==240);
    g_9122=1; assert(scan(0xcc)==0 && g_9122==320); /* both edges center */
    assert(scan(0x47)==0 && g_9122==6); assert(scan(0xc7)==0);
    assert(scan(0x47)==0 && g_9122==0);
    assert(scan(0x4f)==0 && g_9122==633); assert(scan(0xcf)==0);
    assert(scan(0x4f)==0 && g_9122==639);
    assert(scan(0x49)==0 && g_9124==6);
    assert(scan(0x51)==0 && g_9124==473);
    reset(); g_9122=638; g_4362=5; g_4365=1;
    assert(portable_m1b73_queue_runtime_cursor_tick(&runtime) && g_9122==639);
    reset(); g_4333=1; g_4332=2;
    assert(portable_m1b73_queue_runtime_cursor_tick(&runtime) && g_4332==1);
    assert(portable_m1b73_queue_runtime_cursor_tick(&runtime) && g_4332==1 && !renders);
    reset(); g_4365=1; g_4366=1; g_4362=5;
    for(i=0;i<10;++i) assert(portable_m1b73_queue_runtime_cursor_tick(&runtime));
    assert(g_4364==2 && tick_phase==10);
    for(;i<28;++i) assert(portable_m1b73_queue_runtime_cursor_tick(&runtime));
    assert(g_4364==3 && tick_phase==28);
}
static void test_bios(void)
{
    uint16_t key=0;
    unsigned i;
    reset();
    add_key(HOST_EVENT_KEY_DOWN,0x1e61,0);
    add_key(HOST_EVENT_KEY_DOWN,0x3920,0);
    assert(input.input_time.services.key_available(&input,&key)==0);
    assert(input.key_count==0); /* Space clears older A as well as itself */
    reset();
    add_key(HOST_EVENT_KEY_DOWN,0x1e61,0);
    add_key(HOST_EVENT_KEY_DOWN,0x1c0d,0); pending[1].extended=1;
    assert(input.input_time.services.key_available(&input,&key)==1 && key==0x1c0d);
    assert(input.key_count==1); /* E0 IRQ flushes A; final carry-set Enter remains */
    record(0,0,2,0,0xfa1e,0,0);
    record(1,0,0,0,0xfa1c,0,0);
    reset();
    add_key(HOST_EVENT_KEY_DOWN,0x2a00,2);
    add_key(HOST_EVENT_KEY_DOWN,0x1e41,2);
    add_key(HOST_EVENT_KEY_UP,0xaa00,0); /* high byte must be base scan */
    pending[2].key=0x2a00;
    assert(input.input_time.services.key_available(&input,&key)==1 && key==0x1e41);
    assert(input.key_count==1 && input.bios_keyboard_flags==0);
    record(0,0,2,0,0xfa1e,0,2); /* pre-BIOS shift state in make */
    reset();
    add_key(HOST_EVENT_KEY_DOWN,0x1d00,4);
    add_key(HOST_EVENT_KEY_DOWN,0x1910,4);
    assert(input.input_time.services.key_available(&input,&key)==1 && key==0x1910);
    record(0,0,2,0,0xfa1d,0,0); /* old BIOS flags before Ctrl update */
    record(1,0,2,0,0xfa19,0,0x0104);
    record(2,0x8081,4,0,0xf081,0,0x0104);
    reset(); f_1B73_0A40();
    add_key(HOST_EVENT_KEY_DOWN,0x3920,0);
    assert(input.input_time.services.key_available(&input,&key)==1 && key==0x3920);
    assert(g_53CD[0x39]==0x80 && f_1B73_0A30(0x39)==0 && g_5FF2.r.left==0);
    reset(); f_1B73_0A40();
    for(i=0;i<17;++i) add_key(HOST_EVENT_KEY_DOWN,0x1e61,0);
    assert(input.input_time.services.key_available(&input,&key)==1 && key==0x1e61);
    assert(input.key_count==15 && !input.host_closed); /* original BIOS ring full drops */
}
static void test_ring(void)
{
    unsigned i;
    reset(); shift_state=0x80;
    for(i=0;i<6;++i) assert(portable_m1b73_event_enqueue_registers(&events,0,1,2,3,4));
    assert(g_5FF2.r.left==6);
    assert(!portable_m1b73_event_enqueue_registers(&events,0x0201,1,2,3,4));
    assert(shift_state==0x80 && g_5FF2.r.left==6);
    { struct Event e; assert(f_1B73_032E(&e)==5); }
    assert(portable_m1b73_event_enqueue_registers(&events,0x0201,1,2,3,4));
    assert(shift_state==0 && g_5FF2.r.top==0);
    record(6,0x0201,1,2,3,4,1);
}
static void matrix(void)
{
    static const uint16_t flags[] = {0,1,2,4,8,0x104};
    unsigned f,s,j,i,k;
    for(f=0;f<sizeof(flags)/sizeof(flags[0]);++f) for(s=0;s<128;++s) {
        reset(); g_4DA4=0;
        input.bios_keyboard_flags=(uint8_t)flags[f];
        input.bios_keyboard_flags_hi=(uint8_t)(flags[f]>>8);
        for(i=0;i<7;++i) input_queue[i].what=0;
        for(j=0;j<3;++j) {
            uint8_t raw=(uint8_t)(s|(j==2?0x80:0));
            int carry=scan(raw);
            printf("%u,%u,%u,%d,%u,%u,%u,%u,%u,%u,%u",flags[f],s,raw,carry,
                (uint16_t)g_5FF2.r.left,shift_state,g_4362,g_4363,g_4364,
                (uint16_t)g_9122,(uint16_t)g_9124);
            for(i=0;i<(unsigned)g_5FF2.r.left;++i) {
                uint16_t words[8]; memcpy(words,&input_queue[i],16);
                for(k=0;k<8;++k) printf(",%u",words[k]);
            }
            putchar('\n');
        }
    }
}
int main(int argc, char **argv)
{
    PortableM1B73MouseServices services = {0};
    assert(sim_timing_clock_init_bios(&game_clock,14318180,12)==SIM_TIMING_OK);
    assert(sim_timing_clock_init_bios(&bios_clock,14318180,12)==SIM_TIMING_OK);
    bios_clock.tick_count=0x1234;
    assert(portable_input_time_host_init_clocks(&input,&host,&game_clock,&bios_clock)==PORTABLE_INPUT_TIME_OK);
    assert(portable_input_time_host_set_event_observer(&input,observe,NULL)==PORTABLE_INPUT_TIME_OK);
    assert(portable_input_time_host_bind(&input)==PORTABLE_INPUT_TIME_OK);
    g_5FF2.records=input_queue;
    assert(portable_m1b73_bind_source_main_input(&events,&input,&game_clock,&shift_state,input_queue,7));
    services.host_to_source=services.source_to_host=identity;
    services.cursor_header=header; services.hit_test=hit; services.render_cursor=render;
    portable_m1b73_mouse_asm_state.cursor_image=&cursor_image;
    portable_m1b73_mouse_asm_state.cursor_mask=&cursor_mask;
    assert(portable_m1b73_mouse_bind(&mouse,&host,&input,&portable_m1b73_mouse_asm_state,
                                   &width,&height,&services)==PORTABLE_M1B73_MOUSE_OK);
    mouse.dispatch_queue=dispatch;
    assert(portable_m1b73_queue_runtime_bind(&runtime,&events,&mouse,NULL,cursor_mode_callback));
    if (argc==2 && strcmp(argv[1],"--matrix")==0) matrix();
    else {
        test_keys(); test_mouse(); test_cursor(); test_bios(); test_ring();
        puts("PASS input IRQ: make/break, all event words, commands, mouse, cursor, BIOS, ring");
    }
    portable_m1b73_queue_runtime_unbind(&runtime);
    portable_m1b73_mouse_unbind(&mouse);
    portable_m1b73_unbind_source_main_input(&events);
    portable_input_time_host_shutdown(&input);
    return 0;
}
