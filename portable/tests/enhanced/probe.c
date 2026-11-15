/* Test-only observations/semantic submissions. No source state writes, clock
 * calls, memory patches or game-function calls from debugger/UI callbacks. */
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/snapshot.h"
#include "portable/whole_program/enhanced/world.h"
#include "portable/whole_program/enhanced/assets.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "portable/whole_program/platform/sdl3/native_windows.h"
#include "portable/whole_program/platform/sdl3/native_workspace.h"
#include "portable/whole_program/modern/world_view.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

extern int16_t clip_window_z_order[32], CurGameType, CurGameTool;
extern int32_t main_iteration_count;
extern char **edit_life_tiles_handle, **edit_life_alt_tiles_handle;
extern uint8_t LifeA[], LifeB[], LifeR[], CasteAuto[];
extern uint8_t OptionStates[];
extern int16_t snd_interface_initialized;
static unsigned occupied_seen, missing_seen, rendered_seen, manual_events, music_seen;
static unsigned copies, submitted, duplicate_result, copy_errors,repairs;
static int configured;
static const char *mode;
static unsigned balloon_peak,captured;
static unsigned layout_operations,layout_roundtrips,layout_errors,native_layout_operations;
static Workspace passive_layout;
static void dump_assets(void) {
    const char *path=getenv("SIMANT_ENHANCED_DUMP_ASSETS");if(!path)return;
    FILE *out=fopen(path,"wb");if(!out)abort();uint8_t pixels[256];
    for(unsigned set=0;set<2;++set)for(unsigned ground=0;ground<256;++ground) {
        uint32_t meta[]={set,ground,0};
        if(!enhanced_asset_cell(set,ground,0,pixels))abort();
        fwrite(meta,4,3,out);fwrite(pixels,1,256,out);
    }
    for(unsigned set=0;set<2;++set)for(unsigned ground=80;ground<=160;ground+=40)
        for(unsigned code=256;code<1024;++code) {
            uint32_t meta[]={set,ground,code};
            if(!enhanced_asset_cell(set,ground,code,pixels))abort();
            fwrite(meta,4,3,out);fwrite(pixels,1,256,out);
        }
    fclose(out);
    char pics[2048];snprintf(pics,sizeof(pics),"%s.pictures",path);out=fopen(pics,"wb");if(!out)abort();
    for(int id=0;id<30000;++id) {const EnhancedArt *a=enhanced_art(id);if(a) {
        uint32_t meta[]={id,a->width,a->height};fwrite(meta,4,3,out);fwrite(a->pixels,1,a->width*a->height,out);
    }}
    fclose(out);
}
extern int __real_enhanced_world_enabled(void);
int __wrap_enhanced_world_enabled(void) {
    const char *m=getenv("SIMANT_ENHANCED_TEST");
    if(m && !strcmp(m,"scent")) {const EnhancedSnapshot *f=enhanced_snapshot();if(!f || f->world.world_layer<0)return 0;}
    return __real_enhanced_world_enabled();
}
static void report(void)
{
    const EnhancedSnapshot *frame=enhanced_snapshot();
    unsigned scent_cells=0;
    if(frame && frame->world.world_layer>=0) {
        static EnhancedWorldSnapshot plain;plain=frame->world;plain.world_layer=-1;
        for(int x=0;x<128;++x)for(int y=0;y<64;++y) {
            ModernCell a,b;enhanced_world_cell(&frame->world,1,x,y,&a);enhanced_world_cell(&plain,1,x,y,&b);
            scent_cells+=a.ground!=b.ground;
        }
    }
    fprintf(stderr,"ENHANCED_SCENT {\"changed_surface_cells\":%u}\n",scent_cells);
    dump_assets();
    fprintf(stderr,"ENHANCED_CAPTURE {\"balloon_peak\":%u,\"captured\":%u}\n",balloon_peak,captured);
    const EnhancedActionLedger *l=enhanced_action_ledger();
    int16_t automatic; memcpy(&automatic,CasteAuto,2);
    const EnhancedSnapshot *f=enhanced_snapshot();
    uint64_t hash=UINT64_C(14695981039346656037);
    if(f)for(size_t i=0;i<sizeof(f->world);++i)hash=(hash^((const uint8_t *)&f->world)[i])*UINT64_C(1099511628211);
    if(f)fprintf(stderr,"ENHANCED_SCENE {\"world_hash\":\"%016llx\",\"iteration\":%ld,\"plane\":%d,\"layer\":%d,\"generation\":%llu,\"overlay_serial\":%llu,\"art\":%u,\"lines\":%u,\"balloons\":%u,\"yard_actors\":%u,\"repaints\":%u}\n",
        (unsigned long long)hash,(long)main_iteration_count,f->world.plane,f->world.world_layer,(unsigned long long)f->generation,(unsigned long long)f->world.overlays.serial,
        f->world.overlays.art_count,f->world.overlays.line_count,f->world.overlays.balloon_count,f->overview.actors.count,repairs);
    fprintf(stderr,"ENHANCED_PROBE {\"occupied\":%u,\"missing\":%u,\"rendered\":%u,\"music_enabled\":%u,\"manual_events\":%u,\"caste_auto\":%d,\"copies\":%u,\"copy_errors\":%u,\"submitted\":%u,\"duplicate_result\":%u,\"delivered\":%" PRIu64 ",\"prepared\":%" PRIu64 ",\"flush_completed\":%" PRIu64 "}\n",
        occupied_seen,missing_seen,rendered_seen,music_seen,manual_events,automatic,copies,copy_errors,
        submitted,duplicate_result,l->delivered,l->prepared,l->flush_completed);
}
static void configure(void)
{
    if (configured++) return;
    mode=getenv("SIMANT_ENHANCED_TEST");
    atexit(report);
}

#ifdef ENHANCED_ACCEPTANCE
#include "portable/whole_program/window_runtime_owner.h"
#include "portable/whole_program/menu_globals.h"
/* Independent source UI observations exist even with snapshot production off.
 * Do not use an enabled-only enhanced snapshot to establish its own invariance. */
struct EnhancedTestUi {
    uint16_t logical_flags[45], object_counts[45];
    uint8_t logical_rects[45][8];
    uint16_t object_flags[45][64];
    uint8_t menu_state[17][16];
} enhanced_test_ui;
extern void __real_portable_test_step_boundary(unsigned,unsigned);
void __wrap_portable_test_step_boundary(unsigned step,unsigned phase)
{
    __real_portable_test_step_boundary(step,phase);
    if (phase!=1) return;
    memset(&enhanced_test_ui,0,sizeof(enhanced_test_ui));
    for (unsigned i=0; i<45; ++i) {
        const SimWindowRefEntry *e=&sim_window_ref_registry.entries[i];
        if (!e->bound || !e->source_handle || !*e->source_handle ||
            (const void *)*e->source_handle!=e->view.wire || e->view.extent<0x1e) continue;
        memcpy(&enhanced_test_ui.logical_flags[i],e->view.wire+0x1c,2);
        memcpy(enhanced_test_ui.logical_rects[i],e->view.wire,8);
        enhanced_test_ui.object_counts[i]=e->view.count;
        if (e->view.count>64) abort();
        for (unsigned j=0; j<e->view.count; ++j)
            if (e->view.object_sizes[j]>=0x26)
                memcpy(&enhanced_test_ui.object_flags[i][j],e->view.object_table[j]+0x24,2);
    }
    for (unsigned i=0; i<g_menu_view.table_count && i<17; ++i) {
        char **row=g_6054 ? g_6054[i] : NULL;
        for (unsigned j=0; row && j<16 && row[j]; ++j)
            enhanced_test_ui.menu_state[i][j]=(uint8_t)row[j][0];
    }
}
/* The established observer exits with _Exit; append proof of actual passive
 * publications/repaints at its diagnostic seam instead of relying on atexit. */
extern void __real_portable_test_diagnostics(FILE *);
void __wrap_portable_test_diagnostics(FILE *f)
{
    __real_portable_test_diagnostics(f);
    const EnhancedSnapshot *s=enhanced_snapshot();
    fprintf(f,",\"enhanced_generation\":%" PRIu64 ",\"enhanced_repaint_copies\":%u,\"enhanced_copy_errors\":%u,\"enhanced_repaint_renders\":%u",
        s?s->generation:0,copies,copy_errors,repairs);
    fprintf(f,",\"enhanced_layout_operations\":%u,\"enhanced_layout_roundtrips\":%u,\"enhanced_layout_errors\":%u,\"enhanced_native_layout_operations\":%u",
        layout_operations,layout_roundtrips,layout_errors,native_layout_operations);
}
#endif

extern void __real_enhanced_execute_next(void);
void __wrap_enhanced_execute_next(void)
{
    configure();
    const EnhancedSnapshot *f=enhanced_snapshot();
    if(getenv("SIMANT_ENHANCED_LAYOUT_STRESS")&&f&&f->panels.game_type>=0) {
        static int32_t last=-1;
        if(last!=main_iteration_count){last=main_iteration_count;
            if(!layout_operations)ws_preset(&passive_layout,0);
            static EnhancedSnapshot before;before=*f;
            if(native_workspace_active()) {
                if(!native_workspace_operation(layout_operations))++layout_errors;
                else ++native_layout_operations;
                passive_layout=*native_workspace_layout();
            } else ws_exercise(&passive_layout,layout_operations);
            if(!ws_validate(&passive_layout)||memcmp(&before,enhanced_snapshot(),sizeof(before)))++layout_errors;
            /* Validate the production serialization on private native storage. */
            const char *path=getenv("SIMANT_ENHANCED_LAYOUT_ROUNDTRIP");FILE *file=path?fopen(path,"w+"):NULL;
            if(file){Workspace restored;if(!ws_write(&passive_layout,file))++layout_errors;rewind(file);
                if(!ws_read(&restored,file))++layout_errors;else {restored.revision=passive_layout.revision;if(memcmp(&restored,&passive_layout,sizeof(restored)))++layout_errors;}
                fclose(file);++layout_roundtrips;
            }else ++layout_errors;
            ++layout_operations;
        }
    }
    if(f && f->world.overlays.balloon_count>balloon_peak)balloon_peak=f->world.overlays.balloon_count;
    const char *capture=getenv("SIMANT_ENHANCED_CAPTURE");
    if(capture && !captured && f && f->world.overlays.balloon_count && f->world.overlays.line_count)
        captured=native_windows_save_frames(capture);
    if (mode && !strcmp(mode,"stress") && f) {
        static EnhancedSnapshot copy;
        for (unsigned i=0; i<19; ++i) {
            if (!enhanced_snapshot_copy(&copy) || memcmp(f,&copy,sizeof(copy))) ++copy_errors;
            /* Exercise native cell/asset composition on all three planes and
             * actual semantic overlay rasterization with private repaint RAM. */
            static uint8_t raster[2048*1024];
            uint8_t pixels[256];
            for(int plane=1;plane<=3;++plane)for(int x=0;x<4;++x) {
                ModernCell c;enhanced_world_cell(&copy.world,plane,x,16,&c);
                if(!enhanced_asset_cell(copy.world.terrain_set,c.ground,c.life,pixels))++copy_errors;
            }
            enhanced_world_draw(&copy.world,raster,2048,1024,2048);
            ++repairs;
            ++copies;
        }
    }
    if(mode && !strcmp(mode,"spider") && !submitted && f && main_iteration_count>16 && CurGameType>=0 && CurGameTool==-1 && !f->dialogs.modal) {
        EnhancedIntent intent={.id="N05",.parameter=1,.serial=1,.generation=f->generation};
        submitted=enhanced_submit(&intent)==ENHANCED_QUEUED;
    }
    if (mode && !strcmp(mode,"executor") && !submitted && f &&
        main_iteration_count>2 && CurGameType>=0 && CurGameTool==-1 &&
        !f->dialogs.modal) {
        EnhancedIntent intent={.id="B01",.parameter=1,.serial=1,.generation=f->generation};
        submitted=enhanced_submit(&intent)==ENHANCED_QUEUED;
        duplicate_result=enhanced_submit(&intent);
    }
    __real_enhanced_execute_next();
}

extern void __real_ProcCasteEvent(void *);
void __wrap_ProcCasteEvent(void *event)
{
    configure();
    int16_t code; memcpy(&code,(uint8_t *)event+12,2);
    if (code==0x1305) ++manual_events;
    __real_ProcCasteEvent(event);
}

extern int __real_modern_world_cell_pixels(const ModernCell *,uint8_t[256]);
int __wrap_modern_world_cell_pixels(const ModernCell *cell,uint8_t pixels[256])
{
    configure();
    int result=__real_modern_world_cell_pixels(cell,pixels);
    int16_t music; memcpy(&music,OptionStates+2,2);
    if (clip_window_z_order[0]==0x1a00 && !edit_life_tiles_handle &&
        !edit_life_alt_tiles_handle && cell->life && music && snd_interface_initialized) {
        music_seen=1;
        unsigned occupied=0;
        for (unsigned i=0; i<8192; ++i) occupied+=LifeA[i]!=0;
        for (unsigned i=0; i<4096; ++i) occupied+=(LifeB[i]!=0)+(LifeR[i]!=0);
        if (occupied) {
            ModernCell ground={cell->ground,0}; uint8_t ground_pixels[256];
            if (result && __real_modern_world_cell_pixels(&ground,ground_pixels)) {
                occupied_seen=occupied;
                ++rendered_seen;
                missing_seen+=memcmp(pixels,ground_pixels,sizeof(ground_pixels))==0;
            }
        }
    }
    return result;
}
