/* Focused converter controls, or a read-only observer over production objects.
 * No cache repair, RNG replacement or alternate game implementation. */
#include "portable/whole_program/platform/graphics_s00_map_tables.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef MAP_FROZEN_OBSERVER
#include <assert.h>
#include "portable/whole_program/platform/graphics.h"
#include "portable/whole_program/platform/native_video_profile.h"
int16_t gfx_screen_width_pixels = 640;
void (*driver_callback_table[25])();
static SimGraphicsDriver driver;
SimGraphicsDriver *sim_graphics_source_owner(void) { return &driver; }
/* Hardware services are inert only in this isolated boundary control. The
 * real startup/reset/unbind implementation is linked below and exercised. */
SimGraphicsStatus sim_graphics_source_clip_bind(SimGraphicsDriver *g) {(void)g;return SIM_GRAPHICS_OK;}
void sim_graphics_source_clip_unbind(void) {}
struct Rect *const *sim_graphics_source_clip_slot(void) {return NULL;}
SimGraphicsStatus sim_graphics_bind_source_abi(SimGraphicsDriver *g,struct Rect *const *r)
{(void)g;(void)r;return SIM_GRAPHICS_OK;}
SimGraphicsStatus sim_graphics_source_bitmap_bind(SimGraphicsDriver *g) {(void)g;return SIM_GRAPHICS_OK;}
void sim_graphics_source_bitmap_unbind(void) {}
SimGraphicsStatus sim_graphics_source_last_status(void) {return SIM_GRAPHICS_OK;}
void gfx_video_bios_ax(int16_t mode) {(void)mode;}

/* One dispatch point used by ctypes and the compiled negative controls. */
int map_frozen_convert(int transform, int profile, const uint8_t *s, size_t n,
                       uint8_t *d, size_t z)
{
    switch (transform) {
    case 0: return sim_s00_map_0000(s,n,d,z);
    case 1: return sim_s00_map_0137(s,n,d,z);
    case 2: return sim_s00_map_026A(s,n,d,z);
    case 3: return sim_s00_map_03A9(s,n,d,z);
    case 4: return sim_s00_map_04D8(s,n,d,z,(SimS00MapTableProfile)profile);
    case 5: return sim_s00_map_06A3(s,n,d,z,(SimS00MapTableProfile)profile);
    default: return SIM_S00_MAP_TABLE_BAD_ARGUMENT;
    }
}

static void unchanged(const uint8_t *d, size_t n)
{
    for (size_t i=0;i<n;++i) assert(d[i]==0xcc);
}

int main(void)
{
    static const size_t widths[]={128,64,128,64,128,64};
    static const size_t sizes[]={1024,512,256,128,64,32};
    static const uint8_t bad[]={25,26,63,64,127,254};
    uint8_t s[128], copy[128], d[1026];
    unsigned checks=0;
    SimS00MapDosLayout layout=sim_s00_map_original_reference;
    assert(sim_s00_map_bind_dos_layout(&layout)==SIM_S00_MAP_TABLE_OK);
    for (int t=0;t<6;++t) for (int p=0;p<2;++p) {
        size_t n=widths[t],z=sizes[t];
        for (unsigned c=0;c<25;++c) {
            memset(s,c,sizeof(s));memcpy(copy,s,sizeof(s));memset(d,0xcc,sizeof(d));
            assert(map_frozen_convert(t,p,s,n,d+1,z)==SIM_S00_MAP_TABLE_OK);
            assert(d[0]==0xcc && d[z+1]==0xcc && !memcmp(s,copy,sizeof(s)));++checks;
        }
        for (unsigned b=0;b<sizeof(bad);++b) for (size_t pos=0;pos<n;++pos) {
            memset(s,11,sizeof(s));s[pos]=bad[b];memset(d,0xcc,sizeof(d));
            assert(map_frozen_convert(t,p,s,n,d+1,z)==SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR);
            unchanged(d,sizeof(d));++checks;
        }
        memset(s,11,sizeof(s));memset(d,0xcc,sizeof(d));
        assert(map_frozen_convert(t,p,NULL,n,d+1,z)==SIM_S00_MAP_TABLE_BAD_ARGUMENT);
        assert(map_frozen_convert(t,p,s,n,NULL,z)==SIM_S00_MAP_TABLE_BAD_ARGUMENT);
        assert(map_frozen_convert(t,p,s,n-1,d+1,z)==SIM_S00_MAP_TABLE_BAD_SPAN);
        assert(map_frozen_convert(t,p,s,n+1,d+1,z)==SIM_S00_MAP_TABLE_BAD_SPAN);
        assert(map_frozen_convert(t,p,s,n,d+1,z-1)==SIM_S00_MAP_TABLE_BAD_SPAN);
        assert(map_frozen_convert(t,p,s,n,d+1,z+1)==SIM_S00_MAP_TABLE_BAD_SPAN);
        unchanged(d,sizeof(d));checks+=6;
        int supports_ff=t<2 || (t>=4 && p==0);
        for (size_t pos=0;pos<n;++pos) {
            memset(s,11,sizeof(s));s[pos]=255;memset(d,0xcc,sizeof(d));
            int status=map_frozen_convert(t,p,s,n,d+1,z);
            assert(status==(supports_ff?SIM_S00_MAP_TABLE_OK:SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR));
            if(!supports_ff) unchanged(d,sizeof(d));
            sim_s00_map_unbind_dos_layout();memset(d,0xcc,sizeof(d));
            status=map_frozen_convert(t,p,s,n,d+1,z);
            assert(status==(supports_ff?SIM_S00_MAP_TABLE_LAYOUT_UNBOUND:SIM_S00_MAP_TABLE_UNSUPPORTED_COLOR));
            unchanged(d,sizeof(d));
            assert(sim_s00_map_bind_dos_layout(&layout)==SIM_S00_MAP_TABLE_OK);checks+=2;
        }
    }
    memset(s,11,sizeof(s));s[0]=255;memset(d,0xcc,sizeof(d));
    layout.raster_segment++;
    assert(sim_s00_map_bind_dos_layout(&layout)==SIM_S00_MAP_TABLE_UNSUPPORTED_LAYOUT);
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_LAYOUT_UNBOUND);
    unchanged(d,sizeof(d));
    layout=sim_s00_map_original_reference;layout.next_callback_offset++;
    assert(sim_s00_map_bind_dos_layout(&layout)==SIM_S00_MAP_TABLE_UNSUPPORTED_LAYOUT);
    assert(sim_s00_map_bind_dos_layout(NULL)==SIM_S00_MAP_TABLE_BAD_ARGUMENT);
    assert(sim_s00_map_04D8(s,128,d,64,(SimS00MapTableProfile)2)==SIM_S00_MAP_TABLE_BAD_ARGUMENT);
    unchanged(d,sizeof(d));
    /* The real video boundary selects the original profile, permits explicit
     * test overrides and clears it on reset, shutdown and a failed bind. */
    static uint8_t font[256*14],pixels[1];
    driver.pixel_storage=pixels;driver.bios_8x14_source=font;
    driver.bios_8x14_source_size=sizeof(font);
    assert(sim_native_video_startup_bind(&driver)==SIM_NATIVE_VIDEO_OK);
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_LAYOUT_UNBOUND);
    gfx_planar_init_640x480();
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_OK);
    uint8_t reference[1024];memcpy(reference,d,sizeof(reference));
    layout=sim_s00_map_original_reference;layout.load_paragraph=0x82c;
    assert(sim_s00_map_bind_dos_layout(&layout)==SIM_S00_MAP_TABLE_OK);
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_OK);
    assert(memcmp(reference,d,sizeof(reference)));
    gfx_reset_driver_callbacks();memset(d,0xcc,sizeof(d));
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_LAYOUT_UNBOUND);
    unchanged(d,sizeof(d));
    gfx_planar_init_640x350();
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_OK);
    assert(!memcmp(reference,d,sizeof(reference)));
    sim_native_video_startup_unbind();memset(d,0xcc,sizeof(d));
    assert(sim_s00_map_0000(s,128,d,1024)==SIM_S00_MAP_TABLE_LAYOUT_UNBOUND);
    assert(sim_native_video_startup_bind(NULL)==SIM_NATIVE_VIDEO_GRAPHICS_NOT_READY);
    unchanged(d,sizeof(d));
    printf("PASS %u converter controls; whole spans, guards, source immutability, FF scope and fail-closed layout binding\n",checks+6);
    puts("PASS video boundary startup, mode 12h/10h, override, reset, shutdown and failed startup controls");
    return 0;
}
#else
#include <windows.h>
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/enhanced/runtime.h"
extern int32_t main_iteration_count;
extern int16_t MapMode,MapPlane,GamePaused;
extern void **fd_50F6_10E2;
extern uint32_t dos_crt_rng_state(void);
extern uint32_t GetSRandSeed(void);
extern void __real_enhanced_execute_next(void);
static FILE *packs;
static unsigned event_count,pack_count,dirty_packs,phase;
static unsigned post_unfreeze_dirty;
static int32_t phase_iteration;
static HWND map,footer;
static unsigned cache_marks(void)
{
    const uint8_t *cells=NULL;size_t size=0;unsigned count=0;
    if(sim_handles_global_resolve_payload(fd_50F6_10E2,&cells,&size)&&size>=8192)
        for(unsigned i=0;i<8192;++i) if(cells[i]==255)++count;
    return count;
}
struct Event {int16_t what,message,x4,modifiers,h,v,code,xE;};
extern void __real_ProcMapEvent(struct Event *);
void __wrap_ProcMapEvent(struct Event *e)
{
    if(e->code==0x10e) {
        ++event_count;
        fprintf(stderr,"FROZEN_EVENT %u iteration=%ld cache_marks=%u\n",event_count,(long)main_iteration_count,cache_marks());
        const uint8_t *cells=NULL;size_t size=0;
        if(sim_handles_global_resolve_payload(fd_50F6_10E2,&cells,&size)&&size>=8192)
            for(unsigned i=0;i<8192;++i)if(cells[i]==255)fprintf(stderr,"FROZEN_DIRTY %u\n",i);
    }
    __real_ProcMapEvent(e);
}
struct ConversionState {uint32_t crt,srand;uint8_t cache[8192];int has_cache;};
static void before_conversion(struct ConversionState *state)
{
    const uint8_t *cells=NULL;size_t size=0;
    state->crt=dos_crt_rng_state();state->srand=GetSRandSeed();
    state->has_cache=sim_handles_global_resolve_payload(fd_50F6_10E2,&cells,&size)&&size>=8192;
    if(state->has_cache)memcpy(state->cache,cells,8192);
}
static void record(unsigned transform,unsigned profile,char *s,char *d,unsigned n,unsigned z,
                   const struct ConversionState *before)
{
    unsigned dirty=0;
    for(unsigned i=0;i<n;++i) if((uint8_t)s[i]==255)++dirty;
    struct ConversionState after;before_conversion(&after);
    if(before->crt!=after.crt||before->srand!=after.srand||before->has_cache!=after.has_cache||
       (before->has_cache&&memcmp(before->cache,after.cache,8192)))abort();
    if(!packs){packs=fopen(getenv("SIMANT_FROZEN_PACKS"),"wb");if(!packs)abort();}
    uint16_t header[4]={(uint16_t)transform,(uint16_t)profile,(uint16_t)n,(uint16_t)z};
    if(fwrite(header,sizeof(header),1,packs)!=1||fwrite(s,n,1,packs)!=1||fwrite(d,z,1,packs)!=1)abort();
    fflush(packs);++pack_count;if(dirty){++dirty_packs;if(event_count>=2)++post_unfreeze_dirty;}
}
#define PACK_WRAPPER(name,t,n,z) \
extern void __real_##name(char *,char *,int16_t,int16_t); \
void __wrap_##name(char *s,char *d,int16_t w,int16_t c) { \
    uint8_t copy[n];memcpy(copy,s,n);struct ConversionState before;before_conversion(&before); \
    __real_##name(s,d,w,c);if(memcmp(copy,s,n))abort();record(t,0,s,d,n,z,&before); }
PACK_WRAPPER(gfx_planar_map128_pack2,0,128,1024)
PACK_WRAPPER(gfx_planar_map64_pack2,1,64,512)
PACK_WRAPPER(gfx_planar_map128_pack4,2,128,256)
PACK_WRAPPER(gfx_planar_map64_pack4,3,64,128)
extern int16_t gfx_screen_width_pixels;
#define MINI_WRAPPER(name,t,n,z) \
extern void __real_##name(char *,char *); \
void __wrap_##name(char *s,char *d) { \
    uint8_t copy[n];memcpy(copy,s,n);struct ConversionState before;before_conversion(&before); \
    __real_##name(s,d);if(memcmp(copy,s,n))abort(); \
    record(t,gfx_screen_width_pixels==320,s,d,n,z,&before); }
MINI_WRAPPER(gfx_planar_map128_pack8,4,128,64)
MINI_WRAPPER(gfx_planar_map64_pack8,5,64,32)
static HWND named_window(const char *name)
{
    HWND h=NULL;while((h=FindWindowExA(NULL,h,NULL,name))) {
        DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId())return h;
    }return NULL;
}
void __wrap_enhanced_execute_next(void)
{
    __real_enhanced_execute_next();
    if(getenv("SIMANT_FROZEN_ENHANCED")) {
        if(!phase&&main_iteration_count>25&&MapMode==1&&MapPlane==1&&cache_marks()==5&&
           (map=named_window("Map"))&&(footer=named_window("Map / Ant Control Panel"))&&GetDlgItem(footer,0x10e)) {
            SendMessage(GetDlgItem(footer,0x10e),BM_CLICK,0,0);phase=1;phase_iteration=main_iteration_count;
        } else if(phase==1&&event_count==1&&main_iteration_count>phase_iteration+8) {
            RECT r;GetWindowRect(map,&r);MoveWindow(map,r.left+24,r.top+16,r.right-r.left,r.bottom-r.top,TRUE);
            InvalidateRect(map,NULL,FALSE);UpdateWindow(map);phase=2;phase_iteration=main_iteration_count;
            fprintf(stderr,"FROZEN_MOVE cache_marks=%u\n",cache_marks());
        } else if(phase==2&&main_iteration_count>phase_iteration+10) {
            SendMessage(GetDlgItem(footer,0x10e),BM_CLICK,0,0);phase=3;phase_iteration=main_iteration_count;
        } else if(phase==3&&event_count==2&&main_iteration_count>phase_iteration+12) {
            fprintf(stderr,"FROZEN_COMPLETE events=%u packs=%u dirty_packs=%u iteration=%ld cache_marks=%u\n",event_count,pack_count,dirty_packs,(long)main_iteration_count,cache_marks());
            fprintf(stderr,"FROZEN_UNFREEZE dirty_packs_after=%u source_cache_rng_unchanged=1\n",post_unfreeze_dirty);
            exit(dirty_packs&&!post_unfreeze_dirty?0:3);
        }
    } else if(event_count==2&&!phase) {
        phase=1;phase_iteration=main_iteration_count;
    } else if(phase&&main_iteration_count>phase_iteration+12) {
        fprintf(stderr,"FROZEN_COMPLETE events=%u packs=%u dirty_packs=%u iteration=%ld cache_marks=%u\n",event_count,pack_count,dirty_packs,(long)main_iteration_count,cache_marks());
        fprintf(stderr,"FROZEN_UNFREEZE dirty_packs_after=%u source_cache_rng_unchanged=1\n",post_unfreeze_dirty);
        exit(dirty_packs&&!post_unfreeze_dirty?0:3);
    }
}
#endif
