#include "../../../ui_model/windows/render.h"
#include "../../../render/palette.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t *read_file(const char *path,size_t *size)
{
    FILE *file=fopen(path,"rb");
    long length;
    uint8_t *bytes;
    assert(file!=NULL);
    assert(fseek(file,0,SEEK_END)==0);
    length=ftell(file);
    assert(length>=0 && fseek(file,0,SEEK_SET)==0);
    bytes=(uint8_t *)malloc((size_t)length);
    assert(bytes!=NULL || length==0);
    assert(fread(bytes,1,(size_t)length,file)==(size_t)length);
    assert(fclose(file)==0);
    *size=(size_t)length;
    return bytes;
}

static uint64_t fnv1a(const uint8_t *bytes,size_t size)
{
    size_t i;
    uint64_t hash=14695981039346656037ull;
    for(i=0;i<size;i++) { hash^=bytes[i]; hash*=1099511628211ull; }
    return hash;
}

int main(int argc,char **argv)
{
    static const int16_t windows[]={0,1,18,19,25};
    static const uint16_t counts[]={23,31,18,18,22};
    char root[1024],path[1024];
    PortableDatabase database={0};
    PortableDbRecord colors={0};
    PortableWindowRenderer renderer={0};
    PortableFramebuffer framebuffer;
    PortableFont fonts[4];
    PortableBiosFontProvider bios_fonts={0};
    uint8_t *bios8=NULL,*bios14=NULL;
    uint8_t pixels[640*480];
    unsigned i;
    size_t nonzero=0;
    assert(argc==2 || argc==5);
    assert(snprintf(root,sizeof(root),"%s/HCEGANT",argv[1])<(int)sizeof(root));
    assert(portable_db_open(&database,root)==PORTABLE_DB_OK);
    assert(portable_db_load(&database,0x81,0,&colors)==PORTABLE_DB_OK);
    assert(colors.size>=16*6);
    for(i=0;i<4;i++) {
        size_t size;
        uint8_t *bytes;
        assert(snprintf(path,sizeof(path),"%s/FONT%u",argv[1],i+1)<(int)sizeof(path));
        bytes=read_file(path,&size);
        portable_font_init(&fonts[i]);
        assert(portable_font_load(&fonts[i],bytes,size)==PORTABLE_RENDER_OK);
        free(bytes);
        renderer.fonts[i]=&fonts[i];
    }
    assert(portable_framebuffer_init(&framebuffer,640,480,640,pixels)==PORTABLE_RENDER_OK);
    renderer.framebuffer=&framebuffer;
    renderer.database=&database;
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
    for(i=0;i<sizeof(windows)/sizeof(windows[0]);i++) {
        PortableDbRecord record={0};
        PortableWindowResource window;
        PortableWindowStatus decode;
        memset(pixels,0,sizeof(pixels));
        assert(portable_db_load(&database,windows[i],0,&record)==PORTABLE_DB_OK);
        decode=portable_window_decode(&record,&window);
        assert(decode==PORTABLE_WINDOW_OK);
        assert(window.count==counts[i]);
        {
            PortableRenderStatus status=portable_window_draw_native(&window,&renderer);
            if(status!=PORTABLE_RENDER_OK) {
                /* These two actual startup windows have one DOS-driver-only
                 * BIOS font object. Keep that boundary visible in the receipt. */
                const uint16_t expected_unsupported_windows[]={18,19};
                const PortableWindowObject *object=&window.objects[1];
                assert(status==PORTABLE_RENDER_UNSUPPORTED_MODE);
                assert(windows[i]==expected_unsupported_windows[0] ||
                       windows[i]==expected_unsupported_windows[1]);
                assert(object->type==18 && (object->flags&1) &&
                       object->resource_bytes[0x28]==0);
                printf("window=%d objects=%u full_render=unsupported object=1 type=18 font=0 (DOS g_912C/g_9130 driver text)\n",
                       windows[i],window.count);
                portable_window_release(&window);
                portable_db_record_free(&record);
                continue;
            }
        }
        {
            size_t j;
            for(j=0;j<sizeof(pixels);j++) if(pixels[j]) ++nonzero;
        }
        printf("window=%d objects=%u pixels_sha_fnv1a=%016llx\n",
               windows[i],window.count,
               (unsigned long long)fnv1a(pixels,sizeof(pixels)));
        portable_window_release(&window);
        portable_db_record_free(&record);
    }
    assert(nonzero>1000);
    for(i=0;i<4;i++)portable_font_destroy(&fonts[i]);
    free(bios8); free(bios14);
    portable_db_record_free(&colors);
    portable_db_close(&database);
    printf("nonzero_draws=%lu\n",(unsigned long)nonzero);
    return 0;
}
