#include "../../../build/workers/recovered_source_next5/generated/recovered_state.h"

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

int16_t NewGame(int16_t flag);
void SetDefaultWindows(void);

enum { EV_OPEN_CASTE = 1, EV_OPEN_MODE, EV_TITLE, EV_PLANE, EV_IS_OPEN,
       EV_YARD_TO_MAP, EV_MAP_TITLE, EV_OPEN_EDIT, EV_SCENARIO, EV_FILE,
       EV_END_LIFE, EV_END_TARGET, EV_WIND_PROMPT, EV_RAND_YARD,
       EV_PRINTF, EV_WIN_OPEN, EV_CONFIRM, EV_SAVE, EV_CENTER, EV_UPDATE };
static int16_t scenario_values[8], file_values[8];
static unsigned scenario_count, scenario_at, file_count, file_at;
static int16_t win_open_result, confirm_result, confirm_ax, zoom_ax;
static int16_t yard_plane, yard_x, yard_y;
static int16_t events[128][14];
static unsigned event_count;

static void event(int16_t id, int16_t a, int16_t b)
{ if (event_count < 128) {
    int16_t *e=events[event_count++];
    e[0]=id; e[1]=a; e[2]=b;
    e[3]=MapPlane; e[4]=MePlane; e[5]=MeLocX; e[6]=MeLocY;
    e[7]=fd_50F6_0EAC; e[8]=fd_50F6_105E; e[9]=fd_50F6_0354;
    e[10]=fd_50F6_07C8; e[11]=fd_3D57_07A4; e[12]=fd_3D57_07A6;
    e[13]=fd_3D57_02C2[0];
} }

void OpenCasteWindow(void) { event(EV_OPEN_CASTE,0,0); }
void OpenModeWindow(void) { event(EV_OPEN_MODE,0,0); }
void SetEditWinTitle(char *p) { event(EV_TITLE,p==NULL,0); }
void f_015B_053C(int16_t p) { event(EV_PLANE,p,0); }
int16_t win_IsWinOpen(int16_t w) { event(EV_IS_OPEN,w,win_open_result); return win_open_result; }
void YardToMap(void) { event(EV_YARD_TO_MAP,0,0); }
void SetMapTitle(void) { event(EV_MAP_TITLE,0,0); }
void OpenEditWindow(void) { event(EV_OPEN_EDIT,0,0); }
int16_t DoScenario(int16_t flag) { int16_t v=scenario_at<scenario_count?scenario_values[scenario_at++]:0x202; event(EV_SCENARIO,flag,v); return v; }
int16_t o09_35F5_0000(int16_t a,int16_t b) { int16_t v=file_at<file_count?file_values[file_at++]:1; (void)b; event(EV_FILE,a,v); return v; }
void EndLifeTransferMode(void) { event(EV_END_LIFE,0,0); }
void EndTargetMode(void) { event(EV_END_TARGET,0,0); }
void SetDefaultWindPrompt(int16_t v) { event(EV_WIND_PROMPT,v,0); }
void RandYard(void) { event(EV_RAND_YARD,yard_plane,yard_x); MePlane=yard_plane; MeLocX=yard_x; MeLocY=yard_y; }
int16_t WinPrintf(char *f, ...) { event(EV_PRINTF,f!=NULL,MePlane); return 0; }
void win_Open(int16_t w) { event(EV_WIN_OPEN,w,0); }
int16_t f_22BF_0A65(void) { event(EV_CONFIRM,confirm_ax,confirm_result); return confirm_result; }
void o26_39C7_0000(void) { event(EV_SAVE,zoom_ax,0); }
void CenterEdit(int x,int y) { event(EV_CENTER,x,y); }
void UpdateEdit(void) { event(EV_UPDATE,0,0); }

void *newgame_flow_state_create(void) { RecoveredState *s=(RecoveredState *)calloc(1,sizeof *s); if(s) recovered_state_init(s); return s; }
size_t newgame_flow_state_size(void) { return sizeof(RecoveredState); }
void newgame_flow_state_destroy(void *p) { free(p); }
void newgame_flow_state_set(void *p, unsigned field, int16_t value)
{
    RecoveredState *s=(RecoveredState *)p;
    switch(field) {
    case 0: s->MapPlane=value; break; case 1: s->MePlane=value; break;
    case 2: s->MeLocX=value; break; case 3: s->MeLocY=value; break;
    case 4: s->fd_50F6_0EAC=value; break; case 5: s->fd_50F6_105E=value; break;
    case 6: s->fd_50F6_0354=value; break; case 7: s->fd_50F6_07C8=value; break;
    case 8: s->fd_3D57_07A4=value; break; case 9: s->fd_3D57_07A6=value; break;
    case 10: s->fd_3D57_02C2[0]=value; break;
    default: break;
    }
}
int16_t newgame_flow_state_get(const void *p, unsigned field)
{
    const RecoveredState *s=(const RecoveredState *)p;
    switch(field) {
    case 0: return s->MapPlane; case 1: return s->MePlane;
    case 2: return s->MeLocX; case 3: return s->MeLocY;
    case 4: return s->fd_50F6_0EAC; case 5: return s->fd_50F6_105E;
    case 6: return s->fd_50F6_0354; case 7: return s->fd_50F6_07C8;
    case 8: return s->fd_3D57_07A4; case 9: return s->fd_3D57_07A6;
    case 10: return s->fd_3D57_02C2[0]; default: return 0;
    }
}
void newgame_flow_configure(const int16_t *scenarios,unsigned ns,const int16_t *files,unsigned nf,
                            int16_t opened,int16_t confirm,int16_t yp,int16_t yx,int16_t yy,
                            int16_t confirm_input,int16_t zoom_input)
{
    scenario_count=ns>8?8:ns; file_count=nf>8?8:nf;
    memcpy(scenario_values,scenarios,scenario_count*sizeof(int16_t));
    memcpy(file_values,files,file_count*sizeof(int16_t));
    scenario_at=file_at=event_count=0; win_open_result=opened; confirm_result=confirm;
    confirm_ax=confirm_input; zoom_ax=zoom_input;
    yard_plane=yp; yard_x=yx; yard_y=yy;
}
int16_t newgame_flow_run(void *p,int16_t flag)
{ RecoveredBindingFrame f; recovered_bind_begin(&f,(RecoveredState *)p); int r=NewGame(flag); recovered_bind_end(&f,(RecoveredState *)p); return r; }
int newgame_flow_setdefault(void *p)
{ RecoveredBindingFrame f; recovered_bind_begin(&f,(RecoveredState *)p); SetDefaultWindows(); recovered_bind_end(&f,(RecoveredState *)p); return 0; }
unsigned newgame_flow_event_count(void) { return event_count; }
void newgame_flow_events(int16_t *out) { memcpy(out,events,event_count*14*sizeof(int16_t)); }
