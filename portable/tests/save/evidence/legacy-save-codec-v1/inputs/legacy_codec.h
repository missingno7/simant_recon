#ifndef SIMANT_PORTABLE_LEGACY_CODEC_H
#define SIMANT_PORTABLE_LEGACY_CODEC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PORTABLE_LEGACY_SAVE_RECORD_COUNT 307u
#define PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE 48386u

typedef struct PortableLegacySaveRecordSpec {
    uint16_t index;
    uint16_t element_size;
    uint16_t element_count;
    uint32_t payload_offset;
    const char *source_expression;
} PortableLegacySaveRecordSpec;

/*
 * A binding is a borrowed view of one source table row. For interior records,
 * bytes points at the source interior address and extent is the remaining
 * readable/writable extent from that address. All 307 rows must be bound.
 */
typedef struct PortableLegacySaveBinding {
    uint8_t *bytes;
    size_t extent;
} PortableLegacySaveBinding;

typedef struct PortableLegacySavePayload {
    uint8_t *bytes;
    size_t size;
} PortableLegacySavePayload;

typedef enum PortableLegacySaveStatus {
    PORTABLE_LEGACY_SAVE_OK = 0,
    PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT,
    PORTABLE_LEGACY_SAVE_MISSING_BINDING,
    PORTABLE_LEGACY_SAVE_BINDING_TOO_SMALL,
    PORTABLE_LEGACY_SAVE_INPUT_TOO_SHORT,
    PORTABLE_LEGACY_SAVE_INPUT_TRAILING_BYTES,
    PORTABLE_LEGACY_SAVE_ALLOCATION_FAILED
} PortableLegacySaveStatus;

typedef enum PortableLegacySaveInputPolicy {
    /* Require exactly the current 48,386-byte payload. */
    PORTABLE_LEGACY_SAVE_EXACT_LENGTH = 0,
    /* Match LoadGame's stream boundary: consume the expected prefix and ignore trailing bytes. */
    PORTABLE_LEGACY_SAVE_ALLOW_TRAILING_BYTES = 1
} PortableLegacySaveInputPolicy;

const PortableLegacySaveRecordSpec *portable_legacy_save_record_specs(size_t *count);
PortableLegacySaveStatus portable_legacy_save_encode(
    const PortableLegacySaveBinding *bindings,
    size_t binding_count,
    PortableLegacySavePayload *out_payload);
PortableLegacySaveStatus portable_legacy_save_decode(
    const uint8_t *input,
    size_t input_size,
    PortableLegacySaveBinding *bindings,
    size_t binding_count,
    PortableLegacySaveInputPolicy policy,
    size_t *consumed);
void portable_legacy_save_payload_free(PortableLegacySavePayload *payload);
const char *portable_legacy_save_status_name(PortableLegacySaveStatus status);

#ifdef __cplusplus
}
#endif

#endif
