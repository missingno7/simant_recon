/* Bounded native content driver; changes game state only via original events. */
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/platform/window_hosting.h"
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/window_runtime_owner.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
static int phase,started,checks,failures,captured;
static EnhancedSnapshot before;
static const char *test;
#define CHECK(x) do{++checks;if(!(x)){++failures;fprintf(stderr,"CONTENT_FAIL %d: %s\n",__LINE__,#x);}}while(0)
static HWND named(const char *name){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId())continue;char title[160];GetWindowTextA(h,title,sizeof(title));if((!strcmp(title,name)||(!strcmp(name,"Info")&&!strncmp(title,"Info - ",7)))&&(strcmp(name,"SimAnt")||GetMenu(h)))return h;}return NULL;}
static int is(const char *s){return !strcmp(test,s);}
static BOOL CALLBACK capture_inventory(HWND h,LPARAM unused){
    (void)unused;DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId())return TRUE;
    char title[160],cls[80];GetWindowTextA(h,title,sizeof(title));GetClassNameA(h,cls,sizeof(cls));if(strcmp(cls,"SimAntGameWindow")&&strcmp(cls,"SDL_app"))return TRUE;
    RECT r;GetWindowRect(h,&r);fprintf(stderr,"CAPTURE_WINDOW title=%s class=%s visible=%d iconic=%d owner=%p rect=%ld,%ld,%ld,%ld style=%llx\n",title,cls,IsWindowVisible(h),IsIconic(h),(void *)GetWindow(h,GW_OWNER),r.left,r.top,r.right,r.bottom,(unsigned long long)GetWindowLongPtr(h,GWL_STYLE));return TRUE;
}
static void click(HWND h,int x,int y,int double_click){CHECK(h!=NULL);if(!h)return;typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;x=MulDiv(x,d,96);y=MulDiv(y,d,96);SendMessage(h,double_click?WM_LBUTTONDBLCLK:WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));SendMessage(h,WM_LBUTTONUP,0,MAKELPARAM(x,y));}
static unsigned domain_checked;
static void allocation_domain(void){
    typedef struct {int16_t ax,ay,lx,ly,rx,ry;} Verts;
    extern Verts modeVerts,casteVerts;
    extern int16_t IsPointInIsoTri(EnhancedPoint *,EnhancedRect *);
    extern void BoundPointToTri(EnhancedPoint *,EnhancedRect *),GetTriLatDist(uint16_t *,Verts *,EnhancedPoint *);
    const EnhancedSnapshot *s=enhanced_snapshot();
    extern uint16_t triWidth,triHeight;
    for(int owner=0;owner<2;++owner){
        EnhancedRect r=owner?s->panels.caste.triangle:s->panels.behavior.triangle;unsigned char seen[3][101]={{0}};
        if((domain_checked&(1u<<owner))||r.right-r.left!=triWidth||r.bottom-r.top!=triHeight)continue;
        for(int y=r.top;y<r.bottom;++y)for(int x=r.left;x<r.right;++x){EnhancedPoint p={(int16_t)x,(int16_t)y};if(!IsPointInIsoTri(&p,&r))continue;BoundPointToTri(&p,&r);uint16_t level[3];GetTriLatDist(level,owner?&casteVerts:&modeVerts,&p);for(int i=0;i<3;++i)seen[i][(level[i]*100u+0x3fff)/65535]=1;}
        HWND window=named(owner?"Caste Control":"Behavior Control");
        for(int i=0;i<3;++i){HWND combo=GetDlgItem(window,0xe520+i);int expected=0;for(int value=0;value<=100;++value)expected+=seen[i][value];CHECK(SendMessage(combo,CB_GETCOUNT,0,0)==expected);
            for(int item=0;item<expected;++item){int value=SendMessage(combo,CB_GETITEMDATA,item,0);CHECK(value>=0&&value<=100&&seen[i][value]);if(value>=0&&value<=100)seen[i][value]=0;}
            for(int value=0;value<=100;++value)CHECK(!seen[i][value]);
        }
        domain_checked|=1u<<owner;
    }
}
static void configure(void){
    Workspace w=*native_workspace_layout();
    for(int p=0;p<WS_PANELS;++p)w.panels[p].edge=WS_FLOAT;
    w.panels[WS_ANT].x=24;w.panels[WS_ANT].y=64;w.panels[WS_YARD_CONTROL].x=24;w.panels[WS_YARD_CONTROL].y=1320;
    w.panels[WS_GAME].x=24;w.panels[WS_GAME].y=290;w.panels[WS_GAME].w=440;w.panels[WS_GAME].h=340;
    w.panels[WS_MAP].x=490;w.panels[WS_MAP].y=290;w.panels[WS_YARD].x=490;w.panels[WS_YARD].y=680;
    w.panels[WS_BEHAVIOR].x=24;w.panels[WS_BEHAVIOR].y=650;w.panels[WS_CASTE].x=304;w.panels[WS_CASTE].y=650;
    w.panels[WS_HISTORY].x=620;w.panels[WS_HISTORY].y=650;w.panels[WS_INFO].x=620;w.panels[WS_INFO].y=920;
    w.panels[WS_STATUS].x=620;w.panels[WS_STATUS].y=960;
    w.panels[WS_BLACK].x=24;w.panels[WS_BLACK].y=940;w.panels[WS_BLACK].w=440;w.panels[WS_BLACK].h=320;w.panels[WS_BLACK].visible=1;
    HWND main=named("SimAnt");typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(main):96;
    SetWindowPos(main,NULL,12,12,MulDiv(1100,d,96),MulDiv(1540,d,96),SWP_NOZORDER|SWP_NOACTIVATE);
    if(is("docked")){ws_attach(&w,WS_ANT,WS_TOP,0);ws_attach(&w,WS_YARD_CONTROL,WS_BOTTOM,0);ws_attach(&w,WS_MAP,WS_RIGHT,240);ws_attach(&w,WS_BEHAVIOR,WS_LEFT,620);}
    CHECK(native_workspace_apply(&w));
}
static void capture(const char *title){
    if(captured)return;captured=1;
    HWND target=title?named(title):named("SimAnt - Game");if(target){SetForegroundWindow(target);SetFocus(target);RedrawWindow(target,NULL,NULL,RDW_FRAME|RDW_INVALIDATE|RDW_ALLCHILDREN|RDW_UPDATENOW);}
    static EnhancedSnapshot saved;saved=*enhanced_snapshot();EnumWindows(capture_inventory,0);CHECK(native_workspace_capture(getenv("SIMANT_CONTENT_CAPTURE")));CHECK(!memcmp(&saved,enhanced_snapshot(),sizeof(saved)));
    if(title&&(!strcmp(title,"Behavior Control")||!strcmp(title,"Caste Control"))){int caste=!strcmp(title,"Caste Control"),base=caste?0x1300:0x1200;const EnhancedAllocationSnapshot *a=caste?&saved.panels.caste:&saved.panels.behavior;CHECK(SendMessage(GetDlgItem(target,base+4),BM_GETCHECK,0,0)==(a->automatic?BST_CHECKED:BST_UNCHECKED));CHECK(SendMessage(GetDlgItem(target,base+5),BM_GETCHECK,0,0)==(a->automatic?BST_UNCHECKED:BST_CHECKED));}
    RECT root_rect;GetWindowRect(named("SimAnt"),&root_rect);fprintf(stderr,"CONTENT_ORIGIN %ld %ld\n",root_rect.left,root_rect.top);
    if(target&&title){RECT r;GetWindowRect(target,&r);fprintf(stderr,"CONTENT_BOUNDS %ld %ld %ld %ld\n",r.left,r.top,r.right,r.bottom);}
    fprintf(stderr,"CONTENT_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"case\":\"%s\",\"card\":%d,\"links\":%u,\"map_x\":%d,\"map_y\":%d,\"frac\":%u,\"mid\":%u,\"weight\":%u}\n",failures?"false":"true",checks,failures,test,saved.cards.card,saved.cards.link_count,saved.world.origin.x,saved.world.origin.y,saved.panels.behavior.frac,saved.panels.behavior.mid,saved.panels.behavior.weight);
}
extern void __real_enhanced_publish(EnhancedSeam);
void __wrap_enhanced_publish(EnhancedSeam seam){
    __real_enhanced_publish(seam);
    if(!test||!is("triangle-edit")||phase!=2||captured||seam!=ENHANCED_TRACKER_DRAW)return;
    const EnhancedSnapshot *s=enhanced_snapshot();if(s->panels.behavior.frac==before.panels.behavior.frac)return;
    CHECK(enhanced_pointer_tracking(0x1200));capture("Behavior Control");
    HWND h=named("Behavior Control");SendMessage(h,WM_LBUTTONUP,0,0);
}
void __wrap_enhanced_source_poll(void){
    __real_enhanced_source_poll();const EnhancedSnapshot *s=enhanced_snapshot();
    if(test&&is("history-held")&&phase==2&&!captured&&enhanced_pointer_tracking(0x1500)){
        CHECK(s->dialogs.owner==0x1500);capture("History");HWND h=named("History");typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;SendMessage(h,WM_LBUTTONUP,0,MAKELPARAM(MulDiv(160,d,96),MulDiv(62,d,96)));return;
    }
    if(!test||!is("status")||phase<2||!s||s->dialogs.owner!=0x1800||!s->dialogs.modal)return;
    /* ScoreDialog has assigned fields before its first event poll. */
    HWND status=named("Status"),b=GetDlgItem(status,0x180c);if(!status||!b||captured)return;
    CHECK(s->history.score_metrics_available);configure();capture("Status");SendMessage(b,BM_CLICK,0,0);
}
void __wrap_enhanced_execute_next(void){
    if(!test)test=getenv("SIMANT_CONTENT_CASE");const EnhancedSnapshot *s=enhanced_snapshot();if(!test||!s||s->panels.game_type<0){__real_enhanced_execute_next();return;}
    if(is("values")&&phase>=2)allocation_domain();
    if(!phase&&main_iteration_count>20){phase=1;enhanced_submit_event(0xfd26,0,0,0);enhanced_submit_event(0xfd41,0,0,0);}
    if(phase==1&&main_iteration_count>75&&s->panels.paused&&!s->dialogs.modal){phase=2;started=main_iteration_count;before=*s;if(is("values"))allocation_domain();configure();
        if(is("history")||is("history-held")||is("undocked")||is("docked")){enhanced_submit_event(0x113,0,0,0);enhanced_submit_event(0x1503,0,0,0);enhanced_submit_event(0x1504,0,0,0);}
        if(is("info")||is("info-follow")||is("undocked")||is("docked"))enhanced_submit_event(0x115,0,0,0);
        if(is("yard"))enhanced_submit_event(0xfd21,0,0,0);
        if(is("house"))enhanced_submit_event(0xfd22,0,0,0);
        if(is("strategic"))enhanced_submit_event(0xfd23,0,0,0);
        if(is("graphic"))enhanced_submit_event(0xfd24,0,0,0);
        if(is("status"))enhanced_submit_event(0x114,0,0,0);
        if(is("triangle-edit")){
            HWND h=named("Behavior Control");CHECK(h!=NULL);typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;
            SendMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(MulDiv(110,d,96),MulDiv(100,d,96)));
        }
        if(is("map-centre"))click(named("Map"),404,80,0);
        if(is("values")||is("queued-value-map")){HWND combo=GetDlgItem(named("Caste Control"),0xe521);CHECK(combo!=NULL);if(combo){SendMessage(combo,CB_SETCURSEL,72,0);SendMessage(named("Caste Control"),WM_COMMAND,MAKEWPARAM(0xe521,CBN_SELCHANGE),(LPARAM)combo);}if(is("queued-value-map"))click(named("Map"),404,80,0);}
    }
    if(phase==2&&main_iteration_count>started+12&&!s->dialogs.modal){phase=3;
        if(is("history-held")&&!captured){HWND h=named("History");typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;phase=2;SendMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(MulDiv(160,d,96),MulDiv(62,d,96)));started=main_iteration_count;}
        if(is("info-follow")){CHECK(s->cards.links_available&&s->cards.link_count>1);if(s->cards.link_count>1){const EnhancedRect *r=&s->cards.links[1].rect;
            /* Top card picture links retain their exact native source geometry. */
            const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[5];const uint8_t *wire=(const uint8_t *)entry->view.object_table[2];
            int left=sim_window_wire_read_i16(wire,0),top=sim_window_wire_read_i16(wire,2);extern int16_t clip_window_z_order[];

            click(named("Info"),(r->left+r->right)/2-left,(r->top+r->bottom)/2-top,0);started=main_iteration_count;return;}}
    }
    if(phase==3&&main_iteration_count>started+18&&!s->dialogs.modal){phase=4;
        if(is("map-centre"))CHECK(s->world.origin.x!=before.world.origin.x||s->world.origin.y!=before.world.origin.y);
        if(is("triangle-edit"))CHECK(captured);
        if(is("history-held"))CHECK(captured);
        if(is("triangle-edit"))CHECK(s->panels.behavior.frac!=before.panels.behavior.frac||s->panels.behavior.mid!=before.panels.behavior.mid);
        if(is("values")){CHECK((s->panels.caste.mid*100u+0x3fff)/65535==72);CHECK(domain_checked==3);}
        if(is("queued-value-map")){CHECK((s->panels.caste.mid*100u+0x3fff)/65535==72);CHECK(s->world.origin.x>70&&s->world.origin.y<before.world.origin.y);}
        if(is("info-follow"))CHECK(s->cards.card!=128);
        const char *title=is("map")||is("map-centre")?"Map":is("behavior")||is("triangle-edit")?"Behavior Control":is("caste")||is("values")?"Caste Control":is("history")?"History":is("info")||is("info-follow")?"Info":is("yard")?"Yard":is("house")?"House":is("strategic")?"Strategic":is("graphic")?"Graphic":NULL;
        if(is("status")){CHECK(s->dialogs.owner!=0x1800);for(unsigned i=0;i<32;++i)CHECK(s->logical_order[i]!=0x1800);}
        capture(title);
        fprintf(stderr,"CONTENT_COMPLETED {\"passed\":%s,\"checks\":%d,\"failures\":%d}\n",failures?"false":"true",checks,failures);
        exit(0);
    }
    __real_enhanced_execute_next();
}
