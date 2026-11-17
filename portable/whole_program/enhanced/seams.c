#include "runtime.h"
#include "actions.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include <string.h>
#include <stdlib.h>

static int prox_owner=-1, prox_event=-1;
static int game_world_created;
extern int16_t CurGameType;
int enhanced_game_ready(void){return game_world_created&&CurGameType>=0;}
extern int16_t __real_NewGame(int16_t);
int16_t __wrap_NewGame(int16_t flag){
    int16_t result=__real_NewGame(flag);
    /* NewGame returns success only after load/world creation and default windows.
     * CurGameType alone is insufficient: its initial zero also means Tutorial. */
    if(result>=0)game_world_created=1;
    return result;
}
static int magnify_wait,magnify_done;
extern int16_t __real_MagnifyMenu(int16_t,int16_t,int16_t);
int16_t __wrap_MagnifyMenu(int16_t x,int16_t y,int16_t plane){
    const char *enabled=getenv("SIMANT_ENHANCED_PROXIMITY");
    if(!native_workspace_active()||(enabled&&!strcmp(enabled,"0")))return __real_MagnifyMenu(x,y,plane);
    ++magnify_wait;magnify_done=0;int16_t r=__real_MagnifyMenu(x,y,plane);--magnify_wait;magnify_done=0;return r;
}
extern int16_t __real_ButtonHeld(void);
int16_t __wrap_ButtonHeld(void){
    if(magnify_wait&&magnify_done)return 0;
    return __real_ButtonHeld();
}
static int compatibility_owner=-1;
int enhanced_compatibility_owner(void){return compatibility_owner;}
extern void __real_DoWinHelp(int16_t);
void __wrap_DoWinHelp(int16_t owner){
    if(!native_workspace_active()){__real_DoWinHelp(owner);return;}
    compatibility_owner=owner&0xff00;__real_DoWinHelp(owner);compatibility_owner=-1;
}
static int ant_menu,choice_modifiers=-1;
extern int16_t __real_AntMenu(void *);
int16_t __wrap_AntMenu(void *ev){
    ++ant_menu;int16_t result=__real_AntMenu(ev);--ant_menu;choice_modifiers=-1;return result;
}
extern uint8_t __real_dos_keyboard_modifiers(void);
uint8_t __wrap_dos_keyboard_modifiers(void){
    uint8_t flags=__real_dos_keyboard_modifiers();
    return ant_menu&&choice_modifiers>=0 ? (flags&0xf0)|choice_modifiers : flags;
}
int enhanced_proximity_owner(void){return magnify_wait?0x1d00:prox_owner;}
extern int16_t __real_win_DoProxMenu(int16_t,int16_t,int16_t,int16_t,int16_t);
int16_t __wrap_win_DoProxMenu(int16_t win,int16_t item,int16_t count,int16_t x,int16_t y){
    const char *enabled=getenv("SIMANT_ENHANCED_PROXIMITY");
    if(!native_workspace_active() || (enabled&&!strcmp(enabled,"0")))return __real_win_DoProxMenu(win,item,count,x,y);
    prox_owner=win;prox_event=-1;
    int16_t r=__real_win_DoProxMenu(win,item,count,x,y);
    prox_owner=prox_event=-1;
    return r;
}
extern void __real_ButtonHeldInit(void);
void __wrap_ButtonHeldInit(void){
    __real_ButtonHeldInit();
    if(magnify_wait){
        enhanced_publish(ENHANCED_MODAL_POLL);
        native_workspace_proximity(&enhanced_snapshot()->dialogs);magnify_done=1;return;
    }
    if(prox_owner<0)return;
    enhanced_publish(ENHANCED_MODAL_POLL);
    EnhancedDialogsSnapshot menu=enhanced_snapshot()->dialogs;
    prox_event=native_workspace_proximity(&menu);
    if(prox_event<0){prox_owner=-1;return;} /* Visible compatibility fallback. */
    choice_modifiers=native_workspace_proximity_modifiers();
    /* The native choice is the original logical object event. The original
     * win_DoProxMenu still owns its open, selected item, loop, close and result. */
    int h=0,v=0;
    for(unsigned i=0;i<menu.object_count;++i)if(menu.objects[i].id==prox_event){
        const EnhancedRect *r=&menu.objects[i].rect;h=(r->left+r->right)/2;v=(r->top+r->bottom)/2;break;
    }
    if(!portable_m1b73_try_enqueue_command(prox_event,0,0x200,h,v))abort();
}
extern int16_t __real_win_GetProxEvent(void);
int16_t __wrap_win_GetProxEvent(void){
    return prox_owner>=0&&prox_event>=0 ? prox_event : __real_win_GetProxEvent();
}

/* The typed conversion transports DOS saved SI explicitly through both
 * entries (event-omitted-word/caller-frames.json). Preserve that native ABI,
 * including when the enhanced preview is disabled. */
extern int16_t __real_DoEvent(int16_t incoming_si);
extern void __real_ui_pump_events_edge_scroll(int16_t incoming_si);
extern int16_t clip_window_z_order[32];
static unsigned depth;

/* The source calls DoEvent only if guest input is pending. The outer pump
 * is therefore the seam that can admit a new semantic intent while idle. */
void __wrap_ui_pump_events_edge_scroll(int16_t incoming_si)
{
    int outer=depth++==0;
    if (outer) {
        enhanced_publish(ENHANCED_OUTER_BEFORE);
        enhanced_execute_next();
    }
    __real_ui_pump_events_edge_scroll(incoming_si);
    if (outer) {
        enhanced_action_finish();
        enhanced_publish(ENHANCED_OUTER_AFTER);
    }
    --depth;
}

int16_t __wrap_DoEvent(int16_t incoming_si)
{
    int outer=depth++==0;
    if (outer) {
        enhanced_publish(ENHANCED_OUTER_BEFORE);
        enhanced_execute_next();
    }
    int16_t result=__real_DoEvent(incoming_si);
    if (outer) {
        enhanced_action_finish();
        enhanced_publish(ENHANCED_OUTER_AFTER);
    }
    --depth;
    return result;
}

/* Called by the existing source event-poll stub, after previous source
 * operations have completed. Only publish at an established modal owner;
 * never dispatch a new gameplay action from a nested source tracker. */
void enhanced_source_poll(void)
{
    if (!enhanced_contracts_enabled()) return;
    int16_t top=clip_window_z_order[0];
    if ((enhanced_window_flags(top)&0x40) || top==0x1a00 || top==0x1e00 || top==0x2100 || enhanced_transaction_wait() || enhanced_yard_wait() || enhanced_pointer_tracking(0x1500))
        enhanced_publish(ENHANCED_MODAL_POLL);
    enhanced_execute_wait_dismiss();
}
