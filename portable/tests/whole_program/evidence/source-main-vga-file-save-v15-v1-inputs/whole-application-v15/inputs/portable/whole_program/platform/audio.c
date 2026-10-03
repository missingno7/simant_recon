#include "audio.h"

uint8_t *dos_audio_song_span(uint8_t *base, size_t size,
                             uint16_t offset, size_t length)
{
    size_t start = offset;
    if (base == NULL || start > size || length > size - start)
        dos_audio_host_song_bounds_fault(offset, length, size);
    return base + start;
}
