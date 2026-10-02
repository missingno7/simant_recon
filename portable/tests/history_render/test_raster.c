#include "../../ui_model/windows/history_render.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Context {
    PortableHistoryRect rect;
    const PortableFont *font;
} Context;

static int get_rect(void *opaque,int16_t window_id,int16_t object_id,
                    PortableHistoryRect *rect)
{
    Context *context=(Context *)opaque;
    if(window_id!=PORTABLE_HISTORY_WINDOW_ID || object_id!=PORTABLE_HISTORY_OBJECT_ID)
        return 0;
    *rect=context->rect;
    return 1;
}

static int get_height(void *opaque,int16_t *height)
{
    Context *context=(Context *)opaque;
    *height=context->font->metrics[7];
    return 1;
}

static int get_width(void *opaque,const char *text,size_t size,int16_t *width)
{
    Context *context=(Context *)opaque;
    int32_t result=portable_font_string_width(context->font,(const uint8_t *)text,size);
    if(result<INT16_MIN || result>INT16_MAX) return 0;
    *width=(int16_t)result;
    return 1;
}

static int resolve_color(void *opaque,int16_t source_color,uint8_t *color)
{
    (void)opaque;
    if(source_color!=0x43) return 0;
    *color=7;
    return 1;
}

int main(int argc,char **argv)
{
    FILE *file;
    long file_size;
    uint8_t *font_bytes,*color_bytes;
    size_t color_size;
    PortableFont font;
    PortableDatabase windows_db,shared_db;
    PortableDbRecord color_record={0};
    PortableWindowRegistry registry;
    PortableWindowRenderer renderer;
    PortableHistoryActiveResources active;
    PortableHistoryUiSnapshot ui;
    PortableHistoryWindowInput window_input;
    int16_t session_series[10][64];
    uint8_t pixels[640*480];
    PortableFramebuffer framebuffer;
    PortableHistoryInput input;
    PortableHistoryProviders providers;
    PortableHistoryRasterProviders raster;
    PortableHistoryCommand commands[PORTABLE_HISTORY_MAX_COMMANDS];
    size_t count,i,changed=0;
    Context context={{0,0,320,200},&font};
    assert(argc==4);
    file=fopen(argv[1],"rb"); assert(file!=NULL);
    assert(fseek(file,0,SEEK_END)==0); file_size=ftell(file); assert(file_size>0);
    assert(fseek(file,0,SEEK_SET)==0);
    font_bytes=(uint8_t *)malloc((size_t)file_size); assert(font_bytes!=NULL);
    assert(fread(font_bytes,1,(size_t)file_size,file)==(size_t)file_size); fclose(file);
    portable_font_init(&font);
    assert(portable_font_load(&font,font_bytes,(size_t)file_size)==PORTABLE_RENDER_OK);
    memset(&input,0,sizeof(input));
    input.start=0; input.count=64; input.graph=0; input.hilite=0; input.slot=0;
    input.history_color[0]=0;
    input.graph_colors[0]=0x43;
    input.labels[0]="NEST"; input.label_sizes[0]=4;
    for(i=0;i<64;i++) {
        input.series[0][i]=(int16_t)(i*2);
        input.series[1][i]=(int16_t)(i);
    }
    providers.context=&context;
    providers.get_object_rect=get_rect;
    providers.get_font_height=get_height;
    providers.get_text_width=get_width;
    providers.get_fill_color=NULL;
    assert(portable_history_render_graph(&input,&providers,commands,
        PORTABLE_HISTORY_MAX_COMMANDS,&count)==PORTABLE_HISTORY_OK);
    assert(count==68);
    assert(portable_framebuffer_init(&framebuffer,640,480,640,pixels)==PORTABLE_RENDER_OK);
    memset(pixels,0,sizeof(pixels));
    raster.context=&context;
    raster.framebuffer=&framebuffer;
    raster.font3=&font;
    raster.resolve_color=resolve_color;
    raster.fill_object=NULL;
    assert(portable_history_rasterize(commands,count,&raster)==PORTABLE_HISTORY_OK);
    for(i=0;i<sizeof(pixels);i++) if(pixels[i]!=0) changed++;
    assert(changed>0);

    /* Bind real source resources and a current session snapshot through the
     * renderer's public normalized-command API. */
    memset(&windows_db,0,sizeof(windows_db));
    memset(&shared_db,0,sizeof(shared_db));
    memset(&registry,0,sizeof(registry));
    memset(&renderer,0,sizeof(renderer));
    memset(&active,0,sizeof(active));
    memset(&ui,0,sizeof(ui));
    memset(session_series,0,sizeof(session_series));
    assert(portable_db_open(&windows_db,argv[2])==PORTABLE_DB_OK);
    assert(portable_db_open(&shared_db,argv[3])==PORTABLE_DB_OK);
    assert(portable_window_registry_init(&registry,&windows_db,0)==
        PORTABLE_WINDOW_REGISTRY_OK);
    assert(portable_db_load(&windows_db,0x81,0,&color_record)==PORTABLE_DB_OK);
    color_bytes=color_record.data;
    color_size=color_record.size;
    assert(color_bytes!=NULL && color_size>=16u*6u);
    renderer.database=&windows_db;
    renderer.colors=color_bytes;
    renderer.colors_size=color_size;
    renderer.fonts[1]=&font;
    assert(portable_history_active_resources_load(&active,&shared_db,
        &registry,&renderer)==PORTABLE_HISTORY_OK);
    assert(active.labels.count>=10 && active.labels.items[0]!=NULL);
    ui.graph_colors[0]=0x43;
    ui.history_color[0]=0;
    ui.shown_graphs[0]=0;
    ui.shown_graphs[1]=ui.shown_graphs[2]=ui.shown_graphs[3]=(int16_t)0x8000;
    for(i=0;i<64;i++) session_series[0][i]=(int16_t)(i+1);
    assert(portable_history_bind_window(&window_input,session_series,0,64,2,
        &ui,&active.labels)==PORTABLE_HISTORY_OK);
    portable_history_active_providers(&active,&providers);
    assert(portable_history_render_window(&window_input,&providers,commands,
        sizeof(commands)/sizeof(commands[0]),&count)==PORTABLE_HISTORY_OK);
    assert(count==70 && commands[0].kind==PORTABLE_HISTORY_FILL_OBJECT);
    memset(pixels,0,sizeof(pixels));
    assert(portable_framebuffer_init(&framebuffer,640,480,640,pixels)==PORTABLE_RENDER_OK);
    portable_history_active_raster_providers(&active,&framebuffer,&raster);
    assert(portable_history_rasterize(commands,count,&raster)==PORTABLE_HISTORY_OK);
    changed=0;
    for(i=0;i<sizeof(pixels);i++) if(pixels[i]!=0) changed++;
    assert(changed>0);
    printf("history raster: %zu pixels touched; logical resource/session binding passed; DOS pixels unverified\n",changed);
    portable_history_active_resources_free(&active);
    portable_window_registry_destroy(&registry);
    portable_db_record_free(&color_record);
    portable_db_close(&shared_db);
    portable_db_close(&windows_db);
    portable_font_destroy(&font);
    free(font_bytes);
    return 0;
}
