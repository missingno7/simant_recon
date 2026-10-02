#include "source_control_integration.h"

#include "portable/game/simulation/setup.h"
#include "portable/game/recovered/session_bridge.h"

#include <string.h>

enum { OP_CLIP=1,OP_OFF,OP_HELP,OP_HIDE,OP_SHOW,OP_SELECT,OP_GETRECT,OP_DRAW,OP_POLL,OP_STILL };
/* Satisfy only unselected functions in the shared Next10 root:m0798 object;
 * the event fixture never calls these startup/resource leaves. */
void win_GetObjRect(int16_t id,struct Rect *rect){(void)id;(void)rect;}
void hanim_RemoveAnimSet(void *handle){(void)handle;}
void f_208F_0419(struct Pt *size,int16_t id){(void)size;(void)id;}
typedef struct NativeResult {
    int32_t status;
    int16_t automatic,selector,percent;
    uint16_t current[3],presets[12];
    int16_t ideal_caste[4],point[2];
    int event_count;
    int32_t events[64][9];
} NativeResult;
typedef struct Fixture {
    NativeResult *out;
    SimSetupRect rect;
    SimSetupPoint samples[8];
    int sample_count,sample_at,still_calls;
    int fail_op,fail_nth,seen[11];
} Fixture;

static void note(Fixture *f,int op,int a,int b,int c,int d,int e,int g,int h,int i)
{
    int32_t *r;
    if(f->out->event_count>=64)return;
    r=f->out->events[f->out->event_count++];
    r[0]=op;r[1]=a;r[2]=b;r[3]=c;r[4]=d;r[5]=e;r[6]=g;r[7]=h;r[8]=i;
}
static int fail(Fixture *f,int op)
{ return f->fail_op==op && ++f->seen[op]==f->fail_nth; }
static int clip(void *p,uint16_t id){Fixture*f=p;note(f,OP_CLIP,id,0,0,0,0,0,0,0);return !fail(f,OP_CLIP);}
static int off(void *p){Fixture*f=p;note(f,OP_OFF,0,0,0,0,0,0,0,0);return !fail(f,OP_OFF);}
static int help(void *p,uint16_t id){Fixture*f=p;note(f,OP_HELP,id,0,0,0,0,0,0,0);return !fail(f,OP_HELP);}
static int group(void *p,uint16_t w,uint8_t g,int visible)
{Fixture*f=p;int op=visible?OP_SHOW:OP_HIDE;note(f,op,w,g,visible,0,0,0,0,0);return !fail(f,op);}
static int select_object(void *p,uint16_t id)
{Fixture*f=p;note(f,OP_SELECT,id,0,0,0,0,0,0,0);return !fail(f,OP_SELECT);}
static int get_rect(void *p,uint16_t id,SimSetupRect *r)
{Fixture*f=p;*r=f->rect;note(f,OP_GETRECT,id,r->left,r->top,r->right,r->bottom,0,0,0);return !fail(f,OP_GETRECT);}
static int draw(void *p,SimSetupControlKind kind,uint16_t flags,const SimSetupControls*c,int16_t percent)
{
    Fixture*f=p;const SimSetupTriangle*t=kind==SIM_SETUP_MODE_CONTROL?&c->mode_level:&c->caste_level;
    int16_t sel=kind==SIM_SETUP_MODE_CONTROL?c->mode_current:c->caste_current;
    int16_t automatic=kind==SIM_SETUP_MODE_CONTROL?c->mode_auto:c->caste_auto;
    note(f,OP_DRAW,kind,flags,percent,t->frac,t->mid,t->weight,sel,automatic);
    return !fail(f,OP_DRAW);
}
static int poll(void *p,SimSetupPoint *point)
{
    Fixture*f=p;if(f->sample_at<f->sample_count)*point=f->samples[f->sample_at++];
    note(f,OP_POLL,point->x,point->y,0,0,0,0,0,0);return !fail(f,OP_POLL);
}
static int still(void *p,int *down)
{
    Fixture*f=p;++f->still_calls;*down=f->still_calls<f->sample_count;
    note(f,OP_STILL,*down,0,0,0,0,0,0,0);return !fail(f,OP_STILL);
}

int source_control_native_run(int kind,uint16_t code,int16_t start_auto,
    int16_t selector,int16_t percent,const int16_t rect[4],const uint16_t metrics[3],
    const int16_t initial[2],const int16_t point[2],const int16_t *samples,
    int sample_count,int fail_op,int fail_nth,NativeResult *out)
{
    RecoveredState state;RecoveredBindingFrame binding;
    SimSetupControls controls;SimControlEventPrivateState private_state;
    SimControlEventMessage message;SimControlEventProvider provider;Fixture fixture;
    int i;
    if(out==NULL||rect==NULL||metrics==NULL||initial==NULL||point==NULL||
       sample_count<0||sample_count>8||(!samples&&sample_count)||kind<0||kind>1)
        return -1;
    memset(out,0,sizeof *out);memset(&fixture,0,sizeof fixture);
    fixture.out=out;fixture.rect=(SimSetupRect){rect[0],rect[1],rect[2],rect[3]};
    fixture.sample_count=sample_count;fixture.fail_op=fail_op;fixture.fail_nth=fail_nth;
    for(i=0;i<sample_count;i++)fixture.samples[i]=(SimSetupPoint){samples[2*i],samples[2*i+1]};
    memset(&controls,0,sizeof controls);sim_setup_controls_init_data(&controls);
    controls.mode_level=controls.mode_defaults;controls.caste_level=controls.caste_defaults;
    controls.mode_auto=controls.caste_auto=1;
    controls.mode_current=controls.caste_current=0;
    controls.mode_rect=controls.caste_rect=fixture.rect;
    controls.mode_point=controls.caste_point=(SimSetupPoint){point[0],point[1]};
    memcpy(controls.ideal_caste,(int16_t[4]){60,40,0,0},sizeof controls.ideal_caste);
    if(kind==0){controls.mode_current=selector;if(start_auto>=0)controls.mode_auto=start_auto;}
    else{controls.caste_current=selector;if(start_auto>=0)controls.caste_auto=start_auto;}
    private_state=(SimControlEventPrivateState){1,1,metrics[0],metrics[1],metrics[2]};
    if(kind==0)private_state.mode_percent=percent;else private_state.caste_percent=percent;
    recovered_state_init(&state);
    state.ModeAuto=controls.mode_auto;state.CasteAuto=controls.caste_auto;
    memcpy(state.modeLevels,&controls.mode_level,6);memcpy(state.casteLevels,&controls.caste_level,6);
    memcpy(state.fd_3D57_0810,controls.mode_levels,sizeof state.fd_3D57_0810);
    memcpy(state.fd_3D57_07F2,controls.caste_levels,sizeof state.fd_3D57_07F2);
    memcpy(state.IdealCaste,controls.ideal_caste,sizeof controls.ideal_caste);
    state.triWidth=metrics[0];state.triHeight=metrics[1];state.triWidthL=metrics[2];
    state.fd_50F6_3816=(struct TriPoints){(int16_t)(rect[0]+(rect[2]-rect[0])/2),rect[1],rect[0],rect[3],rect[2],rect[3]};
    state.fd_50F6_3822=state.fd_50F6_3816;
    state.fd_50F6_0358=(struct Pt){point[0],point[1]};state.fd_50F6_022E=state.fd_50F6_0358;
    recovered_bind_begin(&binding,&state);
    provider=(SimControlEventProvider){clip,off,help,group,select_object,get_rect,draw,poll,still,&fixture,4096};
    message=(SimControlEventMessage){code,{initial[0],initial[1]}};
    out->status=sim_recovered_source_control_event(&controls,&private_state,
        kind?SIM_SETUP_CASTE_CONTROL:SIM_SETUP_MODE_CONTROL,&message,&provider);
    recovered_bind_end(&binding,&state);
    if(kind==0){out->automatic=state.ModeAuto;out->selector=controls.mode_current;out->percent=private_state.mode_percent;
        memcpy(out->current,state.modeLevels,6);memcpy(out->presets,state.fd_3D57_0810,24);
        out->point[0]=state.fd_50F6_0358.x;out->point[1]=state.fd_50F6_0358.y;}
    else{out->automatic=state.CasteAuto;out->selector=controls.caste_current;out->percent=private_state.caste_percent;
        memcpy(out->current,state.casteLevels,6);memcpy(out->presets,state.fd_3D57_07F2,24);
        out->point[0]=state.fd_50F6_022E.x;out->point[1]=state.fd_50F6_022E.y;}
    memcpy(out->ideal_caste,state.IdealCaste,8);return 0;
}
