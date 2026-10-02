#include "../../../ui_model/windows/control_events.h"

#include <string.h>

enum { OP_CLIP=1, OP_OFF, OP_HELP, OP_HIDE, OP_SHOW, OP_SELECT,
       OP_GETRECT, OP_DRAW, OP_POLL, OP_STILL };
typedef struct AdapterContext {
    SimSetupRect rect;
    SimSetupPoint samples[8];
    int sample_count, sample_at;
    int events[64][9], op_count;
} AdapterContext;

static void note(AdapterContext *c, int op, int a, int b, int d, int e,
                 int f, int g, int h)
{
    if (c->op_count < (int)(sizeof c->events / sizeof c->events[0])) {
        int *row=c->events[c->op_count++];
        row[0]=op;row[1]=a;row[2]=b;row[3]=d;row[4]=e;
        row[5]=f;row[6]=g;row[7]=h;row[8]=0;
    }
}
static int clip(void *p, uint16_t id) { note(p,OP_CLIP,id,0,0,0,0,0,0); return 1; }
static int off(void *p) { note(p,OP_OFF,0,0,0,0,0,0,0); return 1; }
static int help(void *p, uint16_t id) { note(p,OP_HELP,id,0,0,0,0,0,0); return 1; }
static int group(void *p,uint16_t w,uint8_t g,int v)
{ note(p,v?OP_SHOW:OP_HIDE,w,g,v,0,0,0,0);return 1; }
static int select_object(void *p,uint16_t id) { note(p,OP_SELECT,id,0,0,0,0,0,0);return 1; }
static int get_rect(void *p,uint16_t id,SimSetupRect *r)
{ AdapterContext *c=p;*r=c->rect;note(c,OP_GETRECT,id,r->left,r->top,r->right,r->bottom,0,0);return 1; }
static int draw(void *p,SimSetupControlKind k,uint16_t f,
                const SimSetupControls *c,int16_t percent)
{ const SimSetupTriangle *v=k==SIM_SETUP_MODE_CONTROL?&c->mode_level:&c->caste_level;
  int16_t selector=k==SIM_SETUP_MODE_CONTROL?c->mode_current:c->caste_current;
  int16_t automatic=k==SIM_SETUP_MODE_CONTROL?c->mode_auto:c->caste_auto;
  note(p,OP_DRAW,k,f,percent,v->frac,v->mid,v->weight,selector);
  ((AdapterContext*)p)->events[((AdapterContext*)p)->op_count-1][8]=automatic;
  return 1; }
static int poll(void *p,SimSetupPoint *pt)
{ AdapterContext *c=p;if(c->sample_at<c->sample_count)*pt=c->samples[c->sample_at++];
  note(c,OP_POLL,pt->x,pt->y,0,0,0,0,0);return 1; }
static int still(void *p,int *down)
{ AdapterContext *c=p;*down=c->sample_at<c->sample_count;note(c,OP_STILL,*down,0,0,0,0,0,0);return 1; }

/* result: status, auto, selector, percent, current[3], presets[12],
 * ideal[4], point[2], op_count, events[64][9]. */
int control_event_native_run(int kind,int code,int start_auto,
    int start_selector,int start_percent,
    const int16_t rect[4],const uint16_t metrics[3],
    const int16_t initial_point[2],const int16_t control_point[2],
    const int16_t *samples,int sample_count,int32_t result[640])
{
    SimSetupControls c;
    SimControlEventPrivateState p;
    SimControlEventMessage m;
    SimControlEventProvider provider;
    AdapterContext context;
    SimSetupControlKind control_kind=(SimSetupControlKind)kind;
    SimSetupTriangle *level,*rows;
    int16_t *auto_flag,*selector;
    int at=0;
    memset(&c,0,sizeof c);memset(&context,0,sizeof context);
    p=(SimControlEventPrivateState){1,1,metrics[0],metrics[1],metrics[2]};
    sim_setup_controls_init_data(&c);
    context.rect=(SimSetupRect){rect[0],rect[1],rect[2],rect[3]};
    if(sample_count<0||sample_count>8)return -1;
    context.sample_count=sample_count;
    for(int i=0;i<sample_count;i++)context.samples[i]=(SimSetupPoint){samples[2*i],samples[2*i+1]};
    c.mode_auto=c.caste_auto=1;
    c.mode_current=c.caste_current=0;
    c.mode_level=c.mode_levels[0];c.caste_level=c.caste_levels[0];
    c.mode_rect=c.caste_rect=context.rect;
    c.mode_point=c.caste_point=(SimSetupPoint){control_point[0],control_point[1]};
    sim_setup_convert_ideal_caste(&c.caste_level,c.ideal_caste);
    if(start_auto>=0){if(control_kind==SIM_SETUP_MODE_CONTROL)c.mode_auto=(int16_t)start_auto;else c.caste_auto=(int16_t)start_auto;}
    if(control_kind==SIM_SETUP_MODE_CONTROL){c.mode_current=(int16_t)start_selector;p.mode_percent=(int16_t)start_percent;}
    else{c.caste_current=(int16_t)start_selector;p.caste_percent=(int16_t)start_percent;}
    m.code=(uint16_t)code;m.point=(SimSetupPoint){initial_point[0],initial_point[1]};
    provider=(SimControlEventProvider){clip,off,help,group,select_object,get_rect,
        draw,poll,still,&context,0};
    result[at++]=sim_control_process_event(&c,&p,control_kind,&m,&provider);
    auto_flag=control_kind==SIM_SETUP_MODE_CONTROL?&c.mode_auto:&c.caste_auto;
    selector=control_kind==SIM_SETUP_MODE_CONTROL?&c.mode_current:&c.caste_current;
    level=control_kind==SIM_SETUP_MODE_CONTROL?&c.mode_level:&c.caste_level;
    rows=control_kind==SIM_SETUP_MODE_CONTROL?c.mode_levels:c.caste_levels;
    result[at++]=*auto_flag;result[at++]=*selector;
    result[at++]=control_kind==SIM_SETUP_MODE_CONTROL?p.mode_percent:p.caste_percent;
    result[at++]=level->frac;result[at++]=level->mid;result[at++]=level->weight;
    for(int i=0;i<4;i++){result[at++]=rows[i].frac;result[at++]=rows[i].mid;result[at++]=rows[i].weight;}
    for(int i=0;i<4;i++)result[at++]=c.ideal_caste[i];
    {SimSetupPoint pt=control_kind==SIM_SETUP_MODE_CONTROL?c.mode_point:c.caste_point;result[at++]=pt.x;result[at++]=pt.y;}
    result[at++]=context.op_count;
    for(int i=0;i<context.op_count;i++)for(int j=0;j<9;j++)result[at++]=context.events[i][j];
    return at;
}
