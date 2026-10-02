#include "next9_bindings_v3.h"

#include <string.h>

static PortableLegacySaveStatus make_bindings_v3(PortableLegacySaveBinding *bindings,
                                                  size_t binding_count)
{
    size_t count = 0;
    const PortableLegacySaveRecordSpec *specs = portable_legacy_save_record_specs(&count);
    if (bindings == NULL || specs == NULL || binding_count != PORTABLE_LEGACY_SAVE_RECORD_COUNT ||
        count != PORTABLE_LEGACY_SAVE_RECORD_COUNT) return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    memset(bindings, 0, sizeof(*bindings) * binding_count);
#include "next9_bindings_v3_rows.inc"
    return PORTABLE_LEGACY_SAVE_OK;
}

PortableLegacySaveStatus portable_next9_save_encode_v3(
    RecoveredState *state, PortableLegacySavePayload *out_payload)
{
    RecoveredBindingFrame frame;
    PortableLegacySaveBinding bindings[PORTABLE_LEGACY_SAVE_RECORD_COUNT];
    PortableLegacySaveStatus status;
    if (state == NULL) return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    recovered_bind_begin(&frame, state);
    status = make_bindings_v3(bindings, PORTABLE_LEGACY_SAVE_RECORD_COUNT);
    if (status == PORTABLE_LEGACY_SAVE_OK)
        status = portable_legacy_save_encode(bindings, PORTABLE_LEGACY_SAVE_RECORD_COUNT, out_payload);
    recovered_bind_end(&frame, state);
    return status;
}

PortableLegacySaveStatus portable_next9_save_decode_v3(
    RecoveredState *state, const uint8_t *input, size_t input_size,
    PortableLegacySaveInputPolicy policy, size_t *consumed)
{
    RecoveredBindingFrame frame;
    RecoveredState discard;
    PortableLegacySaveBinding bindings[PORTABLE_LEGACY_SAVE_RECORD_COUNT];
    PortableLegacySaveStatus status;
    if (state == NULL) return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    recovered_bind_begin(&frame, state);
    status = make_bindings_v3(bindings, PORTABLE_LEGACY_SAVE_RECORD_COUNT);
    if (status == PORTABLE_LEGACY_SAVE_OK)
        status = portable_legacy_save_decode(input, input_size, bindings,
                                             PORTABLE_LEGACY_SAVE_RECORD_COUNT, policy, consumed);
    if (status == PORTABLE_LEGACY_SAVE_OK) recovered_bind_end(&frame, state);
    else recovered_bind_end(&frame, &discard);
    return status;
}
