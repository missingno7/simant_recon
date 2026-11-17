/* Bounded native-control census and interaction probe. Never global input. */
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/platform/window_hosting.h"
#include <windows.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
static int phase,started,ticks,identifier,failed,observed,cancelled,ready_checks;
static HWND root,target;
static const char *kind,*parent_name;
static uint64_t submitted;
static UINT_PTR timer;
static char presentation[160];
static int point_x,point_y,held;
static unsigned path[12],path_count,path_at;
static HWND inspected;
static int footer_prepared;
static int legacy_selected;
static int legacy_release_owner,legacy_release_tick,legacy_x,legacy_y;
static int initial_pause,target_cancel,outside_cancel;
static const char *setup;
static int spider_stage;
static int expected_native_choice;
static ULONGLONG action_started;
static HWND named(const char *name){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId())continue;char title[200];GetWindowTextA(h,title,sizeof(title));if((!strcmp(title,name)||(!strcmp(name,"Info")&&!strncmp(title,"Info - ",7)))&&(strcmp(name,"SimAnt")||GetMenu(h)))return h;}return NULL;}
static void quoted(const char *s){putc('"',stderr);for(;*s;++s){if(*s=='"'||*s=='\\')putc('\\',stderr);putc(*s>=32?*s:' ',stderr);}putc('"',stderr);}
static void finish(const char *result){
    fprintf(stderr,"SWEEP_RESULT {\"passed\":%s,\"result\":",failed?"false":"true");quoted(result);fprintf(stderr,",\"presentation\":");quoted(presentation);fprintf(stderr,",\"cancelled\":%s,\"ticks\":%d,\"elapsed_ms\":%llu,\"iteration\":%ld}\n",cancelled?"true":"false",ticks,action_started?(unsigned long long)(GetTickCount64()-action_started):0,(long)main_iteration_count);exit(failed?1:0);
}
static void row(HWND h,HWND parent,const char *setup){char name[200],label[200],cls[60];GetWindowTextA(parent,name,sizeof(name));GetWindowTextA(h,label,sizeof(label));GetClassNameA(h,cls,sizeof(cls));
    fprintf(stderr,"SWEEP_CONTROL {\"kind\":\"control\",\"parent\":");quoted(name);fprintf(stderr,",\"label\":");quoted(label);fprintf(stderr,",\"class\":");quoted(cls);fprintf(stderr,",\"id\":%d,\"visible\":%s,\"enabled\":%s,\"setup\":",GetDlgCtrlID(h),IsWindowVisible(h)?"true":"false",IsWindowEnabled(h)?"true":"false");quoted(setup);fprintf(stderr,"}\n");}
static void menu_rows(HMENU menu,const char *prefix){
    for(int i=0;i<GetMenuItemCount(menu);++i){MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_ID|MIIM_SUBMENU|MIIM_STATE|MIIM_FTYPE|MIIM_STRING};char label[160];item.dwTypeData=label;item.cch=sizeof(label);if(!GetMenuItemInfoA(menu,i,TRUE,&item)||item.fType&MFT_SEPARATOR)continue;
        char path[500];snprintf(path,sizeof(path),"%s%s%s",prefix,*prefix?" / ":"",label);if(item.hSubMenu){menu_rows(item.hSubMenu,path);continue;}
        fprintf(stderr,"SWEEP_CONTROL {\"kind\":\"menu\",\"parent\":\"SimAnt\",\"label\":");quoted(path);fprintf(stderr,",\"id\":%u,\"visible\":true,\"enabled\":%s,\"setup\":\"\"}\n",item.wID,item.fState&(MFS_GRAYED|MFS_DISABLED)?"false":"true");
    }
}
static void gesture_row(HWND h,int id,const char *label,int x,int y,int hold){
    char name[200];GetWindowTextA(h,name,sizeof(name));fprintf(stderr,"SWEEP_CONTROL {\"kind\":\"%s\",\"parent\":",hold?"hold":"gesture");quoted(name);fprintf(stderr,",\"label\":");quoted(label);fprintf(stderr,",\"id\":%d,\"x\":%d,\"y\":%d,\"visible\":true,\"enabled\":true,\"setup\":\"%s\"}\n",id,x,y,!strncmp(label,"spider",6)?"spider":"");
}
static void painted_controls(HWND h){
    char name[200];GetWindowTextA(h,name,sizeof(name));RECT r;GetClientRect(h,&r);int id=0,x=0,y=0;
    if(!strcmp(name,"Map")){id=0x102;x=r.right*5/8;y=r.bottom/2;}
    else if(!strcmp(name,"Yard")||!strcmp(name,"House")||!strcmp(name,"Strategic")||!strcmp(name,"Graphic")){id=0x1902;x=r.right/2;y=r.bottom/2;}
    else if(!strcmp(name,"Behavior Control")||!strcmp(name,"Caste Control")){id=!strcmp(name,"Behavior Control")?0x120d:0x130d;x=r.right*110/210;y=r.bottom*80/170;}
    else if(!strcmp(name,"History")){id=0x150e;x=r.right/2;y=r.bottom/3;}
    if(id){gesture_row(h,id,"client hit",x,y,0);gesture_row(h,id,"client press-hold-release",x,y,1);}
    if(!strcmp(name,"SimAnt - Game")){
        const EnhancedSnapshot *s=enhanced_snapshot();const WsPanel *view=&native_workspace_layout()->panels[WS_GAME];
        typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(h):96;
        int x=MulDiv((s->world.player_x*16+8-view->camera_x)*view->zoom,d,9600),y=MulDiv((s->world.player_y*16+8-view->camera_y)*view->zoom,d,9600);
        if(s->world.player_plane==s->world.plane&&x>=0&&x<r.right&&y>=0&&y<r.bottom){gesture_row(h,4,"player click",x,y,0);gesture_row(h,4,"player command menu (hold)",x,y,1);}
        if(s->panels.game_type!=3&&s->world.spider_on){gesture_row(h,4,"spider command click",0,0,0);gesture_row(h,4,"spider command menu (hold)",0,0,1);}
    }
    if(!strncmp(name,"Info",4)){
        const EnhancedSnapshot *s=enhanced_snapshot();const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[5];
        if(entry->bound&&entry->view.count>2){const uint8_t *rect=entry->view.object_table[2];int left=sim_window_wire_read_i16(rect,0),top=sim_window_wire_read_i16(rect,2);
            for(unsigned i=0;i<s->cards.link_count;++i)if(!s->cards.links[i].label[0]){const EnhancedRect *hit=&s->cards.links[i].rect;int x=((hit->left+hit->right)/2-left)*r.right/320,y=((hit->top+hit->bottom)/2-top)*r.bottom/200;if(y>=r.bottom-32)continue;char label[80];snprintf(label,sizeof(label),"picture link %u to %d",i,s->cards.links[i].target);gesture_row(h,0x10000+i,label,x,y,0);gesture_row(h,0x10000+i,label,x,y,1);}
        }
    }
}
static void inventory(void){
    HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId()||!IsWindowVisible(h))continue;
        for(HWND c=GetWindow(h,GW_CHILD);c;c=GetWindow(c,GW_HWNDNEXT)){char cls[50];GetClassNameA(c,cls,sizeof(cls));int id=GetDlgCtrlID(c);if(lstrcmpiA(cls,"BUTTON")&&lstrcmpiA(cls,"EDIT")&&lstrcmpiA(cls,"COMBOBOX"))continue;if(!IsWindowVisible(c)&&id!=0x1206&&id!=0x1207&&id!=0x1208&&id!=0x1306&&id!=0x1307&&id!=0x1308)continue;row(c,h,id==0xe510||id==0xe511?"info-child":IsWindowVisible(c)?"":"manual");}painted_controls(h);
    }
    if(!root||!GetMenu(root)){failed=1;finish("missing-menu-bar");}menu_rows(GetMenu(root),"");finish("inventory");
}
static void key(HWND h,int key){PostMessage(h,WM_KEYDOWN,key,0);PostMessage(h,WM_KEYUP,key,0);}
static HWND presentation_window(void){
    HWND h=GetFocus();if(h)h=GetAncestor(h,GA_ROOT);
    if(h&&h!=root&&IsWindowVisible(h)&&IsWindowEnabled(h))return h;
    h=FindWindowExA(NULL,NULL,"#32768",NULL);if(h){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId())return h;}
    return NULL;
}
static int popup_items(HWND popup){
    char cls[80];GetClassNameA(popup,cls,sizeof(cls));
    if(strcmp(cls,"#32768")){
        const EnhancedDialogsSnapshot *d=&enhanced_snapshot()->dialogs;
        if(d->owner!=0x900&&(d->owner<0xc00||d->owner>0x1100))return 0;
        const EnhancedObjectSnapshot *wanted=NULL;
        for(unsigned i=0;i<d->object_count;++i){const EnhancedObjectSnapshot *o=&d->objects[i];if(o->type!=1||o->id<d->owner+2||!(o->flags&1)||!o->text[0])continue;
            fprintf(stderr,"SWEEP_POPUP {\"id\":%u,\"depth\":%u,\"label\":",(unsigned short)o->id,path_at);quoted(o->text);fprintf(stderr,",\"enabled\":%s}\n",o->flags&2?"true":"false");
            if(path_at<path_count&&path[path_at]==(unsigned short)o->id&&(o->flags&2))wanted=o;
        }
        if(path_at>=path_count)return 0;if(!wanted){failed=1;finish("requested-source-popup-item-unavailable");}
        SimHostedWindowView view;int found=0;for(unsigned i=0;i<sim_window_hosting_count();++i)if(sim_window_hosting_view(i,&view)&&view.id==d->owner){found=1;break;}
        if(!found){failed=1;finish("source-popup-view-missing");}
        int strip=view.drag_bottom>view.drag_top&&view.drag_top>=view.top_y&&view.drag_bottom<view.bottom?view.drag_bottom-view.top_y:0;
        int x=(wanted->rect.left+wanted->rect.right)/2-view.left,y=(wanted->rect.top+wanted->rect.bottom)/2-view.top_y-strip;
        /* Hosted SDL clients use the established native-window replay device:
         * its timestamp updates deterministic held input as well as events. */
        HostEvent event={.kind=HOST_EVENT_MOUSE_MOVE,.x=x,.y=y,.button=1};native_windows_push_pointer(d->owner,&event);++path_at;legacy_selected=1;
        if(d->owner!=0x900||wanted->id<0x903||wanted->id>0x908){event.kind=HOST_EVENT_MOUSE_DOWN;native_windows_push_pointer(d->owner,&event);legacy_release_owner=d->owner;legacy_release_tick=ticks+1;legacy_x=x;legacy_y=y;}
        return 1;
    }
    HMENU menu=(HMENU)SendMessage(popup,0x1e1,0,0);int wanted=-1,enabled_index=0;
    for(int i=0;i<GetMenuItemCount(menu);++i){MENUITEMINFOA item={.cbSize=sizeof(item),.fMask=MIIM_ID|MIIM_STATE|MIIM_FTYPE|MIIM_DATA|MIIM_STRING};char label[200]={0};item.dwTypeData=label;item.cch=sizeof(label);GetMenuItemInfoA(menu,i,TRUE,&item);if(item.fType&MFT_SEPARATOR)continue;
        if(item.fType&MFT_OWNERDRAW&&item.dwItemData)snprintf(label,sizeof(label),"%s",((EnhancedObjectSnapshot *)item.dwItemData)->text);
        int enabled=!(item.fState&(MFS_GRAYED|MFS_DISABLED));fprintf(stderr,"SWEEP_POPUP {\"id\":%u,\"depth\":%u,\"label\":",item.wID,path_at);quoted(label);fprintf(stderr,",\"enabled\":%s}\n",enabled?"true":"false");
        const EnhancedDialogsSnapshot *source=&enhanced_snapshot()->dialogs;
        for(unsigned n=0;n<source->object_count;++n){const EnhancedObjectSnapshot *o=&source->objects[n];if(o->id==item.wID&&o->type==1){if(enabled!=!!(o->flags&2)||!!(item.fState&MFS_CHECKED)!=!!((o->flags&4)||o->id==source->proximity_item))failed=1;break;}}
        if(enabled){if(path_at<path_count&&item.wID==path[path_at])wanted=enabled_index;++enabled_index;}
    }
    if(path_at>=path_count)return 0;
    if(wanted<0){failed=1;finish("requested-popup-item-unavailable");}
    expected_native_choice=(int)path[path_at++];for(int i=0;i<=wanted;++i)key(root,VK_DOWN);key(root,VK_RETURN);return 1;
}
extern int __real_native_workspace_proximity(const EnhancedDialogsSnapshot *);
int __wrap_native_workspace_proximity(const EnhancedDialogsSnapshot *menu){
    expected_native_choice=-1;inspected=NULL;int result=__real_native_workspace_proximity(menu);
    int expected=expected_native_choice<0?menu->owner+1:expected_native_choice;
    fprintf(stderr,"SWEEP_NATIVE_CHOICE owner=%04x expected=%04x actual=%04x\n",(unsigned short)menu->owner,(unsigned short)expected,(unsigned short)result);
    if(result!=expected)failed=1;return result;
}
static int waiting(void){const EnhancedSnapshot *s=enhanced_snapshot();return s&&(s->dialogs.modal||enhanced_proximity_owner()>=0||enhanced_minimap_owner()>=0||enhanced_yard_wait()||s->panels.tool==10||s->panels.tool==11||s->panels.tool==12);}
static void CALLBACK tick(HWND h,UINT message,UINT_PTR id,DWORD now){
    (void)h;(void)message;(void)id;(void)now;++ticks;
    if(GetTickCount64()-action_started>5000){failed=1;finish(waiting()?"uncancellable-presentation":"no-interactive-return");}
    if(legacy_release_owner&&ticks>=legacy_release_tick){HostEvent up={.kind=HOST_EVENT_MOUSE_UP,.button=1,.x=legacy_x,.y=legacy_y};native_windows_push_pointer(legacy_release_owner,&up);legacy_release_owner=0;}
    if(ticks==(identifier==4?8:2)&&held){PostMessage(target,WM_LBUTTONUP,0,MAKELPARAM(point_x,point_y));held=0;}
    if(ticks>=3&&waiting()&&(!inspected||(presentation_window()&&presentation_window()!=inspected))){
        HWND popup=presentation_window();RECT r={0};if(popup)GetClientRect(popup,&r);
        if(popup)GetWindowTextA(popup,presentation,sizeof(presentation));
        char cls[80]={0};if(popup)GetClassNameA(popup,cls,sizeof(cls));int menu=!strcmp(cls,"#32768");int owner=enhanced_snapshot()->dialogs.owner,source_menu=owner==0x900||(owner>=0xc00&&owner<=0x1100);
        if(!popup||r.right<(menu||source_menu?60:160)||r.bottom<(menu||source_menu?20:60)){
            fprintf(stderr,"SWEEP_WAIT owner=%04x focus=%p root=%p popup=%p\n",(unsigned short)enhanced_snapshot()->dialogs.owner,GetFocus(),root,popup);
            HWND w=NULL;while((w=FindWindowExA(NULL,w,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(w,&pid);if(pid!=GetCurrentProcessId())continue;char title[160],cls[80];GetWindowTextA(w,title,sizeof(title));GetClassNameA(w,cls,sizeof(cls));RECT rect;GetWindowRect(w,&rect);fprintf(stderr,"SWEEP_HWND %p %s %s shown=%d enabled=%d bounds=%ld,%ld,%ld,%ld\n",w,cls,title,IsWindowVisible(w),IsWindowEnabled(w),rect.left,rect.top,rect.right,rect.bottom);}
            failed=1;finish("invisible-or-too-small");}
        RECT bounds;GetWindowRect(popup,&bounds);MONITORINFO monitor={.cbSize=sizeof(monitor)};GetMonitorInfo(MonitorFromWindow(popup,MONITOR_DEFAULTTONEAREST),&monitor);
        if(bounds.left<monitor.rcWork.left||bounds.top<monitor.rcWork.top||bounds.right>monitor.rcWork.right||bounds.bottom>monitor.rcWork.bottom){failed=1;finish("off-screen-presentation");}
        int tool=enhanced_snapshot()->panels.tool;
        if(tool==10||tool==11){HWND prompt=FindWindowExA(NULL,NULL,"SimAntCommandPrompt",NULL);RECT client={0};if(prompt)GetClientRect(prompt,&client);
            /* A timer can run after source publication but before the native
             * presentation pass creates/sizes the prompt. Let that pass finish;
             * the wall-clock deadline above still rejects a persistent gap. */
            if(!prompt||!IsWindowVisible(prompt)||client.right<80||client.bottom<16){fprintf(stderr,"SWEEP_PROMPT_PENDING tool=%d tick=%d text=",tool,ticks);quoted(enhanced_snapshot()->panels.prompt);fprintf(stderr,"\n");return;}target_cancel=1;}
        observed=1;inspected=popup;if(!popup_items(popup)){
            if(target_cancel&&outside_cancel){PostMessage(root,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(1,1));PostMessage(root,WM_LBUTTONUP,0,MAKELPARAM(1,1));}
            else key(menu?root:popup,VK_ESCAPE);
        }
    }
    if(ticks==6&&waiting()){
        HWND popup=presentation_window();if(popup){PostMessage(popup,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(-4,-4));PostMessage(popup,WM_LBUTTONUP,0,MAKELPARAM(-4,-4));}
    }
    if(GetTickCount64()-action_started>5000){failed=1;finish(waiting()?"uncancellable-presentation":"no-interactive-return");}
}
static void click(HWND h){RECT r;GetClientRect(h,&r);PostMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(r.right/2,r.bottom/2));PostMessage(h,WM_LBUTTONUP,0,MAKELPARAM(r.right/2,r.bottom/2));}
void __wrap_enhanced_source_poll(void){__real_enhanced_source_poll();static ULONGLONG last;ULONGLONG now=GetTickCount64();if(phase&&now-last>5000){last=now;const EnhancedSnapshot *s=enhanced_snapshot();fprintf(stderr,"SWEEP_PROGRESS phase=%d ticks=%d iteration=%ld owner=%04x modal=%d tool=%d submitted=%llu delivered=%llu\n",phase,ticks,(long)main_iteration_count,(unsigned short)s->dialogs.owner,s->dialogs.modal,s->panels.tool,(unsigned long long)enhanced_action_ledger()->submitted,(unsigned long long)enhanced_action_ledger()->delivered);}}
void __wrap_enhanced_execute_next(void){
    const EnhancedSnapshot *s=enhanced_snapshot();if(!s||!s->panels.world_ready){__real_enhanced_execute_next();return;}
    if(!kind){kind=getenv("SIMANT_SWEEP_KIND");setup=getenv("SIMANT_SWEEP_SETUP");parent_name=getenv("SIMANT_SWEEP_PARENT");identifier=strtol(getenv("SIMANT_SWEEP_ID"),NULL,0);point_x=atoi(getenv("SIMANT_SWEEP_X"));point_y=atoi(getenv("SIMANT_SWEEP_Y"));outside_cancel=atoi(getenv("SIMANT_SWEEP_OUTSIDE"));root=named("SimAnt");const char *p=getenv("SIMANT_SWEEP_PATH");while(p&&*p&&path_count<12){char *end;path[path_count++]=strtoul(p,&end,0);if(end==p||*end!=',')break;p=end+1;}}
    if(!phase&&main_iteration_count>25){phase=1;started=main_iteration_count;
        if(!strcmp(setup,"spider")){enhanced_submit_event(8,0,0,0);enhanced_submit_event(12,0,0,0);}else enhanced_submit_event(11,0,0,0);
        const char *names[]={"Behavior Control","Caste Control","History","Info"};int events[]={0x10f,0x111,0x113,0x115};
        for(int i=0;i<4;++i){HWND w=named(names[i]);if(!w||!IsWindowVisible(w))enhanced_submit_event(events[i],0,0,0);}
        if(identifier>=0x1206&&identifier<=0x1208)enhanced_submit_event(0x1205,0,0,0);
        if(identifier>=0x1306&&identifier<=0x1308)enhanced_submit_event(0x1305,0,0,0);
    }
    if(phase==1&&main_iteration_count>started+20&&!s->dialogs.modal){
        if(!strcmp(setup,"spider")){
            HWND game=named("SimAnt - Game");const WsPanel *view=&native_workspace_layout()->panels[WS_GAME];typedef UINT(WINAPI *Dpi)(HWND);Dpi dpi=(Dpi)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");int d=dpi?dpi(game):96;
            point_x=MulDiv((s->world.spider_x-view->camera_x)*view->zoom,d,9600);point_y=MulDiv((s->world.spider_y-view->camera_y)*view->zoom,d,9600);
            if(!spider_stage){key(game,'X');spider_stage=1;started=main_iteration_count;__real_enhanced_execute_next();return;}
            if(spider_stage==1){if(s->panels.tool!=10){failed=1;finish("spider-exchange-prompt-missing");}SendMessage(game,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(point_x,point_y));SendMessage(game,WM_LBUTTONUP,0,MAKELPARAM(point_x,point_y));spider_stage=2;started=main_iteration_count;__real_enhanced_execute_next();return;}
            if(s->world.player_mode!=1){failed=1;finish("spider-exchange-not-completed");}
        }
        if((identifier==0xe510||identifier==0xe511)&&!footer_prepared){
            HWND info=named("Info");RECT client;GetClientRect(info,&client);const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[5];
            if(entry->bound&&entry->view.count>2){const uint8_t *r=entry->view.object_table[2];int left=sim_window_wire_read_i16(r,0),top=sim_window_wire_read_i16(r,2);
                for(unsigned i=0;i<s->cards.link_count;++i)if(s->cards.links[i].target>1&&s->cards.links[i].target!=128&&!s->cards.links[i].label[0]){const EnhancedRect *hit=&s->cards.links[i].rect;int x=((hit->left+hit->right)/2-left)*client.right/320,y=((hit->top+hit->bottom)/2-top)*client.bottom/200;SendMessage(info,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));SendMessage(info,WM_LBUTTONUP,0,MAKELPARAM(x,y));break;}
            }footer_prepared=1;started=main_iteration_count;__real_enhanced_execute_next();return;
        }
        if(!strcmp(kind,"inventory"))inventory();
        HWND parent=named(!strncmp(parent_name,"Info",4)?"Info":parent_name);int gesture=!strcmp(kind,"gesture")||!strcmp(kind,"hold");target=!strcmp(kind,"menu")?root:gesture?parent:parent?GetDlgItem(parent,identifier):NULL;
        if(!target||!IsWindowVisible(target)||!IsWindowEnabled(target)){finish("unavailable");}
        phase=2;started=main_iteration_count;submitted=enhanced_action_ledger()->delivered;initial_pause=s->panels.paused;action_started=GetTickCount64();
        timer=SetTimer(root,0,100,tick);if(!timer){failed=1;finish("timer-failed");}
        if(!strcmp(kind,"menu")){PostMessage(root,WM_COMMAND,identifier,0);}
        else if(gesture){PostMessage(target,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(point_x,point_y));held=!strcmp(kind,"hold");if(!held)PostMessage(target,WM_LBUTTONUP,0,MAKELPARAM(point_x,point_y));}
        else {char cls[40];GetClassNameA(target,cls,sizeof(cls));
            if(!lstrcmpiA(cls,"EDIT")){SetFocus(target);SetWindowTextA(target,"37");key(target,VK_RETURN);}
            else if(!lstrcmpiA(cls,"COMBOBOX")){SendMessage(target,CB_SETCURSEL,2,0);PostMessage(parent,WM_COMMAND,MAKEWPARAM(identifier,CBN_SELCHANGE),(LPARAM)target);}
            else click(target);
        }
    }
    if(phase==2&&ticks>=4&&!waiting()&&main_iteration_count>started){
        if(target_cancel&&s->panels.paused!=initial_pause){failed=1;finish("cancel-changed-saved-pause");}
        if(path_count&&path[0]>=0x902&&path[0]<=0x909){
            unsigned tool=path[0]-0x902;extern char ExpSubStates[];
            if((path_count>1||tool==0||tool==7)&&s->panels.experiment_tool!=tool){failed=1;finish("wrong-source-experiment-tool");}
            if(path_count>1&&(unsigned char)ExpSubStates[tool]!=(path[path_count-1]&255)-2){failed=1;finish("wrong-source-experiment-substate");}
        }
        HWND ant=named("Map / Ant Control Panel");if(ant&&IsWindowEnabled(ant)){
            cancelled=observed&&(!path_count||target_cancel);phase=3;started=main_iteration_count;submitted=enhanced_action_ledger()->delivered;
            click(GetDlgItem(ant,15));
        }
    }
    if(phase==3&&main_iteration_count>started&&enhanced_action_ledger()->delivered>submitted&&!waiting()){
        KillTimer(root,timer);++ready_checks;if(path_at!=path_count)failed=1;if(identifier==4&&s->panels.game_type!=3&&!observed)failed=1;finish(observed?(path_count?"visible-selected-interactive":"visible-cancelled-interactive"):"interactive");
    }
    __real_enhanced_execute_next();
}
