#include "graphics_s00_raster_source.h"
#include <string.h>

extern char g_3D20[128];

static uint16_t read_word(const uint8_t *p)
{
    return (uint16_t)(p[0] | (uint16_t)p[1] << 8);
}

static uint16_t ror_word(uint16_t value, unsigned count)
{
    count &= 15u;
    return count ? (uint16_t)((value >> count) | (value << (16u-count))) : value;
}

/* m35A6:L0337..L03F3. Coordinates are signed screen words, but byte strides
 * and pointer deltas use SHR and the low result of MUL. No alignment predicate
 * exists in the source: a partial-byte overlap copies its floor byte count. */
SimS00RasterStatus sim_s00_raster_copy_rect(
    const SimS00SourceRect *r, const uint8_t *source, size_t source_size,
    const SimS00SourceRect *c, uint8_t *destination, size_t destination_size)
{
    int16_t left, right, top, bottom;
    uint16_t ss, ds, bytes, rows, si, di;
    unsigned row;
    if (!r || !c || !source || !destination) return SIM_S00_RASTER_INVALID_ARGUMENT;
    if (r->left >= c->right || r->right <= c->left ||
        r->top >= c->bottom || r->bottom <= c->top) return SIM_S00_RASTER_OK;
    left = r->left > c->left ? r->left : c->left;
    right = r->right < c->right ? r->right : c->right;
    top = r->top > c->top ? r->top : c->top;
    bottom = r->bottom < c->bottom ? r->bottom : c->bottom;
    ss = (uint16_t)((uint16_t)(r->right-r->left) >> 3);
    ds = (uint16_t)((uint16_t)(c->right-c->left) >> 3);
    bytes = (uint16_t)((uint16_t)(right-left) >> 3);
    rows = (uint16_t)((uint16_t)(bottom-top) * 4u);
    si = (uint16_t)(4u + (uint16_t)(top-r->top)*4u*ss + ((uint16_t)(left-r->left) >> 3));
    di = (uint16_t)(4u + (uint16_t)(top-c->top)*4u*ds + ((uint16_t)(left-c->left) >> 3));
    /* Explicit-size callers can check storage. The source ABI has no sizes. */
    for (row = 0; row < rows; ++row) {
        uint16_t s = (uint16_t)(si + row*ss), d = (uint16_t)(di + row*ds);
        if ((size_t)s + bytes > source_size || (size_t)d + bytes > destination_size)
            return SIM_S00_RASTER_BUFFER_TOO_SMALL;
    }
    for (row = 0; row < rows; ++row) {
        unsigned byte;
        /* REP MOVSB's forward order, including overlapping RAM views. */
        for (byte = 0; byte < bytes; ++byte)
            destination[(uint16_t)(di+byte)] = source[(uint16_t)(si+byte)];
        si = (uint16_t)(si+ss);
        di = (uint16_t)(di+ds);
    }
    return SIM_S00_RASTER_OK;
}

/* m35A6:0007 L0067/L0087/L008B and 0177 L01E4/L0201/L0205.
 * [bp+0Eh] is a horizontal pixel offset; [bp+10h] is a vertical row offset.
 * MUL BL is byte multiplication: AL=(destination stride*4), BL=row offset.
 * The word writes deliberately cross plane-row boundaries when shifted. */
static SimS00RasterStatus shifted_blit(const uint8_t *image, size_t image_size,
    uint8_t *buffer, size_t buffer_size, int16_t shift, int16_t row_offset, int masked)
{
    static const uint8_t edges[8] = {255,128,192,224,240,248,252,254};
    uint16_t ss, ds, si = 4, di, rows, available;
    unsigned row_count;
    unsigned row, column, plane, columns, rotation = (uint16_t)shift & 7u;
    if (!image || !buffer || image_size < 4 || buffer_size < 4)
        return SIM_S00_RASTER_INVALID_ARGUMENT;
    ss = (uint16_t)((uint16_t)(read_word(image)+7u) >> 3);
    ds = (uint16_t)((uint16_t)(read_word(buffer)+7u) >> 3);
    available = (uint16_t)(read_word(buffer+2)-(uint16_t)row_offset);
    rows = read_word(image+2);
    if ((int16_t)rows > (int16_t)available) rows = available;
    di = (uint16_t)(4u + ((uint16_t)shift >> 3));
    if (row_offset != 0)
        di = (uint16_t)(di + (uint8_t)(ds*4u)*(uint8_t)row_offset);
    columns = (uint8_t)ss;
    if (!columns) columns = 256u; /* MOV CH,BL / DEC CH / JNE */
    row_count = rows ? rows : 65536u; /* DEC word / JNE, including initial zero */
    for (row = 0; row < row_count; ++row) {
        for (column = 0; column < columns; ++column) {
            uint16_t mask;
            uint16_t mask_at = (uint16_t)(si+column);
            if (masked && (size_t)mask_at >= image_size)
                return SIM_S00_RASTER_BUFFER_TOO_SMALL;
            mask = ror_word(masked ? image[mask_at] :
                (column+1u == columns ? edges[read_word(image)&7u] : 255u), rotation);
            for (plane = 0; plane < 4; ++plane) {
                uint16_t s = (uint16_t)(si+column+(plane+(masked?1u:0u))*ss);
                uint16_t d = (uint16_t)(di+column+plane*ds);
                uint16_t data, old, next;
                if ((size_t)s >= image_size || (size_t)d+1u >= buffer_size)
                    return SIM_S00_RASTER_BUFFER_TOO_SMALL;
                data = ror_word(image[s], rotation);
                old = read_word(buffer+d);
                next = (uint16_t)(old ^ ((old ^ data) & mask));
                buffer[d] = (uint8_t)next;
                buffer[d+1u] = (uint8_t)(next >> 8);
            }
        }
        si = (uint16_t)(si+ss*(masked?5u:4u));
        di = (uint16_t)(di+ds*4u);
    }
    return SIM_S00_RASTER_OK;
}

SimS00RasterStatus sim_s00_raster_masked_blit(const uint8_t *image, size_t image_size,
    uint8_t *buffer, size_t buffer_size, int16_t shift, int16_t row_offset)
{
    return shifted_blit(image,image_size,buffer,buffer_size,shift,row_offset,1);
}

SimS00RasterStatus sim_s00_raster_opaque_blit(const uint8_t *image, size_t image_size,
    uint8_t *buffer, size_t buffer_size, int16_t shift, int16_t row_offset)
{
    return shifted_blit(image,image_size,buffer,buffer_size,shift,row_offset,0);
}

SimS00RasterStatus sim_s00_raster_pattern_transfer(const uint8_t pattern[128],
    uint8_t *destination, size_t destination_size, uint16_t width)
{
    unsigned row;
    uint16_t stride = width >> 3;
    if (!pattern || !destination) return SIM_S00_RASTER_INVALID_ARGUMENT;
    for (row = 0; row < 64; ++row)
        if ((size_t)(uint16_t)(row*stride)+2u > destination_size)
            return SIM_S00_RASTER_BUFFER_TOO_SMALL;
    /* m35A6:0406: 64 MOVSW, with BX=(width>>3)-2 between writes. */
    for (row = 0; row < 64; ++row) {
        destination[(uint16_t)(row*stride)] = pattern[row*2u];
        destination[(uint16_t)(row*stride+1u)] = pattern[row*2u+1u];
    }
    return SIM_S00_RASTER_OK;
}

void o00_35A6_02FD(void *r, void *s, void *c, void *d)
{
    (void)sim_s00_raster_copy_rect(r,s,SIZE_MAX,c,d,SIZE_MAX);
}

void o00_35A6_0007(void *image, void *buffer, int16_t shift, int16_t row_offset)
{
    (void)shifted_blit(image,SIZE_MAX,buffer,SIZE_MAX,shift,row_offset,1);
}

void o00_35A6_0177(void *image, void *buffer, int16_t shift, int16_t row_offset)
{
    (void)shifted_blit(image,SIZE_MAX,buffer,SIZE_MAX,shift,row_offset,0);
}

void o00_35A6_0406(void *destination, int16_t width)
{
    (void)sim_s00_raster_pattern_transfer((const uint8_t *)g_3D20,
                                         destination,SIZE_MAX,(uint16_t)width);
}
