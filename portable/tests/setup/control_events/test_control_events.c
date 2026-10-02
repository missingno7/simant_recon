#include "../../../ui_model/windows/control_events.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct Fixture {
    char calls[64][32];
    unsigned count;
    SimSetupPoint polls[4];
    unsigned poll_count, poll_at;
    int down_after_poll;
    SimSetupRect rect;
    int fail_at;
} Fixture;

static int note(Fixture *f, const char *s)
{
    if (f->fail_at && (int)f->count + 1 == f->fail_at) return 0;
    assert(f->count < 64);
    strcpy(f->calls[f->count++], s);
    return 1;
}
static int clip(void *p, uint16_t win) { char b[32]; (void)win; strcpy(b,"clip_set"); return note(p,b); }
static int off(void *p) { return note(p,"clip_off"); }
static int help(void *p, uint16_t ctx) { (void)ctx; return note(p,"help"); }
static int group(void *p, uint16_t win, uint8_t id, int visible)
{ (void)win; (void)id; return note(p, visible ? "group_visible" : "group_invisible"); }
static int select_obj(void *p, uint16_t obj) { (void)obj; return note(p,"select"); }
static int get_rect(void *p, uint16_t obj, SimSetupRect *r)
{ Fixture *f=p; (void)obj; *r=f->rect; return note(p,"get_rect"); }
static int draw(void *p, SimSetupControlKind kind, uint16_t flags,
                const SimSetupControls *c, int16_t percent)
{ (void)kind; (void)flags; (void)c; (void)percent; return note(p,"draw"); }
static int poll(void *p, SimSetupPoint *point)
{ Fixture *f=p; if (!note(f,"poll")) return 0; if (f->poll_at < f->poll_count) *point=f->polls[f->poll_at++]; return 1; }
static int still(void *p, int *down)
{ Fixture *f=p; if (!note(f,"still")) return 0; *down=(int)f->poll_at < f->down_after_poll; return 1; }

static SimControlEventProvider provider(Fixture *f)
{
    SimControlEventProvider p={clip,off,help,group,select_obj,get_rect,draw,
                               poll,still,f,16}; return p;
}
static void init(SimSetupControls *c)
{
    memset(c,0,sizeof *c); sim_setup_controls_init_data(c);
    c->source_data_initialized=1;
    c->mode_auto=1; c->caste_auto=1;
    c->mode_level=c->mode_defaults; c->caste_level=c->caste_defaults;
    c->mode_rect=(SimSetupRect){100,100,200,200};
    c->caste_rect=(SimSetupRect){100,100,200,200};
    c->mode_point=(SimSetupPoint){150,120};
    c->caste_point=(SimSetupPoint){150,120};
}

static void run_one(SimSetupControlKind kind, uint16_t code, int expected_auto,
                    const char *const *events, unsigned event_count)
{
    SimSetupControls c; SimControlEventPrivateState priv={1,1,109,96,54};
    SimControlEventMessage m={code,{150,120}}; Fixture f={0};
    SimControlEventProvider p; SimControlEventStatus status;
    init(&c); f.rect=(kind==SIM_SETUP_MODE_CONTROL)?c.mode_rect:c.caste_rect;
    p=provider(&f);
    status=sim_control_process_event(&c,&priv,kind,&m,&p);
    assert(status==SIM_CONTROL_EVENT_OK);
    assert((kind==SIM_SETUP_MODE_CONTROL?c.mode_auto:c.caste_auto)==expected_auto);
    assert(f.count==event_count);
    for(unsigned i=0;i<event_count;i++) assert(strcmp(f.calls[i],events[i])==0);
}

int main(void)
{
    const char *preset[] = {"clip_set","select","clip_set","draw","group_visible","clip_off"};
    const char *toggle[] = {"clip_set","draw","clip_off"};
    const char *auto_on[] = {"clip_set","group_invisible","clip_off"};
    const char *help_events[] = {"clip_set","help","clip_off"};
    const char *drag[] = {"clip_set","get_rect","select","group_visible","clip_set",
                          "draw","poll","still","draw","poll","still","clip_off"};
    run_one(SIM_SETUP_MODE_CONTROL,0x1203,1,help_events,3);
    run_one(SIM_SETUP_CASTE_CONTROL,0x1303,1,help_events,3);
    run_one(SIM_SETUP_MODE_CONTROL,0x1202,1,(const char *const[]){"clip_set","clip_off"},2);
    run_one(SIM_SETUP_CASTE_CONTROL,0x1315,1,(const char *const[]){"clip_set","clip_off"},2);
    run_one(SIM_SETUP_MODE_CONTROL,0x120f,1,toggle,3);
    run_one(SIM_SETUP_CASTE_CONTROL,0x1311,1,toggle,3);
    run_one(SIM_SETUP_MODE_CONTROL,0x1206,0,preset,6);
    run_one(SIM_SETUP_CASTE_CONTROL,0x1308,0,preset,6);

    {
        SimSetupControls c; SimControlEventPrivateState priv={1,1,109,96,54};
        SimControlEventMessage m={0x120d,{150,120}}; Fixture f={0};
        SimControlEventProvider p;
        init(&c); f.rect=c.mode_rect; f.polls[0]=(SimSetupPoint){180,150};
        f.polls[1]=(SimSetupPoint){180,150}; f.poll_count=2; f.down_after_poll=2;
        p=provider(&f);
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_MODE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_OK);
        if (f.count!=sizeof drag/sizeof drag[0]) { fprintf(stderr,"drag count %u expected %u\n",f.count,(unsigned)(sizeof drag/sizeof drag[0])); for(unsigned i=0;i<f.count;i++) fprintf(stderr,"%s ",f.calls[i]); fputc('\n',stderr); }
        assert(f.count==sizeof drag/sizeof drag[0]);
        for(unsigned i=0;i<sizeof drag/sizeof drag[0];i++) assert(strcmp(f.calls[i],drag[i])==0);
        assert(c.mode_auto==0 && c.mode_levels[0].frac==c.mode_level.frac);
    }
    {
        SimSetupControls c; SimControlEventPrivateState priv={0,0,109,96,54};
        SimControlEventMessage m={0x1204,{0,0}}; Fixture f={0};
        SimControlEventProvider p;
        init(&c); c.mode_auto=0; p=provider(&f);
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_MODE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_OK);
        assert(c.mode_auto==1 && f.count==3);
        for(unsigned i=0;i<3;i++) assert(strcmp(f.calls[i],auto_on[i])==0);
    }
    {
        SimSetupControls c; SimControlEventPrivateState priv={1,0,109,96,54};
        SimControlEventMessage m={0x1210,{0,0}}; Fixture f={0};
        SimControlEventProvider p;
        init(&c); p=provider(&f);
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_MODE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_OK);
        assert(priv.mode_percent==0 && priv.caste_percent==0);
        assert(f.count==3 && strcmp(f.calls[1],"draw")==0);
    }
    {
        SimSetupControls c; SimControlEventPrivateState priv={0,0,109,96,54};
        SimControlEventMessage m={0x1203,{0,0}}; Fixture f={0};
        SimControlEventProvider p=provider(&f);
        p.help=0;
        init(&c);
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_MODE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_PROVIDER_FAILED);
        assert(f.count==2 && strcmp(f.calls[0],"clip_set")==0 && strcmp(f.calls[1],"clip_off")==0);
    }
    {
        SimSetupControls c; SimControlEventPrivateState priv={0,0,109,96,54};
        SimControlEventMessage m={0x1208,{0,0}}; Fixture f={0};
        SimControlEventProvider p=provider(&f);
        init(&c); c.mode_current=1; c.mode_level=(SimSetupTriangle){11,22,33};
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_MODE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_OK);
        assert(c.mode_levels[1].frac==11 && c.mode_levels[1].mid==22 && c.mode_levels[1].weight==33);
        assert(c.mode_current==2 && c.mode_level.frac==c.mode_levels[2].frac);
    }
    {
        SimSetupControls c; SimControlEventPrivateState priv={0,0,109,96,54};
        SimControlEventMessage m={0x130d,{99,150}}; Fixture f={0};
        SimControlEventProvider p;
        init(&c); f.rect=c.caste_rect; p=provider(&f);
        assert(sim_control_process_event(&c,&priv,SIM_SETUP_CASTE_CONTROL,&m,&p)==SIM_CONTROL_EVENT_OK);
        assert(f.count==3 && strcmp(f.calls[1],"get_rect")==0 && strcmp(f.calls[2],"clip_off")==0);
    }
    puts("control event model focused state/order tests passed");
    return 0;
}
