#include "../../ui_model/dialogs/picture_dialog.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t *read_file(const char *path, size_t *size)
{
    FILE *file = fopen(path, "rb");
    long length;
    uint8_t *bytes;
    if (file == NULL)
        return NULL;
    if (fseek(file, 0, SEEK_END) != 0 || (length = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return NULL;
    }
    bytes = (uint8_t *)malloc((size_t)length);
    if (bytes == NULL || fread(bytes, 1, (size_t)length, file) != (size_t)length) {
        free(bytes);
        fclose(file);
        return NULL;
    }
    fclose(file);
    *size = (size_t)length;
    return bytes;
}

int main(int argc, char **argv)
{
    char shared_path[1024], window_path[1024], font_path[1024];
    PortableDatabase shared = {0}, windows = {0};
    PortableDbRecord colors = {0};
    PortableFontSet fonts;
    PortablePictureDialog dialog;
    PortableWindowRenderer renderer = {0};
    PortableFramebuffer framebuffer;
    PortableBiosFontProvider bios = {0};
    uint8_t *bios8, *bios14;
    size_t bios8_size, bios14_size;
    uint8_t pixels[640 * 400];
    PortablePictureDialogRequest request = {0, 11000, 0, 0, 640, 400};
    PortablePictureDialogStatus status;
    const PortableFont *font;
    size_t i;
    int32_t widest = 50;
    int32_t height;
    assert(argc == 2);
    assert(snprintf(shared_path, sizeof(shared_path), "%s/SHARED", argv[1]) <
           (int)sizeof(shared_path));
    assert(snprintf(window_path, sizeof(window_path), "%s/HCEGANT", argv[1]) <
           (int)sizeof(window_path));
    assert(snprintf(font_path, sizeof(font_path), "%s", argv[1]) <
           (int)sizeof(font_path));
    assert(portable_db_open(&shared, shared_path) == PORTABLE_DB_OK);
    assert(portable_db_open(&windows, window_path) == PORTABLE_DB_OK);
    assert(portable_db_load(&windows, 0x81, 0, &colors) == PORTABLE_DB_OK);
    portable_fonts_init(&fonts);
    assert(portable_fonts_load(&fonts, font_path) == PORTABLE_RENDER_OK);
    portable_picture_dialog_init(&dialog);

    /* A disabled, non-forced call is the source PictStrnDialog early exit. */
    status = portable_picture_dialog_prepare(&dialog, &shared, &windows,
                                              &fonts, request);
    assert(status == PORTABLE_PICTURE_DIALOG_SUPPRESSED);
    assert(!dialog.visible && dialog.line_count == 0);

    request.force = 1;
    status = portable_picture_dialog_prepare(&dialog, &shared, &windows,
                                              &fonts, request);
    if (status != PORTABLE_PICTURE_DIALOG_OK) {
        fprintf(stderr, "picture dialog prepare failed: %s\n",
                portable_picture_dialog_status_string(status));
        return 1;
    }
    assert(dialog.visible && dialog.font_id == 4);
    assert(dialog.request.picture_id == 0 && dialog.picture_width == 0 &&
           dialog.picture_height == 0);
    font = portable_fonts_get(&fonts, 4);
    assert(font != NULL);
    for (i = 0; i < dialog.line_count; ++i) {
        int32_t width = portable_font_string_width(font, dialog.lines[i].bytes,
                                                   dialog.lines[i].length);
        if (width > widest)
            widest = width;
    }
    height = (int32_t)dialog.line_count * (font->metrics[7] - 1) + 8;
    assert(dialog.rect.right - dialog.rect.left == widest + 8);
    assert(dialog.rect.bottom - dialog.rect.top == height);
    assert(dialog.rect.left == (640 - widest - 8) / 2);
    assert(dialog.line_count != 0);
    assert(dialog.lines[0].draw_y == dialog.rect.top);
    assert(dialog.text_color_index ==
           ((dialog.window.objects[1].flags & 4u)
                ? (uint8_t)(dialog.window.objects[1].value >> 8)
                : (uint8_t)dialog.window.objects[1].value));
    assert(portable_framebuffer_init(&framebuffer, 640, 400, 640, pixels) ==
           PORTABLE_RENDER_OK);
    memset(pixels, 0, sizeof(pixels));
    renderer.framebuffer = &framebuffer;
    renderer.database = &windows;
    renderer.colors = colors.data;
    renderer.colors_size = colors.size;
    renderer.screen_width = 640;
    bios8 = read_file("build/bios-reference/dosbox-staging-v0.83.0/font-8x8.bin",
                      &bios8_size);
    bios14 = read_file("build/bios-reference/dosbox-staging-v0.83.0/font-8x14.bin",
                       &bios14_size);
    if (bios8 != NULL && bios14 != NULL &&
        portable_bios_font_provider_init(&bios, bios8, bios8_size,
                    bios14, bios14_size, "DOSBox Staging v0.83.0") ==
                    PORTABLE_RENDER_OK)
        renderer.bios_fonts = &bios;
    status = portable_picture_dialog_render(&dialog, &fonts, &renderer);
    if (status != PORTABLE_PICTURE_DIALOG_OK) {
        fprintf(stderr, "picture dialog render failed (BIOS reference %s): %s\n",
                renderer.bios_fonts != NULL ? "available" : "unavailable",
                portable_picture_dialog_status_string(status));
        return 1;
    }
    {
        size_t nonzero = 0;
        for (i = 0; i < sizeof(pixels); ++i)
            if (pixels[i] != 0)
                ++nonzero;
        assert(nonzero != 0);
    }

    /* Exercise packed/raw image measurement and the source image-before-text
     * vertical spacing using a real SHARED kind-2 record. */
    request.picture_id = 128;
    status = portable_picture_dialog_prepare(&dialog, &shared, &windows,
                                              &fonts, request);
    if (status != PORTABLE_PICTURE_DIALOG_OK) {
        fprintf(stderr, "picture dialog image prepare failed: %s\n",
                portable_picture_dialog_status_string(status));
        return 1;
    }
    assert(dialog.picture_width != 0 && dialog.picture_height != 0);
    assert(dialog.rect.bottom - dialog.rect.top ==
           (int32_t)dialog.picture_height + 2 + height);
    assert(dialog.lines[0].draw_y ==
           dialog.rect.top + dialog.picture_height + 2);
    memset(pixels, 0, sizeof(pixels));
    assert(portable_picture_dialog_render(&dialog, &fonts, &renderer) ==
           PORTABLE_PICTURE_DIALOG_OK);
    portable_picture_dialog_dismiss(&dialog);
    assert(dialog.dismissed);
    portable_picture_dialog_release(&dialog);
    portable_fonts_destroy(&fonts);
    portable_db_record_free(&colors);
    portable_db_close(&windows);
    portable_db_close(&shared);
    free(bios8);
    free(bios14);
    puts("picture dialog: tutorial resource, source geometry, and modal state passed");
    return 0;
}
