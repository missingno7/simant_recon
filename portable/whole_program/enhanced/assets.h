#ifndef SIMANT_ENHANCED_ASSETS_H
#define SIMANT_ENHANCED_ASSETS_H
#include <stdint.h>
#include <stddef.h>
typedef struct EnhancedArt { int id, width, height; const uint8_t *pixels; } EnhancedArt;
/* Loaded after the desktop verifier, before DOS main. Native malloc only.
 * All access is const after initialization; transparent pixels are 255. */
int enhanced_assets_load(const char *verified_root);
const char *enhanced_assets_error(void);
void enhanced_assets_free(void);
const EnhancedArt *enhanced_art(int id);
/* Immutable decompressed resources, independent of the game's resource cache. */
const uint8_t *enhanced_resource(int id,int kind,size_t *size);
int enhanced_asset_cell(int terrain, unsigned ground, unsigned life, uint8_t pixels[256]);
int enhanced_font_width(const char *text);
int enhanced_font_height(void);
void enhanced_font_draw(uint8_t *dst,int w,int h,int stride,int x,int y,const char *text,uint8_t color);
#endif
