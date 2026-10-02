#include "../../../ui_model/windows/render.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

static const char *status_name(PortableRenderStatus status)
{
    switch(status) {
    case PORTABLE_RENDER_OK:return "ok";
    case PORTABLE_RENDER_UNSUPPORTED_MODE:return "unsupported-mode";
    case PORTABLE_RENDER_UNSUPPORTED_CODEC:return "unsupported-codec";
    case PORTABLE_RENDER_INVALID_RESOURCE:return "invalid-resource";
    case PORTABLE_RENDER_INVALID_ARGUMENT:return "invalid-argument";
    case PORTABLE_RENDER_TRUNCATED_DATA:return "truncated";
    default:return "other";
    }
}

int main(int argc,char **argv)
{
    static const int16_t ids[]={0,1,18,19,25};
    char root[1024],path[1024];
    PortableDatabase db={0};
    PortableDbRecord colors={0};
    PortableWindowRenderer renderer={0};
    PortableFramebuffer fb;
    PortableFont fonts[4];
    PortableBiosFontProvider bios_fonts={0};
    uint8_t *bios8=NULL,*bios14=NULL;
    uint8_t pixels[640*480];
    unsigned fi;
    size_t total_ok=0,total_unsupported=0;
    assert(argc==2 || argc==5);
    assert(snprintf(root,sizeof(root),"%s/HCEGANT",argv[1])<(int)sizeof(root));
    assert(portable_db_open(&db,root)==PORTABLE_DB_OK);
    assert(portable_db_load(&db,0x81,0,&colors)==PORTABLE_DB_OK);
    for(fi=0;fi<4;fi++) {
        size_t size;
        uint8_t *bytes;
        assert(snprintf(path,sizeof(path),"%s/FONT%u",argv[1],fi+1)<(int)sizeof(path));
        bytes=read_file(path,&size);
        portable_font_init(&fonts[fi]);
        assert(portable_font_load(&fonts[fi],bytes,size)==PORTABLE_RENDER_OK);
        free(bytes);
        renderer.fonts[fi]=&fonts[fi];
    }
    assert(portable_framebuffer_init(&fb,640,480,640,pixels)==PORTABLE_RENDER_OK);
    renderer.framebuffer=&fb;
    renderer.database=&db;
    renderer.colors=colors.data;
    renderer.colors_size=colors.size;
    renderer.screen_width=640;
    if(argc==5) {
        size_t size8,size14;
        bios8=read_file(argv[2],&size8);
        bios14=read_file(argv[3],&size14);
        assert(portable_bios_font_provider_init(&bios_fonts,bios8,size8,
                                                bios14,size14,argv[4])
               ==PORTABLE_RENDER_OK);
        renderer.bios_fonts=&bios_fonts;
    }
    for(size_t wi=0;wi<sizeof(ids)/sizeof(ids[0]);wi++) {
        PortableDbRecord resource={0};
        PortableWindowResource decoded, isolated;
        PortableWindowObject *objects;
        assert(portable_db_load(&db,ids[wi],0,&resource)==PORTABLE_DB_OK);
        assert(portable_window_decode(&resource,&decoded)==PORTABLE_WINDOW_OK);
        objects=(PortableWindowObject *)malloc(decoded.count*sizeof(*objects));
        assert(objects!=NULL);
        memcpy(objects,decoded.objects,decoded.count*sizeof(*objects));
        isolated=decoded;
        isolated.objects=objects;
        isolated.flags=0; /* Test each visible object without a window-decoration pass. */
        printf("window=%d objects=%u\n",ids[wi],decoded.count);
        for(size_t oi=0;oi<decoded.count;oi++) {
            PortableRenderStatus status;
            uint16_t target_flags=objects[oi].flags;
            if(!(target_flags&1)) continue;
            for(size_t other=0;other<decoded.count;other++)
                if(other!=oi) objects[other].flags&=(uint16_t)~1u;
            memset(pixels,0,sizeof(pixels));
            status=portable_window_draw_native(&isolated,&renderer);
            objects[oi].flags=target_flags;
            for(size_t other=0;other<decoded.count;other++)
                if(other!=oi) objects[other].flags=decoded.objects[other].flags;
            if(status==PORTABLE_RENDER_OK) {
                total_ok++;
                printf(" object=%u type=%u status=ok\n",(unsigned)oi,objects[oi].type);
            } else if(status==PORTABLE_RENDER_UNSUPPORTED_MODE ||
                      status==PORTABLE_RENDER_UNSUPPORTED_CODEC) {
                total_unsupported++;
                printf(" object=%u type=%u status=%s font=%u\n",
                       (unsigned)oi,objects[oi].type,status_name(status),
                       objects[oi].resource_bytes[0x28]);
            } else {
                fprintf(stderr,"window=%d object=%u type=%u invalid status=%s\n",
                        ids[wi],(unsigned)oi,objects[oi].type,status_name(status));
                return 2;
            }
        }
        free(objects);
        portable_window_release(&decoded);
        portable_db_record_free(&resource);
    }
    for(fi=0;fi<4;fi++) portable_font_destroy(&fonts[fi]);
    free(bios8); free(bios14);
    portable_db_record_free(&colors);
    portable_db_close(&db);
    printf("supported_objects=%lu explicit_unsupported_objects=%lu\n",
           (unsigned long)total_ok,(unsigned long)total_unsupported);
    return 0;
}
