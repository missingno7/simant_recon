#include "source_control_integration.h"

#include "portable/game/simulation/setup.h"
#include "portable/game/recovered/session_bridge.h"

#include <string.h>
#include <setjmp.h>
#include <stdlib.h>

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
    int16_t unrelated_auto,unrelated_selector,unrelated_percent;
    uint16_t unrelated_current[3],unrelated_presets[12];
    int16_t unrelated_point[2];
    int reentrant_attempted,reentrant_status;
    int event_count;
    int32_t events[64][9];
} NativeResult;
typedef struct Fixture {
    NativeResult *out;
    SimSetupRect rect;
    SimSetupPoint samples[8];
    int sample_count,sample_at,still_calls;
    int fail_op,fail_nth,seen[11];
    int reentrant_enabled;
    int reentrant_attempted,reentrant_status;
    SimSetupControls *controls;
    SimControlEventPrivateState *private_state;
    SimSetupControlKind setup_kind;
    SimControlEventMessage message;
    SimControlEventProvider *provider;
    jmp_buf *outer_env;
    int outer_interrupt_op;
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
static void reenter_or_interrupt(Fixture *f,int op)
{
    if(f->outer_env!=NULL&&f->outer_interrupt_op==op)longjmp(*f->outer_env,1);
    if(f->reentrant_enabled&&!f->reentrant_attempted){
        f->reentrant_attempted=1;
        f->reentrant_status=sim_recovered_source_control_event(f->controls,
            f->private_state,f->setup_kind,&f->message,f->provider);
    }
}
static int clip(void *p,uint16_t id){Fixture*f=p;note(f,OP_CLIP,id,0,0,0,0,0,0,0);reenter_or_interrupt(f,OP_CLIP);return !fail(f,OP_CLIP);}
static int off(void *p){Fixture*f=p;note(f,OP_OFF,0,0,0,0,0,0,0,0);reenter_or_interrupt(f,OP_OFF);return !fail(f,OP_OFF);}
static int help(void *p,uint16_t id){Fixture*f=p;note(f,OP_HELP,id,0,0,0,0,0,0,0);reenter_or_interrupt(f,OP_HELP);return !fail(f,OP_HELP);}
static int group(void *p,uint16_t w,uint8_t g,int visible)
{Fixture*f=p;int op=visible?OP_SHOW:OP_HIDE;note(f,op,w,g,visible,0,0,0,0,0);reenter_or_interrupt(f,op);return !fail(f,op);}
static int select_object(void *p,uint16_t id)
{Fixture*f=p;note(f,OP_SELECT,id,0,0,0,0,0,0,0);reenter_or_interrupt(f,OP_SELECT);return !fail(f,OP_SELECT);}
static int get_rect(void *p,uint16_t id,SimSetupRect *r)
{Fixture*f=p;*r=f->rect;note(f,OP_GETRECT,id,r->left,r->top,r->right,r->bottom,0,0,0);reenter_or_interrupt(f,OP_GETRECT);return !fail(f,OP_GETRECT);}
static int draw(void *p,SimSetupControlKind kind,uint16_t flags,const SimSetupControls*c,int16_t percent)
{
    Fixture*f=p;const SimSetupTriangle*t=kind==SIM_SETUP_MODE_CONTROL?&c->mode_level:&c->caste_level;
    int16_t sel=kind==SIM_SETUP_MODE_CONTROL?c->mode_current:c->caste_current;
    int16_t automatic=kind==SIM_SETUP_MODE_CONTROL?c->mode_auto:c->caste_auto;
    note(f,OP_DRAW,kind,flags,percent,t->frac,t->mid,t->weight,sel,automatic);
    reenter_or_interrupt(f,OP_DRAW);
    return !fail(f,OP_DRAW);
}
static int poll(void *p,SimSetupPoint *point)
{
    Fixture*f=p;if(f->sample_at<f->sample_count)*point=f->samples[f->sample_at++];
    note(f,OP_POLL,point->x,point->y,0,0,0,0,0,0);reenter_or_interrupt(f,OP_POLL);return !fail(f,OP_POLL);
}
static int still(void *p,int *down)
{
    Fixture*f=p;++f->still_calls;*down=f->still_calls<f->sample_count;
    note(f,OP_STILL,*down,0,0,0,0,0,0,0);reenter_or_interrupt(f,OP_STILL);return !fail(f,OP_STILL);
}

int source_control_native_run(int kind,uint16_t code,int16_t start_auto,
    int16_t selector,int16_t percent,const int16_t rect[4],const uint16_t metrics[3],
    const int16_t initial[2],const int16_t point[2],const int16_t *samples,
    int sample_count,int fail_op,int fail_nth,uint16_t drag_cap,int reentrant,
    int outer_interrupt_op,NativeResult *out)
{
    RecoveredState *state=(RecoveredState *)calloc(1,sizeof *state);RecoveredBindingFrame binding;
    SimSetupControls controls;SimControlEventPrivateState private_state;
    SimControlEventMessage message;SimControlEventProvider provider;Fixture fixture;
    int i;
    if(out==NULL||rect==NULL||metrics==NULL||initial==NULL||point==NULL||!state||
       sample_count<0||sample_count>8||(!samples&&sample_count)||kind<0||kind>1)
        {free(state);return -1;}
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
    if(kind==0){
        controls.caste_auto=77;controls.caste_current=3;
        controls.caste_level=(SimSetupTriangle){0x1357,0x2468,0x369a};
        for(i=0;i<4;i++)controls.caste_levels[i]=(SimSetupTriangle){
            (uint16_t)(0xa100+i*3),(uint16_t)(0xa101+i*3),(uint16_t)(0xa102+i*3)};
        controls.caste_point=(SimSetupPoint){-123,321};private_state.caste_percent=77;
    }else{
        controls.mode_auto=66;controls.mode_current=2;
        controls.mode_level=(SimSetupTriangle){0x1020,0x3040,0x5060};
        for(i=0;i<4;i++)controls.mode_levels[i]=(SimSetupTriangle){
            (uint16_t)(0xb200+i*3),(uint16_t)(0xb201+i*3),(uint16_t)(0xb202+i*3)};
        controls.mode_point=(SimSetupPoint){-234,432};private_state.mode_percent=66;
    }
    recovered_state_init(state);
    state->ModeAuto=controls.mode_auto;state->CasteAuto=controls.caste_auto;
    memcpy(state->modeLevels,&controls.mode_level,6);memcpy(state->casteLevels,&controls.caste_level,6);
    memcpy(state->fd_3D57_0810,controls.mode_levels,sizeof state->fd_3D57_0810);
    memcpy(state->fd_3D57_07F2,controls.caste_levels,sizeof state->fd_3D57_07F2);
    memcpy(state->IdealCaste,controls.ideal_caste,sizeof controls.ideal_caste);
    state->triWidth=metrics[0];state->triHeight=metrics[1];state->triWidthL=metrics[2];
    state->fd_50F6_3816=(struct TriPoints){(int16_t)(rect[0]+(rect[2]-rect[0])/2),rect[1],rect[0],rect[3],rect[2],rect[3]};
    state->fd_50F6_3822=state->fd_50F6_3816;
    state->fd_50F6_0358=(struct Pt){point[0],point[1]};state->fd_50F6_022E=state->fd_50F6_0358;
    if(kind==0)state->fd_50F6_022E=(struct Pt){-123,321};
    else state->fd_50F6_0358=(struct Pt){-234,432};
    recovered_bind_begin(&binding,state);
    provider=(SimControlEventProvider){clip,off,help,group,select_object,get_rect,draw,poll,still,&fixture,drag_cap};
    message=(SimControlEventMessage){code,{initial[0],initial[1]}};
    fixture.controls=&controls;fixture.private_state=&private_state;
    fixture.setup_kind=kind?SIM_SETUP_CASTE_CONTROL:SIM_SETUP_MODE_CONTROL;
    fixture.message=message;fixture.provider=&provider;fixture.reentrant_enabled=reentrant;
    fixture.outer_interrupt_op=outer_interrupt_op;
    if(outer_interrupt_op){
        jmp_buf outer;fixture.outer_env=&outer;
        if(setjmp(outer)==0)
            out->status=sim_recovered_source_control_event(&controls,&private_state,
                fixture.setup_kind,&message,&provider);
        else{
            out->status=100;
            return 0;
        }
    }else out->status=sim_recovered_source_control_event(&controls,&private_state,
        fixture.setup_kind,&message,&provider);
    recovered_bind_end(&binding,state);
    if(kind==0){out->automatic=state->ModeAuto;out->selector=controls.mode_current;out->percent=private_state.mode_percent;
        memcpy(out->current,state->modeLevels,6);memcpy(out->presets,state->fd_3D57_0810,24);
        out->point[0]=state->fd_50F6_0358.x;out->point[1]=state->fd_50F6_0358.y;}
    else{out->automatic=state->CasteAuto;out->selector=controls.caste_current;out->percent=private_state.caste_percent;
        memcpy(out->current,state->casteLevels,6);memcpy(out->presets,state->fd_3D57_07F2,24);
        out->point[0]=state->fd_50F6_022E.x;out->point[1]=state->fd_50F6_022E.y;}
    memcpy(out->ideal_caste,state->IdealCaste,8);
    if(kind==0){out->unrelated_auto=controls.caste_auto;out->unrelated_selector=controls.caste_current;
        out->unrelated_percent=private_state.caste_percent;memcpy(out->unrelated_current,&controls.caste_level,6);
        memcpy(out->unrelated_presets,controls.caste_levels,24);out->unrelated_point[0]=controls.caste_point.x;out->unrelated_point[1]=controls.caste_point.y;}
    else{out->unrelated_auto=controls.mode_auto;out->unrelated_selector=controls.mode_current;
        out->unrelated_percent=private_state.mode_percent;memcpy(out->unrelated_current,&controls.mode_level,6);
        memcpy(out->unrelated_presets,controls.mode_levels,24);out->unrelated_point[0]=controls.mode_point.x;out->unrelated_point[1]=controls.mode_point.y;}
    out->reentrant_status=fixture.reentrant_status;out->reentrant_attempted=fixture.reentrant_attempted;
    free(state);
    return 0;
}
