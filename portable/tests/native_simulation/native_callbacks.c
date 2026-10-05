/* Observers for the same explicit caller boundaries used in the DOS fixtures.
 * No ordinary game globals, maps, RNG or simulation implementations live here. */
#include <stdint.h>
#include <stddef.h>

struct Event { int32_t kind, count, args[3]; };
static struct Event events[256];
static int32_t used;
static uint32_t tick;

static void record(int32_t kind, int32_t count, int32_t a, int32_t b, int32_t c)
{
    if (used >= 256) return;
    events[used++] = (struct Event){kind, count, {a, b, c}};
}
void native_fixture_reset(uint32_t initial_tick) { used=0; tick=initial_tick; }
int32_t native_fixture_event_count(void) { return used; }
const struct Event *native_fixture_events(void) { return events; }
void __wrap_DoEditUpdateDraw(void) { record(1,0,0,0,0); }
void __wrap_GotoMyAnt(void) { record(2,0,0,0,0); }
void __wrap_myBeginSound(int16_t a,int16_t b,int16_t c) { record(3,3,a,b,c); }
void __wrap_ResetYellowVars(int16_t a,int16_t b,int16_t c) { record(4,3,a,b,c); }
void __wrap_YellowDeath(int16_t a) { record(5,1,a,0,0); }
void __wrap_myBeginSong(int16_t a,int16_t b) { record(6,2,a,b,0); }
void __wrap_EditMessage(void *p,int32_t duration,int16_t kind)
{ record(7,3,(int32_t)(uintptr_t)p,duration,kind); }
uint32_t __wrap_TickCount(void) { tick+=37; record(8,0,0,0,0); return tick; }
