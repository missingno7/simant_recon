#include "fonts.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void portable_fonts_init(PortableFontSet *set)
{
    unsigned i;
    if(!set) return;
    memset(set,0,sizeof(*set));
    for(i=0;i<4;i++) portable_font_init(&set->fonts[i]);
}

void portable_fonts_destroy(PortableFontSet *set)
{
    unsigned i;
    if(!set) return;
    for(i=0;i<4;i++) portable_font_destroy(&set->fonts[i]);
    set->loaded=0;
}

PortableRenderStatus portable_fonts_load(PortableFontSet *set,const char *asset_dir)
{
    unsigned i;
    if(!set || !asset_dir) return PORTABLE_RENDER_INVALID_ARGUMENT;
    portable_fonts_destroy(set);
    set->error[0]=0;
    for(i=0;i<4;i++) {
        char path[1024];
        FILE *file;
        long length;
        uint8_t *bytes;
        PortableRenderStatus status;
        if(snprintf(path,sizeof(path),"%s/FONT%u",asset_dir,i+1)>=(int)sizeof(path)) {
            snprintf(set->error,sizeof(set->error),"font asset path too long");
            break;
        }
        file=fopen(path,"rb");
        if(!file) {
            snprintf(set->error,sizeof(set->error),"cannot open FONT%u",i+1);
            break;
        }
        if(fseek(file,0,SEEK_END) || (length=ftell(file))<=0 || fseek(file,0,SEEK_SET)) {
            fclose(file);
            snprintf(set->error,sizeof(set->error),"cannot read FONT%u",i+1);
            break;
        }
        bytes=malloc((size_t)length);
        if(!bytes) {
            fclose(file);
            snprintf(set->error,sizeof(set->error),"out of memory loading FONT%u",i+1);
            break;
        }
        if(fread(bytes,1,(size_t)length,file)!=(size_t)length) {
            free(bytes);
            fclose(file);
            snprintf(set->error,sizeof(set->error),"short read in FONT%u",i+1);
            break;
        }
        fclose(file);
        status=portable_font_load(&set->fonts[i],bytes,(size_t)length);
        free(bytes);
        if(status!=PORTABLE_RENDER_OK) {
            snprintf(set->error,sizeof(set->error),"invalid FONT%u (status %d)",i+1,(int)status);
            break;
        }
    }
    if(i!=4) {
        portable_fonts_destroy(set);
        return PORTABLE_RENDER_INVALID_RESOURCE;
    }
    set->loaded=1;
    return PORTABLE_RENDER_OK;
}

const PortableFont *portable_fonts_get(const PortableFontSet *set,unsigned source_id)
{
    return set && set->loaded && source_id>=2 && source_id<=5
        ? &set->fonts[source_id-2] : NULL;
}
