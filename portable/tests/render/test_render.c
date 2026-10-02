#include "../../render/bitmap.h"
#include "../../render/font.h"
#include "../../game/resources/database.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put_le16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void test_primitives(void)
{
    uint8_t pixels[6 * 4];
    PortableFramebuffer fb;
    memset(pixels, 0, sizeof(pixels));
    assert(portable_framebuffer_init(&fb, 6, 4, 6, pixels) == PORTABLE_RENDER_OK);
    portable_framebuffer_set_clip(&fb, (PortableRect){1, 1, 5, 3});
    portable_fill_rect(&fb, (PortableRect){0, 0, 6, 4}, 7);
    assert(pixels[0] == 0 && pixels[1 * 6 + 1] == 7 && pixels[2 * 6 + 4] == 7);
    assert(pixels[2 * 6 + 5] == 0 && pixels[3 * 6 + 1] == 0);
    portable_xor_rect(&fb, (PortableRect){1, 1, 2, 2}, 3);
    assert(pixels[1 * 6 + 1] == (uint8_t)(7 ^ 3));
    portable_fill_rect(&fb, (PortableRect){4, 2, 2, 1}, 5);
    assert(pixels[1 * 6 + 2] == 5 && pixels[1 * 6 + 3] == 5);
    portable_framebuffer_reset_clip(&fb);
    {
        const uint8_t checker[8] = {0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA};
        portable_fill_pattern_1bpp(&fb, (PortableRect){0, 0, 4, 2}, checker, 2, 3);
        assert(pixels[0] == 3 && pixels[1] == 2 && pixels[6] == 2 && pixels[7] == 3);
    }
}

static void test_raw_ega4(void)
{
    uint8_t resource[12 + 4];
    uint8_t pixels[8];
    PortableFramebuffer fb;
    PortableBitmap bitmap;
    memset(resource, 0, sizeof(resource));
    memset(pixels, 0, sizeof(pixels));
    put_le16(resource, 0);
    resource[2] = 0;
    put_le16(resource + 8, 8);
    put_le16(resource + 10, 1);
    resource[12] = 0x80; /* plane 0 */
    resource[13] = 0x40; /* plane 1 */
    resource[14] = 0x20; /* plane 2 */
    resource[15] = 0x10; /* plane 3 */
    assert(portable_framebuffer_init(&fb, 8, 1, 8, pixels) == PORTABLE_RENDER_OK);
    assert(portable_bitmap_view(resource, sizeof(resource), &bitmap) == PORTABLE_RENDER_OK);
    assert(portable_bitmap_draw(&fb, 0, 0, &bitmap) == PORTABLE_RENDER_OK);
    assert(pixels[0] == 1 && pixels[1] == 2 && pixels[2] == 4 && pixels[3] == 8);
    assert(pixels[4] == 0 && pixels[7] == 0);
    assert(portable_bitmap_view(resource, sizeof(resource) - 1, &bitmap) ==
           PORTABLE_RENDER_TRUNCATED_DATA);
}

static void test_interleaved_ega4(void)
{
    uint8_t pixels[16 * 2] = {0};
    uint8_t source[16] = {0};
    PortableFramebuffer fb;
    assert(portable_framebuffer_init(&fb, 16, 2, 16, pixels) == PORTABLE_RENDER_OK);
    source[0] = 0x80; /* plane 0, x=0 */
    source[1] = 0x40; /* plane 1, x=1 */
    source[2] = 0x20; /* plane 2, x=2 */
    source[3] = 0x10; /* plane 3, x=3 */
    source[4] = 0x01; /* plane 0, x=15 */
    assert(portable_bitmap_draw_interleaved_ega4(&fb, 0, 0, 16, 1, source,
                                                  sizeof(source), 2, 8) ==
           PORTABLE_RENDER_OK);
    assert(pixels[0] == 1 && pixels[1] == 2 && pixels[2] == 4 && pixels[3] == 8);
    assert(pixels[15] == 1);
    memset(pixels, 0, sizeof(pixels));
    portable_framebuffer_set_clip(&fb, (PortableRect){1, 0, 3, 1});
    assert(portable_bitmap_draw_interleaved_ega4(&fb, 0, 0, 16, 1, source,
                                                  sizeof(source), 2, 8) ==
           PORTABLE_RENDER_OK);
    assert(pixels[0] == 0 && pixels[1] == 2 && pixels[2] == 4 && pixels[3] == 0);
}

static void test_type3_error_and_mask_merge(void)
{
    uint8_t resource[17] = {0};
    uint8_t pixels[4] = {9, 9, 9, 9};
    uint8_t encoded[5] = {0xA0, 0x80, 0x40, 0x20, 0x10};
    PortableFramebuffer fb;
    PortableBitmap bitmap;
    put_le16(resource, 3);
    put_le16(resource + 8, 4);
    put_le16(resource + 10, 1);
    memcpy(resource + 12, encoded, sizeof(encoded));
    assert(portable_framebuffer_init(&fb, 4, 1, 4, pixels) == PORTABLE_RENDER_OK);
    assert(portable_bitmap_view(resource, sizeof(resource), &bitmap) == PORTABLE_RENDER_OK);
    assert(portable_bitmap_draw(&fb, 0, 0, &bitmap) == PORTABLE_RENDER_OK);
    assert(pixels[0] == 1 && pixels[1] == 9 && pixels[2] == 4 && pixels[3] == 9);
    assert(portable_bitmap_merge_ega4(&fb, 0, 0, 4, 1, encoded, 4, 1) ==
           PORTABLE_RENDER_TRUNCATED_DATA);
}

static void write_be16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)(v >> 8);
    p[1] = (uint8_t)v;
}

static void test_synthetic_font(void)
{
    uint8_t bytes[26 + 4 + 258 * 4];
    uint8_t pixels[8 * 3];
    PortableFramebuffer fb;
    PortableFont font;
    int32_t end_x = -1;
    size_t i;
    memset(bytes, 0, sizeof(bytes));
    memset(pixels, 0, sizeof(pixels));
    write_be16(bytes + 0, 0x8000); /* fixed-width font */
    write_be16(bytes + 2, 0);
    write_be16(bytes + 4, 255);
    write_be16(bytes + 6, 1); /* widMax */
    write_be16(bytes + 8, 1); /* kernMax */
    write_be16(bytes + 12, 1); /* fRectWidth */
    write_be16(bytes + 14, 2); /* fRectHeight */
    write_be16(bytes + 24, 1); /* rowWords */
    bytes[26] = 0xC0;
    bytes[28] = 0xC0; /* font_MakeImage skips the initial bitmap scanline */
    for (i = 0; i < 258; ++i) {
        write_be16(bytes + 30 + i * 2, (uint16_t)(i == 0 ? 0 : i - 1));
        write_be16(bytes + 30 + 258 * 2 + i * 2, 1);
    }
    portable_font_init(&font);
    assert(portable_framebuffer_init(&fb, 8, 3, 8, pixels) == PORTABLE_RENDER_OK);
    assert(portable_font_load(&font, bytes, sizeof(bytes)) == PORTABLE_RENDER_OK);
    assert(portable_font_char_width(&font, 1) == 1);
    assert(portable_font_draw(&fb, &font, 1, 0, (const uint8_t *)"\1\2", 2, 6, &end_x) ==
           PORTABLE_RENDER_OK);
    assert(end_x == 3);
    assert(pixels[2] == 6 && pixels[3] == 6);
    portable_font_destroy(&font);
}

static void test_real_font_file(const char *path)
{
    FILE *f;
    long length;
    uint8_t *bytes;
    uint8_t pixels[160 * 20];
    PortableFramebuffer fb;
    PortableFont font;
    int32_t end_x;
    size_t i;
    size_t nonzero = 0;
    if (path == NULL)
        return;
    f = fopen(path, "rb");
    assert(f != NULL);
    assert(fseek(f, 0, SEEK_END) == 0);
    length = ftell(f);
    assert(length >= 26);
    rewind(f);
    bytes = (uint8_t *)malloc((size_t)length);
    assert(bytes != NULL);
    assert(fread(bytes, 1, (size_t)length, f) == (size_t)length);
    fclose(f);
    portable_font_init(&font);
    assert(portable_font_load(&font, bytes, (size_t)length) == PORTABLE_RENDER_OK);
    assert(font.table_count >= 258 || font.last_char < 255);
    memset(pixels, 0, sizeof(pixels));
    assert(portable_framebuffer_init(&fb, 160, 20, 160, pixels) == PORTABLE_RENDER_OK);
    assert(portable_font_draw(&fb, &font, 2, 1, (const uint8_t *)"SimAnt 123", 10,
                              15, &end_x) == PORTABLE_RENDER_OK);
    assert(end_x == 2 + portable_font_string_width(&font,
                                                    (const uint8_t *)"SimAnt 123", 10));
    for (i = 0; i < sizeof(pixels); ++i)
        nonzero += pixels[i] != 0;
    assert(nonzero != 0);
    portable_font_destroy(&font);
    free(bytes);
}

static void test_actual_hcegant_bitmaps(const char *asset_dir)
{
    char root[512];
    PortableDatabase db;
    PortableDbRecord raw_record, type3_record, packed_record;
    PortableBitmap raw, type3;
    PortableFramebuffer fb;
    uint8_t *pixels;
    size_t i, changed_raw = 0, changed_type3 = 0;
    if (asset_dir == NULL)
        return;
    (void)snprintf(root, sizeof(root), "%s/HCEGANT", asset_dir);
    memset(&db, 0, sizeof(db));
    assert(portable_db_open(&db, root) == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 1210, 2, &raw_record) == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 1200, 2, &type3_record) == PORTABLE_DB_OK);
    assert(portable_db_load(&db, 2500, 2, &packed_record) == PORTABLE_DB_OK);
    assert(portable_bitmap_view(raw_record.data, raw_record.size, &raw) == PORTABLE_RENDER_OK);
    assert(raw.type == 0 && raw.mode == 4 && raw.width == 98 && raw.height == 103);
    assert(portable_bitmap_view(type3_record.data, type3_record.size, &type3) == PORTABLE_RENDER_OK);
    assert(type3.type == 3 && type3.width == 23 && type3.height == 68);
    assert(type3.pixels_size == 5u * 3u * 68u);

    pixels = (uint8_t *)malloc(640u * 350u);
    assert(pixels != NULL);
    memset(pixels, 0, 640u * 350u);
    assert(portable_framebuffer_init(&fb, 640, 350, 640, pixels) == PORTABLE_RENDER_OK);
    assert(packed_record.size == 9644 && packed_record.data[0] == 0xff &&
           packed_record.data[1] == 0xff);
    {
        PortableRenderStatus packed_status = portable_bitmap_draw_resource(
            &fb, 0, 0, packed_record.data, packed_record.size);
        if (packed_status != PORTABLE_RENDER_OK)
            fprintf(stderr, "packed bitmap status: %d\n", (int)packed_status);
        assert(packed_status == PORTABLE_RENDER_OK);
    }
    for (i = 0; i < 256u * 320u; ++i)
        changed_raw += pixels[(i / 320u) * 640u + (i % 320u)] != 0;
    assert(changed_raw > 0);

    memset(pixels, 0, 640u * 350u);
    changed_raw = 0;
    assert(portable_bitmap_draw(&fb, 20, 30, &raw) == PORTABLE_RENDER_OK);
    for (i = 0; i < 640u * 350u; ++i)
        changed_raw += pixels[i] != 0;
    assert(changed_raw > 0);

    memset(pixels, 9, 640u * 350u);
    assert(portable_bitmap_draw(&fb, 40, 50, &type3) == PORTABLE_RENDER_OK);
    for (i = 0; i < 640u * 350u; ++i)
        changed_type3 += pixels[i] != 9;
    assert(changed_type3 > 0);
    portable_framebuffer_set_clip(&fb, (PortableRect){0, 0, 10, 10});
    memset(pixels, 9, 640u * 350u);
    assert(portable_bitmap_draw(&fb, -5, -5, &type3) == PORTABLE_RENDER_OK);
    for (i = 0; i < 640u * 350u; ++i)
        if (i >= 10u * 640u || (i % 640u) >= 10u)
            assert(pixels[i] == 9);
    portable_framebuffer_reset_clip(&fb);
    free(pixels);
    portable_db_record_free(&raw_record);
    portable_db_record_free(&type3_record);
    portable_db_record_free(&packed_record);
    portable_db_close(&db);
}

int main(int argc, char **argv)
{
    char font_path[512];
    unsigned font_no;
    test_primitives();
    test_raw_ega4();
    test_interleaved_ega4();
    test_type3_error_and_mask_merge();
    test_synthetic_font();
    if (argc > 1) {
        for (font_no = 1; font_no <= 4; ++font_no) {
            (void)snprintf(font_path, sizeof(font_path), "%s/FONT%u", argv[1], font_no);
            test_real_font_file(font_path);
        }
        test_actual_hcegant_bitmaps(argv[1]);
    }
    puts("render primitive tests passed");
    return 0;
}
