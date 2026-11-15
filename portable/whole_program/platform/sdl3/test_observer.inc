/* Output-only acceptance observations. Inert without output paths. */
#include "audio_observer.inc"
void portable_test_step_boundary(unsigned step,unsigned phase) {
  test_audio_load();test_step=step;test_phase=phase;
}
extern uint64_t portable_test_audio_isr_periods(void) __attribute__((weak));
void portable_test_diagnostics(FILE *f) {
  if(portable_test_audio_isr_periods)
    fprintf(f,"\"audio_content_isr_periods\":%" PRIu64 ",",portable_test_audio_isr_periods());
  test_audio_close();
  fputs("\"observation_only\":true",f);
}
/* v7 checkpoint hook. Copy current source-owned aperture and palette only.
 * The caller binds palette storage from this executable's DWARF. Do not sync,
 * present, poll input, clear written, read VGA ports or alter VGA latches. */
#ifdef SIMANT_TEST_FRAMES
#include "../graphics.h"
#include "palette_host.h"
void portable_test_screen(FILE *f, const void *palette_address) {
  const SimGraphicsDriver *g = sim_graphics_source_owner();
  const SimSdlPaletteHost *p = palette_address;
  if (!g || !p || g->video_mode != SIM_GRAPHICS_MODE_VGA_640X480 || !p->ready)
    abort();
  uint32_t h[24] = {0x37464153,640,480,0x12,0,80,0,0,1023,15,6,255,0,0};
  /* Native has no INT33 driver: these fields are explicitly not applicable. */
  for (unsigned i=14;i<22;++i) h[i]=UINT32_MAX;
  uint8_t pixels[640*480], masks[64] = {0};
  for (unsigned y=0;y<480;++y) for (unsigned x=0;x<640;++x) {
    unsigned color=0,offset=y*80+x/8;
    for (unsigned plane=0;plane<4;++plane)
      color|=((g->vga.planes[plane][offset]>>(7-(x&7)))&1)<<plane;
    pixels[y*640+x]=(uint8_t)color;
  }
  if (fwrite(h,sizeof(h),1,f)!=1 || fwrite(p->attribute,1,16,f)!=16 ||
      fwrite(p->dac6,1,768,f)!=768 || fwrite(p->dac_written,1,256,f)!=256 ||
      fwrite(p->presentation.rgb,1,48,f)!=48 || fwrite(masks,1,64,f)!=64 ||
      fwrite(pixels,1,sizeof(pixels),f)!=sizeof(pixels)) abort();
  /* The OS/SDL pointer is a compositor overlay, outside indexed scanout.
   * Retain the read-only SDL visibility query as a separate limitation. */
  fprintf(stderr,"Observer host cursor visible=%u\n",(unsigned)SDL_CursorVisible());
}
#endif
