#include "actions.h"
#include "runtime.h"
#include "portable/whole_program/menu_globals.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/platform/m1b73_timer_view.h"
#include <string.h>

static const EnhancedActionContract contracts[] = {
#define ACTION(id, route, entry) {id, route, entry},
#include "catalog.inc"
#undef ACTION
};
unsigned enhanced_action_contract_count(void) { return sizeof(contracts)/sizeof(contracts[0]); }
const EnhancedActionContract *enhanced_action_contract(const char *id)
{
    if (!id) return NULL;
    for (unsigned i=0; i<enhanced_action_contract_count(); ++i)
        if (!strcmp(contracts[i].id,id)) return &contracts[i];
    return NULL;
}

enum { QUEUE_SIZE=32 };
static struct { EnhancedIntent intent; int16_t event, owner; } queue[QUEUE_SIZE];
static unsigned head, count, executing, lease;
static EnhancedActionLedger ledger;
static uint64_t highest_serial;
extern int16_t clip_window_z_order[32], CurGameType, CurGameTool, ui_pending_menu_item;
extern void OpenModeWindow(void), OpenCasteWindow(void), OpenHistoryWindow(void);
extern void win_ToTop(int16_t);
/* Native ABI counts supplied source window parameters explicitly. */
extern void win_Open(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t);

/* These are complete source event entries, not direct handler calls. The
 * source dispatcher still supplies selection, feedback and click history.
 * Remaining L/E/T entries require gesture/wait/prelude proof, not guesses. */
static int event_for(const char *id, int p, int16_t *event, int16_t *owner)
{
    int e=0;
    *owner=INT16_MIN;
    if (!strcmp(id,"S06") && p==0) e=0xfd41;
    else if (!strcmp(id,"S07") && p>=0 && p<4) e=0xfd43+p;
    else if (id[0]=='S' && id[1]=='0' && id[2]>='8' && id[2]<='9' && p==0) e=0xfd31+id[2]-'8';
    else if (id[0]=='S' && id[1]=='1' && id[2]>='0' && id[2]<='3' && p==0) e=0xfd33+id[2]-'0';
    else if (!strcmp(id,"N01") && p>=1 && p<=3) e=0xfd25+p;
    else if (!strcmp(id,"N02") && p>=0 && p<4) e=0xfd21+p;
    else if (!strcmp(id,"N05") && p>=0 && p<4) e=0x000b+p;
    else if (!strcmp(id,"N06") && p>=0 && p<5) { static const int events[]={0x109,0x10a,0x10b,0x10c,0x10d}; e=events[p]; }
    else if ((!strcmp(id,"A01") || !strcmp(id,"B01")) && p>=0 && p<2) e=(id[0]=='A'?0x1204:0x1304)+p;
    else if ((!strcmp(id,"A02") || !strcmp(id,"B02")) && p>=0 && p<3) e=(id[0]=='A'?0x1206:0x1306)+p;
    else if ((!strcmp(id,"A04") || !strcmp(id,"B04")) && p==0) e=id[0]=='A'?0x120f:0x130f;
    else if (!strcmp(id,"I03") && p>=0 && p<10) e=0x1503+p;
    /* N06 and N05 need map/edit owner prelude; phase 0 registers it below. */
    if (!e) return 0;
    *event=(int16_t)(uint16_t)e;
    if (e<0x8000) *owner=(int16_t)(e&0xff00);
    return 1;
}

EnhancedActionResult enhanced_submit(const EnhancedIntent *intent)
{
    if (!enhanced_contracts_enabled()) return ENHANCED_DISABLED;
    if (!intent || intent->id[3]!=0 || !intent->serial) return ENHANCED_BAD_PARAMETER;
    const EnhancedActionContract *c=enhanced_action_contract(intent->id);
    if (!c) return ENHANCED_BAD_PARAMETER;
    if (c->route=='H') return ENHANCED_HOST_ONLY;
    if (intent->sample_count || intent->task_token) return ENHANCED_NEEDS_ADAPTER;
    int16_t event, owner;
    if (!event_for(intent->id,intent->parameter,&event,&owner)) return ENHANCED_NEEDS_ADAPTER;
    if (intent->serial<=highest_serial) return ENHANCED_DUPLICATE;
    if (count==QUEUE_SIZE) return ENHANCED_QUEUE_FULL;
    unsigned tail=(head+count)%QUEUE_SIZE;
    queue[tail].intent=*intent; queue[tail].event=event; queue[tail].owner=owner;
    highest_serial=intent->serial; ++ledger.submitted; ++count;
    return ENHANCED_QUEUED;
}

static int menu_enabled(int16_t event)
{
    unsigned cmd=(uint16_t)event&0xff, menu=(cmd-1)>>4, item=(cmd-1)&15;
    if (menu+1>=g_menu_view.table_count || item>=16 || !g_6054 || !g_6054[menu+1]) return 0;
    /* Native menu uses the same source tables: titles at [0], items at [menu+1]. */
    char **items=g_6054[menu+1];
    for (unsigned i=0; i<=item; ++i) if (!items[i]) return 0;
    return ((uint8_t)items[item][0]&0x80)==0;
}

void enhanced_execute_next(void)
{
    if (!enhanced_contracts_enabled() || !count || executing || CurGameType<0 ||
        CurGameTool!=-1 || ui_pending_menu_item ||
        (enhanced_window_flags(clip_window_z_order[0])&0x40)) return;
    PortableM1B73TimerQueueView ring;
    if (!portable_m1b73_get_source_timer_queue_view(&ring) || !ring.capacity ||
        *ring.capacity<2 || *ring.count<0 || *ring.count>=*ring.capacity-1) return;
    int16_t event=queue[head].event, owner=queue[head].owner;
    if (owner==INT16_MIN && !menu_enabled(event)) return;
    executing=1;
    lease=1;
    if (owner!=INT16_MIN) {
        /* Fixed per-action prelude, independent of native focus and geometry.
         * Always finish win_Open's flush, including when already front. */
        if (owner==0x1200) OpenModeWindow();
        else if (owner==0x1300) OpenCasteWindow();
        else if (owner==0x1500) OpenHistoryWindow();
        else { win_ToTop(owner); win_Open(owner,0,0,0,0,0); }
        ++ledger.prepared; ++ledger.flush_completed;
        if (clip_window_z_order[0]!=owner) {
            head=(head+1)%QUEUE_SIZE; --count; ++ledger.rejected;
            executing=lease=0; return;
        }
    }
    /* Retire BEFORE any source call can poll. No nested callback can retry it.
     * Full-ring deferral was checked before the source prelude. */
    ledger.last_serial=queue[head].intent.serial;
    ledger.last_event=event; ledger.last_owner=owner;
    head=(head+1)%QUEUE_SIZE; --count;
    if (portable_m1b73_try_enqueue_command(event,0,0,0,0)) ++ledger.delivered;
    else { ++ledger.rejected; lease=0; }
    executing=0;
}

const EnhancedActionLedger *enhanced_action_ledger(void) { return &ledger; }
int enhanced_action_lease_active(void) { return lease!=0; }
void enhanced_action_finish(void) { lease=0; }
