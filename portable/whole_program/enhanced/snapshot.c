#include "runtime.h"
#include "actions.h"
#include "overlays.h"
#include "portable/whole_program/window_runtime_owner.h"
#include "canonical_data_views.h"
#include "portable/whole_program/platform/handles.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "proximity_labels.inc"

/* Ordinary source owners. Byte-defined words are read by memcpy, rather
 * than declaring a contradictory scalar object in another translation unit. */
extern uint8_t MapA[], MapB[], MapR[], LifeA[], LifeB[], LifeR[];
extern uint8_t PherMapA[], PherMapF[], PherMapBN[], PherMapBT[], PherMapRN[], PherMapRT[];
extern uint8_t YMapPopB[], YMapPopR[], fd_3D57_0184[];
extern uint8_t CasteAuto[], HistCnt[], LayDownQueenMode[], OptionStates[];
extern uint8_t modeLevels[], casteLevels[];
extern int16_t MapPlane, TERRAINset, YardMode;
extern uint8_t ELayerMode[], MapMode[];
extern EnhancedPoint MapPnt, YMapPnt, CurYardPnt;
extern EnhancedRect editTileRect, map_viewport_rect;
extern int16_t mapXsize, mapYsize, map_side_margin_pixels, multiplier;
extern int16_t MePlane, MeLocX, MeLocY, MeType, MeDir, MeBase, MeEgg, MeMode;
extern int16_t SpidOn, SpidX, SpidY;
extern int16_t ModeAuto, modeSet, casteSet, g_1B62, g_1B64;
extern int16_t ModePopB[6], CastePopB[6];
extern int16_t CurGameType, CurGameTool, GamePaused;
extern int16_t MeHealth, HealthB, HealthR, MeWarnHealth, BlkWarnHealth, BpopT, RpopT;
extern int16_t QueenStorageB, ColonyTotalBlack, ColonyTotalRed;
extern int16_t g_2E26, g_2E04[16], g_2E24;
extern int16_t H_BPop[64], H_RPop[64], H_BFood[64], H_RFood[64], H_BHeal[64], H_RHeal[64];
extern int16_t H_FoodA[64], H_ADead[64], H_PDead[64], H_FDead[64], HistStart;
extern int32_t OverallScore;
extern char *g_19C6;
extern int16_t clip_window_z_order[32];

static EnhancedSnapshot frames[2];
static unsigned current;
static uint64_t generation, task_token;
static int16_t last_owner = INT16_MIN;
static uint16_t last_modal;
static int16_t score_metrics[8];
static int score_available;
static char magnify_text[3][160];
/* Observe completed source text output; ScoreDialog and CalcScore share a
 * TU, so interposition on CalcScore would miss that call. No score is rerun. */
extern void __real_font_PrintStr(int16_t,int16_t,char *);
void __wrap_font_PrintStr(int16_t x,int16_t y,char *message){
    __real_font_PrintStr(x,y,message);
    if(enhanced_contracts_enabled() && message && clip_window_z_order[0]==0x1d00){
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[0x1d];
        if(e->bound&&e->view.count>=5)for(unsigned i=0;i<3;++i){const uint8_t *b=(const void *)e->view.object_table[i+2];
            if(x>=sim_window_wire_read_i16(b,0)&&x<sim_window_wire_read_i16(b,4)&&y>=sim_window_wire_read_i16(b,2)&&y<sim_window_wire_read_i16(b,6))snprintf(magnify_text[i],sizeof(magnify_text[i]),"%s",message);
        }
    }
    if(!enhanced_contracts_enabled() || !message || clip_window_z_order[0]!=0x1800)return;
    const SimWindowRefEntry *e=&sim_window_ref_registry.entries[0x18];
    if(!e->bound||e->view.count<10)return;
    int value=0;const char *p=message;while(*p==' ')++p;
    if(*p<'0'||*p>'9')return;
    while(*p>='0'&&*p<='9'){value=value*10+*p++-'0';if(value>100)return;}
    if(*p!='%')return;
    for(unsigned i=0;i<8;++i){const uint8_t *b=(const uint8_t *)e->view.object_table[2+i];
        if(x>=sim_window_wire_read_i16(b,0)&&x<sim_window_wire_read_i16(b,4)&&y>=sim_window_wire_read_i16(b,2)&&y<sim_window_wire_read_i16(b,6)){
            score_metrics[i]=(int16_t)value;score_available|=1<<i;break;
        }
    }
}
extern void enhanced_read_card_links(EnhancedCardsSnapshot *);
extern void enhanced_read_history_selection(EnhancedHistorySnapshot *);
extern EnhancedPoint mode_knob_center, caste_knob_center;

int enhanced_contracts_enabled(void)
{
    static int initialized, enabled;
    if (!initialized) {
        const char *p = getenv("SIMANT_ENHANCED_CONTRACTS");
        enabled = p && !strcmp(p, "1");
        initialized = 1;
    }
    return enabled;
}

int enhanced_world_enabled(void)
{
    static int initialized,enabled;
    if(!initialized) {const char *p=getenv("SIMANT_ENHANCED_WORLD");enabled=!p || strcmp(p,"0");initialized=1;}
    return enhanced_contracts_enabled() && enabled;
}

static int16_t word(const void *p)
{
    int16_t value;
    memcpy(&value, p, sizeof(value));
    return value;
}

static const SimWindowRefView *window_view(int16_t owner)
{
    unsigned slot = (uint16_t)owner >> 8;
    if (owner < 0 || slot >= SIM_WINDOW_REF_REGISTRY_CAPACITY) return NULL;
    const SimWindowRefEntry *e = &sim_window_ref_registry.entries[slot];
    if (!e->bound || !e->source_handle || !*e->source_handle ||
        (const void *)*e->source_handle != e->view.wire) return NULL;
    return &e->view;
}

uint16_t enhanced_window_flags(int16_t owner)
{
    const SimWindowRefView *v = window_view(owner);
    return v && v->extent >= 0x1e ? (uint16_t)word(v->wire + 0x1c) : 0;
}

static uint8_t text_copy(char *out, size_t capacity, const char *in, size_t limit)
{
    size_t i = 0;
    if (in) while (i + 1 < capacity && i < limit && in[i]) { out[i] = in[i]; ++i; }
    out[i] = 0;
    return in && i == capacity - 1 && i < limit && in[i] != 0;
}

static void world_snapshot(EnhancedWorldSnapshot *w)
{
#define COPY(member, source) memcpy(w->member, source, sizeof(w->member))
    COPY(surface, MapA); COPY(life_surface, LifeA);
    COPY(black, MapB); COPY(life_black, LifeB);
    COPY(red, MapR); COPY(life_red, LifeR);
#undef COPY
    const uint8_t *scent[] = {PherMapA,PherMapF,PherMapBN,PherMapBT,PherMapRN,PherMapRT};
    for (unsigned i=0; i<6; ++i) memcpy(w->scent[i], scent[i], sizeof(w->scent[i]));
    w->plane=MapPlane; w->terrain_set=TERRAINset; w->world_layer=word(ELayerMode);
    w->origin=MapPnt; w->hidden_viewport=editTileRect;
    w->player_plane=MePlane; w->player_x=MeLocX; w->player_y=MeLocY;
    w->player_type=MeType; w->player_dir=MeDir; w->player_base=MeBase;
    w->player_egg=MeEgg; w->player_mode=MeMode;
    enhanced_overlay_copy(w);
    text_copy(w->status,sizeof(w->status),g_19C6,SIZE_MAX);
    w->spider_on=SpidOn; w->spider_x=SpidX; w->spider_y=SpidY;
}

extern char *mapMessage;
extern int16_t BoyMessOn,BoyMsgOffset;
extern char **BoyMsgs;

static void overview_snapshot(EnhancedOverviewSnapshot *o)
{
    extern uint8_t CTab[144],HTab[208],LTab[48],CTabR[40];
    memcpy(o->terrain_colors,CTab,sizeof(o->terrain_colors));
    memcpy(o->house_colors,HTab,sizeof(o->house_colors));
    memcpy(o->life_colors,LTab,sizeof(o->life_colors));
    memcpy(o->nest_colors,CTabR,sizeof(o->nest_colors));
    extern void **fd_50F6_10E2;extern int16_t SpidDir;
    const uint8_t *cells;size_t size;unsigned extent=multiplier==64?4096:8192;
    if(fd_50F6_10E2 && sim_handles_global_resolve_payload(fd_50F6_10E2,&cells,&size) && size>=extent){memcpy(o->map_cells,cells,extent);o->map_cells_available=1;}
    extern int16_t enhanced_read_map_frozen(void);
    o->map_frozen=enhanced_read_map_frozen();o->spider_direction=SpidDir;
    extern int16_t FootHere,FootX,FootY,BoyHere,BoyDir,MowX,MowY;
    o->foot_here=FootHere;o->foot_x=FootX;o->foot_y=FootY;o->boy_here=BoyHere;o->boy_direction=BoyDir;o->mower_x=MowX;o->mower_y=MowY;
    enhanced_yard_copy(o);
    text_copy(o->message,sizeof(o->message),mapMessage,SIZE_MAX);
    if(BoyMessOn && BoyMsgs) text_copy(o->human_balloon,sizeof(o->human_balloon),BoyMsgs[BoyMsgOffset],SIZE_MAX);
    o->map_mode=word(MapMode); o->yard_mode=YardMode; o->tiles=map_viewport_rect;
    o->cell_width=mapXsize; o->cell_height=mapYsize;
    o->pad=map_side_margin_pixels; o->multiplier=multiplier;
    o->yard_selection=YMapPnt; o->current_patch=CurYardPnt;
    memcpy(o->population_black,YMapPopB,192);
    /* Proven YMapPopR adjacency span, kept as its two actual owners. */
    memcpy(o->population_red,YMapPopR,32);
    memcpy((uint8_t *)o->population_red+32,fd_3D57_0184,160);
    o->stored_queens=QueenStorageB; o->placement_auto=word(LayDownQueenMode);
    o->colonies_black=ColonyTotalBlack; o->colonies_red=ColonyTotalRed;
}

static void allocation(EnhancedAllocationSnapshot *a, int16_t automatic,
                       int16_t preset, int16_t percent, const uint8_t *levels,
                       const int16_t *population)
{
    a->automatic=automatic; a->preset=preset; a->percent=percent;
    a->frac=(uint16_t)word(levels); a->mid=(uint16_t)word(levels+2);
    a->weight=(uint16_t)word(levels+4);
    memcpy(a->population,population,sizeof(a->population));
}

static void panels_snapshot(EnhancedPanelsSnapshot *p)
{
    allocation(&p->behavior,ModeAuto,modeSet,g_1B62,modeLevels,ModePopB);
    allocation(&p->caste,word(CasteAuto),casteSet,g_1B64,casteLevels,CastePopB);
    const SimWindowRefView *b=window_view(0x1200), *c=window_view(0x1300);
    if(b && b->count>13)memcpy(&p->behavior.triangle,b->object_table[13],8);
    if(c && c->count>13)memcpy(&p->caste.triangle,c->object_table[13],8);
    const SimWindowRefView *views[]={b,c};EnhancedAllocationSnapshot *allocs[]={&p->behavior,&p->caste};
    for(int a=0;a<2;++a)if(views[a]&&views[a]->count>8)for(int i=0;i<6;++i)
        allocs[a]->control_flags[i]=(uint16_t)word((const uint8_t *)views[a]->object_table[i+3]+0x24);
    p->world_ready=enhanced_game_ready();
    extern uint8_t gfx_colour_translation[],g_1B46[],g_1B4A[];
    for(int i=0;i<3;++i){p->behavior.bar_colors[i]=gfx_colour_translation[g_1B4A[i]&15];p->caste.bar_colors[i]=gfx_colour_translation[g_1B46[i]&15];}
    p->behavior.knob=mode_knob_center;p->caste.knob=caste_knob_center;
    p->game_type=CurGameType; p->tool=CurGameTool;extern int16_t CurExpTool;p->experiment_tool=CurExpTool; p->paused=GamePaused;
    p->speed=GameSpeed.words[0];
    /* Options are the existing proven six-word semantic span. */
    memcpy(p->options,OptionStates,sizeof(p->options));
    p->health_yellow=MeHealth; p->health_black=HealthB; p->health_red=HealthR;
    p->warning_yellow=MeWarnHealth; p->warning_black=BlkWarnHealth;
    p->population_black=BpopT; p->population_red=RpopT;
    /* editMessage is the proven alias of g_19C6 (semantic-spans.json). */
    text_copy(p->prompt,sizeof(p->prompt),g_19C6,SIZE_MAX);p->yard_wait=enhanced_yard_wait();
}

static void cards_snapshot(EnhancedCardsSnapshot *c)
{
    c->card=g_2E26; c->previous_index=g_2E24;
    memcpy(c->previous,g_2E04,sizeof(c->previous));
    int16_t top=clip_window_z_order[0];
    c->help_owner=(enhanced_window_flags(top)&0x40) ? top : INT16_MIN;
    enhanced_read_card_links(c);
}

static void history_snapshot(EnhancedHistorySnapshot *h)
{
    const int16_t *data[]={H_BPop,H_RPop,H_BFood,H_RFood,H_BHeal,H_RHeal,H_FoodA,H_ADead,H_PDead,H_FDead};
    for (unsigned i=0; i<10; ++i) memcpy(h->samples[i],data[i],sizeof(h->samples[i]));
    h->start=HistStart; h->count=word(HistCnt); h->last_overall_score=OverallScore;
    h->status_truncated=text_copy(h->status,sizeof(h->status),g_19C6,SIZE_MAX);
    enhanced_read_history_selection(h);
    h->score_metrics_available=(score_available&(CurGameType==2?255:15))==(CurGameType==2?255:15);
    memcpy(h->score_metrics,score_metrics,sizeof(score_metrics));
}

static void dialogs_snapshot(EnhancedDialogsSnapshot *d)
{
    d->owner=clip_window_z_order[0]; d->flags=enhanced_window_flags(d->owner);
    extern int16_t lastProxObj;d->proximity_item=lastProxObj;
    d->modal=(d->flags&0x40)!=0;
    if (last_owner!=d->owner || last_modal!=d->modal) {
        ++task_token; last_owner=d->owner; last_modal=d->modal;
    }
    d->task_token=task_token;
    const SimWindowRefView *v=window_view(d->owner);
    if (!v) return;
    int menu_picture=-1;
    if(v->count>1 && ((const uint8_t *)v->object_table[1])[0x21]==6 && v->object_sizes[1]>=0x2a)
        menu_picture=word((const uint8_t *)v->object_table[1]+0x28);
    for (unsigned i=0; i<v->count && d->object_count<32; ++i) {
        const uint8_t *b=(const uint8_t *)v->object_table[i];
        size_t extent=v->object_sizes[i];
        if (!b || extent<0x28) continue;
        EnhancedObjectSnapshot *o=&d->objects[d->object_count++];
        o->id=(int16_t)(d->owner+i); o->type=b[0x21]; o->flags=(uint16_t)word(b+0x24);
        memcpy(&o->rect,b,sizeof(o->rect));
        o->bitmap=o->type==6 && extent>=0x2a ? word(b+0x28) : -1;
        const char *text=NULL; size_t limit=0;
        if ((o->type==5 || o->type==9 || o->type==12) && extent>0x2a) {
            text=(const char *)b+0x2a; limit=extent-0x2a;
        } else if ((o->type==16 || o->type==17 || o->type==18) && extent>0x2e) {
            char **handle=v->object_handles_2a[i];
            text=handle ? *handle : (const char *)b+0x2e;
            limit=handle ? SIZE_MAX : extent-0x2e;
        }
        o->text_truncated=text_copy(o->text,sizeof(o->text),text,limit);
        if(o->type==1 && i>=2){const char *label=proximity_label(menu_picture,i-2);if(label)text_copy(o->text,sizeof(o->text),label,SIZE_MAX);}
        if(d->owner==0x1d00&&i>=2&&i<=4)snprintf(o->text,sizeof(o->text),"%s%s",i==3?"Behavior: ":i==4?"Carrying: ":"",magnify_text[i-2]);
    }
}

void enhanced_publish(EnhancedSeam seam)
{
    if (!enhanced_contracts_enabled()) return;
    EnhancedSnapshot *f=&frames[current^1];
    memset(f,0,sizeof(*f));
    f->seam=seam;
    world_snapshot(&f->world); overview_snapshot(&f->overview);
    /* A nested wait can interrupt temporary life removal or an incomplete
     * overlay redraw. Keep the last published scene while the source owns
     * that wait; current source prompt text still changes independently. */
    if(seam==ENHANCED_MODAL_POLL && generation && frames[current].world.plane==f->world.plane){
        char status[sizeof(f->world.status)];memcpy(status,f->world.status,sizeof(status));
        f->world=frames[current].world;memcpy(f->world.status,status,sizeof(status));
    }
    panels_snapshot(&f->panels); cards_snapshot(&f->cards);
    history_snapshot(&f->history); dialogs_snapshot(&f->dialogs);
    memcpy(f->logical_order,clip_window_z_order,sizeof(f->logical_order));
    f->generation=++generation;
    current^=1;
}

const EnhancedSnapshot *enhanced_snapshot(void) { return generation ? &frames[current] : NULL; }
int enhanced_snapshot_copy(EnhancedSnapshot *out)
{
    const EnhancedSnapshot *f=enhanced_snapshot();
    if (!f || !out) return 0;
    memcpy(out,f,sizeof(*out));
    return 1;
}
