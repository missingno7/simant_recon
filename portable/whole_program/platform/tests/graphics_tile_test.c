/* Isolated driver boundary for the original-instruction tile tests.
 * Cursor services are disabled in both machines; bitmap fallback is observed,
 * not simulated. No source game routine is replaced by this harness. */
#include "../graphics_tile_upload.h"
#include "../graphics_bitmap_source.h"
#include "../graphics_source_clip.h"
#include "../graphics_capture_source.h"
#include "../ega_map_readback.h"
#include <string.h>

void (*driver_callback_table[25])();
int16_t g_3DB6 = 80;
char g_3D20[128];
uint16_t g_3DD4;
uint8_t g_4331, g_4333, g_4365, g_4366;
uint16_t g_4340, g_4342, g_4344, g_4346;
struct Rect *g_5AAC;
static struct Rect clips[2];
static SimGraphicsDriver graphics;
static uint8_t pixels[640*480], fallback[128];
static int calls;

SimGraphicsDriver *sim_graphics_source_owner(void) { return &graphics; }
int sim_graphics_source_clip_active(void) { return g_5AAC != NULL; }
SimGraphicsCursorHooksStatus sim_graphics_cursor_hooks_bind(const SimGraphicsCursorHooks *h)
{ (void)h; return SIM_GRAPHICS_CURSOR_HOOKS_OK; }
void sim_graphics_cursor_hooks_unbind(void) { }
int sim_graphics_cursor_hooks_is_bound(void) { return 1; }
int sim_graphics_cursor_hooks_hide(void) { return 1; }
int sim_graphics_cursor_hooks_update(void) { return 1; }
int sim_graphics_cursor_hooks_redraw_if_shown(void) { return 1; }
static void observe_bitmap(int16_t x,int16_t y,char *data,int16_t w,int16_t h)
{ (void)x; (void)y; (void)w; (void)h; ++calls; memcpy(fallback,data,128); }
static int read_plane(void *context,uint8_t plane,uint16_t offset,uint8_t *output)
{ (void)context; return sim_graphics_tile_upload_read_plane(plane,offset,output,128)==SIM_GRAPHICS_TILE_UPLOAD_OK; }

void tile_test_reset(int clip, const uint8_t *planes)
{
    memset(&graphics,0,sizeof(graphics)); sim_vga_reset(&graphics.vga);
    memcpy(graphics.vga.planes,planes,sizeof(graphics.vga.planes));
    graphics.pixel_storage=pixels; graphics.video_mode=SIM_GRAPHICS_MODE_VGA_640X480;
    clips[0]=(struct Rect){0,0,640,480}; clips[1]=(struct Rect){0,INT16_MIN,0,0};
    g_5AAC=clip ? clips : NULL; g_4333=1; g_3DD4=0x8800; calls=0;
    (*(SimGraphicsBitmapCallback *)(void *)&driver_callback_table[9])=observe_bitmap;
    sim_graphics_tile_upload_bind(&graphics);
    portable_ega_map_readback_unbind(); portable_ega_map_readback_bind(read_plane,NULL);
}
int tile_test_call(int16_t x,int16_t y,uint16_t offset)
{ return sim_graphics_tile_cache_blit(x,y,offset); }
int tile_test_capture(int16_t left,int16_t top,int16_t right,int16_t bottom,uint8_t *data)
{
    sim_graphics_source_capture_bind(&graphics);
    (*(SimGraphicsCaptureCallback *)(void *)&driver_callback_table[8])(left,top,right,bottom,(char *)data);
    return graphics.last_status;
}
const uint8_t *tile_test_planes(void) { return &graphics.vga.planes[0][0]; }
const uint8_t *tile_test_fallback(void) { return fallback; }
const uint8_t *tile_test_pattern(void) { return (const uint8_t *)g_3D20; }
int tile_test_calls(void) { return calls; }
unsigned tile_test_state(unsigned field)
{
    switch(field) {
    case 0:return g_3DD4; case 1:return graphics.vga.map_mask;
    case 2:return graphics.vga.read_map; case 3:return graphics.vga.mode;
    case 4:return graphics.vga.graphics_index; case 5:return graphics.vga.sequencer_index;
    default:return 0;
    }
}
