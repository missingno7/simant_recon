#include <stdint.h>
typedef struct {
    const uint8_t *data;
    int16_t id;
    uint8_t kind;
    uint8_t flags;
} LegacyPointerEntry;
_Static_assert(sizeof(LegacyPointerEntry) == 8,
               "host pointer entry must not masquerade as DOS 8-byte wire entry");
