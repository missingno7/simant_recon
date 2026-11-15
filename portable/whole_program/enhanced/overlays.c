#include "overlays.h"
#include "runtime.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/algorithms/line16b5.h"
#include "portable/whole_program/window_source_rects.h"
#include <string.h>
#include <stdlib.h>

typedef char **Handle;
extern EnhancedPoint MapPnt;
extern struct Rect editTileRect,map_viewport_rect;
extern int16_t MapPlane,SpidX,SpidY,message_balloon_count,g_3DD2;
extern EnhancedPoint CurBalloonPnts[];
extern int16_t CurBalloonPlane[],CurBalloonFlags[];
extern char *CurBalloonMsgs[];
extern Handle yardAnimHandle;

static EnhancedWorldOverlays selected,staging;
static EnhancedYardActors actors;
static unsigned depth,draw_depth;
static int active,spider_target;
static int origin_x,origin_y,spider_x,spider_y;
static void text_copy(char *out,size_t n,const char *in) {
    size_t i=0;if(in)while(i+1<n && in[i]){out[i]=in[i];++i;}out[i]=0;
}
void enhanced_overlay_push(void) { ++depth; }
void enhanced_overlay_pop(void) {
    if(active && depth==draw_depth) {selected=staging;active=0;spider_target=0;}
    if(depth)--depth;
}
extern void __real_clip_intersect_rect_list(struct Rect *);
void __wrap_clip_intersect_rect_list(struct Rect *rects)
{
    if(enhanced_contracts_enabled() && !active && rects && !memcmp(rects,&editTileRect,8)) {
        memset(&staging,0,sizeof(staging));staging.available=1;staging.plane=MapPlane;
        staging.origin=MapPnt;memcpy(&staging.scope,&editTileRect,8);
        staging.serial=selected.serial+1;active=1;draw_depth=depth;
        origin_x=MapPnt.x*16-editTileRect.left;origin_y=MapPnt.y*16-editTileRect.top;
    }
    __real_clip_intersect_rect_list(rects);
}
extern void __real_gfx_buffer_line_target(void *,int16_t);
void __wrap_gfx_buffer_line_target(void *target,int16_t mode)
{
    spider_target=active && target==&spider_composite_bitmap;
    if(spider_target) {spider_x=(SpidX&~15)-48;spider_y=(SpidY&~15)-48;}
    __real_gfx_buffer_line_target(target,mode);
}
extern void __real_anim_bitmap_to_buffer(int16_t,int16_t,char *,int16_t);
void __wrap_anim_bitmap_to_buffer(int16_t x,int16_t y,char *target,int16_t id)
{
    if(active && target==(char *)&spider_composite_bitmap && staging.art_count<4) {
        staging.art[staging.art_count++]=(EnhancedArtPose){id,(int16_t)(spider_x+x),(int16_t)(spider_y+y),0};
    }
    __real_anim_bitmap_to_buffer(x,y,target,id);
}
extern void __real_gfx_buffer_line(int16_t,int16_t,int16_t,int16_t,int16_t);
void __wrap_gfx_buffer_line(int16_t x0,int16_t y0,int16_t x1,int16_t y1,int16_t color)
{
    if(spider_target && staging.line_count<96)
        staging.lines[staging.line_count++]=(EnhancedLine){x0+spider_x,y0+spider_y,x1+spider_x,y1+spider_y,color};
    __real_gfx_buffer_line(x0,y0,x1,y1,color);
}
extern Handle __real_MakeBalloon(char *,int16_t);
Handle __wrap_MakeBalloon(char *text,int16_t tail)
{
    Handle h=__real_MakeBalloon(text,tail);
    if(active && h && !staging.balloon_count) {
        for(int i=0;i<message_balloon_count && i<6;++i) if(text==CurBalloonMsgs[i]) {
            EnhancedBalloon *b=&staging.balloons[staging.balloon_count++];
            b->anchor=CurBalloonPnts[i];b->plane=CurBalloonPlane[i];b->style=CurBalloonFlags[i];b->tail=tail;
            text_copy(b->text,sizeof(b->text),text);break;
        }
    }
    return h;
}
void enhanced_overlay_rect(int16_t x0,int16_t y0,int16_t x1,int16_t y1,int16_t color)
{
    if(active && ((color&0xf0)==0x10 || (color&0xf0)==0x20) && staging.rect_count<4)
        staging.rects[staging.rect_count++]=(EnhancedOverlayRect){{x0+origin_x,y0+origin_y,x1+origin_x,y1+origin_y},color,g_3DD2};
}
void enhanced_overlay_copy(EnhancedWorldSnapshot *world) {world->overlays=selected;world->overlays_available=selected.available;}

/* Mirror the converted animation record layout only to copy the completed
 * source selection. No image/buffer bytes or native addresses are published.
 * Reading after RenderAnimSet also observes reinsertion, sentinels, hide and
 * remove tails that Add/Set hooks alone would miss (anim.c). */
#pragma pack(push,2)
struct NativeAnimObject {
    char show,drawn,wasDrawn,dirty,moved,remove;
    struct Rect old,rect;
    int16_t x,y,w,h;
    uint16_t size;
    int16_t id;
    Handle buf;
    int16_t pri,pic;
    char *bufp;
};
struct NativeAnimSet { int16_t count; Handle objs; int16_t max,nextId; };
#pragma pack(pop)
_Static_assert(sizeof(struct NativeAnimSet)==14,"converted two-byte-packed AnimSet");
_Static_assert(sizeof(struct NativeAnimObject)==54,"converted two-byte-packed AnimObj");
extern void __real_hanim_RenderAnimSet(Handle);
void __wrap_hanim_RenderAnimSet(Handle h)
{
    __real_hanim_RenderAnimSet(h);
    if(!enhanced_contracts_enabled() || h!=yardAnimHandle)return;
    size_t size;
    const uint8_t *bytes;
    if(!sim_handles_global_resolve_payload(h,&bytes,&size))abort();
    const struct NativeAnimSet *set=(const void *)bytes;
    if(!set || size<sizeof(*set))abort();
    if(!sim_handles_global_resolve_payload(set->objs,&bytes,&size))abort();
    const struct NativeAnimObject *objs=(const void *)bytes;
    if(set->count<0 || set->count>96 || !objs || size<(size_t)set->count*sizeof(*objs))abort();
    memset(&actors,0,sizeof(actors));
    for(int i=0;i<set->count;++i)if(objs[i].show && !objs[i].remove) {
        unsigned n=actors.count++;actors.ids[n]=objs[i].id;
        actors.poses[n]=(EnhancedArtPose){objs[i].pic,objs[i].x-map_viewport_rect.left,
            objs[i].y-map_viewport_rect.top,objs[i].pri};
    }
}
extern void __real_hanim_RemoveAnimSet(Handle);
void __wrap_hanim_RemoveAnimSet(Handle h) {
    if(h==yardAnimHandle)memset(&actors,0,sizeof(actors));
    __real_hanim_RemoveAnimSet(h);
}
void enhanced_yard_copy(EnhancedOverviewSnapshot *yard) {yard->actors=actors;}
