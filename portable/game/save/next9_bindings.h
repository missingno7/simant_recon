#ifndef SIMANT_PORTABLE_NEXT9_SAVE_BINDINGS_H
#define SIMANT_PORTABLE_NEXT9_SAVE_BINDINGS_H

#include "legacy_codec.h"
#include "recovered_state.h"

/*
 * Bind the exact legacy 307-row stream to the Next9 source state. Encoding
 * imports state into the generated source TLS; decoding exports only after a
 * fully validated successful decode. The row-99 interior is raw bytes.
 */
PortableLegacySaveStatus portable_next9_save_encode(
    RecoveredState *state, PortableLegacySavePayload *out_payload);
PortableLegacySaveStatus portable_next9_save_decode(
    RecoveredState *state, const uint8_t *input, size_t input_size,
    PortableLegacySaveInputPolicy policy, size_t *consumed);

#endif
