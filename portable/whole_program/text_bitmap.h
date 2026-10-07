#ifndef SIMANT_WHOLE_PROGRAM_TEXT_BITMAP_H
#define SIMANT_WHOLE_PROGRAM_TEXT_BITMAP_H

#include <stddef.h>
#include <stdint.h>

#define PORTABLE_TEXT_BITMAP_CAPACITY 1040u
#define PORTABLE_TEXT_BITMAP_TEXT_CAPACITY 80u

typedef enum PortableTextBitmapStatus {
    PORTABLE_TEXT_BITMAP_OK = 0,
    PORTABLE_TEXT_BITMAP_INVALID_ARGUMENT,
    PORTABLE_TEXT_BITMAP_UNSUPPORTED_PROFILE,
    PORTABLE_TEXT_BITMAP_UNSUPPORTED_FONT,
    PORTABLE_TEXT_BITMAP_UNSUPPORTED_CHARACTER,
    PORTABLE_TEXT_BITMAP_UNTERMINATED_TEXT,
    PORTABLE_TEXT_BITMAP_BUFFER_TOO_SMALL
} PortableTextBitmapStatus;

typedef enum PortableTextBitmapDrawKind {
    PORTABLE_TEXT_BITMAP_NO_DRAW = 0,
    PORTABLE_TEXT_BITMAP_DRAW_BITMAP,
    PORTABLE_TEXT_BITMAP_DRAW_DIRECT_TEXT
} PortableTextBitmapDrawKind;

typedef struct PortableTextBitmapInput {
    uint8_t hardware_profile;
    uint8_t character_width;
    uint8_t cell_height;
    uint16_t glyph_height;
    const uint8_t *glyph_rows;
    size_t glyph_rows_size;
    /* Original code indexes from `_g_5FBE` with the raw high-byte value. */
    const uint8_t *fold_lookup_window;
    size_t fold_lookup_window_size;
    const uint8_t *text;
    size_t text_size;
    int16_t x;
    int16_t y;
} PortableTextBitmapInput;

/* Borrowed writable views of the canonical source owners. This descriptor
 * carries addresses and extents only; it never owns a shadow bitmap/string. */
typedef struct PortableTextBitmapOwnerView {
    uint16_t *width;
    uint16_t *height;
    uint8_t *pixels;
    size_t pixels_capacity;
    uint8_t *copied_text;
    size_t copied_text_capacity;
    uint8_t *copied_text_terminator;
} PortableTextBitmapOwnerView;

typedef struct PortableTextBitmapResult {
    PortableTextBitmapDrawKind draw_kind;
    size_t copied_characters;
    uint16_t drawn_width;
    uint16_t drawn_height;
    uint16_t stride_bytes;
    /* Direct-text mode borrows input->text for the immediate source sink call. */
    const uint8_t *direct_text;
    size_t direct_text_size;
} PortableTextBitmapResult;

PortableTextBitmapStatus portable_text_bitmap_prepare(
    const PortableTextBitmapInput *input,
    PortableTextBitmapOwnerView *owners,
    PortableTextBitmapResult *result);

#endif
