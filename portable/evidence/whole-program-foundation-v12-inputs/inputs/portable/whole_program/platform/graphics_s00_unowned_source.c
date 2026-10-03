#include "graphics_s00_unowned_source.h"

#include <stdio.h>
#include <stdlib.h>

void o00_35A6_0006(void)
{
    /* S00:m35A6.asm is a literal RETF with no state effects. */
}

static _Noreturn void reject_unsupported_cga_entry(void)
{
    (void)fprintf(stderr,
                  "unsupported native video profile entry: o00_31AD_1AE7\n");
    (void)fflush(stderr);
    _Exit(70);
}

void o00_31AD_1AE7(void)
{
    reject_unsupported_cga_entry();
}
