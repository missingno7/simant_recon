#include "legacy_codec.h"

#include <stdlib.h>
#include <string.h>

static const PortableLegacySaveRecordSpec k_records[] = {
#include "legacy_records.inc"
};

const PortableLegacySaveRecordSpec *portable_legacy_save_record_specs(size_t *count)
{
    if (count != NULL) {
        *count = sizeof(k_records) / sizeof(k_records[0]);
    }
    return k_records;
}

static int host_is_little_endian(void)
{
#if defined(PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN)
    return 0;
#else
    const uint16_t one = 1u;
    return *((const uint8_t *)&one) == 1u;
#endif
}

static PortableLegacySaveStatus validate_bindings(
    const PortableLegacySaveBinding *bindings,
    size_t binding_count)
{
    size_t i;
    if (bindings == NULL || binding_count != PORTABLE_LEGACY_SAVE_RECORD_COUNT) {
        return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    }
    for (i = 0; i < PORTABLE_LEGACY_SAVE_RECORD_COUNT; ++i) {
        const size_t need = (size_t)k_records[i].element_size * k_records[i].element_count;
        if (bindings[i].bytes == NULL) {
            return PORTABLE_LEGACY_SAVE_MISSING_BINDING;
        }
        if (bindings[i].extent < need) {
            return PORTABLE_LEGACY_SAVE_BINDING_TOO_SMALL;
        }
        if (bindings[i].storage_order != PORTABLE_LEGACY_SAVE_RAW_BYTES &&
            bindings[i].storage_order != PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16 &&
            bindings[i].storage_order != PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32) {
            return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
        }
        if (bindings[i].storage_order != PORTABLE_LEGACY_SAVE_RAW_BYTES &&
            need % (size_t)bindings[i].storage_order != 0) {
            return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
        }
    }
    return PORTABLE_LEGACY_SAVE_OK;
}

static void copy_to_stream(uint8_t *dest, const uint8_t *src,
                           uint16_t element_size, uint16_t element_count,
                           PortableLegacySaveStorageOrder storage_order)
{
    size_t i;
    const size_t component_size = (size_t)storage_order;
    const size_t byte_count = (size_t)element_size * element_count;
    if (storage_order == PORTABLE_LEGACY_SAVE_RAW_BYTES ||
        host_is_little_endian() || component_size == 1u) {
        memcpy(dest, src, byte_count);
        return;
    }
    for (i = 0; i < byte_count / component_size; ++i) {
        size_t j;
        for (j = 0; j < component_size; ++j) {
            dest[i * component_size + j] = src[i * component_size + (component_size - j - 1u)];
        }
    }
}

static void copy_from_stream(uint8_t *dest, const uint8_t *src,
                             uint16_t element_size, uint16_t element_count,
                             PortableLegacySaveStorageOrder storage_order)
{
    /* Byte reversal is its own inverse. */
    copy_to_stream(dest, src, element_size, element_count, storage_order);
}

PortableLegacySaveStatus portable_legacy_save_encode(
    const PortableLegacySaveBinding *bindings,
    size_t binding_count,
    PortableLegacySavePayload *out_payload)
{
    PortableLegacySaveStatus status;
    uint8_t *bytes;
    size_t i;
    if (out_payload == NULL) {
        return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    }
    out_payload->bytes = NULL;
    out_payload->size = 0;
    status = validate_bindings(bindings, binding_count);
    if (status != PORTABLE_LEGACY_SAVE_OK) {
        return status;
    }
    bytes = (uint8_t *)malloc(PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);
    if (bytes == NULL) {
        return PORTABLE_LEGACY_SAVE_ALLOCATION_FAILED;
    }
    for (i = 0; i < PORTABLE_LEGACY_SAVE_RECORD_COUNT; ++i) {
        copy_to_stream(bytes + k_records[i].payload_offset,
                       bindings[i].bytes,
                       k_records[i].element_size,
                       k_records[i].element_count,
                       bindings[i].storage_order);
    }
    out_payload->bytes = bytes;
    out_payload->size = PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE;
    return PORTABLE_LEGACY_SAVE_OK;
}

PortableLegacySaveStatus portable_legacy_save_decode(
    const uint8_t *input,
    size_t input_size,
    PortableLegacySaveBinding *bindings,
    size_t binding_count,
    PortableLegacySaveInputPolicy policy,
    size_t *consumed)
{
    PortableLegacySaveStatus status;
    size_t i;
    if (consumed != NULL) {
        *consumed = 0;
    }
    if (input == NULL || (policy != PORTABLE_LEGACY_SAVE_EXACT_LENGTH &&
                          policy != PORTABLE_LEGACY_SAVE_ALLOW_TRAILING_BYTES)) {
        return PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT;
    }
    if (input_size < PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE) {
        return PORTABLE_LEGACY_SAVE_INPUT_TOO_SHORT;
    }
    if (policy == PORTABLE_LEGACY_SAVE_EXACT_LENGTH &&
        input_size != PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE) {
        return PORTABLE_LEGACY_SAVE_INPUT_TRAILING_BYTES;
    }
    status = validate_bindings(bindings, binding_count);
    if (status != PORTABLE_LEGACY_SAVE_OK) {
        return status;
    }
    /* Validate the complete input and every destination before changing state. */
    for (i = 0; i < PORTABLE_LEGACY_SAVE_RECORD_COUNT; ++i) {
        copy_from_stream(bindings[i].bytes,
                         input + k_records[i].payload_offset,
                         k_records[i].element_size,
                         k_records[i].element_count,
                         bindings[i].storage_order);
    }
    if (consumed != NULL) {
        *consumed = PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE;
    }
    return PORTABLE_LEGACY_SAVE_OK;
}

void portable_legacy_save_payload_free(PortableLegacySavePayload *payload)
{
    if (payload != NULL) {
        free(payload->bytes);
        payload->bytes = NULL;
        payload->size = 0;
    }
}

const char *portable_legacy_save_status_name(PortableLegacySaveStatus status)
{
    switch (status) {
    case PORTABLE_LEGACY_SAVE_OK: return "ok";
    case PORTABLE_LEGACY_SAVE_INVALID_ARGUMENT: return "invalid-argument";
    case PORTABLE_LEGACY_SAVE_MISSING_BINDING: return "missing-binding";
    case PORTABLE_LEGACY_SAVE_BINDING_TOO_SMALL: return "binding-too-small";
    case PORTABLE_LEGACY_SAVE_INPUT_TOO_SHORT: return "input-too-short";
    case PORTABLE_LEGACY_SAVE_INPUT_TRAILING_BYTES: return "input-trailing-bytes";
    case PORTABLE_LEGACY_SAVE_ALLOCATION_FAILED: return "allocation-failed";
    default: return "unknown";
    }
}
