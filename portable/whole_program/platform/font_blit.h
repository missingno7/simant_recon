#ifndef SIMANT_WHOLE_FONT_BLIT_H
#define SIMANT_WHOLE_FONT_BLIT_H

#include <stddef.h>
#include <stdint.h>
#include "../types/fonts.h"

/* Native safe owner for the shared glyph bitmap. The frozen source declares
 * g_5ABE as 1040 bytes while font_MakeImage clears 1280; the native span keeps
 * the required clear and bounded supported glyph rows inside owned storage. */
#define SIM_FONT_BITMAP_CAPACITY 1280u
extern char g_5ABE[SIM_FONT_BITMAP_CAPACITY];
extern struct Bitmap fd_50F6_392C;
extern int16_t fd_55B3_6770; /* source bytes per glyph row */
extern int16_t fd_55B3_6772; /* destination bytes per bitmap row */

struct Bitmap *sim_font_bitmap_bind(void);
/* Checked native boundary around the generated source renderer. A NULL result
 * means the source dimensions exceeded the owned font/image spans. */
struct Bitmap *sim_font_make_image(uint8_t *text, int16_t x, struct Font *font);
/* Original public symbol, supplied by this checked adapter while the generated
 * definition is compiled under sim_font_make_image_source. */
struct Bitmap *font_MakeImage(uint8_t *text, int16_t x, struct Font *font);
void sim_font_blit_reset_status(void);
int sim_font_blit_last_status(void);

/* Source ABI for the genuine assembly entries in root:m2650.asm. */
void f_2650_000F(char *source, char *destination, int16_t width,
                 int16_t height, int16_t source_x, int16_t destination_x);

#endif
