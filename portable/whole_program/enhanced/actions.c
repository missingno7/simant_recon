#include "actions.h"
#include "runtime.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/menu_globals.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/platform/m1b73_timer_view.h"
#include <string.h>
#include "portable/platform/host.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
static const EnhancedActionContract contracts [] = {
#define ACTION(id, route, entry) {id, route, entry},
#include "catalog.inc"
#undef ACTION
};
unsigned enhanced_action_contract_count(void) {
    return sizeof (contracts) / sizeof (contracts [0]);
}
const EnhancedActionContract * enhanced_action_contract(const char * id) {
    if (! id) return NULL;
    for (unsigned i = 0; i < enhanced_action_contract_count(); ++ i) if (! strcmp(contracts [i].id, id)) return & contracts [i];
    return NULL;
}
enum {
    QUEUE_SIZE = 32
};
static struct {
    EnhancedIntent intent;
    int16_t event, owner;
    int screen_x,screen_y;
}
queue [QUEUE_SIZE];
static unsigned head, count, executing, lease;
static uint64_t dismiss_token;static int dismiss_owner;
static int cancel_target;
static struct { int event,x,y,down,active,armed,double_pending,button,external; } pointer;
static int queen_wait,queen_click;
extern void __real_PlaceQueenInYard(void);
void __wrap_PlaceQueenInYard(void){
    ++queen_wait;__real_PlaceQueenInYard();--queen_wait;queen_click=0;
}
int enhanced_queen_wait(void){return queen_wait!=0;}
static int special_transfer_wait;
extern void __real_EditMessage(char *,int32_t,int16_t);
extern char **WindPromptStrs;
void __wrap_EditMessage(char *text,int32_t duration,int16_t mode){
    __real_EditMessage(text,duration,mode);
    if(WindPromptStrs&&text==WindPromptStrs[20])special_transfer_wait=1;
    else if(!text&&duration==-2)special_transfer_wait=0;
}
int enhanced_yard_wait(void){return queen_wait||special_transfer_wait;}
static EnhancedActionLedger ledger;
static uint64_t highest_serial;
extern int16_t edit_scroll_and_redraw(int16_t, int16_t);
extern int16_t clip_window_z_order [32], CurGameType, CurGameTool, ui_pending_menu_item;
extern void OpenModeWindow(void), OpenCasteWindow(void), OpenHistoryWindow(void);
extern void win_ToTop(int16_t);
extern void MapToYard(void), YardToMap(void);
extern int16_t win_IsWinOpen(int16_t);
/* Native ABI counts supplied source window parameters explicitly. */
extern void win_Open(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t);
/* These are complete source event entries, not direct handler calls. The
 * source dispatcher still supplies selection, feedback and click history.
 * Remaining L/E/T entries require gesture/wait/prelude proof, not guesses. */
static int event_for(const char * id, int p, int16_t * event, int16_t * owner) {
    int e = 0;
    * owner = INT16_MIN;
    if (! strcmp(id, "S06") && p == 0) e = 0xfd41;
    else if (! strcmp(id, "S07") && p >= 0 && p < 4) e = 0xfd43 + p;
    else if (id [0] == 'S' && id [1] == '0' && id [2] >= '8' && id [2] <= '9' && p == 0) e = 0xfd31 + id [2] - '8';
    else if (id [0] == 'S' && id [1] == '1' && id [2] >= '0' && id [2] <= '3' && p == 0) e = 0xfd33 + id [2] - '0';
    else if (! strcmp(id, "N01") && p >= 1 && p <= 3) e = 0xfd25 + p;
    else if (! strcmp(id, "N02") && p >= 0 && p < 4) e = 0xfd21 + p;
    else if (! strcmp(id, "N05") && p >= 0 && p < 4) e = 0x000b + p;
    else if (! strcmp(id, "N06") && p >= 0 && p < 5) {
        static const int events [] = {
            0x109, 0x10a, 0x10b, 0x10c, 0x10d
        };
        e = events [p];
    }
    else if ((! strcmp(id, "A01") || ! strcmp(id, "B01")) && p >= 0 && p < 2) e = (id [0] == 'A' ? 0x1204 : 0x1304) + p;
    else if ((! strcmp(id, "A02") || ! strcmp(id, "B02")) && p >= 0 && p < 3) e = (id [0] == 'A' ? 0x1206 : 0x1306) + p;
    else if ((! strcmp(id, "A04") || ! strcmp(id, "B04")) && p == 0) e = id [0] == 'A' ? 0x120f : 0x130f;
    else if (! strcmp(id, "I03") && p >= 0 && p < 10) e = 0x1503 + p;
    /* N06 and N05 need map/edit owner prelude; phase 0 registers it below. */
    if (! e) return 0;
    * event = (int16_t)(uint16_t) e;
    if (e < 0x8000) * owner = (int16_t)(e & 0xff00);
    return 1;
}
/* Exact event alternatives from ProcMenu/ProcEditEvent/ProcMapEvent/ProcYardEvent.
 * In particular 0106..08 clear map scents; 0008..0A do not. */
typedef struct Binding {
    unsigned event;
    const char * id;
    int parameter;
} Binding;
static const Binding bindings [] = {
    {
        0xfd01, "S14", 0
    }, {
        0xfd03, "S01", 0
    }, {
        0xfd04, "S03", 0
    }, {
        0xfd05, "S04", 0
    }, {
        0xfd06, "S04", 1
    }, {
        0xfd08, "S05", 0
    }, {
        0xfd11, "N09", 0
    }, {
        0xfd12, "N09", 1
    }, {
        0xfd13, "N09", 2
    }, {
        0xfd14, "N09", 3
    }, {
        0xfd15, "N09", 4
    }, {
        0xfd16, "N09", 5
    }, {
        0xfd17, "Y05", 1
    }, {
        0xfd21, "N02", 0
    }, {
        0xfd22, "N02", 1
    }, {
        0xfd23, "N02", 2
    }, {
        0xfd24, "N02", 3
    }, {
        0xfd26, "N01", 1
    }, {
        0xfd27, "N01", 2
    }, {
        0xfd28, "N01", 3
    }, {
        0xfd31, "S08", 0
    }, {
        0xfd32, "S09", 0
    }, {
        0xfd33, "S10", 0
    }, {
        0xfd34, "S11", 0
    }, {
        0xfd35, "S12", 0
    }, {
        0xfd36, "S13", 0
    }, {
        0xfd41, "S06", 0
    }, {
        0xfd43, "S07", 0
    }, {
        0xfd44, "S07", 1
    }, {
        0xfd45, "S07", 2
    }, {
        0xfd46, "S07", 3
    }, {
        5, "N10", 0
    }, {
        6, "I05", 0
    }, {
        7, "E01", 0
    }, {
        8, "N01", 1
    }, {
        9, "N01", 2
    }, {
        10, "N01", 3
    }, {
        11, "N05", 0
    }, {
        12, "N05", 1
    }, {
        13, "N05", 2
    }, {
        14, "N05", 3
    }, {
        15, "S06", 0
    }, {
        16, "N07", 0
    }, {
        17, "P11", 0
    }, {
        18, "P11", 1
    }, {
        0x105, "N02", 0
    }, {
        0x106, "N01", 1
    }, {
        0x107, "N01", 2
    }, {
        0x108, "N01", 3
    }, {
        0x109, "N06", 0
    }, {
        0x10a, "N06", 1
    }, {
        0x10b, "N06", 2
    }, {
        0x10c, "N06", 3
    }, {
        0x10d, "N06", 4
    }, {
        0x10e, "N08", 0
    }, {
        0x10f, "N09", 2
    }, {
        0x110, "K02", 0
    }, {
        0x111, "N09", 3
    }, {
        0x112, "K01", 0
    }, {
        0x113, "N09", 4
    }, {
        0x114, "Y05", 1
    }, {
        0x115, "N09", 5
    }, {
        0x116, "I05", 1
    }, {
        0x117, "E01", 1
    }, {
        0x118, "Y05", 0
    }, {
        0x1203, "I05", 2
    }, {
        0x1204, "A01", 0
    }, {
        0x1205, "A01", 1
    }, {
        0x1206, "A02", 0
    }, {
        0x1207, "A02", 1
    }, {
        0x1208, "A02", 2
    }, {
        0x120f, "A04", 0
    }, {
        0x1303, "I05", 3
    }, {
        0x1304, "B01", 0
    }, {
        0x1305, "B01", 1
    }, {
        0x1306, "B02", 0
    }, {
        0x1307, "B02", 1
    }, {
        0x1308, "B02", 2
    }, {
        0x130f, "B04", 0
    }, {
        0x1503, "I03", 0
    }, {
        0x1504, "I03", 1
    }, {
        0x1505, "I03", 2
    }, {
        0x1506, "I03", 3
    }, {
        0x1507, "I03", 4
    }, {
        0x1508, "I03", 5
    }, {
        0x1509, "I03", 6
    }, {
        0x150a, "I03", 7
    }, {
        0x150b, "I03", 8
    }, {
        0x150c, "I03", 9
    }, {
        0x150d, "I05", 4
    }, {
        0x150e, "I04", 0
    }, {
        0x1907, "N02", 0
    }, {
        0x1908, "N02", 1
    }, {
        0x1909, "N02", 2
    }, {
        0x190a, "N02", 3
    }, {
        0x190b, "Y02", 0
    }, {
        0x190d, "Y03", 0
    }, {
        0x190e, "Y03", 1
    }, {
        0x1910, "Y04", 0
    }, {
        0x1911, "I05", 5
    }
};
int enhanced_event_binding(unsigned event, const char * * id, int * parameter) {
    for (unsigned i = 0; i < sizeof (bindings) / sizeof (bindings [0]); ++ i) if (bindings [i].event == event) {
        if (id) * id = bindings [i].id;
        if (parameter) * parameter = bindings [i].parameter;
        return 1;
    }
    return 0;
}
EnhancedActionResult enhanced_submit_event(unsigned event, int h, int v, int modifiers) {
    const char * id;
    int parameter;
    if (! enhanced_event_binding(event, & id, & parameter)) return ENHANCED_NEEDS_ADAPTER;
    EnhancedIntent intent = {
        .parameter = parameter,.source_event = (int16_t) event,.h = h,.v = v,.modifiers = modifiers,.serial = highest_serial + 1
    };
    memcpy(intent.id, id, 4);
    return enhanced_submit(& intent);
}
EnhancedActionResult enhanced_submit_pan(int dx, int dy) {
    EnhancedIntent i = {
        .id = "N03",.h = dx,.v = dy,.serial = highest_serial + 1
    };
    return enhanced_submit(& i);
}
EnhancedActionResult enhanced_submit(const EnhancedIntent * intent) {
    if (! enhanced_contracts_enabled()) return ENHANCED_DISABLED;
    if (! intent || intent->id [3] != 0 || ! intent->serial) return ENHANCED_BAD_PARAMETER;
    const EnhancedActionContract * c = enhanced_action_contract(intent->id);
    if (! c) return ENHANCED_BAD_PARAMETER;
    if (c->route == 'H') return ENHANCED_HOST_ONLY;
    if (intent->sample_count || intent->task_token) return ENHANCED_NEEDS_ADAPTER;
    int16_t event, owner;
    if ((intent->parameter == -2 || intent->parameter == -3) && (intent->source_event==4 || intent->source_event==0x102 || intent->source_event==0x1902 || intent->source_event==0x120d || intent->source_event==0x130d || intent->source_event==0x502 || intent->source_event==0x150e)) {
        event=intent->source_event;owner=event&0xff00;
        const char *expected=event==4?"P01":event==0x102?"N04":event==0x1902?"Y01":event==0x120d?"A03":event==0x130d?"B03":event==0x150e?"I04":"I01";
        if(strcmp(intent->id,expected))return ENHANCED_BAD_PARAMETER;
        if(intent->parameter==-3 && ((event!=0x120d&&event!=0x130d)||intent->h<0||intent->h>100||intent->v<0||intent->v>2))return ENHANCED_BAD_PARAMETER;
    }
    else if (! strcmp(intent->id, "N03")) {
        if (intent->h < - 128 || intent->h > 128 || intent->v < - 64 || intent->v > 64 || (! intent->h && ! intent->v)) return ENHANCED_BAD_PARAMETER;
        event = 0;
        owner = INT16_MIN;
    }
    else if (intent->source_event) {
        const char * id;
        int parameter;
        if (! enhanced_event_binding((uint16_t) intent->source_event, & id, & parameter) || strcmp(id, intent->id) || parameter != intent->parameter) return ENHANCED_BAD_PARAMETER;
        event = intent->source_event;
        owner = (uint16_t) event >= 0xfd00 ? INT16_MIN : (event & 0xff00);
    }
    else if (! event_for(intent->id, intent->parameter, & event, & owner)) return ENHANCED_NEEDS_ADAPTER;
    if (intent->serial <= highest_serial) return ENHANCED_DUPLICATE;
    if (count == QUEUE_SIZE) return ENHANCED_QUEUE_FULL;
    unsigned tail = (head + count) % QUEUE_SIZE;
    queue [tail].intent = * intent;
    queue [tail].event = event;
    queue [tail].owner = owner;
    native_workspace_request_point(&queue[tail].screen_x,&queue[tail].screen_y);
    highest_serial = intent->serial;
    ++ ledger.submitted;
    ++ count;
    return ENHANCED_QUEUED;
}
static int menu_enabled(int16_t event) {
    unsigned cmd = (uint16_t) event & 0xff, menu = (cmd - 1) >> 4, item = (cmd - 1) & 15;
    if (menu + 1 >= g_menu_view.table_count || item >= 16 || ! g_6054 || ! g_6054 [menu + 1]) return 0;
    /* Native menu uses the same source tables: titles at [0], items at [menu+1]. */
    if (! g_6054 [0] || ! g_6054 [0] [menu] || ((uint8_t) g_6054 [0] [menu] [0] & 0x80)) return 0;
    char * * items = g_6054 [menu + 1];
    for (unsigned i = 0; i <= item; ++ i) if (! items [i]) return 0;
    return((uint8_t) items [item] [0] & 0x80) == 0;
}
/* Source projection runs after owner preparation: world pixels, overview cells,
 * source-object offsets, or History graph fractions in thousandths. */
static void enhanced_pointer_coordinates(int x,int y,int *h,int *v) {
    unsigned event=pointer.event,slot=event>>8,index=event&255;
    const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[slot];
    int left=0,top=0;
    if(entry->bound && index<entry->view.count) {
        const uint8_t *b=(const uint8_t *)entry->view.object_table[index];
        left=sim_window_wire_read_i16(b,0);top=sim_window_wire_read_i16(b,2);
    }
    extern EnhancedPoint MapPnt;extern EnhancedRect editTileRect,map_viewport_rect;
    extern int16_t mapXsize,mapYsize,multiplier;
    if(event==4){*h=x-MapPnt.x*16+editTileRect.left;*v=y-MapPnt.y*16+editTileRect.top;}
    else if(event==0x102){*h=map_viewport_rect.left+x*mapXsize+mapXsize/2;*v=map_viewport_rect.top+y*mapYsize+mapYsize/2;}
    else if(event==0x1902){*h=map_viewport_rect.left+x;*v=map_viewport_rect.top+y;}
    else if(event==0x150e){const uint8_t *b=(const uint8_t *)entry->view.object_table[index];*h=left+(sim_window_wire_read_i16(b,4)-left)*x/1000;*v=top+(sim_window_wire_read_i16(b,6)-top)*y/1000;}
    else {*h=left+x;*v=top+y;}
}
/* Device seam; source StillDown/GetMousePos continue to own their trackers. */
extern void portable_m1b73_semantic_pointer(int,int,int);
int enhanced_submit_wait_dismiss(void){
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(s&&!s->dialogs.modal&&(s->panels.tool==10||s->panels.tool==11)){cancel_target=s->panels.tool;return 1;}
    if(s&&s->dialogs.owner==0x1f00&&enhanced_cancel_credits())return 1;
    if(!s || !(s->dialogs.flags&1) || (s->dialogs.owner!=0x1400 && s->dialogs.owner!=0x1700))return 0;
    dismiss_token=s->dialogs.task_token;dismiss_owner=s->dialogs.owner;return 1;
}
void enhanced_execute_wait_dismiss(void){
    if(enhanced_yard_wait()&&queen_click&&clip_window_z_order[0]==0x1900){
        int h,v;enhanced_pointer_coordinates(pointer.x,pointer.y,&h,&v);
        enhanced_pointer_poll();
        if(portable_m1b73_try_enqueue_command(0x1902,0,0x200,h,v)){queen_click=0;++ledger.delivered;}
    }
    if(!dismiss_token)return;
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(!s || s->dialogs.task_token!=dismiss_token || s->dialogs.owner!=dismiss_owner){dismiss_token=0;return;}
    if(portable_m1b73_try_enqueue_command((int16_t)0xff00,0,0x200,0,479))dismiss_token=0;
}
int enhanced_pointer_tracking(int owner){return pointer.armed && (pointer.event&0xff00)==owner && clip_window_z_order[0]==owner;}
int enhanced_transaction_wait(void){return lease && !pointer.armed;}
void enhanced_pointer_poll(void) {
    if(!pointer.armed)return;
    if(pointer.external){if(!lease)pointer.armed=pointer.active=0;return;}
    if(clip_window_z_order[0]!=(pointer.event&0xff00)){
        /* A native menu/held inspector takes capture from the world HWND.
         * Its release still belongs to the source device, even while another
         * logical owner is front and the outer action lease remains live. */
        if(!pointer.down){extern int16_t mouse_x_pixels,mouse_y_pixels;portable_m1b73_semantic_pointer(mouse_x_pixels,mouse_y_pixels,0);}
        if(!lease&&!pointer.down){
            if(!pointer.external){extern int16_t mouse_x_pixels,mouse_y_pixels;portable_m1b73_semantic_pointer(mouse_x_pixels,mouse_y_pixels,0);}
            pointer.armed=pointer.active=0;
        }
        return;
    }
    int h,v;enhanced_pointer_coordinates(pointer.x,pointer.y,&h,&v);
    portable_m1b73_semantic_pointer(h,v,pointer.down);
    if(pointer.double_pending && portable_m1b73_try_enqueue_command(pointer.event,0,pointer.double_pending,h,v)){
        pointer.double_pending=0;++ledger.delivered;
    }
    if(!lease&&!pointer.down)pointer.armed=pointer.active=0;
}
int enhanced_pointer_input(HostInputState *s){
    if(enhanced_experiment_input(s))return 1;
    if(!pointer.armed || pointer.external || clip_window_z_order[0]!=(pointer.event&0xff00))return 0;
    int h,v;enhanced_pointer_coordinates(pointer.x,pointer.y,&h,&v);
    memset(s,0,sizeof(*s));s->x=h;s->y=v;s->left_button_down=(pointer.down&1)!=0;return 1;
}
void enhanced_pointer_external_release(void){if(pointer.armed && clip_window_z_order[0]!=(pointer.event&0xff00)){pointer.down=0;pointer.external=1;}}
void enhanced_pointer_update(int x,int y,int down){pointer.x=x;pointer.y=y;pointer.down=down?pointer.button:0;}
EnhancedActionResult enhanced_submit_pointer(unsigned event,int x,int y,int modifiers){
    if(enhanced_yard_wait()&&clip_window_z_order[0]==0x1900&&event==0x1902){
        if(queen_click)return ENHANCED_QUEUE_FULL;
        pointer.event=event;pointer.button=1;pointer.external=0;pointer.armed=pointer.active=1;
        enhanced_pointer_update(x,y,1);queen_click=1;++highest_serial;++ledger.submitted;return ENHANCED_QUEUED;
    }
    if(pointer.active){
        if(pointer.armed && pointer.event==(int)event && (modifiers&0x6000) && !pointer.double_pending){
            pointer.button=(modifiers&0x4800)?2:1;enhanced_pointer_update(x,y,1);pointer.double_pending=modifiers;++highest_serial;++ledger.submitted;return ENHANCED_QUEUED;
        }
        return ENHANCED_QUEUE_FULL;
    }
    const char *id=event==4?"P01":event==0x102?"N04":event==0x1902?"Y01":event==0x120d?"A03":event==0x130d?"B03":event==0x502?"I01":event==0x150e?"I04":NULL;
    if(!id)return ENHANCED_NEEDS_ADAPTER;
    EnhancedIntent i={.parameter=-2,.source_event=event,.h=x,.v=y,.modifiers=modifiers,.serial=highest_serial+1};
    memcpy(i.id,id,4);
    EnhancedActionResult result=enhanced_submit(&i);
    if(result==ENHANCED_QUEUED){pointer.external=0;pointer.event=event;pointer.button=(modifiers&0x4800)?2:1;pointer.active=1;enhanced_pointer_update(x,y,1);}
    return result;
}
typedef struct NativeTriLevel {uint16_t frac,mid,weight;} NativeTriLevel;
typedef struct NativeTriVerts {int16_t ax,ay,lx,ly,rx,ry;} NativeTriVerts;
extern NativeTriVerts modeVerts,casteVerts;
extern int16_t IsPointInIsoTri(EnhancedPoint *,EnhancedRect *);
extern void BoundPointToTri(EnhancedPoint *,EnhancedRect *);
extern void GetTriLatDist(NativeTriLevel *,NativeTriVerts *,EnhancedPoint *);
/* Labelled percentages choose an original reachable triangle pixel. The
 * canonical conversion is evaluated into local words only; the actual update,
 * preset save and IdealCaste release tail still run through Proc*Event. */
static int allocation_point(int owner,int axis,int percent,int *h,int *v){
    extern uint8_t modeLevels[],casteLevels[];
    const SimWindowRefEntry *e=&sim_window_ref_registry.entries[(unsigned)owner>>8];
    if(!e->bound||e->view.count<=13||axis<0||axis>2||percent<0||percent>100)return 0;
    EnhancedRect r;memcpy(&r,e->view.object_table[13],8);NativeTriLevel current;memcpy(&current,owner==0x1200?modeLevels:casteLevels,6);
    uint32_t best=UINT32_MAX,error=UINT32_MAX;int found=0;
    for(int y=r.top;y<r.bottom;++y)for(int x=r.left;x<r.right;++x){
        EnhancedPoint pt={(int16_t)x,(int16_t)y};if(!IsPointInIsoTri(&pt,&r))continue;
        BoundPointToTri(&pt,&r);NativeTriLevel level;GetTriLatDist(&level,owner==0x1200?&modeVerts:&casteVerts,&pt);
        const uint16_t *a=(const uint16_t *)&level,*b=(const uint16_t *)&current;
        int actual=(a[axis]*100u+0x3fff)/65535;unsigned delta=actual>percent?actual-percent:percent-actual;
        uint32_t distance=0;for(int i=0;i<3;++i)distance+=a[i]>b[i]?a[i]-b[i]:b[i]-a[i];
        if(delta<error||(delta==error&&distance<best)){error=delta;best=distance;*h=pt.x;*v=pt.y;found=1;}
    }
    return found;
}
EnhancedActionResult enhanced_submit_allocation(int owner,int axis,int percent){
    if((owner!=0x1200&&owner!=0x1300)||axis<0||axis>2||percent<0||percent>100)return ENHANCED_BAD_PARAMETER;
    EnhancedIntent i={.parameter=-3,.source_event=owner+13,.h=percent,.v=axis,.serial=highest_serial+1};
    memcpy(i.id,owner==0x1200?"A03":"B03",4);return enhanced_submit(&i);
}
static uint8_t allocation_values[2][3][101];
static int allocation_shape[2][2],allocation_ready[2];
int enhanced_allocation_values(int owner,int axis,uint8_t values[101]){
    int which=owner==0x1200?0:owner==0x1300?1:-1;
    if(which<0||axis<0||axis>2||!allocation_ready[which])return 0;
    memcpy(values,allocation_values[which][axis],101);return 1;
}
void enhanced_allocation_catalog_refresh(void){
    extern uint16_t triWidth,triHeight;
    for(int owner=0;owner<2;++owner){
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[owner?0x13:0x12];
        if(!e->bound||e->view.count<=13)continue;
        EnhancedRect r;memcpy(&r,e->view.object_table[13],8);int w=r.right-r.left,h=r.bottom-r.top;
        if(w<3||h<3||w!=triWidth||h!=triHeight)continue;
        if(allocation_ready[owner]&&allocation_shape[owner][0]==w&&allocation_shape[owner][1]==h)continue;
        NativeTriVerts vertices={(int16_t)(r.left+w/2),r.top,r.left,r.bottom,r.right,r.bottom};
        memset(allocation_values[owner],0,sizeof(allocation_values[owner]));
        for(int y=r.top;y<r.bottom;++y)for(int x=r.left;x<r.right;++x){
            EnhancedPoint p={(int16_t)x,(int16_t)y};if(!IsPointInIsoTri(&p,&r))continue;
            BoundPointToTri(&p,&r);NativeTriLevel levels;GetTriLatDist(&levels,&vertices,&p);
            const uint16_t values[]={levels.frac,levels.mid,levels.weight};
            for(int i=0;i<3;++i)allocation_values[owner][i][(values[i]*100u+0x3fff)/65535]=1;
        }
        allocation_shape[owner][0]=w;allocation_shape[owner][1]=h;allocation_ready[owner]=1;
    }
}
void enhanced_execute_next(void) {
    if(cancel_target&&enhanced_contracts_enabled()){
        /* Original completion entries restore SaveGamePaused themselves. No
         * native assignment or synthetic Pause toggle changes that state. */
        extern void EndLifeTransferMode(void),EndTargetMode(void);
        int tool=cancel_target;cancel_target=0;
        if(CurGameTool==tool){if(tool==10)EndLifeTransferMode();else EndTargetMode();}
    }
    if(enhanced_contracts_enabled()&&CurGameType>=0)enhanced_allocation_catalog_refresh();
    if (! enhanced_contracts_enabled() || ! count || executing || CurGameType < 0 || ui_pending_menu_item || (enhanced_window_flags(clip_window_z_order [0]) & 0x40)) return;
    PortableM1B73TimerQueueView ring;
    if (! portable_m1b73_get_source_timer_queue_view(& ring) || ! ring.capacity || * ring.capacity < 2 || * ring.count < 0 || * ring.count >= * ring.capacity - 1) return;
    int16_t event = queue [head].event, owner = queue [head].owner;
    if (event && owner == INT16_MIN && ! menu_enabled(event)) return;
    executing = 1;
    lease = 1;
    native_workspace_activate_point(queue[head].screen_x,queue[head].screen_y);
    if (owner != INT16_MIN) {
        /* Fixed per-action prelude, independent of native focus and geometry.
         * Always finish win_Open's flush, including when already front. */
        if (owner == 0x1200) OpenModeWindow();
        else if (owner == 0x1300) OpenCasteWindow();
        else if (owner == 0x1500) OpenHistoryWindow();
        else {
            if (owner == 0x1900) MapToYard();
            else if (owner == 0x100 && !win_IsWinOpen(0x100)) YardToMap();
            win_ToTop(owner);
            win_Open(owner, 0, 0, 0, 0, 0);
        }
        ++ ledger.prepared;
        ++ ledger.flush_completed;
        if (clip_window_z_order [0] != owner) {
            head = (head + 1) % QUEUE_SIZE;
            -- count;
            ++ ledger.rejected;
            if(queue[(head+QUEUE_SIZE-1)%QUEUE_SIZE].intent.parameter==-2)pointer.active=0;
            executing = lease = 0;
            return;
        }
    }
    /* Retire BEFORE any source call can poll. No nested callback can retry it.
     * Full-ring deferral was checked before the source prelude. */
    ledger.last_serial = queue [head].intent.serial;
    ledger.last_event = event;
    ledger.last_owner = owner;
    head = (head + 1) % QUEUE_SIZE;
    -- count;
    EnhancedIntent * intent = & queue [(head + QUEUE_SIZE - 1) % QUEUE_SIZE].intent;
    int h = intent->h, v = intent->v;
    if (! strcmp(intent->id, "P11") && v == - 1) {
        const SimWindowRefEntry * entry = & sim_window_ref_registry.entries [0];
        unsigned object = (uint16_t) event;
        if (entry->bound && object < entry->view.count) {
            const uint8_t * b = (const uint8_t *) entry->view.object_table [object];
            int top = sim_window_wire_read_i16(b, 2), bottom = sim_window_wire_read_i16(b, 6);
            v = bottom - (bottom - top) * h / 100;
            h = sim_window_wire_read_i16(b, 0);
        }
    }
    if(intent->parameter==-3 && !allocation_point(owner,intent->v,intent->h,&h,&v)){
        ++ledger.rejected;executing=lease=0;return;
    }
    if (! event) {
        edit_scroll_and_redraw(intent->h, intent->v);
        ++ ledger.delivered;
        lease = 0;
    }
    else {
        if(intent->parameter==-2) {
            pointer.event=event;
            if(event==4){
                extern EnhancedPoint MapPnt;extern EnhancedRect editTileRect;
                int tx=intent->h/16,ty=intent->v/16,w=(editTileRect.right-editTileRect.left)/16,h=(editTileRect.bottom-editTileRect.top)/16;
                if(tx<MapPnt.x||tx>=MapPnt.x+w||ty<MapPnt.y||ty>=MapPnt.y+h)edit_scroll_and_redraw(tx-w/2-MapPnt.x,ty-h/2-MapPnt.y);
            }
            pointer.armed=1;pointer.active=1;
            enhanced_pointer_coordinates(intent->h,intent->v,&h,&v);
            enhanced_pointer_poll();
        }
        if (portable_m1b73_try_enqueue_command(event, 0, intent->modifiers, h, v)) ++ ledger.delivered;
        else {++ledger.rejected;lease=0;}
    }
    executing = 0;
}
const EnhancedActionLedger * enhanced_action_ledger(void) {
    return & ledger;
}
int enhanced_action_lease_active(void) {
    return lease != 0;
}
void enhanced_action_finish(void) {
    if(pointer.armed&&!pointer.down){
        if(!pointer.external)enhanced_pointer_poll();
        pointer.active=pointer.armed=pointer.double_pending=0;
    }
    lease = 0;
}
/* Discrete source objects retain their original first-click FIFO route. Live
 * canvas trackers use enhanced_submit_pointer instead of this hit lookup. */
int enhanced_submit_hit(int owner, int h, int v) {
    if (! enhanced_contracts_enabled() || (enhanced_window_flags(clip_window_z_order [0]) & 0x40)) return 0;
    unsigned slot = (unsigned) owner >> 8;
    if (slot >= SIM_WINDOW_REF_REGISTRY_CAPACITY) return 0;
    const SimWindowRefEntry * e = & sim_window_ref_registry.entries [slot];
    if (! e->bound) return 0;
    for (unsigned i = 0; i < e->view.count; ++ i) {
        const uint8_t * b = (const uint8_t *) e->view.object_table [i];
        if (! b || e->view.object_sizes [i] < 0x28 || ! (sim_window_wire_read_u16(b, 0x24) & 2)) continue;
        if (h < sim_window_wire_read_i16(b, 0) || h >= sim_window_wire_read_i16(b, 4) || v < sim_window_wire_read_i16(b, 2) || v >= sim_window_wire_read_i16(b, 6)) continue;
        unsigned event = owner + i;
        if (enhanced_event_binding(event, NULL, NULL)) return enhanced_submit_event(event, h, v, 0) == ENHANCED_QUEUED;
    }
    return 0;
}
