#include "graphics_s00_unowned_source.h"

#include <stdio.h>
#include <stdlib.h>

void gfx_planar_buffer_noop(void)
{
    /* S00:m35A6.asm is a literal RETF with no state effects. */
}

static _Noreturn void reject_unsupported_cga_entry(void)
{
    (void)fprintf(stderr,
                  "unsupported native video profile entry: gfx_planar_init_320x200\n");
    (void)fflush(stderr);
    _Exit(70);
}

void gfx_planar_init_320x200(void)
{
    reject_unsupported_cga_entry();
}
