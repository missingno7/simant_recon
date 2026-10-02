#include "game/save/next9_bindings_v3.h"
#include "next9_source_sentinels_v3.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    RecoveredState state;
    PortableLegacySavePayload payload = {0};
    FILE *file;
    uint8_t *expected;
    size_t size, got;
    long file_size;
    if (argc != 2) return 90;
    file = fopen(argv[1], "rb");
    if (file == NULL) return 91;
    if (fseek(file, 0, SEEK_END) != 0 || (file_size = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0) return 92;
    size = (size_t)file_size;
    if (size != PORTABLE_LEGACY_SAVE_PAYLOAD_SIZE) return 93;
    expected = (uint8_t *)malloc(size);
    if (expected == NULL) return 94;
    got = fread(expected, 1, size, file);
    if (fclose(file) != 0 || got != size) return 95;
    recovered_state_init(&state);
    portable_next9_fill_source_address_sentinels(&state);
    if (portable_next9_save_encode_v3(&state, &payload) != PORTABLE_LEGACY_SAVE_OK) return 96;
    if (payload.size != size || memcmp(payload.bytes, expected, size) != 0) {
        portable_legacy_save_payload_free(&payload);
        free(expected);
        fputs("source-address sentinel stream mismatch\n", stderr);
        return 1;
    }
    portable_legacy_save_payload_free(&payload);
    free(expected);
    puts("next9_v3_independent_source_sentinels=PASS rows=307 bytes=48386");
    return 0;
}
