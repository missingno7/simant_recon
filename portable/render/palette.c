#include "palette.h"

PortableRenderStatus portable_palette_load_ega(PortablePalette *palette,
                                               const uint8_t *bytes,size_t size)
{
    unsigned i;
    PortablePalette parsed;
    if(!palette || !bytes) return PORTABLE_RENDER_INVALID_ARGUMENT;
    if(size<2) return PORTABLE_RENDER_TRUNCATED_DATA;
    if(bytes[0]!=16) return PORTABLE_RENDER_UNSUPPORTED_MODE;
    if(bytes[1]==1) {
        if(size<18) return PORTABLE_RENDER_TRUNCATED_DATA;
        for(i=0;i<16;i++) parsed.ega_registers[i]=(uint8_t)(bytes[i+2]&63);
    } else if(bytes[1]==0) {
        if(size<50) return PORTABLE_RENDER_TRUNCATED_DATA;
        for(i=0;i<16;i++) {
            const uint8_t *q=bytes+2+i*3;
            parsed.ega_registers[i]=(uint8_t)(((((q[0]&0x10) |
                ((((q[1]&0x10)|((q[2]&0x10)>>1))>>1)|(q[2]&0x20)))>>1 |
                (q[1]&0x20))>>1)|(q[0]&0x20));
        }
    } else return PORTABLE_RENDER_UNSUPPORTED_MODE;
    for(i=0;i<16;i++) {
        uint8_t e=parsed.ega_registers[i];
        parsed.rgb[i][0]=(uint8_t)(((e&4)?170:0)+((e&32)?85:0));
        parsed.rgb[i][1]=(uint8_t)(((e&2)?170:0)+((e&16)?85:0));
        parsed.rgb[i][2]=(uint8_t)(((e&1)?170:0)+((e&8)?85:0));
    }
    *palette=parsed;
    return PORTABLE_RENDER_OK;
}
