/* Real native button, popup and source centring regression. Runs only inside
 * hidden_desktop.install(); no global input or desktop capture. */
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
extern int __real_native_workspace_minimap(const EnhancedRect *,const EnhancedRect *,EnhancedPoint *);
extern void __real_CenterEdit(int16_t,int16_t);
static int phase,started,checks,failures,seen,moves,chosen_x,chosen_y,timer_ticks;
static int expected_x,expected_y,plane;
static HWND root;
static const char *test;
static EnhancedWorldSnapshot waiting;
static EnhancedRect source_rect;
#define CHECK(x) do{++checks;if(!(x)){++failures;fprintf(stderr,"MINIMAP_FAIL %d %s\n",__LINE__,#x);}}while(0)
static HWND named(const char *title){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,title))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId())return h;}return NULL;}
static int cancel(void){return !strcmp(test,"escape")||!strcmp(test,"outside")||!strcmp(test,"drag-outside")||!strcmp(test,"drag-away")||!strncmp(test,"gutter-",7);}
static RECT camera_pixels(HWND h,RECT area,int map){
    RECT client;GetClientRect(h,&client);int w=client.right,he=client.bottom;uint32_t *pixels=NULL;
    BITMAPINFO info={.bmiHeader={sizeof(BITMAPINFOHEADER),w,-he,1,32,BI_RGB}};
    HDC dc=CreateCompatibleDC(NULL);HBITMAP bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,(void **)&pixels,NULL,0);HGDIOBJ old=SelectObject(dc,bitmap);
    if(map)CHECK(native_workspace_content_paint(h,dc,0));else SendMessage(h,WM_PRINTCLIENT,(WPARAM)dc,PRF_CLIENT);
    GdiFlush();RECT box={w,he,0,0};unsigned yellow=0;
    for(int y=area.top;y<area.bottom;++y)for(int x=area.left;x<area.right;++x)if((pixels[y*w+x]&0xffffff)==0xfff304){++yellow;if(x<box.left)box.left=x;if(x>=box.right)box.right=x+1;if(y<box.top)box.top=y;if(y>=box.bottom)box.bottom=y+1;}
    CHECK(yellow>20);SelectObject(dc,old);DeleteObject(bitmap);DeleteDC(dc);return box;
}
static void CALLBACK tick(HWND window,UINT msg,UINT_PTR id,DWORD now){
    (void)window;(void)msg;(void)id;(void)now;
    HWND h=named("Minimap - Esc cancels");if(!h)return;
    if(timer_ticks++>5){CHECK(0);SendMessage(h,WM_CLOSE,0,0);return;}
    if(timer_ticks!=1)return;
    RECT r,c,button;GetWindowRect(h,&r);GetClientRect(h,&c);GetWindowRect(GetDlgItem(named("Map / Ant Control Panel"),5),&button);
    MONITORINFO monitor={.cbSize=sizeof(monitor)};POINT at={button.left+8,button.top+8};GetMonitorInfo(MonitorFromPoint(at,MONITOR_DEFAULTTONEAREST),&monitor);
    CHECK(IsWindowVisible(h)&&IsWindowEnabled(h));CHECK(GetFocus()==h);CHECK(c.right>=500&&c.bottom>=300);
    CHECK(r.left>=monitor.rcWork.left&&r.top>=monitor.rcWork.top&&r.right<=monitor.rcWork.right&&r.bottom<=monitor.rcWork.bottom);
    int left=button.left+16,top=button.top+16;
    if(left+r.right-r.left>monitor.rcWork.right)left=monitor.rcWork.right-(r.right-r.left);
    if(top+r.bottom-r.top>monitor.rcWork.bottom)top=monitor.rcWork.bottom-(r.bottom-r.top);
    if(left<monitor.rcWork.left)left=monitor.rcWork.left;if(top<monitor.rcWork.top)top=monitor.rcWork.top;
    CHECK(r.left==left&&r.top==top);
    CHECK(!memcmp(&waiting,&enhanced_snapshot()->world,sizeof(waiting)));CHECK(IsWindowVisible(named("SimAnt - Game")));
    int width=r.right-r.left,height=r.bottom-r.top;
    RECT map={MulDiv(12,width,536),MulDiv(38,height,350),MulDiv(524,width,536),MulDiv(294,height,350)};
    HWND overview=named("Map");CHECK(overview!=NULL);RECT overview_client;GetClientRect(overview,&overview_client);
    RECT small=camera_pixels(h,map,0),large=camera_pixels(overview,overview_client,1);
    CHECK(abs(small.left-map.left-MulDiv(large.left,map.right-map.left,overview_client.right))<=2);
    CHECK(abs(small.right-map.left-MulDiv(large.right,map.right-map.left,overview_client.right))<=2);
    CHECK(abs(small.top-map.top-MulDiv(large.top,map.bottom-map.top,overview_client.bottom))<=2);
    CHECK(abs(small.bottom-map.top-MulDiv(large.bottom,map.bottom-map.top,overview_client.bottom))<=2);
    const char *capture=getenv("SIMANT_MINIMAP_CAPTURE");if(capture)CHECK(native_workspace_capture(capture));
    fprintf(stderr,"MINIMAP_OPEN {\"left\":%ld,\"top\":%ld,\"width\":%ld,\"height\":%ld,\"player\":%d,\"spider\":%d}\n",r.left,r.top,c.right,c.bottom,waiting.player_mode,waiting.spider_on);
    if(!strcmp(test,"escape")){PostMessage(h,WM_KEYDOWN,VK_ESCAPE,0);return;}
    if(!strcmp(test,"outside")){PostMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(-2,-2));PostMessage(h,WM_LBUTTONUP,0,MAKELPARAM(-2,-2));return;}
    if(!strcmp(test,"drag-away")){PostMessage(h,WM_LBUTTONUP,0,MAKELPARAM(-200,-200));return;}
    /* Client map is [12,38,524,294] in source-independent native DIPs. */
    RECT hit=map;if(plane>1){while((hit.left-map.left)*128/(map.right-map.left)<32)++hit.left;while((hit.right-1-map.left)*128/(map.right-map.left)>=96)--hit.right;}
    int x=map.left+(map.right-map.left)*5/8,y=map.top+(map.bottom-map.top)/2;
    if(!strcmp(test,"edge-right")||!strcmp(test,"edge-corner"))x=hit.right-1;
    if(!strcmp(test,"edge-bottom")||!strcmp(test,"edge-corner"))y=map.bottom-1;
    if(!strcmp(test,"edge-left"))x=hit.left;
    if(!strcmp(test,"edge-top"))y=map.top;
    if(!strcmp(test,"gutter-left"))x=map.left;
    if(!strcmp(test,"gutter-right"))x=map.right-1;
    expected_x=(x-map.left)*128/(map.right-map.left)-(plane>1?32:0);expected_y=(y-map.top)*64/(map.bottom-map.top);
    if(!strcmp(test,"click")||!strncmp(test,"edge-",5)||!strncmp(test,"gutter-",7))PostMessage(h,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(x,y));
    PostMessage(h,WM_MOUSEMOVE,MK_LBUTTON,MAKELPARAM(x,y));
    if(!strcmp(test,"drag-outside")){x=-2;y=-2;}
    PostMessage(h,WM_LBUTTONUP,0,MAKELPARAM(x,y));
}
int __wrap_native_workspace_minimap(const EnhancedRect *r,const EnhancedRect *c,EnhancedPoint *p){
    source_rect=*r;waiting=enhanced_snapshot()->world;UINT_PTR timer=SetTimer(root,0,100,tick);CHECK(timer!=0);
    int result=__real_native_workspace_minimap(r,c,p);KillTimer(root,timer);++seen;CHECK(result==!cancel());return result;
}
void __wrap_CenterEdit(int16_t x,int16_t y){if(phase==2){++moves;chosen_x=x;chosen_y=y;}__real_CenterEdit(x,y);}
void __wrap_enhanced_source_poll(void){__real_enhanced_source_poll();}
void __wrap_enhanced_execute_next(void){
    const EnhancedSnapshot *s=enhanced_snapshot();if(!s||!s->panels.world_ready){__real_enhanced_execute_next();return;}
    if(!test){test=getenv("SIMANT_MINIMAP_CASE");plane=atoi(getenv("SIMANT_MINIMAP_PLANE"));root=named("SimAnt");CHECK(native_workspace_active());}
    if(!phase&&main_iteration_count>25){phase=1;enhanced_submit_event(7+plane,0,0,0);started=main_iteration_count;}
    if(phase==1&&main_iteration_count>started+20&&!s->dialogs.modal){
        CHECK(s->world.plane==plane);
        phase=2;started=main_iteration_count;HWND b=GetDlgItem(named("Map / Ant Control Panel"),5);CHECK(b&&IsWindowEnabled(b));
        SendMessage(b,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(8,8));
        if(strncmp(test,"drag",4))SendMessage(b,WM_LBUTTONUP,0,MAKELPARAM(8,8));
    }
    if(phase==2&&seen&&main_iteration_count>started+10&&!s->dialogs.modal){
        CHECK(IsWindowEnabled(named("Map / Ant Control Panel")));CHECK(moves==!cancel());
        if(!cancel()){CHECK(chosen_x==expected_x);CHECK(chosen_y==expected_y);}
        fprintf(stderr,"MINIMAP_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"seen\":%d,\"moves\":%d,\"x\":%d,\"y\":%d,\"simulation_advanced\":true}\n",failures?"false":"true",checks,failures,seen,moves,chosen_x,chosen_y);exit(failures?1:0);
    }
    __real_enhanced_execute_next();
}
