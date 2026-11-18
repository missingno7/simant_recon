/* Fixed-client reset matrix and live UI scaling through the actual native menu. */
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/sdl3/native_menu.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/actions.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "source_fingerprint.h"
extern int32_t main_iteration_count;
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
extern int __real_portable_m1b73_try_enqueue_command(int16_t,int16_t,int16_t,int16_t,int16_t);
static int phase,started,checks,failures,work_width,work_height,hit_case,hits,menu_ticks;
static HWND root;static int status_seen;
static const int scales[]={0,100,125,150,175,200,250,300};
#define CHECK(x) do{++checks;if(!(x)){++failures;fprintf(stderr,"UI_SCALE_FAIL %d %s\n",__LINE__,#x);}}while(0)
extern BOOL WINAPI __real_GetMonitorInfoA(HMONITOR,LPMONITORINFO),__real_GetMonitorInfoW(HMONITOR,LPMONITORINFO);
BOOL WINAPI __wrap_GetMonitorInfoA(HMONITOR h,LPMONITORINFO m){typedef BOOL(WINAPI *F)(HMONITOR,LPMONITORINFO);F f=(F)GetProcAddress(GetModuleHandleA("user32.dll"),"GetMonitorInfoA");BOOL r=f(h,m);if(r&&work_width)m->rcWork=(RECT){0,0,work_width,work_height};return r;}
BOOL WINAPI __wrap_GetMonitorInfoW(HMONITOR h,LPMONITORINFO m){typedef BOOL(WINAPI *F)(HMONITOR,LPMONITORINFO);F f=(F)GetProcAddress(GetModuleHandleA("user32.dll"),"GetMonitorInfoW");BOOL r=f(h,m);if(r&&work_width)m->rcWork=(RECT){0,0,work_width,work_height};return r;}
BOOL(WINAPI *__wrap___imp_GetMonitorInfoA)(HMONITOR,LPMONITORINFO)=__wrap_GetMonitorInfoA;
BOOL(WINAPI *__wrap___imp_GetMonitorInfoW)(HMONITOR,LPMONITORINFO)=__wrap_GetMonitorInfoW;
static HWND named(const char *name){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId())continue;char text[200];GetWindowTextA(h,text,sizeof(text));if((!strcmp(text,name)||(!strcmp(name,"Info")&&!strncmp(text,"Info - ",7)))&&(strcmp(name,"SimAnt")||GetMenu(h)))return h;}return NULL;}
static void save(HWND h,const char *name){
 char path[2400];snprintf(path,sizeof(path),"%s/%s.bmp",getenv("SIMANT_UI_OUT"),name);RECT r;GetWindowRect(h,&r);int w=r.right-r.left,he=r.bottom-r.top;
 BITMAPINFO info={.bmiHeader={sizeof(BITMAPINFOHEADER),w,-he,1,32,BI_RGB}};void *pixels;HDC dc=CreateCompatibleDC(NULL);HBITMAP bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,&pixels,NULL,0);HGDIOBJ old=SelectObject(dc,bitmap);
 CHECK(PrintWindow(h,dc,0));int state=SaveDC(dc);native_workspace_content_paint(h,dc,1);RestoreDC(dc,state);GdiFlush();
 BITMAPFILEHEADER file={.bfType=0x4d42,.bfSize=54+w*he*4,.bfOffBits=54};FILE *f=fopen(path,"wb");CHECK(f);if(f){fwrite(&file,1,sizeof(file),f);fwrite(&info.bmiHeader,1,40,f);fwrite(pixels,1,w*he*4,f);fclose(f);}SelectObject(dc,old);DeleteObject(bitmap);DeleteDC(dc);
}
static void layout_checks(int dpi){
 const char *names[]={"Map / Ant Control Panel","Yard Control Panel","Map","Yard","Behavior Control","Caste Control","History","Info","Status"};
 const int panels[]={WS_ANT,WS_YARD_CONTROL,WS_MAP,WS_YARD,WS_BEHAVIOR,WS_CASTE,WS_HISTORY,WS_INFO,WS_STATUS};
 for(int i=0;i<9;++i){HWND h=named(names[i]);if((i==3||i==8)&&!h)continue;CHECK(h);if(!h)continue;
  RECT r;GetClientRect(h,&r);int w,he;ws_fixed_content(panels[i],&w,&he);if(r.right!=MulDiv(w,dpi,96)||r.bottom!=MulDiv(he,dpi,96))fprintf(stderr,"UI_GEOMETRY name=%s client=%ld,%ld want=%d,%d dpi=%d\n",names[i],r.right,r.bottom,MulDiv(w,dpi,96),MulDiv(he,dpi,96),dpi);CHECK(r.right==MulDiv(w,dpi,96));CHECK(r.bottom==MulDiv(he,dpi,96));CHECK(!(GetWindowLongPtr(h,GWL_STYLE)&WS_THICKFRAME));
  for(HWND c=GetWindow(h,GW_CHILD);c;c=GetWindow(c,GW_HWNDNEXT)){if(!(GetWindowLong(c,GWL_STYLE)&WS_VISIBLE))continue;RECT cr;GetWindowRect(c,&cr);MapWindowPoints(NULL,h,(POINT *)&cr,2);if(cr.left<0||cr.top<0||cr.right>r.right||cr.bottom>r.bottom)fprintf(stderr,"UI_CHILD name=%s id=%x rect=%ld,%ld,%ld,%ld\n",names[i],GetDlgCtrlID(c),cr.left,cr.top,cr.right,cr.bottom);CHECK(cr.left>=0&&cr.top>=0&&cr.right<=r.right&&cr.bottom<=r.bottom);
   POINT at={(cr.left+cr.right)/2,(cr.top+cr.bottom)/2};CHECK(ChildWindowFromPointEx(h,at,CWP_SKIPINVISIBLE)==c);
   HFONT font=(HFONT)SendMessage(c,WM_GETFONT,0,0);if(font){LOGFONT log;GetObject(font,sizeof(log),&log);CHECK(abs(log.lfHeight)==MulDiv(13,dpi,96));}
  }
 }
}
static void matrix(void){
 uint64_t before=source_fingerprint();EnhancedSnapshot published=*enhanced_snapshot();
 int physical[]={96,120,144};
 for(int area=0;area<2;++area){work_width=area?2560:1920;work_height=area?1400:1040;
  for(int d=0;d<3;++d){native_workspace_set_ui_scale(0);
   for(int p=0;p<WS_PANELS;++p){HWND h=named(ws_name(p));if(!h)continue;RECT r;GetWindowRect(h,&r);SendMessage(h,WM_DPICHANGED,MAKELONG(physical[d],physical[d]),(LPARAM)&r);}
   RECT rr;GetWindowRect(root,&rr);SendMessage(root,WM_DPICHANGED,MAKELONG(physical[d],physical[d]),(LPARAM)&rr);
   SendMessage(root,WM_COMMAND,0xe100,0);layout_checks(physical[d]);
   fprintf(stderr,"UI_RESET_MATRIX area=%dx%d dpi=%d\n",work_width,work_height,physical[d]);
   for(int j=1;j<8;++j){SendMessage(root,WM_COMMAND,0xe400+j,0);CHECK(native_workspace_layout()->ui_scale==scales[j]);layout_checks(MulDiv(scales[j],96,100));
    HMENU options=GetSubMenu(GetMenu(root),3),menu=GetSubMenu(options,GetMenuItemCount(options)-1);CHECK(menu);SendMessage(root,WM_INITMENUPOPUP,(WPARAM)menu,0);for(int k=0;k<8;++k)CHECK(!!(GetMenuState(menu,0xe400+k,MF_BYCOMMAND)&MF_CHECKED)==(k==j));}
  }
 }
 work_width=work_height=0;CHECK(source_fingerprint()==before);CHECK(!memcmp(&published,enhanced_snapshot(),sizeof(published)));
 for(int i=1;i<=5;i+=4){SendMessage(root,WM_COMMAND,0xe400+i,0);char path[2400];snprintf(path,sizeof(path),"%s/game-%d.bmp",getenv("SIMANT_UI_OUT"),scales[i]);CHECK(native_workspace_capture(path));}
 native_workspace_set_ui_scale(100);
 const char *names[]={"Map / Ant Control Panel","Yard Control Panel","Map","Behavior Control","Caste Control","History","Info"};
 const char *files[]={"ant-after","yard-control-after","map-after","behavior-after","caste-after","history-after","info-after"};for(int i=0;i<7;++i)save(named(names[i]),files[i]);
}
static void CALLBACK menu_tick(HWND h,UINT msg,UINT_PTR id,DWORD now){(void)h;(void)msg;(void)id;(void)now;++menu_ticks;
 if(menu_ticks==1){PostMessage(root,WM_KEYDOWN,VK_END,0);PostMessage(root,WM_KEYUP,VK_END,0);PostMessage(root,WM_KEYDOWN,VK_RIGHT,0);PostMessage(root,WM_KEYUP,VK_RIGHT,0);}
 if(menu_ticks==3){char path[2400];snprintf(path,sizeof(path),"%s/ui-scale-menu.bmp",getenv("SIMANT_UI_OUT"));CHECK(native_workspace_capture(path));EndMenu();}
 if(menu_ticks>8){CHECK(0);EndMenu();}
}
int __wrap_portable_m1b73_try_enqueue_command(int16_t code,int16_t m,int16_t mods,int16_t x,int16_t y){if(code==0x180c)fprintf(stderr,"UI_STATUS_EVENT modifiers=%x point=%d,%d\n",mods,x,y);if(phase==3&&code==0x102){++hits;extern EnhancedRect map_viewport_rect;extern int16_t mapXsize,mapYsize;CHECK(x==map_viewport_rect.left+80*mapXsize+mapXsize/2&&y==map_viewport_rect.top+32*mapYsize+mapYsize/2);}return __real_portable_m1b73_try_enqueue_command(code,m,mods,x,y);}
extern int __real_native_windows_present(const HostPalette *);
int __wrap_native_windows_present(const HostPalette *palette){
 int result=__real_native_windows_present(palette);HWND status=named("Status");
 if(phase==7&&status&&IsWindowVisible(status)){
  phase=8;status_seen=1;
  /* This callback observes the first visible frame inside source win_Open.
   * A player cannot choose UI Scale from the disabled frame during that
   * transaction. Check the scale selected before opening the dialog. */
  fprintf(stderr,"UI_STATUS_CHECK_BEGIN\n");layout_checks(MulDiv(native_workspace_layout()->ui_scale,96,100));fprintf(stderr,"UI_STATUS_LAYOUT_DONE\n");save(status,"status-after");fprintf(stderr,"UI_STATUS_CAPTURE_DONE\n");
  HWND button=GetDlgItem(status,0x180c);CHECK(button);CHECK(IsWindowEnabled(status));CHECK(IsWindowEnabled(button));fprintf(stderr,"UI_STATUS owner=%x compat=%x objects=%u\n",(unsigned short)enhanced_snapshot()->dialogs.owner,(unsigned short)enhanced_compatibility_owner(),enhanced_snapshot()->dialogs.object_count);for(unsigned i=0;i<enhanced_snapshot()->dialogs.object_count;++i)if(enhanced_snapshot()->dialogs.objects[i].id==0x180c)fprintf(stderr,"UI_STATUS_OBJECT flags=%x type=%d\n",enhanced_snapshot()->dialogs.objects[i].flags,enhanced_snapshot()->dialogs.objects[i].type);RECT r;GetClientRect(button,&r);PostMessage(button,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(r.right/2,r.bottom/2));PostMessage(button,WM_LBUTTONUP,0,MAKELPARAM(r.right/2,r.bottom/2));started=main_iteration_count;
 }
 return result;
}
void __wrap_enhanced_source_poll(void){__real_enhanced_source_poll();static ULONGLONG last;if(GetTickCount64()-last>5000){last=GetTickCount64();fprintf(stderr,"UI_PROGRESS phase=%d iteration=%ld\n",phase,(long)main_iteration_count);}}
void __wrap_enhanced_execute_next(void){
 const EnhancedSnapshot *s=enhanced_snapshot();if(!s||!s->panels.world_ready){__real_enhanced_execute_next();return;}
 if(!phase&&main_iteration_count>2){root=named("SimAnt");CHECK(root);const char *persisted=getenv("SIMANT_UI_PERSISTED");
  if(persisted){CHECK(native_workspace_layout()->ui_scale==atoi(persisted));fprintf(stderr,"UI_PERSIST_RESULT {\"passed\":%s,\"scale\":%d}\n",failures?"false":"true",native_workspace_layout()->ui_scale);exit(failures?1:0);}
  CHECK(native_workspace_layout()->ui_scale==125);phase=1;started=main_iteration_count;
  const int events[]={0x10f,0x111,0x113,0x115,0xfd21};for(int i=0;i<5;++i)enhanced_submit_event(events[i],0,0,0);
 }
 if(phase==1&&main_iteration_count>started+1&&enhanced_action_ledger()->submitted==enhanced_action_ledger()->delivered&&!s->dialogs.modal){matrix();phase=2;
  SetForegroundWindow(root);SetFocus(root);UINT_PTR timer=0xe752;CHECK(SetTimer(root,timer,100,menu_tick));RECT at;GetWindowRect(root,&at);TrackPopupMenuEx(GetSubMenu(GetMenu(root),3),TPM_LEFTALIGN|TPM_TOPALIGN,at.left+200,at.top+50,root,NULL);KillTimer(root,timer);CHECK(menu_ticks>=3);enhanced_submit_event(0x106,0,0,0);started=main_iteration_count;phase=6;
 }
 if(phase==6&&main_iteration_count>started+4&&!s->dialogs.modal)phase=2;
 if(phase==2){static const int hit_scales[]={100,150,200,300};if(hit_case==4){native_workspace_set_ui_scale(200);phase=7;enhanced_submit_event(0x114,0,0,0);__real_enhanced_execute_next();return;}

  int old=hits;native_workspace_set_ui_scale(hit_scales[hit_case]);HWND map=named("Map");RECT r;GetClientRect(map,&r);phase=3;started=main_iteration_count;
  SendMessage(map,WM_LBUTTONDOWN,MK_LBUTTON,MAKELPARAM(r.right*5/8,r.bottom/2));SendMessage(map,WM_LBUTTONUP,0,MAKELPARAM(r.right*5/8,r.bottom/2));CHECK(hits==old);
 }
 if(phase==3&&main_iteration_count>started+4&&!s->dialogs.modal){CHECK(hits==hit_case+1);++hit_case;phase=2;}
 if(phase==8&&main_iteration_count>started+1&&!s->dialogs.modal&&!enhanced_action_lease_active()){
  CHECK(status_seen);fprintf(stderr,"UI_SCALE_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"hit_scales\":%d,\"matrix_dpi\":[96,120,144],\"work_areas\":[[1920,1040],[2560,1400]],\"persisted_scale\":200,\"status_first_frame\":true}\n",failures?"false":"true",checks,failures,hit_case);exit(failures?1:0);
 }
 __real_enhanced_execute_next();
}
