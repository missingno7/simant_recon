#include "ega_map_readback.h"

#include "../state/asm_display_data_v1.h"

#include <stdlib.h>
#include <string.h>
extern uint16_t g_3DD4;

static PortableEgaReadPlane active_reader;
static void *active_context;

int portable_ega_map_readback_bind(PortableEgaReadPlane read_plane,
                                   void *context)
{
    if (read_plane == NULL || active_reader != NULL)
        return 0;
    active_reader = read_plane;
    active_context = context;
    return 1;
}

void portable_ega_map_readback_unbind(void)
{
    active_reader = NULL;
    active_context = NULL;
}

void o00_31AD_1A8F(int16_t row, int16_t col)
{
    uint8_t temporary[128];
    uint8_t *busy=(uint8_t *)&g_3DD4;
    /* m31AD:L1A98/L1ABF changes only the low display-lock byte. */
    ++*busy;
    if (active_reader == NULL ||
        !active_reader(active_context, (uint8_t)row, (uint16_t)col,
                       temporary))
        abort();
    memcpy(g_3D20, temporary, sizeof(temporary));
    --*busy;
}
