#include "../../../ui_model/windows/render.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t glyph_row(unsigned code,unsigned row)
{
    unsigned shift=row%5u;
    return (uint8_t)(((code*29u+row*71u)^((code>>shift)*11u)^
                      (0x81u>>(row%8u)))&0xffu);
}

static uint32_t pixel_hash(const uint8_t *pixels,size_t size)
{
    size_t i;
    uint32_t hash=2166136261u;
    for(i=0;i<size;i++) { hash^=pixels[i]; hash*=16777619u; }
    return hash;
}

static void make_font(uint8_t *rows,unsigned height)
{
    unsigned code,row;
    for(code=0;code<256;code++)
        for(row=0;row<height;row++)
            rows[code*height+row]=glyph_row(code,row);
}

static void check_font(unsigned font_id,unsigned screen_width,unsigned height,
                       const PortableBiosFontProvider *provider)
{
    uint8_t pixels[8*14];
    uint8_t colors[6]={3,0,3,3,0,0};
    uint8_t object_bytes[0x2c]={0};
    PortableWindowObject object={0};
    PortableWindowResource window={0};
    PortableDatabase database={0};
    PortableFramebuffer framebuffer;
    PortableWindowRenderer renderer={0};
    unsigned row,col;
    const unsigned char code=0xa5;
    object_bytes[0x28]=(uint8_t)font_id;
    object_bytes[0x2a]=code;
    object_bytes[0x2b]=0;
    object.type=9;
    object.flags=1;
    object.rect=(PortableWindowRect){0,0,8,(int16_t)height};
    object.resource_bytes=object_bytes;
    object.resource_size=sizeof(object_bytes);
    window.objects=&object;
    window.count=1;
    memset(pixels,0,sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer,8,height,8,pixels)==PORTABLE_RENDER_OK);
    renderer.framebuffer=&framebuffer;
    renderer.database=&database;
    renderer.colors=colors;
    renderer.colors_size=sizeof(colors);
    renderer.screen_width=(uint16_t)screen_width;
    renderer.bios_fonts=provider;
    assert(portable_window_draw_native(&window,&renderer)==PORTABLE_RENDER_OK);
    for(row=0;row<height;row++) {
        uint8_t expected=glyph_row(code,row);
        for(col=0;col<8;col++) {
            uint8_t actual=pixels[row*8+col];
            uint8_t want=(expected&(uint8_t)(0x80u>>col))?3:0;
            assert(actual==want);
        }
    }
    printf("font_id=%u screen_width=%u glyph_height=%u raster_contract=pass pixel_fnv1a=%08x glyph_rows=",
           font_id,screen_width,height,pixel_hash(pixels,8*height));
    for(row=0;row<height;row++) printf("%02x",glyph_row(code,row));
    putchar('\n');
}

int main(void)
{
    uint8_t rows8[256*8],rows14[256*14];
    uint8_t colors[6]={3,0,3,3,0,0};
    uint8_t object_bytes[0x2c]={0};
    PortableBiosFontProvider provider={0};
    PortableWindowObject object={0};
    PortableWindowResource window={0};
    PortableDatabase database={0};
    PortableFramebuffer framebuffer;
    PortableWindowRenderer renderer={0};
    uint8_t pixels[8*14];
    make_font(rows8,8);
    make_font(rows14,14);
    provider.font_8x8=(PortableBiosFontBitmap){rows8,sizeof(rows8),8,8,
                                               "controlled-fixture-8x8"};
    provider.font_8x14=(PortableBiosFontBitmap){rows14,sizeof(rows14),8,14,
                                                "controlled-fixture-8x14"};
    check_font(0,640,14,&provider);
    check_font(1,640,8,&provider);
    check_font(0,320,8,&provider);
    check_font(1,320,14,&provider);

    object_bytes[0x28]=0;
    object_bytes[0x2a]='A'; object_bytes[0x2b]=0;
    object.type=9; object.flags=1;
    object.rect=(PortableWindowRect){0,0,8,14};
    object.resource_bytes=object_bytes; object.resource_size=sizeof(object_bytes);
    window.objects=&object; window.count=1;
    memset(pixels,0,sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer,8,14,8,pixels)==PORTABLE_RENDER_OK);
    renderer.framebuffer=&framebuffer; renderer.database=&database;
    renderer.colors=colors;
    renderer.colors_size=sizeof(colors); renderer.screen_width=640;
    renderer.bios_fonts=&provider;
    provider.font_8x14.glyph_rows_size--;
    assert(portable_window_draw_native(&window,&renderer)==PORTABLE_RENDER_UNSUPPORTED_MODE);
    puts("malformed_provider=explicitly_unsupported");
    return 0;
}
