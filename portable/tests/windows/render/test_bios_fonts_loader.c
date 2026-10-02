#include "../../../game/resources/bios_fonts.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(int argc,char **argv)
{
    PortableBiosFonts fonts;
    assert(argc==3);
    portable_bios_fonts_init(&fonts);
    assert(portable_bios_fonts_load(&fonts,argv[2])==PORTABLE_BIOS_FONTS_OK);
    assert(fonts.font_8x8_size==256u*8u && fonts.font_8x14_size==256u*14u);
    assert(fonts.provider.font_8x8.glyph_rows==fonts.font_8x8);
    assert(fonts.provider.font_8x14.glyph_rows==fonts.font_8x14);
    assert(strcmp(fonts.provider.font_8x8.provider_id,fonts.provider_id)==0);
    assert(strstr(fonts.provider_id,"7b40053b7ac580843d0461eba8c36a47a990e66c")!=NULL);
    assert(portable_bios_fonts_load(&fonts,"build/missing-bios-reference")
           ==PORTABLE_BIOS_FONTS_IO_ERROR);
    assert(fonts.font_8x8==NULL && fonts.font_8x14==NULL);
    assert(fonts.provider.font_8x8.glyph_rows==NULL && fonts.provider.font_8x14.glyph_rows==NULL);
    assert(portable_bios_fonts_error(&fonts)[0]!='\0');
    assert(portable_bios_fonts_load(&fonts,argv[2])==PORTABLE_BIOS_FONTS_OK);
    portable_bios_fonts_free(&fonts);
    assert(fonts.font_8x8==NULL && fonts.provider_id[0]=='\0');
    puts("pinned BIOS reference load, cleanup on failure, and reload passed");
    return 0;
}
