/* Test-only observations/semantic submissions. No source state writes, clock
 * calls, memory patches or game-function calls from debugger/UI callbacks. */
#include "portable/whole_program/enhanced/actions.h"
#include "portable/whole_program/enhanced/snapshot.h"
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
static unsigned copies, submitted, duplicate_result, copy_errors;
static int configured;
static const char *mode;
static void report(void)
{
    const EnhancedActionLedger *l=enhanced_action_ledger();
    int16_t automatic; memcpy(&automatic,CasteAuto,2);
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
    fprintf(f,",\"enhanced_generation\":%" PRIu64 ",\"enhanced_repaint_copies\":%u,\"enhanced_copy_errors\":%u",
        s?s->generation:0,copies,copy_errors);
}
#endif

extern void __real_enhanced_execute_next(void);
void __wrap_enhanced_execute_next(void)
{
    configure();
    const EnhancedSnapshot *f=enhanced_snapshot();
    if (mode && !strcmp(mode,"stress") && f) {
        static EnhancedSnapshot copy;
        for (unsigned i=0; i<19; ++i) {
            if (!enhanced_snapshot_copy(&copy) || memcmp(f,&copy,sizeof(copy))) ++copy_errors;
            ++copies;
        }
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
