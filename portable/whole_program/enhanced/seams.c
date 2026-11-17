#include "runtime.h"
#include "actions.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include <string.h>
#include <stdlib.h>

static int prox_owner=-1, prox_event=-1;
static int credits_wait,credits_cancel;
int enhanced_cancel_credits(void){if(!credits_wait)return 0;credits_cancel=1;return 1;}
extern void __real_AboutDialog(void);
void __wrap_AboutDialog(void){credits_wait=native_workspace_active();credits_cancel=0;__real_AboutDialog();credits_wait=credits_cancel=0;}
extern int16_t __real_DialogAbortOrCont(void);
int16_t __wrap_DialogAbortOrCont(void){int16_t result=__real_DialogAbortOrCont();return credits_wait&&credits_cancel?1:result;}
static int minimap_wait,minimap_ready,minimap_close;
static int world_press;
extern void __real_processEdit(void *);
extern int16_t CurGameTool;
void __wrap_processEdit(void *event){
    const int16_t *words=event;
    extern int16_t CurGameType;
    /* A queued native click retains its initial press until processEdit samples
     * it, even if the physical release arrived during source double-click wait.
     * Later held samples and all shift/double/experimental tools stay original. */
    int previous=world_press;
    world_press=native_workspace_active()&&enhanced_pointer_tracking(0)&&CurGameType!=3&&CurGameTool==-1&&!(words[1]&3)&&!(words[3]&0x6000);
    __real_processEdit(event);world_press=previous;
}
int enhanced_minimap_owner(void){return minimap_wait?0x1400:-1;}
extern void __real_OpenMiniMapWin(void);
void __wrap_OpenMiniMapWin(void){
    const char *enabled=getenv("SIMANT_ENHANCED_MINIMAP");
    if(!native_workspace_active()||(enabled&&!strcmp(enabled,"0"))){__real_OpenMiniMapWin();return;}
    minimap_wait=1;minimap_ready=minimap_close=0;
    __real_OpenMiniMapWin();
    minimap_wait=minimap_ready=minimap_close=0;
}
extern int16_t __real_StillDown(void);
extern EnhancedRect miniMapRect,miniMapCursorRect;
int16_t __wrap_StillDown(void){
    if(!minimap_wait){int16_t held=__real_StillDown();if(world_press){world_press=0;return held|1;}return held;}
    /* First check follows Mini_DrawMapI and DrawMiniMapCursor. Replay one
     * ordinary map hit; the original loop alone converts it and moves the view. */
    if(!minimap_ready){
        minimap_ready=1;enhanced_publish(ENHANCED_MODAL_POLL);
        EnhancedPoint point;
        int selected=native_workspace_minimap(&miniMapRect,&miniMapCursorRect,&point);
        if(!portable_m1b73_try_enqueue_command(selected?0x1401:(int16_t)0xff00,0,0x200,selected?point.x:0,selected?point.y:479))abort();
        minimap_close=selected;
    }else if(minimap_close){
        if(!portable_m1b73_try_enqueue_command((int16_t)0xff00,0,0x200,0,479))abort();
        minimap_close=0;
    }
    return 0;
}
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
static int experiment_wait,experiment_stage,experiment_choice,experiment_owner;
static int experiment_selected,experiment_root_consumed,experiment_leaf_consumed;
static EnhancedPoint experiment_point;
int enhanced_experiment_menu_active(void){return experiment_wait;}
int enhanced_experiment_input(HostInputState *state){
    if(!experiment_wait)return 0;
    memset(state,0,sizeof(*state));state->x=experiment_point.x;state->y=experiment_point.y;
    state->dos_modifiers=(uint8_t)native_workspace_proximity_modifiers();return 1;
}
extern int16_t __real_DoExpMenu(int16_t,int16_t);
int16_t __wrap_DoExpMenu(int16_t x,int16_t y){
    const char *enabled=getenv("SIMANT_ENHANCED_PROXIMITY");
    if(!native_workspace_active()||(enabled&&!strcmp(enabled,"0")))return __real_DoExpMenu(x,y);
    experiment_wait=1;experiment_stage=0;experiment_owner=0x900;experiment_selected=-1;experiment_root_consumed=experiment_leaf_consumed=0;experiment_point=(EnhancedPoint){x,y};
    int16_t result=__real_DoExpMenu(x,y);experiment_wait=experiment_stage=0;return result;
}
static void experiment_event(int code){if(!portable_m1b73_try_enqueue_command((int16_t)code,0,0x200,experiment_point.x,experiment_point.y))abort();}
static int experiment_menu(void){
    enhanced_publish(ENHANCED_MODAL_POLL);EnhancedDialogsSnapshot menu=enhanced_snapshot()->dialogs;
    int choice=native_workspace_proximity(&menu);if(choice<0){experiment_wait=0;return -1;}
    experiment_owner=menu.owner;
    for(unsigned i=0;i<menu.object_count;++i)if(menu.objects[i].id==choice){const EnhancedRect *r=&menu.objects[i].rect;experiment_point=(EnhancedPoint){(r->left+r->right)/2,(r->top+r->bottom)/2};break;}
    /* Selection/highlighting is the source widget operation. DoExpMenu alone
     * chooses/opens its submenu, changes ExpSubStates and returns the tool. */
    if(choice>=menu.owner+2){
        extern void _win_SetProxItem(int16_t),portable_m1b73_semantic_pointer(int,int,int);
        experiment_selected=choice;
        _win_SetProxItem((int16_t)choice);portable_m1b73_semantic_pointer(experiment_point.x,experiment_point.y,0);
    }
    return choice;
}
extern int16_t __real_hotbox_pointer_hit_id(void);
int16_t __wrap_hotbox_pointer_hit_id(void){
    /* The native widget is the proximity hit device during this transaction.
     * This keeps the source FBxx highlight/selection update authoritative. */
    return experiment_wait&&experiment_selected>=0?(int16_t)experiment_selected:__real_hotbox_pointer_hit_id();
}
extern int16_t __real_MagnifyMenu(int16_t,int16_t,int16_t);
int16_t __wrap_MagnifyMenu(int16_t x,int16_t y,int16_t plane){
    const char *enabled=getenv("SIMANT_ENHANCED_PROXIMITY");
    if(!native_workspace_active()||(enabled&&!strcmp(enabled,"0")))return __real_MagnifyMenu(x,y,plane);
    ++magnify_wait;magnify_done=0;int16_t r=__real_MagnifyMenu(x,y,plane);--magnify_wait;magnify_done=0;return r;
}
extern int16_t __real_ButtonHeld(void);
int16_t __wrap_ButtonHeld(void){
    if(magnify_wait&&magnify_done)return 0;
    if(experiment_wait&&experiment_stage==1&&experiment_root_consumed){
        extern int16_t clip_window_z_order[32];
        if(clip_window_z_order[0]==0x900){experiment_stage=3;experiment_event(experiment_choice);}
        else {
            int choice=experiment_menu();
            if(experiment_wait){
                if(choice<experiment_owner+2){
                    SDL_Event key={.type=SDL_EVENT_KEY_DOWN};key.key.scancode=SDL_SCANCODE_ESCAPE;key.key.down=1;SDL_PushEvent(&key);key.type=SDL_EVENT_KEY_UP;key.key.down=0;SDL_PushEvent(&key);experiment_stage=3;
                }else{experiment_stage=2;experiment_event(0xfb00|(experiment_owner>>8));}
            }
        }
    }else if(experiment_wait&&experiment_stage==2&&experiment_leaf_consumed){
        /* The preceding proximity notification has now updated the original
         * submenu state. Deliver its original accept event on the next poll. */
        experiment_stage=3;experiment_event(0xff00);
    }
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
int enhanced_proximity_owner(void){return experiment_wait?experiment_owner:magnify_wait?0x1d00:prox_owner;}
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
    if(experiment_wait&&!experiment_stage){
        experiment_choice=experiment_menu();
        if(experiment_wait){experiment_stage=experiment_choice>=0x902?1:3;experiment_event(experiment_stage==1?0xfb09:experiment_choice);}
        return;
    }
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
    if(experiment_wait){
        if(experiment_stage==1)experiment_root_consumed=1;
        if(experiment_stage==2)experiment_leaf_consumed=1;
    }
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
