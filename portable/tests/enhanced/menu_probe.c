/* Real source clicks and Win32 menu input; no writes to game state. */
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/window_runtime_owner.h"
#include <windows.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
char menu_observer_anchor;
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
extern int __real_native_workspace_proximity(const EnhancedDialogsSnapshot *);
extern void __real_YellowCommand(int16_t);
static int phase,started,checks,failures,seen,command=-1,timer_step,choice,owner,original,setup;
static POINT clicked;
static HWND root;
static HMENU live_menu;
static const char *kind;
static EnhancedWorldSnapshot waiting_world;
static EnhancedDialogsSnapshot expected_menu;
static int lastworldx,lastworldy;
static int modifiers;
static int keyboard_cancel;
static void click_world(int,int,int);
#define CHECK(x) do{++checks;if(!(x)){++failures;fprintf(stderr,"MENU_FAIL %d %s\n",__LINE__,#x);}}while(0)
/* Closed source selectors share "SimAnt"; the native frame owns the menu bar. */
static HWND named(const char *title){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,title))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId()&&(!title||strcmp(title,"SimAnt")||GetMenu(h)))return h;}return NULL;}
static void dump(int slot){
    const char *path=getenv("SIMANT_MENU_CONFIG");if(!path)return;
    FILE *in=fopen(path,"r");char base[2048],name[2100];unsigned count;if(!in||fscanf(in,"%2047s%u",base,&count)!=2)abort();
    snprintf(name,sizeof(name),"%s.%d",base,slot);FILE *out=fopen(name,"wb");if(!out)abort();
    for(unsigned i=0;i<count;++i){unsigned slices;if(fscanf(in,"%u",&slices)!=1)abort();for(unsigned j=0;j<slices;++j){long long offset;unsigned size;if(fscanf(in,"%lld%u",&offset,&size)!=2)abort();fwrite(&menu_observer_anchor+offset,1,size,out);}}
    fclose(in);fclose(out);
}
static void key(SDL_Scancode scan){SDL_Event e={.type=SDL_EVENT_KEY_DOWN};e.key.scancode=scan;e.key.down=1;SDL_PushEvent(&e);e.type=SDL_EVENT_KEY_UP;e.key.down=0;SDL_PushEvent(&e);}
static unsigned marker_count(const EnhancedWorldSnapshot *w){unsigned n=0;for(int x=0;x<128;++x)for(int y=0;y<64;++y)n+=w->life_surface[x][y]>=254;for(int x=0;x<64;++x)for(int y=0;y<64;++y)n+=(w->life_black[x][y]>=254)+(w->life_red[x][y]>=254);return n;}
static LRESULT CALLBACK watch_menu(HWND h,UINT msg,WPARAM wp,LPARAM lp,UINT_PTR id,DWORD_PTR data){
    (void)id;(void)data;if(msg==WM_INITMENUPOPUP)live_menu=(HMENU)wp;
    return DefSubclassProc(h,msg,wp,lp);
}
static void source_choice(void){
    const EnhancedSnapshot *s=enhanced_snapshot();int code=s->dialogs.owner+(choice<0?1:choice+2);
    if(s->dialogs.owner==0x700||s->dialogs.owner==0x800||s->dialogs.owner==0x2000)click_world(lastworldx,lastworldy,0);
    int h=0,v=0;for(unsigned i=0;i<s->dialogs.object_count;++i)if(s->dialogs.objects[i].id==code){const EnhancedRect *r=&s->dialogs.objects[i].rect;h=(r->left+r->right)/2;v=(r->top+r->bottom)/2;break;}
    CHECK(portable_m1b73_try_enqueue_command(code,0,0x200,h,v));seen=1;
}
static void CALLBACK menu_timer(HWND h,UINT message,UINT_PTR id,DWORD now){
    (void)h;(void)message;(void)id;(void)now;
    HWND menu=named(NULL);menu=FindWindowExA(NULL,NULL,"#32768",NULL);if(!menu)return;
    DWORD pid;GetWindowThreadProcessId(menu,&pid);if(pid!=GetCurrentProcessId())return;
    if(timer_step++==0){
        if(!live_menu)live_menu=(HMENU)SendMessage(menu,MN_GETHMENU,0,0);
        CHECK(live_menu!=NULL);
        if(live_menu)for(unsigned i=0;i<expected_menu.object_count;++i){const EnhancedObjectSnapshot *o=&expected_menu.objects[i];if(o->id<owner+2||!(o->flags&1)||!o->text[0])continue;
            UINT state=GetMenuState(live_menu,o->id,MF_BYCOMMAND);CHECK(state!=(UINT)-1);
            CHECK(!!(state&(MF_DISABLED|MF_GRAYED))==!(o->flags&2));CHECK(!!(state&MF_CHECKED)==!!((o->flags&4)||o->id==expected_menu.proximity_item));
        }
        RECT r;GetWindowRect(menu,&r);MONITORINFO monitor={.cbSize=sizeof(monitor)};GetMonitorInfo(MonitorFromPoint(clicked,MONITOR_DEFAULTTONEAREST),&monitor);
        CHECK(r.left>=monitor.rcWork.left&&r.top>=monitor.rcWork.top&&r.right<=monitor.rcWork.right&&r.bottom<=monitor.rcWork.bottom);
        CHECK(abs(r.left-clicked.x)<400&&abs(r.top-clicked.y)<400);
        CHECK(marker_count(&enhanced_snapshot()->world)==marker_count(&waiting_world));
        CHECK(!memcmp(&enhanced_snapshot()->world,&waiting_world,sizeof(waiting_world)));
        CHECK(IsWindowVisible(named("SimAnt - Game")));
        const char *capture=getenv("SIMANT_MENU_CAPTURE");if(capture)CHECK(native_workspace_capture(capture));
        fprintf(stderr,"MENU_OPEN {\"owner\":%d,\"left\":%ld,\"top\":%ld,\"right\":%ld,\"bottom\":%ld,\"anchor_x\":%ld,\"anchor_y\":%ld,\"markers\":%u,\"art\":%u,\"lines\":%u}\n",owner,r.left,r.top,r.right,r.bottom,clicked.x,clicked.y,marker_count(&waiting_world),waiting_world.overlays.art_count,waiting_world.overlays.line_count);
        if(choice==-2){PostMessage(root,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(1,1));PostMessage(root,WM_LBUTTONUP,0,MAKELPARAM(1,1));}
        else if(choice<0)PostMessage(root,WM_KEYDOWN,VK_ESCAPE,0);
        else {for(int i=0;i<=choice;++i)PostMessage(root,WM_KEYDOWN,VK_DOWN,0);PostMessage(root,WM_KEYDOWN,VK_RETURN,0);}
    }
    if(timer_step>10){EndMenu();CHECK(0);}
}
int __wrap_native_workspace_proximity(const EnhancedDialogsSnapshot *menu){
    owner=menu->owner;expected_menu=*menu;waiting_world=enhanced_snapshot()->world;
    const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[(unsigned)owner>>8];
    fprintf(stderr,"MENU_OBJECTS count=%u source=%u bound=%d\n",menu->object_count,entry->view.count,entry->bound);
    CHECK(owner==(!strcmp(kind,"scent")?0x600:!strcmp(kind,"tools")?0xa00:!strcmp(kind,"full-tools")?0xb00:!strcmp(kind,"magnify")?0x1d00:!strcmp(kind,"spider")?0x2000:!strcmp(kind,"queen")?0x800:0x700));
    unsigned text=0;for(unsigned i=0;i<menu->object_count;++i)if(menu->objects[i].id>=owner+2 && menu->objects[i].text[0]){++text;fprintf(stderr,"MENU_ITEM %04x %04x %s\n",menu->objects[i].id,menu->objects[i].flags,menu->objects[i].text);}
    CHECK(text>0||owner==0xb00);CHECK(choice<0||(unsigned)choice<text);
    CHECK(!strcmp(kind,"spider")?waiting_world.overlays.art_count>0&&waiting_world.overlays.line_count>0:marker_count(&waiting_world)>0);
    SetWindowSubclass(root,watch_menu,97,0);live_menu=NULL;
    UINT_PTR timer=SetTimer(root,0,120,menu_timer);CHECK(timer!=0);timer_step=0;
    BYTE was[256],keys[256];GetKeyboardState(was);memcpy(keys,was,sizeof(keys));keys[VK_SHIFT]=(modifiers&2)?0x80:0;keys[VK_MENU]=(modifiers&8)?0x80:0;SetKeyboardState(keys);
    int result=__real_native_workspace_proximity(menu);SetKeyboardState(was);KillTimer(root,timer);RemoveWindowSubclass(root,watch_menu,97);seen=1;
    fprintf(stderr,"MENU_NATIVE_RETURN %04x\n",result);CHECK(result==owner+(choice<0?1:choice+2));return result;
}
void __wrap_YellowCommand(int16_t cmd){if(phase==3)command=cmd;__real_YellowCommand(cmd);}
static void click_world(int worldx,int worldy,int down){
    lastworldx=worldx;lastworldy=worldy;
    HWND game=named("SimAnt - Game");CHECK(game!=NULL);const Workspace *w=native_workspace_layout();
    const WsPanel *v=&w->panels[WS_GAME];typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");double z=v->zoom/100.0*(dpi?dpi(game):96)/96.;
    int x=(worldx-v->camera_x)*z,y=(worldy-v->camera_y)*z;RECT cr;GetClientRect(game,&cr);CHECK(x>=0&&x<cr.right&&y>=0&&y<cr.bottom);
    clicked=(POINT){x,y};ClientToScreen(game,&clicked);
    SendMessage(game,down?WM_LBUTTONDOWN:WM_LBUTTONUP,down?MK_LBUTTON:0,MAKELPARAM(x,y));
}
static void CALLBACK magnify_release(HWND h,UINT message,UINT_PTR id,DWORD now){(void)h;(void)message;(void)now;KillTimer(root,id);click_world(lastworldx,lastworldy,0);seen=1;}
extern void __real_native_workspace_manage_window(SDL_Window *,int,int,int);
void __wrap_native_workspace_manage_window(SDL_Window *w,int logical,int width,int height){
    __real_native_workspace_manage_window(w,logical,width,height);
    if(original&&phase==3&&!strcmp(kind,"magnify")&&logical==0x1d00&&!seen){seen=2;CHECK(SetTimer(root,0,150,magnify_release)!=0);}
}
void __wrap_enhanced_source_poll(void){
    __real_enhanced_source_poll();const EnhancedSnapshot *s=enhanced_snapshot();if(!s)return;
    if(s->dialogs.owner==0x1a00||s->dialogs.owner==0x1400||s->dialogs.owner==0x1700){key(SDL_SCANCODE_ESCAPE);portable_m1b73_try_enqueue_command((int16_t)0xff00,0,0x200,10,479);}
    if(phase<2)return;
    if(original&&phase==3&&!seen&&(s->dialogs.owner==0x600||s->dialogs.owner==0x700||s->dialogs.owner==0x800||s->dialogs.owner==0xa00||s->dialogs.owner==0xb00||s->dialogs.owner==0x2000))source_choice();
}
void __wrap_enhanced_execute_next(void){
    const EnhancedSnapshot *s=enhanced_snapshot();if(!s||s->panels.game_type<0){__real_enhanced_execute_next();return;}
    if(!kind){kind=getenv("SIMANT_MENU_KIND");choice=atoi(getenv("SIMANT_MENU_CHOICE"));modifiers=atoi(getenv("SIMANT_MENU_MODIFIERS"));keyboard_cancel=atoi(getenv("SIMANT_MENU_KEYBOARD_CANCEL"));original=!strcmp(getenv("SIMANT_MENU_MODE"),"original");root=named("SimAnt");CHECK(native_workspace_active());CHECK(root&&GetMenu(root)&&IsWindowVisible(root));}
    if(!phase&&main_iteration_count>25){phase=1;enhanced_submit_event(15,0,0,0);enhanced_submit_event(11,0,0,0);if(!strcmp(kind,"spider")){enhanced_submit_event(8,0,0,0);enhanced_submit_event(12,0,0,0);}}
    if(phase==1&&main_iteration_count>85&&s->panels.paused&&!s->dialogs.modal){
        if(!strcmp(kind,"spider")&&s->world.player_mode!=1){
            if(!setup){setup=1;key(SDL_SCANCODE_X);started=main_iteration_count;}
            if(main_iteration_count>started+8&&s->panels.tool==10){phase=2;click_world(s->world.spider_x,s->world.spider_y,1);click_world(s->world.spider_x,s->world.spider_y,0);started=main_iteration_count;}
        }else{phase=2;started=main_iteration_count;}
    }
    if(phase==2&&main_iteration_count>started+20&&!s->dialogs.modal){
        if(!strcmp(kind,"spider")&&s->world.player_mode!=1){CHECK(0);exit(2);}
        Workspace w=*native_workspace_layout();RECT cr;GetClientRect(named("SimAnt - Game"),&cr);
        int x=!strcmp(kind,"spider")?s->world.spider_x:s->world.player_x*16+8,y=!strcmp(kind,"spider")?s->world.spider_y:s->world.player_y*16+8;
        w.panels[WS_GAME].zoom=100;w.panels[WS_GAME].camera_x=x-cr.right/2;w.panels[WS_GAME].camera_y=y-cr.bottom/2;if(w.panels[WS_GAME].camera_x<0)w.panels[WS_GAME].camera_x=0;if(w.panels[WS_GAME].camera_y<0)w.panels[WS_GAME].camera_y=0;
        CHECK(native_workspace_apply(&w));phase=3;started=main_iteration_count;dump(0);
        if(modifiers){SDL_Event e={.type=SDL_EVENT_KEY_DOWN};e.key.scancode=modifiers==2?SDL_SCANCODE_LSHIFT:SDL_SCANCODE_LALT;e.key.down=1;e.key.mod=modifiers==2?SDL_KMOD_LSHIFT:SDL_KMOD_LALT;SDL_PushEvent(&e);}
        if(!strcmp(kind,"scent")||!strcmp(kind,"tools")||!strcmp(kind,"full-tools")){HWND b=GetDlgItem(named("Map / Ant Control Panel"),!strcmp(kind,"scent")?16:7);CHECK(b!=NULL);POINT at={500,350};clicked=at;native_workspace_anchor(at.x,at.y);enhanced_submit_event(!strcmp(kind,"scent")?16:7,0,0,0);}
        else if(!strcmp(kind,"magnify")){
            int found=0;for(int xx=0;xx<64&&!found;++xx)for(int yy=2;yy<64;++yy){unsigned life=s->world.life_black[xx][yy];if(life&&life<254){x=xx*16+8;y=yy*16+8;found=1;break;}}
            CHECK(found);w=*native_workspace_layout();w.panels[WS_GAME].camera_x=x-cr.right/2;w.panels[WS_GAME].camera_y=y-cr.bottom/2;if(w.panels[WS_GAME].camera_x<0)w.panels[WS_GAME].camera_x=0;if(w.panels[WS_GAME].camera_y<0)w.panels[WS_GAME].camera_y=0;native_workspace_apply(&w);click_world(x,y,1);
        }
        else click_world(x,y,1);
    }
    if(phase==3&&seen&&main_iteration_count>started+12&&!s->dialogs.modal){
        if(!original&&strcmp(kind,"scent")&&strcmp(kind,"tools")&&strcmp(kind,"full-tools")){
            HWND focus=GetFocus();char title[128]={0},type[128]={0};GetWindowTextA(focus,title,sizeof(title));GetClassNameA(focus,type,sizeof(type));
            fprintf(stderr,"MENU_FOCUS title=%s class=%s enabled=%d\n",title,type,IsWindowEnabled(focus));
            CHECK(focus==named("SimAnt - Game"));
        }
        if(keyboard_cancel){
            CHECK(s->panels.tool==10);phase=4;started=main_iteration_count;
            if(original)key(SDL_SCANCODE_X);
            else {HWND focus=GetFocus();SendMessage(focus,WM_KEYDOWN,'X',0);SendMessage(focus,WM_KEYUP,'X',0);}
            __real_enhanced_execute_next();return;
        }
        dump(1);fprintf(stderr,"MENU_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"command\":%d,\"seen\":%d,\"mode\":%d,\"tool\":%d,\"freeze_recovered\":true}\n",failures?"false":"true",checks,failures,command,seen,s->world.player_mode,s->panels.tool);exit(failures?1:0);
    }
    if(phase==4&&main_iteration_count>started+12&&!s->dialogs.modal){
        CHECK(s->panels.tool==-1);dump(1);fprintf(stderr,"MENU_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"command\":%d,\"seen\":%d,\"mode\":%d,\"tool\":%d,\"keyboard_cancel\":true,\"freeze_recovered\":true}\n",failures?"false":"true",checks,failures,command,seen,s->world.player_mode,s->panels.tool);exit(failures?1:0);
    }
    __real_enhanced_execute_next();
}
