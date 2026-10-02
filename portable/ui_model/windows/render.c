#include "render.h"

#include <limits.h>
#include <stdlib.h>

PortableRenderStatus portable_bios_font_provider_init(
    PortableBiosFontProvider *provider,
    const uint8_t *font_8x8,size_t font_8x8_size,
    const uint8_t *font_8x14,size_t font_8x14_size,
    const char *provider_id)
{
    if(provider==NULL || provider_id==NULL || provider_id[0]=='\0')
        return PORTABLE_RENDER_INVALID_ARGUMENT;
    if(font_8x8==NULL || font_8x8_size!=256u*8u ||
       font_8x14==NULL || font_8x14_size!=256u*14u)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    provider->font_8x8=(PortableBiosFontBitmap){font_8x8,font_8x8_size,8,8,
                                                provider_id};
    provider->font_8x14=(PortableBiosFontBitmap){font_8x14,font_8x14_size,8,14,
                                                 provider_id};
    return PORTABLE_RENDER_OK;
}

static PortableRect render_rect(PortableWindowRect r)
{
    PortableRect result={r.left,r.top,r.right,r.bottom};
    return result;
}

static void fill_patterned(PortableFramebuffer *fb, PortableRect r,
                           uint8_t foreground, uint8_t background)
{
    /* The first 16-byte screen fill pattern is the source's 55/AA checker
     * from m1B4E.asm:g_41C0. It is repeated as an 8-row pattern here. */
    static const uint8_t pattern[8]={0x55,0x55,0xaa,0xaa,0x55,0x55,0xaa,0xaa};
    portable_fill_pattern_1bpp(fb,r,pattern,foreground,background);
}

static void fill_color(PortableFramebuffer *fb, PortableRect r,
                       const uint8_t entry[6], uint8_t hardware_profile)
{
    if (entry[2]==entry[3] || (hardware_profile&1))
        portable_fill_rect(fb,r,entry[2]);
    else
        fill_patterned(fb,r,entry[3],entry[2]);
}

static void draw_outline(PortableFramebuffer *fb, PortableRect r,
                         int width, uint8_t color)
{
    if(width==0) return;
    portable_fill_rect(fb,(PortableRect){r.left+width,r.top+width,
                                          r.right-width,r.top},color);
    portable_fill_rect(fb,(PortableRect){r.left+width,r.bottom-width,
                                          r.right-width,r.bottom},color);
    portable_fill_rect(fb,(PortableRect){r.left+width,r.top,r.left,r.bottom},color);
    portable_fill_rect(fb,(PortableRect){r.right,r.top,r.right-width,r.bottom},color);
}

static void draw_horizontal_outline(PortableFramebuffer *fb, PortableRect r,
                                    int width, uint8_t color)
{
    if(width==0) return;
    portable_fill_rect(fb,(PortableRect){r.left+width,r.top+width,
                                          r.right-width,r.top},color);
    portable_fill_rect(fb,(PortableRect){r.left+width,r.bottom-width,
                                          r.right-width,r.bottom},color);
}

static void draw_vertical_outline(PortableFramebuffer *fb, PortableRect r,
                                  int width, uint8_t color)
{
    if(width==0) return;
    portable_fill_rect(fb,(PortableRect){r.left+width,r.top,r.left,r.bottom},color);
    portable_fill_rect(fb,(PortableRect){r.right,r.top,r.right-width,r.bottom},color);
}

static int read_u16(const uint8_t *p)
{
    return p[0] | ((int)p[1]<<8);
}

static int cstring_length(const uint8_t *bytes, size_t size, size_t *length)
{
    size_t i;
    for(i=0;i<size;i++) if(bytes[i]==0) { *length=i; return 1; }
    return 0;
}

static int has_percent(const uint8_t *text, size_t size)
{
    size_t i;
    for(i=0;i<size;i++) if(text[i]=='%') return 1;
    return 0;
}

static const PortableFont *select_font(const PortableWindowRenderer *renderer,
                                       unsigned source_id)
{
    if(source_id<2 || source_id>5) return NULL;
    return renderer->fonts[source_id-2];
}

static const PortableBiosFontBitmap *select_bios_font(
    const PortableWindowRenderer *renderer,unsigned source_id)
{
    int use_8x14;
    const PortableBiosFontBitmap *font;
    if(source_id>1 || renderer->bios_fonts==NULL) return NULL;
    /* f_24AB_02AD swaps g_912C and g_9130 at 320 pixels. The source font
     * initializers bind those callbacks to the 8x8 and 8x14 BIOS tables. */
    use_8x14=(source_id==0) ? renderer->screen_width!=320
                              : renderer->screen_width==320;
    font=use_8x14 ? &renderer->bios_fonts->font_8x14
                  : &renderer->bios_fonts->font_8x8;
    if(font->glyph_rows==NULL || font->glyph_width!=8 ||
       (font->glyph_height!=8 && font->glyph_height!=14) ||
       font->glyph_rows_size<(size_t)256*font->glyph_height)
        return NULL;
    return font;
}

static void draw_bios_bitmap_string(PortableFramebuffer *framebuffer,
                                    const PortableBiosFontBitmap *font,
                                    int32_t x,int32_t y,const uint8_t *text,
                                    size_t length,uint8_t color)
{
    size_t i;
    for(i=0;i<length;i++) {
        const uint8_t *glyph=font->glyph_rows+(size_t)text[i]*font->glyph_height;
        unsigned row,col;
        int64_t glyph_x=(int64_t)x+(int64_t)i*font->glyph_width;
        for(row=0;row<font->glyph_height;row++) {
            uint8_t bits=glyph[row];
            for(col=0;col<font->glyph_width;col++)
                if(bits&(uint8_t)(0x80u>>col))
                    portable_put_pixel(framebuffer,(int32_t)(glyph_x+col),
                                       y+(int32_t)row,color);
        }
    }
}

static PortableRenderStatus draw_justified_text(
    const PortableWindowRenderer *renderer, const uint8_t *text, size_t length,
    PortableRect rect, unsigned justification, uint8_t color, unsigned font_id)
{
    const PortableFont *font=select_font(renderer,font_id);
    const PortableBiosFontBitmap *bios_font=NULL;
    int32_t text_width,text_height,x,y;
    if(length==0) return PORTABLE_RENDER_OK;
    if(font==NULL) {
        bios_font=select_bios_font(renderer,font_id);
        if(bios_font==NULL || length>(size_t)INT32_MAX/8u)
            return PORTABLE_RENDER_UNSUPPORTED_MODE;
        text_width=(int32_t)(length*8u);
        text_height=bios_font->glyph_height;
    } else {
        text_width=portable_font_string_width(font,text,length);
        text_height=font->metrics[7];
    }
    switch(justification) {
    case 0: x=rect.left+(rect.right-rect.left-text_width)/2; break;
    case 1: x=rect.left+4; break;
    case 2: x=rect.right-text_width-4; break;
    /* Mode 3 also paints the two surrounding bands using the DOS display
     * driver's g_3DE2 color and g_3DDC cell height. Those inputs are not yet
     * supplied to this renderer, so do not approximate that behavior. */
    case 3: return PORTABLE_RENDER_UNSUPPORTED_MODE;
    default: return PORTABLE_RENDER_UNSUPPORTED_MODE;
    }
    if(x<rect.left) x=rect.left;
    y=(rect.bottom+rect.top-text_height)/2;
    {
        PortableRect old_clip=renderer->framebuffer->clip;
        PortableRect clip=rect;
        if(clip.left<old_clip.left)clip.left=old_clip.left;
        if(clip.top<old_clip.top)clip.top=old_clip.top;
        if(clip.right>old_clip.right)clip.right=old_clip.right;
        if(clip.bottom>old_clip.bottom)clip.bottom=old_clip.bottom;
        portable_framebuffer_set_clip(renderer->framebuffer,clip);
        if(font!=NULL &&
           portable_font_draw(renderer->framebuffer,font,x,y,text,length,color,NULL)
           !=PORTABLE_RENDER_OK) {
            portable_framebuffer_set_clip(renderer->framebuffer,old_clip);
            return PORTABLE_RENDER_INVALID_RESOURCE;
        }
        if(bios_font!=NULL)
            draw_bios_bitmap_string(renderer->framebuffer,bios_font,x,y,text,
                                    length,color);
        portable_framebuffer_set_clip(renderer->framebuffer,old_clip);
    }
    return PORTABLE_RENDER_OK;
}

static PortableRenderStatus draw_simple_text(
    const PortableWindowObject *object, uint16_t index,
    const PortableWindowResource *window,
    const PortableWindowRenderer *renderer, const uint8_t entry[6])
{
    size_t length;
    unsigned font_id=object->resource_bytes[0x28];
    (void)index;
    (void)window;
    if(!cstring_length(object->resource_bytes+0x2a,
                       object->resource_size-0x2a,&length))
        return PORTABLE_RENDER_INVALID_RESOURCE;
    return draw_justified_text(renderer,object->resource_bytes+0x2a,length,
                               render_rect(object->rect),
                               (object->flags&0x180u)>>7,entry[0],font_id);
}

static PortableRenderStatus draw_formatted_text(
    const PortableWindowObject *object, uint16_t index,
    const PortableWindowResource *window,
    const PortableWindowRenderer *renderer, const uint8_t entry[6])
{
    const uint8_t *text;
    size_t length;
    size_t start=0x2e;
    size_t remaining;
    unsigned font_id=object->resource_bytes[0x28];
    uint32_t text_pointer=(uint32_t)read_u16(object->resource_bytes+0x2a) |
                         ((uint32_t)read_u16(object->resource_bytes+0x2c)<<16);
    if(start>object->resource_size) return PORTABLE_RENDER_INVALID_RESOURCE;
    if(renderer->resolve_text!=NULL &&
       renderer->resolve_text(renderer->text_context,window->resource_id,index,
                              object->resource_bytes+start,
                              object->resource_size-start,&text,&length)) {
        /* Native projections may resolve known formatted objects without
         * manufacturing the runtime far pointer written by the DOS caller. */
    } else {
        if(text_pointer!=0) return PORTABLE_RENDER_UNSUPPORTED_MODE;
        text=object->resource_bytes+start;
        remaining=object->resource_size-start;
        if(!cstring_length(text,remaining,&length))
            return PORTABLE_RENDER_INVALID_RESOURCE;
        /* The DOS renderer leaves literal printf templates blank until its
         * formatted-text state is enabled. */
        if(!renderer->formatting_enabled && has_percent(text,length))
            return PORTABLE_RENDER_OK;
    }
    return draw_justified_text(renderer,text,length,render_rect(object->rect),
                               (object->flags&0x180u)>>7,entry[0],font_id);
}

static PortableRenderStatus draw_image(const PortableWindowRenderer *renderer,
                                       int16_t id, int32_t x, int32_t y,
                                       int32_t *width, int32_t *height)
{
    PortableDbRecord record={0};
    PortableBitmap bitmap;
    PortableRenderStatus status;
    PortableDbStatus db_status=portable_db_load(renderer->database,id,2,&record);
    if(db_status!=PORTABLE_DB_OK) return PORTABLE_RENDER_INVALID_RESOURCE;
    status=portable_bitmap_view(record.data,record.size,&bitmap);
    if(status==PORTABLE_RENDER_OK) {
        if(width)*width=bitmap.width;
        if(height)*height=bitmap.height;
    }
    status=portable_bitmap_draw_resource(renderer->framebuffer,x,y,
                                         record.data,record.size);
    portable_db_record_free(&record);
    return status;
}

static PortableRenderStatus measure_image(const PortableWindowRenderer *renderer,
                                          int16_t id,int32_t *width,int32_t *height)
{
    PortableDbRecord record={0};
    PortableBitmap bitmap;
    const uint8_t *bytes;
    size_t size;
    uint8_t *decoded=NULL;
    size_t decoded_size=0;
    PortableRenderStatus status;
    if(portable_db_load(renderer->database,id,2,&record)!=PORTABLE_DB_OK)
        return PORTABLE_RENDER_INVALID_RESOURCE;
    bytes=record.data; size=record.size;
    if(size>=2 && (bytes[0]==0xff || bytes[0]==0x00) &&
       (bytes[1]==0xff || bytes[1]==0x80)) {
        status=portable_bitmap_decode_packed(bytes,size,&decoded,&decoded_size);
        if(status!=PORTABLE_RENDER_OK) goto done;
        bytes=decoded; size=decoded_size;
    }
    status=portable_bitmap_view(bytes,size,&bitmap);
    if(status==PORTABLE_RENDER_OK) {
        if(width)*width=bitmap.width;
        if(height)*height=bitmap.height;
    }
done:
    portable_bitmap_release_decoded(decoded);
    portable_db_record_free(&record);
    return status;
}

static PortableRenderStatus draw_button_border(
    const PortableWindowObject *object,const PortableWindowRenderer *renderer,
    const uint8_t entry[6])
{
    PortableRect r=render_rect(object->rect);
    if(object->flags&4) {
        draw_outline(renderer->framebuffer,r,3,entry[0]);
        if(!(renderer->hardware_profile&1))
            draw_outline(renderer->framebuffer,r,2,entry[3]);
    } else {
        int i;
        for(i=3;i>0;i--) {
            draw_horizontal_outline(renderer->framebuffer,r,i,entry[3]);
            if(entry[2]==entry[3] || (renderer->hardware_profile&1))
                draw_vertical_outline(renderer->framebuffer,r,i,entry[2]);
            else {
                static const uint8_t pattern[8]={0x55,0x55,0xaa,0xaa,
                                                  0x55,0x55,0xaa,0xaa};
                PortableRect left={r.left+i,r.top,r.left,r.bottom};
                PortableRect right={r.right,r.top,r.right-i,r.bottom};
                portable_fill_pattern_1bpp(renderer->framebuffer,left,pattern,
                                           entry[2],entry[3]);
                portable_fill_pattern_1bpp(renderer->framebuffer,right,pattern,
                                           entry[2],entry[3]);
            }
        }
    }
    return PORTABLE_RENDER_OK;
}

static PortableRenderStatus draw_object(
    const PortableWindowResource *window,uint16_t index,
    const PortableWindowObject *object,const PortableWindowRenderer *renderer,
    const uint8_t entry[6])
{
    PortableRect r=render_rect(object->rect);
    int width=(int)(int8_t)object->resource_bytes[0x28];
    PortableRenderStatus status=PORTABLE_RENDER_OK;
    switch(object->type) {
    case 0:
        fill_color(renderer->framebuffer,r,entry,renderer->hardware_profile);
        draw_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    case 1:
        break;
    case 2:
        fill_color(renderer->framebuffer,r,entry,renderer->hardware_profile);
        break;
    case 5: case 17:
        portable_fill_rect(renderer->framebuffer,r,entry[2]);
        status=draw_button_border(object,renderer,
                    renderer->colors+(size_t)object->resource_bytes[0x26]*6);
        if(status==PORTABLE_RENDER_OK)
            status=object->type==5
                ? draw_simple_text(object,index,window,renderer,entry)
                : draw_formatted_text(object,index,window,renderer,entry);
        break;
    case 9:
        status=draw_simple_text(object,index,window,renderer,entry);
        break;
    case 6: case 13: {
        int16_t id;
        if(object->type==6) id=object->has_bitmap_override
            ? object->bitmap_override : (int16_t)read_u16(object->resource_bytes+0x28);
        else id=(int16_t)read_u16(object->resource_bytes+
                         ((object->flags&4u)?0x28:0x2a));
        status=draw_image(renderer,id,r.left,r.top,NULL,NULL);
        break;
    }
    case 12: case 18:
        fill_color(renderer->framebuffer,r,entry,renderer->hardware_profile);
        portable_fill_rect(renderer->framebuffer,
                           (PortableRect){r.left,r.bottom-1,r.right,r.bottom},entry[0]);
        status=draw_formatted_text(object,index,window,renderer,entry);
        break;
    case 15:
        draw_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    case 16:
        status=draw_formatted_text(object,index,window,renderer,entry);
        break;
    case 19:
        draw_horizontal_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    case 20:
        draw_vertical_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    case 21:
        fill_color(renderer->framebuffer,r,entry,renderer->hardware_profile);
        draw_horizontal_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    case 22:
        fill_color(renderer->framebuffer,r,entry,renderer->hardware_profile);
        draw_vertical_outline(renderer->framebuffer,r,width,entry[0]);
        break;
    default:
        return PORTABLE_RENDER_UNSUPPORTED_MODE;
    }
    if(status==PORTABLE_RENDER_OK && (object->flags&4u) &&
       (object->type==1 || object->type==6))
        portable_xor_rect(renderer->framebuffer,r,15);
    return status;
}

static PortableRenderStatus draw_window_decoration(
    const PortableWindowResource *window,const PortableWindowRenderer *renderer)
{
    PortableWindowRect base=window->rect;
    int32_t m;
    int32_t width,height;
    PortableRenderStatus status;
    const unsigned flags=window->flags;
    if((flags&(4|8|0x10|0x100|0x400))==0) return PORTABLE_RENDER_OK;
    if(window->count==0) return PORTABLE_RENDER_INVALID_RESOURCE;
    m=window->objects[0].resource_bytes[0x28];
    base.bottom=(int16_t)(base.bottom-m);
    if(renderer->screen_width==320) m/=2;
    base.left=(int16_t)(base.left+m);
    base.right=(int16_t)(base.right-m);
    base.top=(int16_t)(base.top+m);
    if(flags&4) {
        status=draw_image(renderer,0x64,base.left,base.top,&width,&height);
        if(status!=PORTABLE_RENDER_OK)return status;
        base.left=(int16_t)(base.left+width);
    }
    if(flags&8) {
        status=measure_image(renderer,0x70,&width,&height);
        if(status!=PORTABLE_RENDER_OK)return status;
        status=draw_image(renderer,0x70,base.right-width,base.bottom-height,NULL,NULL);
        if(status!=PORTABLE_RENDER_OK)return status;
    }
    if(flags&0x100) {
        int16_t id=(flags&0x80)?0x66:0x67;
        status=measure_image(renderer,id,&width,&height);
        if(status!=PORTABLE_RENDER_OK)return status;
        base.right=(int16_t)(base.right-width);
        status=draw_image(renderer,id,base.right,base.top,NULL,NULL);
        if(status!=PORTABLE_RENDER_OK)return status;
    }
    if(flags&0x10) {
        status=draw_image(renderer,0x65,base.left,base.top,NULL,NULL);
        if(status!=PORTABLE_RENDER_OK)return status;
    }
    if(flags&0x400) {
        status=measure_image(renderer,0x69,&width,&height);
        if(status!=PORTABLE_RENDER_OK)return status;
        base.right=(int16_t)(base.right-width);
        status=draw_image(renderer,0x69,base.right,base.top,NULL,NULL);
        if(status!=PORTABLE_RENDER_OK)return status;
    }
    return PORTABLE_RENDER_OK;
}

PortableRenderStatus portable_window_draw_native(
    const PortableWindowResource *window,const PortableWindowRenderer *renderer)
{
    size_t i;
    if(!window || !renderer || !renderer->framebuffer || !renderer->database ||
       !renderer->colors) return PORTABLE_RENDER_INVALID_ARGUMENT;
    if(window->flags & 0x20) return PORTABLE_RENDER_OK;
    for(i=0;i<window->count;i++) {
        const PortableWindowObject *object=&window->objects[i];
        uint8_t color_index=(uint8_t)((object->flags&4)?object->value>>8:object->value);
        const uint8_t *entry;
        PortableRect rect=render_rect(object->rect);
        PortableRect old_clip=renderer->framebuffer->clip;
        PortableRenderStatus status;
        if(!(object->flags&1)) continue;
        if((size_t)color_index*6+6>renderer->colors_size)
            return PORTABLE_RENDER_INVALID_RESOURCE;
        entry=renderer->colors+(size_t)color_index*6;
        if(object->flags&0x200) {
            if(rect.left<old_clip.left) rect.left=old_clip.left;
            if(rect.top<old_clip.top) rect.top=old_clip.top;
            if(rect.right>old_clip.right) rect.right=old_clip.right;
            if(rect.bottom>old_clip.bottom) rect.bottom=old_clip.bottom;
            portable_framebuffer_set_clip(renderer->framebuffer,rect);
        }
        status=draw_object(window,(uint16_t)i,object,renderer,entry);
        portable_framebuffer_set_clip(renderer->framebuffer,old_clip);
        if(status!=PORTABLE_RENDER_OK) return status;
    }
    return draw_window_decoration(window,renderer);
}
