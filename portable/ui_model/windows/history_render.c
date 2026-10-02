#include "history_render.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t history_table_a[PORTABLE_HISTORY_SERIES_COUNT]={
    0,2,4,6,7,1,3,5,8,9
};
static const uint8_t history_table_b[PORTABLE_HISTORY_SERIES_COUNT]={
    1,3,5,6,9,0,2,4,9,8
};

static void raster_line(PortableFramebuffer *fb,int32_t x0,int32_t y0,
                        int32_t x1,int32_t y1,uint8_t color)
{
    int32_t dx=(x1>=x0) ? x1-x0 : x0-x1;
    int32_t sx=(x0<x1) ? 1 : -1;
    int32_t dy=(y1>=y0) ? y0-y1 : y1-y0;
    int32_t sy=(y0<y1) ? 1 : -1;
    int32_t error=dx+dy;
    for(;;) {
        int32_t twice;
        portable_put_pixel(fb,x0,y0,color);
        if(x0==x1 && y0==y1) break;
        twice=2*error;
        if(twice>=dy) { error+=dy; x0+=sx; }
        if(twice<=dx) { error+=dx; y0+=sy; }
    }
}

static int raster_resolve(const PortableHistoryRasterProviders *providers,
                          int16_t source_color,uint8_t *color)
{
    return providers->resolve_color!=NULL &&
        providers->resolve_color(providers->context,source_color,color);
}

static int16_t wrap16(int32_t value)
{
    uint16_t bits=(uint16_t)value;
    int32_t signed_value=(bits<=INT16_MAX) ? (int32_t)bits : (int32_t)bits-65536;
    return (int16_t)signed_value;
}

static int16_t div16(int16_t numerator,int16_t denominator)
{
    int32_t quotient=(int32_t)numerator/(int32_t)denominator;
    return wrap16(quotient);
}

static PortableHistoryStatus append(PortableHistoryCommand *commands,
    size_t capacity,size_t *count,PortableHistoryCommand command)
{
    if(*count>=capacity) return PORTABLE_HISTORY_OUTPUT_FULL;
    commands[(*count)++]=command;
    return PORTABLE_HISTORY_OK;
}

static PortableHistoryCommand command(PortableHistoryCommandKind kind)
{
    PortableHistoryCommand c;
    memset(&c,0,sizeof(c));
    c.kind=kind;
    return c;
}

static int valid_common(const PortableHistoryInput *input,
    const PortableHistoryProviders *providers,PortableHistoryCommand *commands,
    size_t *command_count)
{
    return input!=NULL && providers!=NULL && providers->get_object_rect!=NULL &&
        providers->get_font_height!=NULL && providers->get_text_width!=NULL &&
        commands!=NULL && command_count!=NULL;
}

PortableHistoryStatus portable_history_render_graph(
    const PortableHistoryInput *input,const PortableHistoryProviders *providers,
    PortableHistoryCommand *commands,size_t capacity,size_t *command_count)
{
    PortableHistoryRect r;
    PortableHistoryCommand c;
    PortableHistoryStatus status;
    int16_t width,height,color,font_height,text_width;
    int16_t graph_index,start_index,max_value=0,divisor=1,multiplier=1;
    int16_t j,n,x,y,px,py,ty;
    size_t out=0,text_size;
    char value_text[16];
    const char *text;
    int written;

    if(!valid_common(input,providers,commands,command_count))
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    *command_count=0;
    if(input->graph<0 || input->graph>=PORTABLE_HISTORY_SERIES_COUNT ||
       input->slot<0 || input->slot>=PORTABLE_HISTORY_VISIBLE_GRAPHS ||
       input->start<0 || input->start>=PORTABLE_HISTORY_SAMPLES ||
       input->count<0 || input->count>PORTABLE_HISTORY_SAMPLES ||
       input->hilite<0 || input->hilite>1 ||
       input->history_color[input->graph]<0 || input->history_color[input->graph]>=4)
        return PORTABLE_HISTORY_BAD_DOMAIN;
    graph_index=(int16_t)(((input->graph&1)*5)+(input->graph>>1));
    color=input->graph_colors[input->history_color[input->graph]];
    if(!providers->get_object_rect(providers->context,PORTABLE_HISTORY_WINDOW_ID,
                                    PORTABLE_HISTORY_OBJECT_ID,&r))
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    width=wrap16((int32_t)r.right-r.left-0x40);
    r.bottom=wrap16((int32_t)r.bottom-8);
    r.top=wrap16((int32_t)r.top+8);
    height=wrap16((int32_t)r.bottom-r.top);
    /* Real resource windows produce positive, small dimensions. The bound
     * prevents invoking C signed overflow outside the observed service domain. */
    if(width<=0 || height<=0 || width>4096 || height>4096)
        return PORTABLE_HISTORY_BAD_DOMAIN;

    j=(int16_t)(((int32_t)input->start-input->count)&0x3f);
    for(n=0;n<input->count;n++) {
        int16_t a=input->series[history_table_a[graph_index]][j];
        int16_t b=input->series[history_table_b[graph_index]][j];
        if(a>max_value) max_value=a;
        if(b>max_value) max_value=b;
        j=(int16_t)((j+1)&0x3f);
    }
    if(max_value>0) {
        for(multiplier=1;
            wrap16((int32_t)max_value*multiplier)<height;
            multiplier=wrap16((int32_t)multiplier+1)) {
            if(multiplier==INT16_MAX) return PORTABLE_HISTORY_BAD_DOMAIN;
        }
        if(multiplier>1) multiplier=wrap16((int32_t)multiplier-1);
        else {
            divisor=1;
            while(div16(max_value,divisor)>height) {
                if(divisor==INT16_MAX) return PORTABLE_HISTORY_BAD_DOMAIN;
                divisor=wrap16((int32_t)divisor+1);
            }
        }
    }
    start_index=(int16_t)(input->start&0x3f);
    j=start_index;
    x=r.left;
    if(divisor==1)
        y=wrap16((int32_t)r.bottom-wrap16((int32_t)input->series[history_table_a[graph_index]][input->start]*multiplier));
    else
        y=wrap16((int32_t)r.bottom-div16(input->series[history_table_a[graph_index]][input->start],divisor));
    px=x; py=y;
    for(n=1;n<64;n++) {
        int16_t scaled;
        j=(int16_t)((j+1)&0x3f);
        scaled=div16(wrap16((int32_t)n*width),64);
        x=wrap16((int32_t)scaled+input->slot+r.left);
        if(divisor==1)
            y=wrap16((int32_t)r.bottom-wrap16((int32_t)input->series[history_table_a[graph_index]][j]*multiplier));
        else
            y=wrap16((int32_t)r.bottom-div16(input->series[history_table_a[graph_index]][j],divisor));
        c=command(PORTABLE_HISTORY_LINE);
        c.a=px; c.b=py; c.c=x; c.d=y; c.e=color;
        status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
        px=x; py=y;
    }
    if(input->hilite==0) {
        text=input->labels[graph_index];
        text_size=input->label_sizes[graph_index];
        if(text==NULL || text_size>=PORTABLE_HISTORY_MAX_TEXT)
            return text==NULL ? PORTABLE_HISTORY_BAD_ARGUMENT : PORTABLE_HISTORY_TEXT_TOO_LONG;
    } else {
        written=snprintf(value_text,sizeof(value_text),"%d",input->series[history_table_a[graph_index]][j]);
        if(written<0 || (size_t)written>=sizeof(value_text)) return PORTABLE_HISTORY_BAD_DOMAIN;
        text=value_text; text_size=(size_t)written;
    }
    c=command(PORTABLE_HISTORY_SET_COLOR); c.a=color; c.b=0; c.c=color;
    status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
    c=command(PORTABLE_HISTORY_SET_FONT); c.a=3;
    status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
    if(!providers->get_font_height(providers->context,&font_height) || font_height==0)
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    ty=wrap16((int32_t)y-div16(font_height,2));
    c=command(PORTABLE_HISTORY_TEXT); c.a=x; c.b=ty; c.text_size=(uint16_t)text_size;
    memcpy(c.text,text,text_size);
    status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
    if(!providers->get_text_width(providers->context,text,text_size,&text_width))
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    c=command(PORTABLE_HISTORY_OUTLINE);
    c.a=wrap16((int32_t)x-1); c.b=wrap16((int32_t)ty-1);
    c.c=wrap16((int32_t)text_width+x+1); c.d=wrap16((int32_t)ty+font_height+1); c.e=1;
    status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
    c=command(PORTABLE_HISTORY_SET_FONT); c.a=0;
    status=append(commands,capacity,&out,c); if(status!=PORTABLE_HISTORY_OK) return status;
    *command_count=out;
    return PORTABLE_HISTORY_OK;
}

PortableHistoryStatus portable_history_render_window(
    const PortableHistoryWindowInput *input,const PortableHistoryProviders *providers,
    PortableHistoryCommand *commands,size_t capacity,size_t *command_count)
{
    PortableHistoryCommand fill,graph_command,subcommands[PORTABLE_HISTORY_MAX_COMMANDS];
    PortableHistoryStatus status;
    size_t total=0,subcount,i,j;
    int16_t fill_color;
    if(input==NULL || providers==NULL || commands==NULL || command_count==NULL)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    *command_count=0;
    if((input->flags&2)==0) return PORTABLE_HISTORY_OK;
    if(providers->get_fill_color==NULL ||
       !providers->get_fill_color(providers->context,PORTABLE_HISTORY_OBJECT_ID,&fill_color))
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    fill=command(PORTABLE_HISTORY_FILL_OBJECT); fill.a=PORTABLE_HISTORY_OBJECT_ID; fill.b=fill_color;
    status=append(commands,capacity,&total,fill); if(status!=PORTABLE_HISTORY_OK) return status;
    for(i=0;i<PORTABLE_HISTORY_VISIBLE_GRAPHS;i++) {
        int16_t graph=input->shown_graphs[i];
        if(graph==(int16_t)0x8000) continue;
        if(graph<0 || graph>=PORTABLE_HISTORY_SERIES_COUNT) return PORTABLE_HISTORY_BAD_DOMAIN;
        graph_command=command(PORTABLE_HISTORY_DRAW_GRAPH);
        graph_command.a=graph; graph_command.b=0; graph_command.c=(int16_t)i;
        status=append(commands,capacity,&total,graph_command); if(status!=PORTABLE_HISTORY_OK) return status;
        {
            PortableHistoryInput one=input->render;
            one.graph=graph; one.hilite=0; one.slot=(int16_t)i;
            status=portable_history_render_graph(&one,providers,subcommands,
                PORTABLE_HISTORY_MAX_COMMANDS,&subcount);
        }
        if(status!=PORTABLE_HISTORY_OK) return status;
        if(subcount>capacity-total) return PORTABLE_HISTORY_OUTPUT_FULL;
        for(j=0;j<subcount;j++) commands[total++]=subcommands[j];
    }
    *command_count=total;
    return PORTABLE_HISTORY_OK;
}

PortableHistoryStatus portable_history_rasterize(
    const PortableHistoryCommand *commands,size_t command_count,
    const PortableHistoryRasterProviders *providers)
{
    size_t i;
    int16_t active_source_color=0;
    uint8_t active_color=0;
    int16_t active_font=0;
    if((commands==NULL && command_count!=0) || providers==NULL ||
       providers->framebuffer==NULL || providers->framebuffer->pixels==NULL)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    for(i=0;i<command_count;i++) {
        const PortableHistoryCommand *c=&commands[i];
        uint8_t color;
        switch(c->kind) {
        case PORTABLE_HISTORY_SET_COLOR:
            active_source_color=c->a;
            if(!raster_resolve(providers,active_source_color,&active_color))
                return PORTABLE_HISTORY_PROVIDER_FAILED;
            break;
        case PORTABLE_HISTORY_SET_FONT:
            if(c->a!=0 && c->a!=3) return PORTABLE_HISTORY_RASTER_UNSUPPORTED;
            active_font=c->a;
            break;
        case PORTABLE_HISTORY_LINE:
            if(!raster_resolve(providers,c->e,&color))
                return PORTABLE_HISTORY_PROVIDER_FAILED;
            raster_line(providers->framebuffer,c->a,c->b,c->c,c->d,color);
            break;
        case PORTABLE_HISTORY_TEXT:
            if(active_font!=3 || providers->font3==NULL)
                return PORTABLE_HISTORY_RASTER_UNSUPPORTED;
            if(portable_font_draw(providers->framebuffer,providers->font3,
                c->a,c->b,(const uint8_t *)c->text,c->text_size,active_color,NULL)
                !=PORTABLE_RENDER_OK)
                return PORTABLE_HISTORY_RASTER_FAILED;
            break;
        case PORTABLE_HISTORY_OUTLINE:
            if(c->e<0) return PORTABLE_HISTORY_RASTER_UNSUPPORTED;
            if(c->e!=0) {
                int32_t width=c->e;
                raster_line(providers->framebuffer,c->a+width,c->b+width,
                    c->c-width,c->b,active_color);
                raster_line(providers->framebuffer,c->a+width,c->d-width,
                    c->c-width,c->d,active_color);
                raster_line(providers->framebuffer,c->a+width,c->b,
                    c->a,c->d,active_color);
                raster_line(providers->framebuffer,c->c,c->b,
                    c->c-width,c->d,active_color);
            }
            break;
        case PORTABLE_HISTORY_FILL_OBJECT:
            if(providers->fill_object==NULL ||
               !providers->fill_object(providers->context,c->a,c->b,active_color))
                return PORTABLE_HISTORY_PROVIDER_FAILED;
            break;
        case PORTABLE_HISTORY_DRAW_GRAPH:
            /* This marker is followed by the expanded graph's draw commands. */
            break;
        default:
            return PORTABLE_HISTORY_RASTER_UNSUPPORTED;
        }
    }
    (void)active_source_color;
    return PORTABLE_HISTORY_OK;
}

const char *portable_history_status_string(PortableHistoryStatus status)
{
    switch(status) {
    case PORTABLE_HISTORY_OK: return "ok";
    case PORTABLE_HISTORY_BAD_ARGUMENT: return "bad argument";
    case PORTABLE_HISTORY_BAD_DOMAIN: return "unsupported history/resource domain";
    case PORTABLE_HISTORY_PROVIDER_FAILED: return "resource/font provider failed";
    case PORTABLE_HISTORY_OUTPUT_FULL: return "command buffer full";
    case PORTABLE_HISTORY_TEXT_TOO_LONG: return "resource label too long";
    case PORTABLE_HISTORY_RASTER_UNSUPPORTED: return "unsupported raster command";
    case PORTABLE_HISTORY_RASTER_FAILED: return "resource font raster failed";
    default: return "unknown status";
    }
}

void portable_history_labels_free(PortableHistoryLabels *labels)
{
    if(labels==NULL) return;
    free(labels->items);
    free(labels->sizes);
    free(labels->storage);
    memset(labels,0,sizeof(*labels));
}

PortableHistoryStatus portable_history_labels_load(
    PortableHistoryLabels *labels,PortableDatabase *shared_database)
{
    PortableDbRecord record={0};
    PortableHistoryLabels loaded={0};
    PortableDbStatus db_status;
    size_t cursor=2,storage_cursor=0,i;
    uint8_t count;
    if(labels==NULL || shared_database==NULL || shared_database->entries==NULL)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    db_status=portable_db_load(shared_database,PORTABLE_HISTORY_LABELS_ID,
                                PORTABLE_HISTORY_STRING_KIND,&record);
    if(db_status!=PORTABLE_DB_OK) return PORTABLE_HISTORY_PROVIDER_FAILED;
    if(record.data==NULL || record.size<2u || record.id!=PORTABLE_HISTORY_LABELS_ID ||
       record.kind!=PORTABLE_HISTORY_STRING_KIND) {
        portable_db_record_free(&record);
        return PORTABLE_HISTORY_BAD_DOMAIN;
    }
    count=record.data[1];
    if(count<PORTABLE_HISTORY_SERIES_COUNT || count==0 ||
       record.size>SIZE_MAX-(size_t)count) {
        portable_db_record_free(&record);
        return PORTABLE_HISTORY_BAD_DOMAIN;
    }
    loaded.items=(char **)calloc(count,sizeof(*loaded.items));
    loaded.sizes=(size_t *)calloc(count,sizeof(*loaded.sizes));
    loaded.storage=(char *)malloc(record.size+(size_t)count);
    if(loaded.items==NULL || loaded.sizes==NULL || loaded.storage==NULL) {
        portable_db_record_free(&record);
        portable_history_labels_free(&loaded);
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    }
    loaded.count=count;
    for(i=0;i<count;i++) {
        size_t length;
        if(cursor>=record.size) goto invalid;
        length=record.data[cursor++];
        if(length>record.size-cursor || length>=PORTABLE_HISTORY_MAX_TEXT)
            goto invalid;
        loaded.items[i]=loaded.storage+storage_cursor;
        loaded.sizes[i]=length;
        if(length!=0) memcpy(loaded.items[i],record.data+cursor,length);
        loaded.items[i][length]='\0';
        storage_cursor+=length+1u;
        cursor+=length;
    }
    if(cursor!=record.size) goto invalid;
    portable_db_record_free(&record);
    *labels=loaded;
    return PORTABLE_HISTORY_OK;
invalid:
    portable_db_record_free(&record);
    portable_history_labels_free(&loaded);
    return PORTABLE_HISTORY_BAD_DOMAIN;
}

PortableHistoryStatus portable_history_bind_session(
    PortableHistoryInput *input,
    const int16_t history_series[PORTABLE_HISTORY_SERIES_COUNT][PORTABLE_HISTORY_SAMPLES],
    int16_t history_start,int16_t history_count,int16_t graph,int16_t hilite,
    int16_t slot,const PortableHistoryUiSnapshot *ui,
    const PortableHistoryLabels *labels)
{
    size_t i;
    if(input==NULL || history_series==NULL || ui==NULL || labels==NULL ||
       labels->items==NULL || labels->sizes==NULL || labels->count<10)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    if(history_start<0 || history_start>=PORTABLE_HISTORY_SAMPLES ||
       history_count<0 || history_count>PORTABLE_HISTORY_SAMPLES ||
       graph<0 || graph>=PORTABLE_HISTORY_SERIES_COUNT || hilite<0 || hilite>1 ||
       slot<0 || slot>=PORTABLE_HISTORY_VISIBLE_GRAPHS)
        return PORTABLE_HISTORY_BAD_DOMAIN;
    memcpy(input->series,history_series,sizeof(input->series));
    for(i=0;i<PORTABLE_HISTORY_SERIES_COUNT;i++) {
        input->history_color[i]=ui->history_color[i];
        input->labels[i]=labels->items[i];
        input->label_sizes[i]=labels->sizes[i];
    }
    memcpy(input->graph_colors,ui->graph_colors,sizeof(input->graph_colors));
    input->start=history_start;
    input->count=history_count;
    input->graph=graph;
    input->hilite=hilite;
    input->slot=slot;
    return PORTABLE_HISTORY_OK;
}

PortableHistoryStatus portable_history_bind_window(
    PortableHistoryWindowInput *input,
    const int16_t history_series[PORTABLE_HISTORY_SERIES_COUNT][PORTABLE_HISTORY_SAMPLES],
    int16_t history_start,int16_t history_count,int16_t flags,
    const PortableHistoryUiSnapshot *ui,const PortableHistoryLabels *labels)
{
    PortableHistoryStatus status;
    if(input==NULL || ui==NULL) return PORTABLE_HISTORY_BAD_ARGUMENT;
    status=portable_history_bind_session(&input->render,history_series,
        history_start,history_count,0,0,0,ui,labels);
    if(status!=PORTABLE_HISTORY_OK) return status;
    input->flags=flags;
    memcpy(input->shown_graphs,ui->shown_graphs,sizeof(input->shown_graphs));
    return PORTABLE_HISTORY_OK;
}

static int active_get_rect(void *opaque,int16_t window_id,int16_t object_id,
                           PortableHistoryRect *rect)
{
    const PortableHistoryActiveResources *resources=(const PortableHistoryActiveResources *)opaque;
    if(resources==NULL || !resources->ready || rect==NULL ||
       window_id!=PORTABLE_HISTORY_WINDOW_ID || object_id!=PORTABLE_HISTORY_OBJECT_ID)
        return 0;
    *rect=resources->current_window_rect;
    return 1;
}

static int active_get_font_height(void *opaque,int16_t *height)
{
    const PortableHistoryActiveResources *resources=(const PortableHistoryActiveResources *)opaque;
    const PortableFont *font;
    if(resources==NULL || !resources->ready || height==NULL) return 0;
    font=resources->renderer->fonts[1];
    if(font==NULL || font->metrics[7]<=0) return 0;
    *height=font->metrics[7];
    return 1;
}

static int active_get_text_width(void *opaque,const char *text,size_t text_size,
                                 int16_t *width)
{
    const PortableHistoryActiveResources *resources=(const PortableHistoryActiveResources *)opaque;
    int32_t measured;
    if(resources==NULL || !resources->ready || width==NULL ||
       (text==NULL && text_size!=0)) return 0;
    measured=portable_font_string_width(resources->renderer->fonts[1],
        (const uint8_t *)text,text_size);
    if(measured<INT16_MIN || measured>INT16_MAX) return 0;
    *width=(int16_t)measured;
    return 1;
}

static int active_get_fill_color(void *opaque,int16_t object_id,int16_t *color)
{
    const PortableHistoryActiveResources *resources=(const PortableHistoryActiveResources *)opaque;
    if(resources==NULL || !resources->ready || color==NULL ||
       object_id!=PORTABLE_HISTORY_OBJECT_ID) return 0;
    /* f_1B4E_000D maps the low nibble through g_41C0=[0..15]; f(0)=0. */
    *color=0;
    return 1;
}

static int active_resolve_color(void *opaque,int16_t source_color,uint8_t *color)
{
    PortableHistoryActiveResources *resources=(PortableHistoryActiveResources *)opaque;
    size_t color_index,color_offset;
    if(resources==NULL || !resources->ready || color==NULL || source_color<0)
        return 0;
    /* S24's graphColors carry the DOS indexed color word; f_1B4E_000D maps
     * it through g_41C0, whose shipped table is the identity low nibble. */
    color_index=(uint16_t)source_color&0x0fu;
    color_offset=color_index*6u;
    if(color_offset>=resources->renderer->colors_size) return 0;
    /* Color-table byte zero is the active foreground index used for text. */
    *color=(uint8_t)(resources->renderer->colors[color_offset]&0x0fu);
    return 1;
}

static int active_fill_object(void *opaque,int16_t object_id,int16_t source_color,
                              uint8_t framebuffer_color)
{
    PortableHistoryActiveResources *resources=(PortableHistoryActiveResources *)opaque;
    PortableHistoryRect r;
    PortableRect rect;
    if(resources==NULL || !resources->ready || object_id!=PORTABLE_HISTORY_OBJECT_ID ||
       source_color!=0) return 0;
    r=resources->current_window_rect;
    rect=(PortableRect){r.left,r.top,r.right,r.bottom};
    if(resources->framebuffer==NULL || resources->framebuffer->pixels==NULL) return 0;
    portable_fill_rect(resources->framebuffer,rect,framebuffer_color);
    return 1;
}

PortableHistoryStatus portable_history_active_resources_load(
    PortableHistoryActiveResources *resources,PortableDatabase *shared_database,
    PortableWindowRegistry *registry,const PortableWindowRenderer *renderer)
{
    PortableWindowRect rect;
    PortableHistoryStatus status;
    if(resources==NULL || shared_database==NULL || registry==NULL || renderer==NULL ||
       registry->database==NULL || renderer->database!=registry->database ||
       renderer->colors==NULL || renderer->colors_size<6u || renderer->fonts[1]==NULL)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    memset(resources,0,sizeof(*resources));
    status=portable_history_labels_load(&resources->labels,shared_database);
    if(status!=PORTABLE_HISTORY_OK) return status;
    if(portable_window_registry_get_object_rect(registry,
        PORTABLE_HISTORY_OBJECT_ID,&rect)!=PORTABLE_WINDOW_REGISTRY_OK) {
        portable_history_labels_free(&resources->labels);
        return PORTABLE_HISTORY_PROVIDER_FAILED;
    }
    resources->registry=registry;
    resources->renderer=renderer;
    resources->current_window_rect=(PortableHistoryRect){rect.left,rect.top,
                                                        rect.right,rect.bottom};
    resources->ready=1;
    return PORTABLE_HISTORY_OK;
}

void portable_history_active_resources_free(PortableHistoryActiveResources *resources)
{
    if(resources==NULL) return;
    portable_history_labels_free(&resources->labels);
    memset(resources,0,sizeof(*resources));
}

PortableHistoryStatus portable_history_active_resources_set_rect(
    PortableHistoryActiveResources *resources,const PortableHistoryRect *current_rect)
{
    if(resources==NULL || !resources->ready || current_rect==NULL)
        return PORTABLE_HISTORY_BAD_ARGUMENT;
    resources->current_window_rect=*current_rect;
    return PORTABLE_HISTORY_OK;
}

void portable_history_active_providers(PortableHistoryActiveResources *resources,
                                       PortableHistoryProviders *providers)
{
    if(providers==NULL) return;
    providers->context=resources;
    providers->get_object_rect=active_get_rect;
    providers->get_font_height=active_get_font_height;
    providers->get_text_width=active_get_text_width;
    providers->get_fill_color=active_get_fill_color;
}

void portable_history_active_raster_providers(
    PortableHistoryActiveResources *resources,PortableFramebuffer *framebuffer,
    PortableHistoryRasterProviders *providers)
{
    if(providers==NULL) return;
    providers->context=resources;
    providers->framebuffer=framebuffer;
    if(resources!=NULL) resources->framebuffer=framebuffer;
    providers->font3=(resources!=NULL && resources->renderer!=NULL)
        ? resources->renderer->fonts[1] : NULL;
    providers->resolve_color=active_resolve_color;
    providers->fill_object=active_fill_object;
}

