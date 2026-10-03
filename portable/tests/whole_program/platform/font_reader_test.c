#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/handles.h"
#include "portable/whole_program/types/fonts.h"
#include "portable/render/font.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Font *font_ReadFont(char *name);
struct Font *font_DumpFont(struct Font *font);
int16_t _font_CharWidth(int16_t ch, struct Font *font);
static uint8_t *read_asset(const char *path, size_t *length) {
    FILE *fp = fopen(path, "rb"); long n; uint8_t *bytes;
    assert(fp && fseek(fp, 0, SEEK_END) == 0); n = ftell(fp); assert(n >= 0);
    rewind(fp); bytes = (uint8_t *)malloc((size_t)n); assert(bytes);
    assert(fread(bytes, 1, (size_t)n, fp) == (size_t)n); fclose(fp); *length = (size_t)n; return bytes;
}
static void check_one(unsigned index) {
    char path[64], name[16]; size_t length, i; uint8_t *bytes; PortableFont parsed; struct Font *loaded;
    snprintf(path, sizeof(path), "FONT%u", index + 1); snprintf(name, sizeof(name), "FONT%u", index + 1);
    bytes = read_asset(path, &length); portable_font_init(&parsed);
    assert(portable_font_load(&parsed, bytes, length) == PORTABLE_RENDER_OK);
    loaded = font_ReadFont(name); assert(loaded);
    assert(memcmp(loaded, parsed.metrics, sizeof(parsed.metrics)) == 0);
    assert(loaded->proportional == parsed.proportional && loaded->missing == parsed.missing_char);
    assert((size_t)loaded->rowWords * (size_t)loaded->fRectHeight * 2u == parsed.image_size);
    assert((size_t)(loaded->lastChar - loaded->firstChar + 3) == parsed.table_count);
    assert(memcmp(loaded->image, parsed.image, parsed.image_size) == 0);
    assert(memcmp(loaded->locTable, parsed.loc_table, parsed.table_count * sizeof(*parsed.loc_table)) == 0);
    assert(memcmp(loaded->owTable, parsed.ow_table, parsed.table_count * sizeof(*parsed.ow_table)) == 0);
    for (i = 0; i < parsed.table_count; ++i) assert(_font_CharWidth((int16_t)i, loaded) == portable_font_char_width(&parsed, (uint8_t)i));
    assert(font_DumpFont(loaded) == NULL); portable_font_destroy(&parsed); free(bytes);
}
int main(void) {
    unsigned i; assert(sim_handles_global_configure(8192, 4096) == SIM_HANDLE_OK);
    assert(dos_files_set_root("assets") == 0);
    for (i = 0; i < 4; ++i) check_one(i);
    dos_files_close_all();
    puts("generated font_ReadFont integration passed for FONT1-FONT4"); return 0;
}


