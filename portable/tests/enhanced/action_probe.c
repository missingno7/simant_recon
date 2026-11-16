/* Independent control-path comparator, linked only by action_equivalence.py.
 * Baseline replays original events at the same source seam; native lanes use HWNDs. */
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/platform/window_hosting.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
char action_observer_anchor;
extern int32_t main_iteration_count;
extern int16_t clip_window_z_order [];
extern void __real_enhanced_execute_next(void), __real_enhanced_source_poll(void);
extern int16_t edit_scroll_and_redraw(int16_t,int16_t);
extern int16_t win_IsWinOpen(int16_t);
extern void win_ToTop(int16_t), win_Open(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t);
extern void OpenModeWindow(void), OpenCasteWindow(void), OpenHistoryWindow(void), MapToYard(void), YardToMap(void);
static int phase, number, started, modal_inputs,tool_setup,fill_setup,alt_setup,tracking,held_samples,held_calls,recruit_calls,info_setup;
static int held_case(unsigned n){return n>=0xe510&&n<=0xe516;}
static int wanted_tool(unsigned n){return n==0xe516?2:n-0xe510+1;}
static HWND named(const char * name) {
    HWND h = NULL;
    while ((h = FindWindowExA(NULL, h, NULL, !strcmp(name,"Info")?NULL:name))) {
        DWORD pid;
        GetWindowThreadProcessId(h, & pid);
        if (pid == GetCurrentProcessId()){if(!strcmp(name,"Info")){char title[160];GetWindowTextA(h,title,sizeof(title));if(strncmp(title,"Info - ",7))continue;}return h;}
    }
    return NULL;
}
static void dump(int slot) {
    const char * path = getenv("SIMANT_ACTION_CONFIG");
    FILE * config = fopen(path, "r");
    if (! config) abort();
    char base [2048];
    unsigned count;
    if (fscanf(config, "%2047s%u", base, & count) != 2) abort();
    char output [2100];
    snprintf(output, sizeof (output), "%s.%d", base, slot);
    FILE * out = fopen(output, "wb");
    if (! out) abort();
    for (unsigned i = 0; i < count; ++ i) {
        unsigned slices;
        if (fscanf(config, "%u", & slices) != 1) abort();
        for (unsigned j = 0; j < slices; ++ j) {
            long long offset;
            unsigned size;
            if (fscanf(config, "%lld%u", & offset, & size) != 2) abort();
            fwrite(& action_observer_anchor + offset, 1, size, out);
        }
    }
    fclose(config);
    fclose(out);
}
static int gesture_code(unsigned n){return (n>=0xe500&&n<=0xe507)||held_case(n)||n==0xe517;}
static void gesture(unsigned n,int reference){
    int owner=n==0xe500?0x100:n==0xe501?0x1200:n==0xe502?0x1300:n==0xe506?0x1900:n==0xe507?0x1500:0;
    int x=n==0xe500?404:n==0xe501||n==0xe502?110:n==0xe506?240:64;
    int y=n==0xe500?80:n==0xe501||n==0xe502?100:n==0xe506?100:64;
    if(n==0xe507){x=160;y=62;}
    if(n==0xe517){const EnhancedSnapshot *s=enhanced_snapshot();x=(s->world.player_x-s->world.origin.x)*16+8;y=(s->world.player_y-s->world.origin.y)*16+8;}
    int event=owner+(owner==0x1200||owner==0x1300?13:owner==0x1500?14:owner?2:4),mods=n==0xe504?0x2000:0x200;
    if(reference){
        if(owner==0x1200)OpenModeWindow();else if(owner==0x1300)OpenCasteWindow();else if(owner==0x1500)OpenHistoryWindow();else {if(owner==0x1900)MapToYard();if(owner==0x100&&!win_IsWinOpen(0x100))YardToMap();win_ToTop(owner);win_Open(owner,0,0,0,0,0);}
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[(unsigned)owner>>8];const uint8_t *b=(const uint8_t *)e->view.object_table[event&255];
        int h=sim_window_wire_read_i16(b,0),v=sim_window_wire_read_i16(b,2);
        if(owner==0x1200||owner==0x1300){h+=(x-44)*(sim_window_wire_read_i16(b,4)-h)/132;v+=(y-42)*(sim_window_wire_read_i16(b,6)-v)/88;}
        else if(owner==0x100){extern int16_t mapXsize,mapYsize;h+=(x/4)*mapXsize+mapXsize/2;v+=(y/4)*mapYsize+mapYsize/2;}
        else if(!owner){extern EnhancedRect editTileRect;h=editTileRect.left+x;v=editTileRect.top+y;}
        else if(owner==0x1900){extern EnhancedRect map_viewport_rect;h=map_viewport_rect.left+x;v=map_viewport_rect.top+y;}
        else if(owner==0x1500){h+=(sim_window_wire_read_i16(b,4)-h)/2;v+=(sim_window_wire_read_i16(b,6)-v)/2;}
        else {h+=x;v+=y;}
        extern void portable_m1b73_semantic_pointer(int,int,int);portable_m1b73_semantic_pointer(h,v,held_case(n)||n==0xe517);
        if(!portable_m1b73_try_enqueue_command(event,0,mods,h,v))abort();
    }else{
        HWND h=named(owner==0x100?"Map":owner==0x1200?"Behavior Control":owner==0x1300?"Caste Control":owner==0x1900?"Yard":owner==0x1500?"History":"SimAnt - Game");if(!h)abort();
        if(n==0xe505){Workspace w=*native_workspace_layout();w.panels[WS_GAME].zoom=300;native_workspace_apply(&w);x*=3;y*=3;}
        typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;x=MulDiv(x,d,96);y=MulDiv(y,d,96);
        SendMessage(h,n==0xe504?WM_LBUTTONDBLCLK:WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));if(!held_case(n)&&n!=0xe517)SendMessage(h,WM_LBUTTONUP,0,MAKELPARAM(x,y));
    }
}
extern int16_t __real_myButton(void);
extern void __real_processExp(int16_t,int16_t,int16_t),__real_YellowCommand(int16_t);
void __wrap_YellowCommand(int16_t command){if(phase==2&&command==1)++recruit_calls;__real_YellowCommand(command);}
void __wrap_processExp(int16_t x,int16_t y,int16_t shift){
    if(phase==2&&held_case(number)){tracking=1;++held_calls;held_samples=0;}
    __real_processExp(x,y,shift);tracking=0;
}
int16_t __wrap_myButton(void){
    if(tracking){
        static const int samples[4][3]={{80,64,1},{80,64,1},{128,96,1},{128,96,0}};
        unsigned at=held_samples++;
        if(!strcmp(getenv("SIMANT_ACTION_MODE"),"coalesced")&&at==1)at=held_samples++;
        if(at>3)at=3;int x=samples[at][0],y=samples[at][1],down=samples[at][2];
        if(!strcmp(getenv("SIMANT_ACTION_MODE"),"original")){
            extern EnhancedRect editTileRect;extern void portable_m1b73_semantic_pointer(int,int,int);
            portable_m1b73_semantic_pointer(editTileRect.left+x,editTileRect.top+y,down);
        }else{
            HWND h=named("SimAnt - Game");typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;
            SendMessage(h,down?WM_MOUSEMOVE:WM_LBUTTONUP,down?MK_LBUTTON:0,MAKELPARAM(MulDiv(x,d,96),MulDiv(y,d,96)));enhanced_pointer_poll();
        }
    }
    return __real_myButton();
}
static void card_action(unsigned event,int reference){
    const EnhancedSnapshot *s=enhanced_snapshot();int index=-1,target=event==0xe51a?1:event==0xe51b?128:0;
    for(unsigned i=0;i<s->cards.link_count;++i)if((!target&&i==1)||s->cards.links[i].target==target){index=i;break;}
    if(index<0)exit(73);const EnhancedRect *r=&s->cards.links[index].rect;int x=(r->left+r->right)/2,y=(r->top+r->bottom)/2;
    if(reference){win_ToTop(0x500);win_Open(0x500,0,0,0,0,0);extern void portable_m1b73_semantic_pointer(int,int,int);portable_m1b73_semantic_pointer(x,y,0);portable_m1b73_try_enqueue_command(0x502,0,0x200,x,y);}
    else {HWND h=named("Info");if(target)SendMessage(GetDlgItem(h,target==1?0xe510:0xe511),BM_CLICK,0,0);
        else {const uint8_t *wire=(const uint8_t *)sim_window_ref_registry.entries[5].view.object_table[2];x-=sim_window_wire_read_i16(wire,0);y-=sim_window_wire_read_i16(wire,2);typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;x=MulDiv(x,d,96);y=MulDiv(y,d,96);SendMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));SendMessage(h,WM_LBUTTONUP,0,MAKELPARAM(x,y));}}
}
static void original(unsigned event) {
    if(event>=0xe519&&event<=0xe51b){card_action(event,1);return;}
    if(event==0xe518)event=0x1910;
    if(gesture_code(event)){gesture(event,1);return;}
    if(event==0xe400){edit_scroll_and_redraw(2,0);return;}
    int h = 0, v = 0;
    if (event == 0xe310 || event == 0xe311) {
        event = event == 0xe310 ? 17 : 18;
        const SimWindowRefEntry * e = & sim_window_ref_registry.entries [0];
        const uint8_t * b = (const uint8_t *) e->view.object_table [event];
        h=sim_window_wire_read_i16(b,0);v=sim_window_wire_read_i16(b,6)-(sim_window_wire_read_i16(b,6)-sim_window_wire_read_i16(b,2))/2;
    }
    int16_t owner = event >= 0xfd00 ? INT16_MIN : (int16_t)(event & 0xff00);
    if (owner != INT16_MIN) {
        if (owner == 0x1200) OpenModeWindow();
        else if (owner == 0x1300) OpenCasteWindow();
        else if (owner == 0x1500) OpenHistoryWindow();
        else {
            if (owner == 0x100 && !win_IsWinOpen(0x100)) YardToMap();
            if (owner == 0x1900) MapToYard();
            win_ToTop(owner);
            win_Open(owner, 0, 0, 0, 0, 0);
        }
    }
    if (! portable_m1b73_try_enqueue_command((int16_t) event, 0, 0, h, v)) abort();
}
void __wrap_enhanced_source_poll(void) {
    if(phase==2&&number==0xe518&&enhanced_queen_wait()){
        extern int16_t QueenStorageB;extern EnhancedPoint CurYardPnt,g_2A42;extern EnhancedRect map_viewport_rect;
        static int previous;
        if(previous==QueenStorageB||QueenStorageB<=0){__real_enhanced_source_poll();return;}previous=QueenStorageB;
        int tx=CurYardPnt.x==11?10:CurYardPnt.x+1,ty=CurYardPnt.y;
        int x=g_2A42.x+28*tx-10*ty+14,y=g_2A42.y+10*ty+5;
        if(!strcmp(getenv("SIMANT_ACTION_MODE"),"original")){
            extern void portable_m1b73_semantic_pointer(int,int,int);portable_m1b73_semantic_pointer(map_viewport_rect.left+x,map_viewport_rect.top+y,0);
            portable_m1b73_try_enqueue_command(0x1902,0,0x200,map_viewport_rect.left+x,map_viewport_rect.top+y);
        }else{
            HWND h=named("Yard");typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;
            SendMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(MulDiv(x,d,96),MulDiv(y,d,96)));SendMessage(h,WM_LBUTTONUP,0,MAKELPARAM(MulDiv(x,d,96),MulDiv(y,d,96)));
        }
        ++modal_inputs;__real_enhanced_source_poll();return;
    }
    __real_enhanced_source_poll();
    extern int16_t clip_window_z_order[];
    int owner=clip_window_z_order[0];
    if((phase==2||(phase==1&&held_case(strtol(getenv("SIMANT_ACTION_EVENT"),NULL,0)))) && (owner==0x700||owner==0x1400||owner==0x600||owner==0x900||owner==0xa00||owner==0xb00||owner==0x1700))enhanced_publish(ENHANCED_MODAL_POLL);
    const EnhancedSnapshot * s = enhanced_snapshot();
    if ((phase != 2 && !(phase==1&&held_case(strtol(getenv("SIMANT_ACTION_EVENT"),NULL,0)))) || ! s || modal_inputs > 8 || !(s->dialogs.modal || owner==0x700||owner==0x1400||owner==0x600||owner==0x900||owner==0xa00||owner==0xb00||owner==0x1700)) return;
    /* Retained source tasks are answered through ordinary SDL keyboard events. */
    static uint64_t token;static unsigned signature;
    unsigned content=2166136261u;
    for(unsigned i=0;i<s->dialogs.object_count;++i){const EnhancedObjectSnapshot *o=&s->dialogs.objects[i];for(unsigned j=0;j<sizeof(o->text);++j)content=(content^(unsigned char)o->text[j])*16777619u;content=(content^o->rect.left)*16777619u;content=(content^o->rect.top)*16777619u;}
    if (token == s->dialogs.task_token && signature==content) return;
    token = s->dialogs.task_token;signature=content;
    ++ modal_inputs;
    if(owner==0x700 && number==0xe517){
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[7];if(!e->bound||e->view.count<3)return;
        const uint8_t *b=(const uint8_t *)e->view.object_table[2];int x=(sim_window_wire_read_i16(b,0)+sim_window_wire_read_i16(b,4))/2,y=(sim_window_wire_read_i16(b,2)+sim_window_wire_read_i16(b,6))/2;
        const EnhancedSnapshot *frame=enhanced_snapshot();enhanced_pointer_update(frame->world.player_x*16+8,frame->world.player_y*16+8,0);
        /* The real menu's mouse-up transfers input ownership back from the
         * native canvas. Match host.c's external-release path in this fixture. */
        enhanced_pointer_external_release();
        extern void portable_m1b73_semantic_pointer(int,int,int);portable_m1b73_semantic_pointer(x,y,0);
        portable_m1b73_try_enqueue_command(0x702,0,0x200,x,y);return;
    }
    if(owner==0x1400||owner==0x1700){portable_m1b73_try_enqueue_command((int16_t)0xff00,0,0x200,20,420);return;}
    if(owner==0x600||owner==0x900||owner==0xa00||owner==0xb00){
        /* Complete the original proximity transaction with its own first
         * selectable result, through ordinary input. Both lanes do this. */
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[(unsigned)owner>>8];
        if(e->bound && e->view.count>2){
            const uint8_t *b=(const uint8_t *)e->view.object_table[2];
            int x=(sim_window_wire_read_i16(b,0)+sim_window_wire_read_i16(b,4))/2,y=(sim_window_wire_read_i16(b,2)+sim_window_wire_read_i16(b,6))/2;
            /* The source menu consumes a selectable object event, preserving
             * its dispatcher and click-feedback rather than a result write. */
            unsigned target=owner+2;unsigned test_event=(unsigned)strtol(getenv("SIMANT_ACTION_EVENT"),NULL,0);
            if(owner==0x900&&held_case(test_event))target+=wanted_tool(test_event);
            portable_m1b73_try_enqueue_command(target,0,0x200,x,y);
        }return;
    }
    if(s->dialogs.owner==0x1800){
        /* ScoreDialog accepts a real click; 180C is its source Continue text.
         * Escape is deliberately not substituted for this original outcome. */
        const char *mode=getenv("SIMANT_ACTION_MODE");
        if(strcmp(mode,"original")){HWND b=GetDlgItem(named("Status"),0x180c);if(!b)abort();if(!strcmp(mode,"keyboard")){SetFocus(b);SendMessage(b,WM_KEYDOWN,VK_SPACE,0);SendMessage(b,WM_KEYUP,VK_SPACE,0);}else SendMessage(b,BM_CLICK,0,0);return;}
        for(unsigned i=0;i<s->dialogs.object_count;++i)if(s->dialogs.objects[i].id==0x180c){
            const EnhancedRect *r=&s->dialogs.objects[i].rect;
            for(unsigned j=0;j<sim_window_hosting_count();++j){SimHostedWindowView view;if(sim_window_hosting_view(j,&view)&&view.id==0x1800){
                int strip=view.drag_bottom>view.drag_top&&view.drag_top>=view.top_y&&view.drag_bottom<view.bottom?view.drag_bottom-view.top_y:0;
                HostEvent down={.kind=HOST_EVENT_MOUSE_DOWN,.button=SDL_BUTTON_LEFT,.x=(r->left+r->right)/2-view.left,.y=(r->top+r->bottom)/2-view.top_y-strip},up=down;up.kind=HOST_EVENT_MOUSE_UP;
                native_windows_push_pointer(0x1800,&down);native_windows_push_pointer(0x1800,&up);return;
            }}
        }
        return;
    }
    SDL_Event down = {
        .type = SDL_EVENT_KEY_DOWN
    }
    , up = {
        .type = SDL_EVENT_KEY_UP
    };
    down.key.scancode = SDL_SCANCODE_ESCAPE;
    down.key.key = SDLK_ESCAPE;
    down.key.down = 1;
    up.key = down.key;
    up.type = SDL_EVENT_KEY_UP;
    up.key.down = 0;
    SDL_PushEvent(& down);
    SDL_PushEvent(& up);
}
void __wrap_enhanced_execute_next(void) {
    const EnhancedSnapshot * s = enhanced_snapshot();
    if (! s || s->panels.game_type < 0) {
        __real_enhanced_execute_next();
        return;
    }
    if (! phase && main_iteration_count > 20) {
        phase = 1;
        enhanced_submit_event(0xfd41, 0, 0, 0);
        unsigned test_event=(unsigned)strtol(getenv("SIMANT_ACTION_EVENT"),NULL,0);
        if(held_case(test_event)){enhanced_submit_event(7,0,0,0);enhanced_submit_event(test_event==0xe516?9:8,0,0,0);}
        if(test_event==0xe517)enhanced_submit_event(11,0,0,0);
        if(test_event==0xe506)enhanced_submit_event(0xfd21,0,0,0);
        if(test_event>=0x1503&&test_event<=0x150c)enhanced_submit_event(0x113,0,0,0);
        if(test_event==0xe507)enhanced_submit_event(0x113,0,0,0);
        if(test_event>=0xe519&&test_event<=0xe51b)enhanced_submit_event(0x115,0,0,0);
        if(test_event==0x1204||test_event==0x1304)enhanced_submit_event(test_event+1,0,0,0);
        if((test_event>=0x1206&&test_event<=0x1208)||(test_event>=0x1306&&test_event<=0x1308))enhanced_submit_event((test_event&0xff00)+(test_event%256==7?6:7),0,0,0);
        if(test_event==0xe518){
            /* Shipped four-key cheat, through the source keyboard transaction;
             * no QueenStorage write or fabricated save fixture. */
            extern char cheat_code_table[][4];
            for(int i=0;i<4;++i){int key=(unsigned char)~cheat_code_table[15][i];SDL_Event e={.type=SDL_EVENT_KEY_DOWN};e.key.key=key;e.key.scancode=SDL_SCANCODE_A+key-'a';e.key.down=1;SDL_PushEvent(&e);e.type=SDL_EVENT_KEY_UP;e.key.down=0;SDL_PushEvent(&e);}
            enhanced_submit_event(0xfd21,0,0,0);
        }
    }
    if (phase == 1 && main_iteration_count > 70 && s->panels.paused && ! s->dialogs.modal) {
        number = (int) strtol(getenv("SIMANT_ACTION_EVENT"), NULL, 0);
        const char * mode = getenv("SIMANT_ACTION_MODE");
        if(number==0xe51a||number==0xe51b){if(!info_setup){info_setup=1;card_action(0xe519,1);__real_enhanced_execute_next();return;}if(s->cards.card==128){__real_enhanced_execute_next();return;}}
        if(number==0xe518){extern int16_t QueenStorageB;if(QueenStorageB!=10){__real_enhanced_execute_next();return;}}
        if(held_case(number)){
            if(s->panels.game_type!=3){__real_enhanced_execute_next();return;}
            if(s->panels.experiment_tool!=wanted_tool(number)){
                if(!tool_setup){tool_setup=1;enhanced_submit_event(7,0,0,0);}__real_enhanced_execute_next();return;
            }
            if(number==0xe516){
                if(!fill_setup){fill_setup=main_iteration_count;gesture(0xe503,1);__real_enhanced_execute_next();return;}
                if(main_iteration_count<fill_setup+4){__real_enhanced_execute_next();return;}
                if(!alt_setup){SDL_Event e={.type=SDL_EVENT_KEY_DOWN};e.key.scancode=SDL_SCANCODE_LALT;e.key.mod=SDL_KMOD_LALT;e.key.down=1;SDL_PushEvent(&e);alt_setup=1;__real_enhanced_execute_next();return;}
                extern uint8_t dos_keyboard_modifiers(void);if(!(dos_keyboard_modifiers()&8)){__real_enhanced_execute_next();return;}
            }
        }
        phase = 2;
        started = main_iteration_count;
        dump(0);
        if (! strcmp(mode, "original")) original(number);
        else if (! strcmp(mode, "menu")) {
            HWND main = NULL;
            while ((main = FindWindowExA(NULL, main, NULL, "SimAnt"))) {
                DWORD pid;
                GetWindowThreadProcessId(main, & pid);
                if (pid == GetCurrentProcessId() && GetMenu(main)) break;
            }
            if (! main) abort();
            SendMessage(main, WM_COMMAND, (WPARAM) number, 0);
        }
        else if(number>=0xe519&&number<=0xe51b)card_action(number,0);
        else if(number==0xe518)SendMessage(GetDlgItem(named("Yard Control Panel"),0x1910),BM_CLICK,0,0);
        else if(gesture_code(number))gesture(number,0);
        else if (number == 0xe400) {
            HWND game=named("SimAnt - Game");
            typedef UINT(WINAPI *Dpi)(HWND);
            Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");
            int delta=MulDiv(32,dpi?dpi(game):96,96);
            SendMessage(game,WM_MBUTTONDOWN,MK_MBUTTON,MAKELPARAM(150,120));
            SendMessage(game,WM_MOUSEMOVE,MK_MBUTTON,MAKELPARAM(150-delta,120));
            SendMessage(game,WM_MBUTTONUP,0,MAKELPARAM(150-delta,120));
        }
        else if (number >= 0xfd43 && number <= 0xfd46) {
            HWND h = named("Map / Ant Control Panel");
            if (! strcmp(mode, "keyboard")) {
                SetFocus(h);
                SendMessage(h, WM_KEYDOWN, '1' + number - 0xfd43, 0);
            }
            else {
                SendMessage(GetDlgItem(h, 0xe300), CB_SETCURSEL, number - 0xfd43, 0);
                SendMessage(h, WM_COMMAND, MAKEWPARAM(0xe300, CBN_SELCHANGE), (LPARAM) GetDlgItem(h, 0xe300));
            }
        }
        else {
            int panel = atoi(getenv("SIMANT_ACTION_PANEL"));
            HWND h = named(panel==8?"Behavior Control":panel==9?"Caste Control":panel==10?"History":panel == 4 ? "Map / Ant Control Panel" : "Yard Control Panel");
            HWND b = GetDlgItem(h, number);
            if (! h || ! b) {
                fprintf(stderr, "ACTION_MISSING_CONTROL %x\n", number);
                exit(71);
            }
            if (number == 0xe310 || number == 0xe311) {
                RECT r;
                GetClientRect(b, & r);
                if (!strcmp(mode, "keyboard")) {
                    SetFocus(b);
                    SendMessage(b, WM_KEYDOWN, '5', 0);
                } else {
                    SendMessage(b, WM_LBUTTONDOWN, MK_LBUTTON, MAKELPARAM(r.right / 2, r.bottom / 2));
                    SendMessage(b, WM_LBUTTONUP, 0, MAKELPARAM(r.right / 2, r.bottom / 2));
                }
            }
            else if (! strcmp(mode, "keyboard")) {
                SetFocus(b);
                SendMessage(b, WM_KEYDOWN, VK_SPACE, 0);
                SendMessage(b, WM_KEYUP, VK_SPACE, 0);
            }
            else SendMessage(b, BM_CLICK, 0, 0);
        }
    }
    else if (phase == 2 && main_iteration_count > started + 4 && ! s->dialogs.modal) {
        phase = 3;
        if(held_case(number)&&(held_calls!=1||held_samples!=4)){fprintf(stderr,"ACTION_HELD_INCOMPLETE calls=%d samples=%d\n",held_calls,held_samples);exit(72);}
        if(number==0xe517&&recruit_calls!=1){fprintf(stderr,"ACTION_RECRUIT_INCOMPLETE calls=%d\n",recruit_calls);exit(72);}
        if((number==0xe519&&s->cards.card==128)||((number==0xe51a||number==0xe51b)&&s->cards.card!=128)){fprintf(stderr,"ACTION_CARD_INCOMPLETE card=%d\n",s->cards.card);exit(72);}
        if(number==0xe518){extern int16_t QueenStorageB;if(QueenStorageB!=9||modal_inputs!=1){fprintf(stderr,"ACTION_QUEEN_INCOMPLETE remaining=%d inputs=%d\n",QueenStorageB,modal_inputs);exit(72);}}
        dump(1);
        const EnhancedActionLedger * l = enhanced_action_ledger();
        fprintf(stderr, "ACTION_RESULT {\"event\":%d,\"before_iteration\":%d,\"after_iteration\":%ld,\"delivered\":%llu,\"modal_inputs\":%d,\"held_calls\":%d,\"held_samples\":%d,\"recruit_calls\":%d}\n", number, started, (long) main_iteration_count, (unsigned long long) l->delivered, modal_inputs,held_calls,held_samples,recruit_calls);
        exit(0);
    }
    __real_enhanced_execute_next();
}
