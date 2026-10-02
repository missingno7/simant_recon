/* Draft bridge from source-extracted m0798 handlers into the active Next10
 * TLS image and existing portable host providers. Not in production build. */
#include "source_control_integration.h"

#include <setjmp.h>
#include <string.h>

typedef struct SourceControlFrame {
    SimSetupControls *controls;
    SimControlEventPrivateState *private_state;
    SimSetupControlKind kind;
    const SimControlEventProvider *provider;
    jmp_buf local_abort;
    SimControlEventStatus failure;
    uint32_t drag_samples;
    uint16_t drag_cap;
} SourceControlFrame;

static _Thread_local SourceControlFrame *active_frame;
static _Thread_local SourceControlFrame frame_storage;
_Thread_local int16_t *source_mode_selector;
_Thread_local int16_t *source_caste_selector;
_Thread_local int16_t *source_mode_percent;
_Thread_local int16_t *source_caste_percent;

extern void SetTriLatPoint(uint16_t *level, struct TriPoints *tri,
                           struct Pt *point);
extern void cvtLevels2IdealCaste(int16_t *ideal);
extern _Thread_local uint16_t casteLevels[3];

typedef struct SourceTriLevelWords { uint16_t frac, mid, weight; } SourceTriLevelWords;
_Static_assert(sizeof(SourceTriLevelWords) == 6, "source triple is three words");
_Static_assert(sizeof(struct Pt) == sizeof(SimSetupPoint), "source/UI point layout");
_Static_assert(sizeof(struct Rect) == sizeof(SimSetupRect), "source/UI rect layout");
_Static_assert(sizeof(((RecoveredState *)0)->fd_3D57_0810) == 24,
               "four flat mode preset triples");
_Static_assert(sizeof(((RecoveredState *)0)->fd_3D57_07F2) == 24,
               "four flat caste preset triples");

static void source_fail(SimControlEventStatus status)
{
    SourceControlFrame *frame=active_frame;
    if (frame == NULL) return;
    frame->failure=status;
    longjmp(frame->local_abort,1);
}

static void source_publish_controls(void)
{
    SourceControlFrame *f=active_frame;
    SimSetupControls *c;
    if(f==NULL)return;
    c=f->controls;
    if(f->kind==SIM_SETUP_MODE_CONTROL){
        c->mode_auto=ModeAuto;c->mode_current=*source_mode_selector;
        memcpy(&c->mode_level,modeLevels,sizeof c->mode_level);
        memcpy(c->mode_levels,fd_3D57_0810,sizeof c->mode_levels);
        c->mode_point=(SimSetupPoint){fd_50F6_0358.x,fd_50F6_0358.y};
    }else{
        c->caste_auto=CasteAuto;c->caste_current=*source_caste_selector;
        memcpy(&c->caste_level,casteLevels,sizeof c->caste_level);
        memcpy(c->caste_levels,fd_3D57_07F2,sizeof c->caste_levels);
        memcpy(c->ideal_caste,IdealCaste,sizeof c->ideal_caste);
        c->caste_point=(SimSetupPoint){fd_50F6_022E.x,fd_50F6_022E.y};
    }
}

void source_clip_set(int16_t window_id)
{
    source_publish_controls();
    if(active_frame->provider->clip_set_window==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->clip_set_window(active_frame->provider->context,
                                                (uint16_t)window_id))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_clip_off(void)
{
    source_publish_controls();
    if(active_frame->provider->clip_off==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->clip_off(active_frame->provider->context))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_help(int16_t help_context)
{
    source_publish_controls();
    if(active_frame->provider->help==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->help(active_frame->provider->context,
                                     (uint16_t)help_context))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_group_invisible(int16_t window_id,int16_t group_id)
{
    source_publish_controls();
    if(active_frame->provider->set_group_visible==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->set_group_visible(active_frame->provider->context,
             (uint16_t)window_id,(uint8_t)group_id,0))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_group_visible(int16_t window_id,int16_t group_id)
{
    source_publish_controls();
    if(active_frame->provider->set_group_visible==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->set_group_visible(active_frame->provider->context,
             (uint16_t)window_id,(uint8_t)group_id,1))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_select_object(int16_t object_id)
{
    source_publish_controls();
    if(active_frame->provider->select_object==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->select_object(active_frame->provider->context,
                                              (uint16_t)object_id))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_get_rect(int16_t object_id,struct Rect *rect)
{
    SimSetupRect r;
    source_publish_controls();
    if(active_frame->provider->get_object_rect==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->get_object_rect(active_frame->provider->context,
                                               (uint16_t)object_id,&r))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
    rect->left=r.left;rect->top=r.top;rect->right=r.right;rect->bottom=r.bottom;
}

static void source_draw(int16_t flags,SimSetupControlKind kind)
{
    SimSetupControls *c;
    uint16_t *levels;
    struct TriPoints *tri;
    struct Pt *point;
    int16_t percent;
    if(active_frame==NULL)source_fail(SIM_CONTROL_EVENT_BAD_ARGUMENT);
    c=active_frame->controls;
    if(kind==SIM_SETUP_MODE_CONTROL){levels=modeLevels;tri=&fd_50F6_3816;
        point=&fd_50F6_0358;percent=*source_mode_percent;}
    else{levels=casteLevels;tri=&fd_50F6_3822;point=&fd_50F6_022E;
        percent=*source_caste_percent;}
    /* Original DrawControlLevels first recomputes the point with this compiled
     * m0798 dependency. The event source then exposes the updated TLS state to
     * the host draw callback, matching the source call boundary. */
    SetTriLatPoint(levels,tri,point);
    source_publish_controls();
    if(active_frame->provider->draw_control==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->draw_control(active_frame->provider->context,
            kind,(uint16_t)flags,c,percent))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
}
void source_draw_mode(int16_t flags) { source_draw(flags,SIM_SETUP_MODE_CONTROL); }
void source_draw_caste(int16_t flags) { source_draw(flags,SIM_SETUP_CASTE_CONTROL); }

void source_pointer_update(struct Pt *point)
{
    SimSetupPoint p;
    source_publish_controls();
    if(active_frame->drag_cap!=0&&active_frame->drag_samples>=active_frame->drag_cap)
        source_fail(SIM_CONTROL_EVENT_DRAG_LIMIT);
    if(active_frame->provider->pointer_poll==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    p=(SimSetupPoint){point->x,point->y};
    if(!active_frame->provider->pointer_poll(active_frame->provider->context,&p))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
    point->x=p.x;point->y=p.y;
    ++active_frame->drag_samples;
}
int16_t source_still_down(void)
{
    int down=0;
    source_publish_controls();
    if(active_frame->provider->still_down==NULL)
        source_fail(SIM_CONTROL_EVENT_PROVIDER_MISSING);
    if(!active_frame->provider->still_down(active_frame->provider->context,&down))
        source_fail(SIM_CONTROL_EVENT_PROVIDER_FAILED);
    return (int16_t)(down!=0);
}
void *source_copy_bytes(void *destination,const void *source,uint16_t count)
{ return memcpy(destination,source,count); }
int16_t source_compare_bytes(const void *left,const void *right,uint16_t count)
{ int v=memcmp(left,right,count);return (int16_t)((v>0)-(v<0)); }

void sim_recovered_source_control_abort_cleanup(void)
{
    active_frame=NULL;
    source_mode_selector=NULL;source_caste_selector=NULL;
    source_mode_percent=NULL;source_caste_percent=NULL;
}

SimControlEventStatus sim_recovered_source_control_event(
    SimSetupControls *controls,SimControlEventPrivateState *private_state,
    SimSetupControlKind kind,const SimControlEventMessage *message,
    const SimControlEventProvider *provider)
{
    SourceControlFrame *frame=&frame_storage;
    if(controls==NULL||private_state==NULL||message==NULL||provider==NULL||
       (kind!=SIM_SETUP_MODE_CONTROL&&kind!=SIM_SETUP_CASTE_CONTROL)||
       active_frame!=NULL||source_mode_selector!=NULL||source_caste_selector!=NULL||
       source_mode_percent!=NULL||source_caste_percent!=NULL)
        return SIM_CONTROL_EVENT_BAD_ARGUMENT;
    if((kind==SIM_SETUP_MODE_CONTROL &&
        (controls->mode_current<0||controls->mode_current>3))||
       (kind==SIM_SETUP_CASTE_CONTROL &&
        (controls->caste_current<0||controls->caste_current>3)))
        return SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
    if(triWidth==0||triHeight<=2||triWidthL==0||triWidthL>triWidth)
        return SIM_CONTROL_EVENT_INVALID_SOURCE_STATE;
    memset(frame,0,sizeof *frame);
    frame->controls=controls;frame->private_state=private_state;frame->kind=kind;
    frame->provider=provider;frame->failure=SIM_CONTROL_EVENT_OK;
    frame->drag_cap=provider->max_drag_samples;
    active_frame=frame;
    source_mode_selector=&controls->mode_current;
    source_caste_selector=&controls->caste_current;
    source_mode_percent=&private_state->mode_percent;
    source_caste_percent=&private_state->caste_percent;
    if(setjmp(frame->local_abort)==0){
        struct CtlMsg source_message={{0},{message->point.x,message->point.y},(int16_t)message->code};
        if(kind==SIM_SETUP_MODE_CONTROL)ProcModeEvent(&source_message);
        else ProcCasteEvent(&source_message);
    }
    source_publish_controls();
    {
        SimControlEventStatus result=frame->failure;
        sim_recovered_source_control_abort_cleanup();
        return result;
    }
}
