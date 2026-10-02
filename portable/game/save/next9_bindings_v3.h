#ifndef SIMANT_PORTABLE_NEXT9_SAVE_BINDINGS_V3_H
#define SIMANT_PORTABLE_NEXT9_SAVE_BINDINGS_V3_H

#include "legacy_codec.h"
#include "recovered_state.h"

PortableLegacySaveStatus portable_next9_save_encode_v3(
    RecoveredState *state, PortableLegacySavePayload *out_payload);
PortableLegacySaveStatus portable_next9_save_decode_v3(
    RecoveredState *state, const uint8_t *input, size_t input_size,
    PortableLegacySaveInputPolicy policy, size_t *consumed);

#endif
