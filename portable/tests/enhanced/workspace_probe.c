/* Runs against the normal shipped startup. Test callbacks mutate host state only. */
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include <windows.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void);
static int completed;
static int modal_tested;
static int failures,checks;
#define CHECK(c) do {++checks;if(!(c)){++failures;fprintf(stderr,"WORKSPACE_CHECK failed: %s at %d\n",#c,__LINE__);}}while(0)
static HWND find_class(HWND parent,const char *cls){HWND h=NULL;char name[120];while((h=FindWindowExA(parent,h,NULL,NULL))){GetClassNameA(h,name,sizeof(name));if(!strcmp(name,cls))return h;HWND child=find_class(h,cls);if(child)return child;}return NULL;}
static HWND root(void){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,"SimAnt - Native Workspace Preview"))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId())return h;}return NULL;}
static HWND group_named(HWND main,const char *name){HWND h=NULL;while((h=FindWindowExA(main,h,"SimAntWorkspaceGroup",NULL))){char title[80];GetWindowTextA(h,title,sizeof(title));if(!strcmp(title,name))return h;}return NULL;}
static void inspectors(Workspace *w){ws_preset(w,0);int ids[]={4,5,6,7,11};for(int i=0;i<5;++i)ws_hide(w,ids[i]);
    ws_reveal(w,1);ws_move(w,1,0,WS_RIGHT,0);ws_reveal(w,2);ws_move(w,2,1,WS_RIGHT,0);w->panels[1].plane=1;w->panels[2].plane=2;
    w->nodes[w->root].ratio=334;
}
static void scene(int id,HWND main) {
    Workspace w=*native_workspace_layout();
    ws_preset(&w,0);
    if(id==1)inspectors(&w);
    if(id==2){ws_reveal(&w,1);ws_move(&w,1,0,WS_STACK,0);ws_reveal(&w,2);ws_move(&w,2,0,WS_STACK,0);}
    if(id==3){
        RECT bounds;GetWindowRect(main,&bounds);MONITORINFO monitor={.cbSize=sizeof(monitor)};
        GetMonitorInfo(MonitorFromWindow(main,MONITOR_DEFAULTTONEAREST),&monitor);
        typedef UINT (WINAPI *DpiReader)(HWND);DpiReader read=(DpiReader)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");
        UINT dpi=read?read(main):96;
        ws_reveal(&w,1);ws_float(&w,1,MulDiv(bounds.left-monitor.rcWork.left,96,dpi)+80,
            MulDiv(bounds.top-monitor.rcWork.top,96,dpi)+80,500,380);
    }
    CHECK(native_workspace_apply(&w));
    if(id==5)SetWindowPos(main,NULL,30,30,740,520,SWP_NOZORDER|SWP_NOACTIVATE);
    if(id==6||id==7){int dpi=id==6?144:192;RECT r={20,20,20+1120*dpi/96,20+760*dpi/96};SendMessage(main,WM_DPICHANGED,MAKELONG(dpi,dpi),(LPARAM)&r);}
    RedrawWindow(main,NULL,NULL,RDW_INVALIDATE|RDW_ALLCHILDREN|RDW_UPDATENOW);
}
extern void __real_enhanced_source_poll(void);
void __wrap_enhanced_source_poll(void) {
    __real_enhanced_source_poll();
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(!getenv("SIMANT_WORKSPACE_MODAL_TEST")||modal_tested||!completed||!s||!s->dialogs.modal||s->dialogs.owner!=0x1a00)return;
    modal_tested=1;static EnhancedSnapshot before;before=*s;int prior=failures;
    for(int i=0;i<10;++i)CHECK(native_workspace_operation(i));
    const Workspace *w=native_workspace_layout();int g=ws_group(w,22);CHECK(g>=0);
    if(g>=0){CHECK(!w->nodes[g].collapsed);CHECK(w->nodes[g].panels[w->nodes[g].active]==22);
        Workspace attempt=*w;CHECK(!ws_hide(&attempt,22));CHECK(!ws_collapse(&attempt,g));}
    CHECK(!memcmp(&before,enhanced_snapshot(),sizeof(before)));
    fprintf(stderr,"WORKSPACE_MODAL {\"passed\":%s,\"owner\":%d,\"generation\":%llu}\n",failures==prior?"true":"false",s->dialogs.owner,(unsigned long long)s->generation);
}
static void exercise(HWND main) {
    Workspace old=*native_workspace_layout();
    for(unsigned i=0;i<10;++i)CHECK(native_workspace_operation(i));
    CHECK(native_workspace_apply(&old));
    HWND group=group_named(main,"World");CHECK(group!=NULL);HWND canvas=GetDlgItem(group,4);SetFocus(canvas);
    SendMessage(canvas,WM_KEYDOWN,VK_F6,0);CHECK(GetFocus()!=canvas);
    SendMessage(main,WM_COMMAND,102,0);CHECK(ws_group(native_workspace_layout(),1)>=0);
    int g=ws_group(native_workspace_layout(),0);HWND world_group=group_named(main,"World");
    if(world_group){HWND tab=GetDlgItem(world_group,1);CHECK(tab!=NULL);}
    SendMessage(main,WM_COMMAND,413,0); /* Reset Layout */
    CHECK(ws_group(native_workspace_layout(),1)<0);
    (void)g;
    Workspace keyboard=*native_workspace_layout();ws_reveal(&keyboard,1);ws_move(&keyboard,1,0,WS_STACK,0);
    CHECK(native_workspace_apply(&keyboard));
    int group_id=ws_group(native_workspace_layout(),1),active=native_workspace_layout()->nodes[group_id].active;
    HWND inspector=group_named(main,"Inspector 1");CHECK(inspector!=NULL);
    SetFocus(GetDlgItem(inspector,4));
    BYTE keys[256],modified[256];GetKeyboardState(keys);memcpy(modified,keys,sizeof(keys));modified[VK_CONTROL]=0x80;SetKeyboardState(modified);
    SendMessage(GetDlgItem(inspector,4),WM_KEYDOWN,VK_TAB,0);SetKeyboardState(keys);
    CHECK(native_workspace_layout()->nodes[group_id].active!=active);
    HWND splitter=find_class(main,TRACKBAR_CLASSA);CHECK(splitter!=NULL);
    Workspace before_split=*native_workspace_layout();SendMessage(splitter,WM_KEYDOWN,VK_RIGHT,0);
    CHECK(memcmp(before_split.nodes,native_workspace_layout()->nodes,sizeof(before_split.nodes))!=0);
    keyboard=*native_workspace_layout();ws_float(&keyboard,1,90000,-90000,480,320);CHECK(native_workspace_apply(&keyboard));
    HWND tool=NULL;while((tool=FindWindowExA(NULL,tool,"SimAntWorkspaceFloat",NULL)))if(GetWindow(tool,GW_OWNER)==main&&IsWindowVisible(tool))break;
    CHECK(tool!=NULL);if(tool){RECT bounds;GetWindowRect(tool,&bounds);MONITORINFO monitor={.cbSize=sizeof(monitor)};GetMonitorInfo(MonitorFromWindow(tool,MONITOR_DEFAULTTONEAREST),&monitor);
        CHECK(bounds.left>=monitor.rcWork.left&&bounds.top>=monitor.rcWork.top&&bounds.right<=monitor.rcWork.right&&bounds.bottom<=monitor.rcWork.bottom);
        SendMessage(tool,WM_CLOSE,0,0);CHECK(ws_group(native_workspace_layout(),1)<0);}
    CHECK(native_workspace_apply(&old));
    const char *path=getenv("SIMANT_WORKSPACE_LAYOUT");FILE *file=fopen(path,"r");Workspace disk;
    CHECK(file!=NULL);if(file){CHECK(ws_read(&disk,file));fclose(file);disk.revision=old.revision;CHECK(!memcmp(&old,&disk,sizeof(old)));}
}
void __wrap_enhanced_execute_next(void) {
    __real_enhanced_execute_next();
    const EnhancedSnapshot *snapshot=enhanced_snapshot();
    if(completed||!snapshot||snapshot->panels.game_type<0||main_iteration_count<24)return;
    completed=1;HWND main=root();CHECK(main!=NULL);CHECK(native_workspace_active());
    typedef UINT (WINAPI *DpiReader)(HWND);DpiReader dpi=(DpiReader)GetProcAddress(GetModuleHandleA("user32.dll"),"GetDpiForWindow");
    fprintf(stderr,"WORKSPACE_ENV {\"physical_window_dpi\":%u,\"source_iteration\":%ld}\n",dpi?dpi(main):0,(long)main_iteration_count);
    static EnhancedSnapshot before;before=*snapshot;
    fprintf(stderr,"WORKSPACE_WORLD origin=%d,%d player=%d,%d plane=%d\n",snapshot->world.origin.x,snapshot->world.origin.y,snapshot->world.player_x,snapshot->world.player_y,snapshot->world.plane);
    exercise(main);
    const char *number=getenv("SIMANT_WORKSPACE_SCENE");int id=number?atoi(number):0;scene(id,main);
    POINT cursor;GetCursorPos(&cursor);
    if(id==4){HWND group=group_named(main,"World");HWND tab=GetDlgItem(group,1);RECT r;GetWindowRect(tab,&r);SetCursorPos(r.left+20,r.top+10);
        SendMessage(tab,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(20,10));SetCursorPos(r.left+80,r.top+70);SendMessage(tab,WM_MOUSEMOVE,MK_LBUTTON,MAKELPARAM(80,70));}
    const char *capture=getenv("SIMANT_WORKSPACE_CAPTURE");if(capture)CHECK(native_workspace_capture(capture));
    CHECK(!memcmp(&before,enhanced_snapshot(),sizeof(before)));
    const char *ready=getenv("SIMANT_WORKSPACE_READY");if(ready){FILE *f=fopen(ready,"w");if(f){fprintf(f,"%lu\n",GetCurrentProcessId());fclose(f);}
        UINT64 end=GetTickCount64()+15000;
        while(GetTickCount64()<end&&GetFileAttributesA(ready)!=INVALID_FILE_ATTRIBUTES){MSG msg;while(PeekMessage(&msg,NULL,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessage(&msg);}Sleep(20);}}
    if(id==4){SendMessage(main,WM_KEYDOWN,VK_ESCAPE,0);SetCursorPos(cursor.x,cursor.y);}
    CHECK(!memcmp(&before,enhanced_snapshot(),sizeof(before)));
    fprintf(stderr,"WORKSPACE_UI {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"scene\":%d,\"generation\":%llu}\n",failures?"false":"true",checks,failures,id,(unsigned long long)snapshot->generation);
}
