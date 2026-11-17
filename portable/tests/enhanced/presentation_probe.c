/* Owner regressions: source lifecycle, first show, masked art and typed inputs. */
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/assets.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/platform/m1b73_event_enqueue.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/platform/window_hosting.h"
#include <windows.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern int32_t main_iteration_count;
extern int __real_native_windows_present(const HostPalette *);
extern void __real_enhanced_execute_next(void),__real_enhanced_source_poll(void);
static int checks,failures,phase,started,frames,shown[2],startup_seen[4],mask_count,art_count,numeric_step,delivered,received;
static const char *test;
static HostPalette palette;
static uint16_t expected[3],previous[3];
static int want_owner,want_axis,want_percent;
static uint64_t submitted;
static int slow_draws;
#define CHECK(x) do{++checks;if(!(x)){++failures;fprintf(stderr,"PRESENT_FAIL %d %s\n",__LINE__,#x);}}while(0)
static HWND named(const char *s){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid!=GetCurrentProcessId())continue;char title[160];GetWindowTextA(h,title,sizeof(title));if(!strcmp(title,s)&&(!strcmp(s,"SimAnt")?GetMenu(h)!=NULL:1))return h;}return NULL;}
static int is(const char *s){return test&&!strcmp(test,s);}
static void finish(void){fprintf(stderr,"PRESENT_RESULT {\"passed\":%s,\"checks\":%d,\"failures\":%d,\"frames\":%d,\"art\":%d,\"masked_pixels\":%d,\"numeric_inputs\":%d,\"delivered\":%d,\"first_behavior\":%d,\"first_caste\":%d}\n",failures?"false":"true",checks,failures,frames,art_count,mask_count,numeric_step,delivered,shown[0],shown[1]);exit(failures?1:0);}
static void save_window(HWND h,const char *name){
    char path[2400];snprintf(path,sizeof(path),"%s/%s.bmp",getenv("SIMANT_PRESENT_OUT"),name);
    RECT r;GetWindowRect(h,&r);int w=r.right-r.left,he=r.bottom-r.top;
    BITMAPINFO info={.bmiHeader={sizeof(BITMAPINFOHEADER),w,-he,1,32,BI_RGB}};void *pixels=NULL;
    HDC dc=CreateCompatibleDC(NULL);HBITMAP bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,&pixels,NULL,0);HGDIOBJ old=SelectObject(dc,bitmap);
    int state=SaveDC(dc);CHECK(PrintWindow(h,dc,0));RestoreDC(dc,state);
    state=SaveDC(dc);if(!native_workspace_content_paint(h,dc,1))CHECK(native_windows_capture_client(h,dc));RestoreDC(dc,state);GdiFlush();
    RECT client;GetClientRect(h,&client);POINT origin={0,0};ClientToScreen(h,&origin);int ox=origin.x-r.left,oy=origin.y-r.top;
    uint32_t first=((uint32_t *)pixels)[oy*w+ox];int different=0;
    for(int y=oy;y<oy+client.bottom;++y)for(int x=ox;x<ox+client.right;++x)different+=(((uint32_t *)pixels)[y*w+x]&0xffffff)!=(first&0xffffff);
    CHECK(different>100);
    if(strstr(name,"behavior-")||strstr(name,"caste-"))for(int i=0;i<3;++i){
        int ink=0;
        for(int y=46+i*20;y<64+i*20;++y)for(int x=6;x<40;++x){uint32_t pixel=((uint32_t *)pixels)[(oy+y*client.bottom/170)*w+ox+x*client.right/210];ink+=((pixel>>16)&255)<100&&((pixel>>8)&255)<100&&(pixel&255)<100;}
        CHECK(ink>5);
    }
    BITMAPFILEHEADER header={.bfType=0x4d42,.bfSize=54+w*he*4,.bfOffBits=54};FILE *f=fopen(path,"wb");CHECK(f!=NULL);
    if(f){fwrite(&header,1,sizeof(header),f);fwrite(&info.bmiHeader,1,40,f);fwrite(pixels,1,w*he*4,f);fclose(f);}SelectObject(dc,old);DeleteObject(bitmap);DeleteDC(dc);
}
static void first_controls(int which,HWND h){
    const EnhancedSnapshot *s=enhanced_snapshot();const EnhancedAllocationSnapshot *a=which?&s->panels.caste:&s->panels.behavior;int base=which?0x1300:0x1200;
    CHECK(s->panels.world_ready);CHECK(main_iteration_count<5||is("reopen"));
    for(int i=0;i<6;++i){HWND child=GetDlgItem(h,base+3+i);CHECK(child!=NULL);CHECK(!!IsWindowVisible(child)==!!(a->control_flags[i]&1));CHECK(!!IsWindowEnabled(child)==!!(a->control_flags[i]&2));CHECK((SendMessage(child,BM_GETCHECK,0,0)==BST_CHECKED)==!!(a->control_flags[i]&4));}
    const uint16_t values[]={a->frac,a->mid,a->weight};
    for(int i=0;i<3;++i){HWND edit=GetDlgItem(h,0xe520+i);char text[32],cls[32];GetClassNameA(edit,cls,sizeof(cls));GetWindowTextA(edit,text,sizeof(text));CHECK(!lstrcmpiA(cls,"EDIT"));CHECK(text[0]);CHECK(atoi(text)==(values[i]*100u+0x3fff)/65535);CHECK(!(GetWindowLong(edit,GWL_STYLE)&ES_READONLY));}
    save_window(h,which?(shown[which]?"caste-reopened":"caste-first"):(shown[which]?"behavior-reopened":"behavior-first"));++shown[which];
}
static void art_masks(void){
    enum{W=1030,H=1030};BITMAPINFO info={.bmiHeader={sizeof(BITMAPINFOHEADER),W,-H,1,32,BI_RGB}};uint32_t *pixels;
    HDC dc=CreateCompatibleDC(NULL);HBITMAP bmp=CreateDIBSection(dc,&info,DIB_RGB_COLORS,(void **)&pixels,NULL,0);HGDIOBJ old=SelectObject(dc,bmp);
    FILE *in=fopen(getenv("SIMANT_PRESENT_ART"),"r");int id;CHECK(in!=NULL);if(!in)abort();
    while(fscanf(in,"%d",&id)==1){const EnhancedArt *a=enhanced_art(id);CHECK(a!=NULL);if(!a)continue;
        for(int i=0;i<W*H;++i)pixels[i]=0x17354b;
        CHECK(native_workspace_art_paint(dc,id,2,2));GdiFlush();++art_count;
        int errors=0;
        for(int y=0;y<a->height;++y)for(int x=0;x<a->width;++x){unsigned value=a->pixels[y*a->width+x];uint32_t expected_pixel=0x17354b;
            if(value==255)++mask_count;else {const uint8_t *rgb=palette.rgb[value&15];expected_pixel=(rgb[0]<<16)|(rgb[1]<<8)|rgb[2];}
            errors+=(pixels[(y+2)*W+x+2]&0xffffff)!=expected_pixel;
        }
        CHECK(errors==0);CHECK(pixels[0]==0x17354b);
    }
    fclose(in);CHECK(art_count==252);CHECK(mask_count>0);SelectObject(dc,old);DeleteObject(bmp);DeleteDC(dc);
}
static LRESULT CALLBACK slow_paint(HWND h,UINT message,WPARAM wp,LPARAM lp,UINT_PTR id,DWORD_PTR data){
    (void)id;(void)data;if(message==WM_DRAWITEM&&((DRAWITEMSTRUCT *)lp)->CtlID==5){++slow_draws;Sleep(80);}
    return DefSubclassProc(h,message,wp,lp);
}
static void paint_cadence(void){
    HWND h=named("Map / Ant Control Panel");CHECK(h!=NULL);SetWindowSubclass(h,slow_paint,88,0);
    EnhancedSnapshot before=*enhanced_snapshot();Sleep(60);native_workspace_present(&palette);CHECK(slow_draws==1);
    native_workspace_present(&palette);CHECK(slow_draws==1);CHECK(!memcmp(&before,enhanced_snapshot(),sizeof(before)));
    RemoveWindowSubclass(h,slow_paint,88);fprintf(stderr,"SLOW_PAINT draws=%d delay_ms=80 immediate_repaint=0\n",slow_draws);
}
typedef struct {int16_t ax,ay,lx,ly,rx,ry;} Verts;
extern Verts modeVerts,casteVerts;
extern int16_t IsPointInIsoTri(EnhancedPoint *,EnhancedRect *);
extern void BoundPointToTri(EnhancedPoint *,EnhancedRect *),GetTriLatDist(uint16_t *,Verts *,EnhancedPoint *);
extern int __real_portable_m1b73_try_enqueue_command(int16_t,int16_t,int16_t,int16_t,int16_t);
int __wrap_portable_m1b73_try_enqueue_command(int16_t code,int16_t message,int16_t mods,int16_t h,int16_t v){
    if(is("numeric")&&phase==3&&code==want_owner+13){
        ++received;EnhancedPoint point={h,v};GetTriLatDist(expected,want_owner==0x1200?&modeVerts:&casteVerts,&point);
        const SimWindowRefEntry *entry=&sim_window_ref_registry.entries[(unsigned)want_owner>>8];EnhancedRect r;memcpy(&r,entry->view.object_table[13],8);
        unsigned target_error=abs((int)((expected[want_axis]*100u+0x3fff)/65535)-want_percent),minimum=100;uint32_t best=UINT32_MAX,actual_distance=0;
        for(int i=0;i<3;++i)actual_distance+=abs((int)expected[i]-previous[i]);
        for(int y=r.top;y<r.bottom;++y)for(int x=r.left;x<r.right;++x){EnhancedPoint p={x,y};if(!IsPointInIsoTri(&p,&r))continue;BoundPointToTri(&p,&r);uint16_t levels[3];GetTriLatDist(levels,want_owner==0x1200?&modeVerts:&casteVerts,&p);unsigned e=abs((int)((levels[want_axis]*100u+0x3fff)/65535)-want_percent);uint32_t dist=0;for(int i=0;i<3;++i)dist+=abs((int)levels[i]-previous[i]);if(e<minimum){minimum=e;best=dist;}else if(e==minimum&&dist<best)best=dist;}
        CHECK(target_error==minimum);CHECK(actual_distance==best);
    }
    return __real_portable_m1b73_try_enqueue_command(code,message,mods,h,v);
}
static const char *inputs[]={"37","72","-5","120","bad","","19%","100","0","999999999999","51x"," 42 "};
static void numeric_begin(void){
    int owner=(numeric_step/36)?0x1300:0x1200,axis=(numeric_step/12)%3,at=numeric_step%12;want_owner=owner;want_axis=axis;
    const EnhancedAllocationSnapshot *a=owner==0x1200?&enhanced_snapshot()->panels.behavior:&enhanced_snapshot()->panels.caste;
    previous[0]=a->frac;previous[1]=a->mid;previous[2]=a->weight;memcpy(expected,previous,6);
    want_percent=at==2?0:at==3||at==9?100:at==6?19:atoi(inputs[at]);
    submitted=enhanced_action_ledger()->submitted;received=0;HWND window=named(owner==0x1200?"Behavior Control":"Caste Control"),edit=GetDlgItem(window,0xe520+axis);SetFocus(edit);SetWindowTextA(edit,inputs[at]);
    if(at&1)SetFocus(window);else SendMessage(edit,WM_KEYDOWN,VK_RETURN,0);
    started=main_iteration_count;phase=3;
}
int __wrap_native_windows_present(const HostPalette *p){
    int result=__real_native_windows_present(p);palette=*p;++frames;if(!test)test=getenv("SIMANT_PRESENT_CASE");
    if(!test)return result;
    const EnhancedSnapshot *s=enhanced_snapshot();
    if(is("startup")||is("startup-tutorial")||is("startup-load")){
        const char *names[]={"SimAnt - Game","Map / Ant Control Panel","Yard Control Panel","Map","Yard","Behavior Control","Caste Control","History","Info","Status"};
        if(!enhanced_game_ready())for(unsigned i=0;i<sizeof(names)/sizeof(names[0]);++i){HWND h=named(names[i]);CHECK(!h||!IsWindowVisible(h));}
        for(unsigned i=0;i<sim_window_hosting_count();++i){SimHostedWindowView view;if(!sim_window_hosting_view(i,&view)||!view.open)continue;int slot=view.id==0x300?0:view.id==0x1e00?1:view.id==0x200?2:view.id==0x1600?3:-1;
            if(slot>=0&&!startup_seen[slot]){HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,NULL))){DWORD pid;GetWindowThreadProcessId(h,&pid);char cls[64];GetClassNameA(h,cls,sizeof(cls));if(pid==GetCurrentProcessId()&&IsWindowVisible(h)&&!strcmp(cls,"SDL_app")&&h!=named("SimAnt")){startup_seen[slot]=1;save_window(h,slot==0?"title":slot==1?"registration":slot==2?"game-choice":"load-choice");break;}}}
        }
        if(is("startup-load")&&startup_seen[3]){CHECK(startup_seen[0]&&startup_seen[1]&&startup_seen[2]);CHECK(!enhanced_game_ready());finish();}
        if(!is("startup-load")&&s&&s->panels.world_ready&&IsWindowVisible(named("SimAnt - Game"))){CHECK(startup_seen[0]&&startup_seen[1]&&startup_seen[2]);finish();}
    }
    if(is("first-frame")||is("reopen"))for(int which=0;which<2;++which){HWND h=named(which?"Caste Control":"Behavior Control");if(h&&IsWindowVisible(h)&&((phase==0&&shown[which]==0)||(phase==2&&shown[which]==1)))first_controls(which,h);}
    if(is("first-frame")&&shown[0]&&shown[1])finish();
    return result;
}
void __wrap_enhanced_source_poll(void){__real_enhanced_source_poll();}
void __wrap_enhanced_execute_next(void){
    if(!test)test=getenv("SIMANT_PRESENT_CASE");const EnhancedSnapshot *s=enhanced_snapshot();
    if(!s||!s->panels.world_ready){__real_enhanced_execute_next();return;}
    if(is("reopen")){
        if(!phase&&shown[0]&&shown[1]&&main_iteration_count>10){phase=1;SendMessage(named("Behavior Control"),WM_CLOSE,0,0);SendMessage(named("Caste Control"),WM_CLOSE,0,0);started=main_iteration_count;}
        if(phase==1&&main_iteration_count>started+8){phase=2;enhanced_submit_event(0x10f,0,0,0);enhanced_submit_event(0x111,0,0,0);}
        if(phase==2&&shown[0]==2&&shown[1]==2)finish();
    }
    if(is("icons")||is("numeric")||is("slow-paint")){
        if(!phase&&main_iteration_count>20){phase=1;enhanced_submit_event(15,0,0,0);enhanced_submit_event(8,0,0,0);enhanced_submit_event(0x106,0,0,0);enhanced_submit_event(12,0,0,0);started=main_iteration_count;}
        if(phase==1&&main_iteration_count>started+16&&s->panels.paused&&!s->dialogs.modal){phase=2;
            if(is("slow-paint")){paint_cadence();finish();}
            if(is("icons")){CHECK(s->world.spider_on&&s->world.plane==1&&s->overview.map_mode==1);art_masks();save_window(named("Map"),"map-spider");finish();}
            numeric_begin();
        }
        if(is("numeric")&&phase==3&&main_iteration_count>started+8&&!s->dialogs.modal){
            int at=numeric_step%12,valid=at!=4&&at!=5&&at!=10;
            const EnhancedAllocationSnapshot *a=want_owner==0x1200?&s->panels.behavior:&s->panels.caste;uint16_t levels[]={a->frac,a->mid,a->weight};
            CHECK(received==valid);CHECK(enhanced_action_ledger()->submitted==submitted+valid);CHECK(!memcmp(levels,expected,6));
            if(valid){++delivered;CHECK(!a->automatic);extern uint16_t modeSetLevels[],casteSetLevels[];CHECK(!memcmp((want_owner==0x1200?modeSetLevels:casteSetLevels)+a->preset*3,levels,6));
                if(want_owner==0x1300){extern int16_t IdealCaste[4];CHECK(IdealCaste[0]==(levels[1]*100u+0x3fff)/65535);CHECK(IdealCaste[1]==(levels[2]*100u+0x3fff)/65535);CHECK(IdealCaste[2]==(levels[0]*50u+0x3fff)/65535);CHECK(IdealCaste[3]==IdealCaste[2]);}
            }
            for(int i=0;i<3;++i){char text[32];GetWindowTextA(GetDlgItem(named(want_owner==0x1200?"Behavior Control":"Caste Control"),0xe520+i),text,sizeof(text));CHECK(atoi(text)==(levels[i]*100u+0x3fff)/65535);}
            if(++numeric_step==72)finish();numeric_begin();
        }
    }
    __real_enhanced_execute_next();
}
