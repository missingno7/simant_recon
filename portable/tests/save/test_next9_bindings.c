#include "game/save/next9_bindings.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t k_table_initial[20] = {
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static int fail(const char *message)
{
    fprintf(stderr, "FAIL: %s\n", message);
    return 1;
}

int main(int argc, char **argv)
{
    RecoveredState original, restored;
    PortableLegacySavePayload payload = {0};
    const PortableLegacySaveRecordSpec *specs;
    size_t count = 0, consumed = 0;

    recovered_state_init(&original);
    if (memcmp(original.fd_3D57_087A + 20, k_table_initial, sizeof k_table_initial) != 0)
        return fail("source table initializer differs from its pinned 20-byte save interior");

    /* Negative control: the source-initializer assertion must detect a changed byte. */
    original.fd_3D57_087A[20] ^= 1u;
    if (memcmp(original.fd_3D57_087A + 20, k_table_initial, sizeof k_table_initial) == 0)
        return fail("initializer negative control failed to detect a mutation");
    original.fd_3D57_087A[20] ^= 1u;

    memset(original.fd_50F6_0F46, 0x81, sizeof original.fd_50F6_0F46);
    memset(original.fd_50F6_0FC6, 0x92, sizeof original.fd_50F6_0FC6);
    memset(original.fd_50F6_0F84, 0xA3, sizeof original.fd_50F6_0F84);
    memset(original.fd_50F6_1008, 0xB4, sizeof original.fd_50F6_1008);
    original.fd_50F6_103C = (int16_t)0x8123;
    original.fd_50F6_1048 = (int16_t)0x4567;
    original.fd_3E1D_0000[0][0] = (int16_t)0xBEEF;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
    /* Represent the same native numeric values as a big-endian host would. */
    ((uint8_t *)(void *)&original.fd_50F6_103C)[0] = 0x81;
    ((uint8_t *)(void *)&original.fd_50F6_103C)[1] = 0x23;
    ((uint8_t *)(void *)&original.fd_50F6_1048)[0] = 0x45;
    ((uint8_t *)(void *)&original.fd_50F6_1048)[1] = 0x67;
    ((uint8_t *)(void *)original.fd_3E1D_0000)[0] = 0xBE;
    ((uint8_t *)(void *)original.fd_3E1D_0000)[1] = 0xEF;
#endif
    original.fd_3D57_087A[20] = 0x5A;
    original.fd_3D57_087A[39] = 0xC3;

    if (portable_next9_save_encode(&original, &payload) != PORTABLE_LEGACY_SAVE_OK)
        return fail("encode all 307 Next9 bindings");
    if (payload.size != PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE)
        return fail("encoded stream has the wrong extent");
    specs = portable_legacy_save_record_specs(&count);
    if (count != 307) return fail("record schema count changed");
    if (memcmp(payload.bytes + specs[61].payload_offset, original.fd_50F6_0F46, 50) != 0 ||
        memcmp(payload.bytes + specs[62].payload_offset, original.fd_50F6_0FC6, 50) != 0 ||
        memcmp(payload.bytes + specs[63].payload_offset, original.fd_50F6_0F84, 50) != 0 ||
        memcmp(payload.bytes + specs[64].payload_offset, original.fd_50F6_1008, 50) != 0)
        return fail("the four complete 50-byte DrawSwarm arrays were not serialized");
    if (memcmp(payload.bytes + specs[99].payload_offset,
               original.fd_3D57_087A + 20, 20) != 0)
        return fail("row 99 did not serialize exactly the source object's [20,40) slice");
    if (payload.bytes[specs[29].payload_offset] != 0xEF ||
        payload.bytes[specs[29].payload_offset + 1] != 0xBE)
        return fail("row 29 did not serialize its typed numeric16 backing as DOS little endian");

    recovered_state_init(&restored);
    if (portable_next9_save_decode(&restored, payload.bytes, payload.size,
                                   PORTABLE_LEGACY_SAVE_EXACT_LENGTH,
                                   &consumed) != PORTABLE_LEGACY_SAVE_OK)
        return fail("decode all 307 Next9 bindings");
    if (consumed != PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE ||
        memcmp(&original.fd_50F6_0F46, &restored.fd_50F6_0F46, 200) != 0 ||
        original.fd_50F6_103C != restored.fd_50F6_103C ||
        original.fd_50F6_1048 != restored.fd_50F6_1048 ||
        memcmp(original.fd_3D57_087A, restored.fd_3D57_087A, 72) != 0 ||
        memcmp(original.fd_3E1D_0000, restored.fd_3E1D_0000, 384) != 0)
        return fail("round-trip did not preserve all seven additive state fields");
    portable_legacy_save_payload_free(&payload);
    if (argc == 2) {
        FILE *input = fopen(argv[1], "rb");
        uint8_t *bytes = (uint8_t *)malloc(PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE);
        size_t got;
        RecoveredState dos_state;
        PortableLegacySavePayload replay = {0};
        if (input == NULL || bytes == NULL) return fail("could not read captured DOS payload");
        got = fread(bytes, 1, PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE, input);
        if (fgetc(input) != EOF || fclose(input) != 0 || got != PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE)
            return fail("captured DOS payload does not have the exact stream extent");
        recovered_state_init(&dos_state);
        if (portable_next9_save_decode(&dos_state, bytes, got,
                                       PORTABLE_LEGACY_SAVE_EXACT_LENGTH,
                                       &consumed) != PORTABLE_LEGACY_SAVE_OK ||
            portable_next9_save_encode(&dos_state, &replay) != PORTABLE_LEGACY_SAVE_OK ||
            replay.size != got || memcmp(replay.bytes, bytes, got) != 0)
            return fail("native 307-row adapter did not reproduce actual DOS write stream");
        portable_legacy_save_payload_free(&replay);
        free(bytes);
        puts("legacy_save_next9_dos_stream=PASS actual_DOS_rows=307 bytes=48386 byte_exact=yes");
    } else if (argc != 1) {
        return fail("usage: test_next9_bindings [captured-DOS-payload]");
    }
    puts("legacy_save_next9_bindings=PASS rows=307 bytes=48386 additive_fields=7 initializer_positive=PASS negative=PASS storage_controls=row29_numeric16_row99_raw=PASS");
    return 0;
}
