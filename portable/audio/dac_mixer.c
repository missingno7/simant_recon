#include "dac_mixer.h"

#include <stdlib.h>

void portable_dac_free_pcm(uint8_t *pcm)
{
    free(pcm);
}
