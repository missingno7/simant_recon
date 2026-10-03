#ifndef SIMANT_WHOLE_PROGRAM_TEXT_BITMAP_BRIDGE_H
#define SIMANT_WHOLE_PROGRAM_TEXT_BITMAP_BRIDGE_H

#include "text_bitmap.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Bind the source-only state needed by m1FBD's raw `_g_5FBE + AL` lookup.
 * The span is borrowed and must cover the live source DGROUP bytes beginning
 * at `_g_5FBE`; it is not a replacement fold table. NULL keeps ASCII usable
 * while making width-4 high-byte folding fail closed. */
PortableTextBitmapStatus portable_text_bitmap_bind_source(
    uint8_t hardware_profile,
    const uint8_t *fold_lookup_window,
    size_t fold_lookup_window_size);
void portable_text_bitmap_unbind_source(void);
PortableTextBitmapStatus portable_text_bitmap_source_status(void);
const PortableTextBitmapState *portable_text_bitmap_source_state(void);

/* Native implementation of the original far source ABI. Native C callers use
 * the ordinary C stack ABI; x/y/text widths and side effects retain the source
 * contract. A graphics source owner must already be bound. */
void f_1FBD_0000(int16_t x, int16_t y, char *text);

#ifdef __cplusplus
}
#endif

#endif
