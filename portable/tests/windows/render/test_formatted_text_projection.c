#include "../../../ui_model/windows/render.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ResolverState { int calls; int resolve; } ResolverState;

static int resolve_title(void *context,int16_t window_id,uint16_t object_index,
                         const uint8_t *format,size_t format_size,
                         const uint8_t **text,size_t *text_size)
{
    ResolverState *state=(ResolverState *)context;
    static const uint8_t resolved[]="A";
    state->calls++;
    assert(window_id==0x1901 && object_index==0);
    assert(format_size>=3 && format[0]=='%' && format[1]=='s' && format[2]==0);
    if(!state->resolve)return 0;
    *text=resolved;
    *text_size=1;
    return 1;
}

static uint8_t *read_file(const char *path,size_t *size)
{
    FILE *file=fopen(path,"rb");
    long length;
    uint8_t *bytes;
    assert(file!=NULL && fseek(file,0,SEEK_END)==0);
    length=ftell(file);
    assert(length>=0 && fseek(file,0,SEEK_SET)==0);
    bytes=(uint8_t *)malloc((size_t)length);
    assert(bytes!=NULL || length==0);
    assert(fread(bytes,1,(size_t)length,file)==(size_t)length);
    assert(fclose(file)==0);
    *size=(size_t)length;
    return bytes;
}

int main(int argc,char **argv)
{
    uint8_t resource_bytes[0x31]={0};
    uint8_t pixels[64*32];
    uint8_t colors[6]={15,15,0,0,0,0};
    uint8_t *font_bytes;
    size_t font_size;
    PortableFont font;
    PortableDatabase database={0};
    PortableFramebuffer framebuffer;
    PortableWindowRenderer renderer={0};
    PortableWindowObject object={0};
    PortableWindowResource window={0};
    ResolverState resolver={0};
    assert(argc==3);
    font_bytes=read_file(argv[2],&font_size);
    portable_font_init(&font);
    assert(portable_font_load(&font,font_bytes,font_size)==PORTABLE_RENDER_OK);
    free(font_bytes);
    assert(portable_framebuffer_init(&framebuffer,64,32,64,pixels)==PORTABLE_RENDER_OK);
    renderer.framebuffer=&framebuffer;
    renderer.database=&database;
    renderer.colors=colors;
    renderer.colors_size=sizeof(colors);
    renderer.screen_width=640;
    renderer.fonts[0]=&font;
    renderer.resolve_text=resolve_title;
    renderer.text_context=&resolver;
    window.resource_id=0x1901;
    window.count=1;
    window.objects=&object;
    object.resource_size=sizeof(resource_bytes);
    object.resource_bytes=resource_bytes;
    object.type=16;
    object.flags=PORTABLE_WINDOW_OBJECT_VISIBLE;
    object.value=0;
    object.rect=(PortableWindowRect){2,2,48,22};
    resource_bytes[0x21]=16;
    resource_bytes[0x28]=2;
    memcpy(resource_bytes+0x2e,"%s",3);

    /* The model resolves a known title with a zero serialized DOS far pointer. */
    resolver.resolve=1;
    assert(portable_window_draw_native(&window,&renderer)==PORTABLE_RENDER_OK);
    assert(resolver.calls==1);
    {
        size_t i;
        int drew=0;
        for(i=0;i<sizeof(pixels);i++)if(pixels[i]!=0)drew=1;
        assert(drew);
    }

    /* A failed projection preserves the original zero-pointer literal fallback. */
    memset(pixels,0,sizeof(pixels));
    resolver.calls=0;
    resolver.resolve=0;
    renderer.formatting_enabled=0;
    assert(portable_window_draw_native(&window,&renderer)==PORTABLE_RENDER_OK);
    assert(resolver.calls==1);
    {
        size_t i;
        for(i=0;i<sizeof(pixels);i++)assert(pixels[i]==0);
    }

    /* A nonzero DOS pointer still requires a successful native projection. */
    resource_bytes[0x2a]=1;
    assert(portable_window_draw_native(&window,&renderer)==PORTABLE_RENDER_UNSUPPORTED_MODE);
    assert(resolver.calls==2);
    portable_font_destroy(&font);
    puts("formatted projection override, zero-pointer fallback, and nonzero-pointer failure passed");
    return 0;
}
