#include "../../game/save/legacy_codec.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t *g_storage[PORTABLE_LEGACY_SAVE_RECORD_COUNT];
static PortableLegacySaveBinding g_bindings[PORTABLE_LEGACY_SAVE_RECORD_COUNT];

static void assert_encoded_record(const PortableLegacySaveRecordSpec *spec,
                                  const uint8_t *original,
                                  const uint8_t *encoded,
                                  PortableLegacySaveStorageOrder storage_order)
{
    const size_t byte_count = (size_t)spec->element_size * spec->element_count;
    const size_t component_size = (size_t)storage_order;
#if defined(PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN)
    size_t offset;
    if (storage_order == PORTABLE_LEGACY_SAVE_RAW_BYTES) {
        assert(memcmp(original, encoded, byte_count) == 0);
        return;
    }
    for (offset = 0; offset < byte_count; offset += component_size) {
        size_t j;
        for (j = 0; j < component_size; ++j) {
            assert(encoded[offset + j] == original[offset + component_size - j - 1u]);
        }
    }
#else
    (void)component_size;
    assert(memcmp(original, encoded, byte_count) == 0);
#endif
}

static void setup_bindings(void)
{
    size_t count = 0;
    const PortableLegacySaveRecordSpec *specs = portable_legacy_save_record_specs(&count);
    size_t i;
    assert(count == PORTABLE_LEGACY_SAVE_RECORD_COUNT);
    for (i = 0; i < count; ++i) {
        const size_t bytes = (size_t)specs[i].element_size * specs[i].element_count;
        size_t j;
        g_storage[i] = (uint8_t *)malloc(bytes);
        assert(g_storage[i] != NULL);
        for (j = 0; j < bytes; ++j) {
            g_storage[i][j] = (uint8_t)(i * 29u + j * 17u + (j >> 3));
        }
        g_bindings[i].bytes = g_storage[i];
        g_bindings[i].extent = bytes;
        g_bindings[i].storage_order =
            (specs[i].element_size == 1u || i == 99u)
                ? PORTABLE_LEGACY_SAVE_RAW_BYTES
                : (specs[i].element_size == 2u
                       ? PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_16
                       : PORTABLE_LEGACY_SAVE_NATIVE_NUMERIC_32);
    }
}

static void teardown_bindings(void)
{
    size_t i;
    for (i = 0; i < PORTABLE_LEGACY_SAVE_RECORD_COUNT; ++i) {
        free(g_storage[i]);
        g_storage[i] = NULL;
    }
}

static void test_specs_and_round_trip(void)
{
    size_t count = 0;
    size_t i;
    uint32_t expected_offset = 0;
    const PortableLegacySaveRecordSpec *specs = portable_legacy_save_record_specs(&count);
    PortableLegacySavePayload encoded = {0};
    uint8_t **originals;
    size_t consumed = 0;
    assert(count == PORTABLE_LEGACY_SAVE_RECORD_COUNT);
    originals = (uint8_t **)calloc(count, sizeof(*originals));
    assert(originals != NULL);
    for (i = 0; i < count; ++i) {
        size_t n = (size_t)specs[i].element_size * specs[i].element_count;
        originals[i] = (uint8_t *)malloc(n);
        assert(originals[i] != NULL);
        memcpy(originals[i], g_bindings[i].bytes, n);
        assert(specs[i].index == i);
        assert(specs[i].payload_offset == expected_offset);
        expected_offset += (uint32_t)n;
    }
    assert(expected_offset == PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);
    assert(portable_legacy_save_encode(g_bindings, count, &encoded) == PORTABLE_LEGACY_SAVE_OK);
    assert(encoded.size == PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);

    for (i = 0; i < count; ++i) {
        size_t n = (size_t)specs[i].element_size * specs[i].element_count;
        assert_encoded_record(&specs[i], originals[i],
                              encoded.bytes + specs[i].payload_offset,
                              g_bindings[i].storage_order);
        memset(g_bindings[i].bytes, 0xA5, n);
    }
    assert(portable_legacy_save_decode(encoded.bytes, encoded.size, g_bindings, count,
                                       PORTABLE_LEGACY_SAVE_EXACT_LENGTH, &consumed) ==
           PORTABLE_LEGACY_SAVE_OK);
    assert(consumed == PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);
    for (i = 0; i < count; ++i) {
        size_t n = (size_t)specs[i].element_size * specs[i].element_count;
        assert(memcmp(g_bindings[i].bytes, originals[i], n) == 0);
        free(originals[i]);
    }
    free(originals);
    portable_legacy_save_payload_free(&encoded);
    assert(encoded.bytes == NULL && encoded.size == 0);
}

static void test_failure_boundaries_are_non_mutating(void)
{
    uint8_t *before = (uint8_t *)malloc(32);
    uint8_t input[PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE + 1u];
    PortableLegacySaveBinding bad[PORTABLE_LEGACY_SAVE_RECORD_COUNT];
    size_t consumed = 99;
    assert(before != NULL);
    memset(input, 0x39, sizeof(input));
    memcpy(before, g_bindings[0].bytes, 32);
    assert(portable_legacy_save_decode(input, sizeof(input) - 2u, g_bindings,
                                       PORTABLE_LEGACY_SAVE_RECORD_COUNT,
                                       PORTABLE_LEGACY_SAVE_ALLOW_TRAILING_BYTES,
                                       &consumed) == PORTABLE_LEGACY_SAVE_INPUT_TOO_SHORT);
    assert(consumed == 0);
    assert(memcmp(before, g_bindings[0].bytes, 32) == 0);
    assert(portable_legacy_save_decode(input, sizeof(input), g_bindings,
                                       PORTABLE_LEGACY_SAVE_RECORD_COUNT,
                                       PORTABLE_LEGACY_SAVE_EXACT_LENGTH,
                                       &consumed) == PORTABLE_LEGACY_SAVE_INPUT_TRAILING_BYTES);
    assert(memcmp(before, g_bindings[0].bytes, 32) == 0);
    assert(portable_legacy_save_decode(input, sizeof(input), g_bindings,
                                       PORTABLE_LEGACY_SAVE_RECORD_COUNT,
                                       PORTABLE_LEGACY_SAVE_ALLOW_TRAILING_BYTES,
                                       &consumed) == PORTABLE_LEGACY_SAVE_OK);
    assert(consumed == PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);
    memcpy(before, g_bindings[0].bytes, 32);
    memcpy(bad, g_bindings, sizeof(bad));
    bad[44].bytes = NULL;
    assert(portable_legacy_save_decode(input, PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE, bad,
                                       PORTABLE_LEGACY_SAVE_RECORD_COUNT,
                                       PORTABLE_LEGACY_SAVE_EXACT_LENGTH,
                                       &consumed) == PORTABLE_LEGACY_SAVE_MISSING_BINDING);
    assert(memcmp(before, g_bindings[0].bytes, 32) == 0);
    memcpy(bad, g_bindings, sizeof(bad));
    bad[99].extent -= 1;
    assert(portable_legacy_save_decode(input, PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE, bad,
                                       PORTABLE_LEGACY_SAVE_RECORD_COUNT,
                                       PORTABLE_LEGACY_SAVE_EXACT_LENGTH,
                                       &consumed) == PORTABLE_LEGACY_SAVE_BINDING_TOO_SMALL);
    assert(memcmp(before, g_bindings[0].bytes, 32) == 0);
    free(before);
}

static void test_encode_binding_errors(void)
{
    PortableLegacySavePayload encoded = {(uint8_t *)1, 1};
    PortableLegacySaveBinding bad[PORTABLE_LEGACY_SAVE_RECORD_COUNT];
    memcpy(bad, g_bindings, sizeof(bad));
    bad[44].bytes = NULL;
    assert(portable_legacy_save_encode(bad, PORTABLE_LEGACY_SAVE_RECORD_COUNT, &encoded) ==
           PORTABLE_LEGACY_SAVE_MISSING_BINDING);
    assert(encoded.bytes == NULL && encoded.size == 0);
    memcpy(bad, g_bindings, sizeof(bad));
    bad[99].extent -= 1;
    assert(portable_legacy_save_encode(bad, PORTABLE_LEGACY_SAVE_RECORD_COUNT, &encoded) ==
           PORTABLE_LEGACY_SAVE_BINDING_TOO_SMALL);
    assert(encoded.bytes == NULL && encoded.size == 0);
}

int main(void)
{
    setup_bindings();
    test_specs_and_round_trip();
    test_failure_boundaries_are_non_mutating();
    test_encode_binding_errors();
    teardown_bindings();
    puts("legacy_save_codec=PASS rows=307 bytes=48386 synthetic_roundtrip=yes");
    return 0;
}
