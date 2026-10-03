#include "portable/whole_program/state/startup_globals_v1.h"
#include "portable/whole_program/platform/handles.h"

#include <stdint.h>

int main(void)
{
    static char *payload;
    static char **handle = &payload;
    SimHandle canonical;

    _Static_assert(sizeof(SimYardCacheHandle) == sizeof(void *),
                   "yard cache handles must retain the native pointer width");
    canonical = handle;
    fd_55B3_2A36 = handle;
    fd_55B3_2A3A = canonical;
    if (fd_55B3_2A36 != canonical || fd_55B3_2A3A != handle)
        return 1;
    if (fd_55B3_2A42[0] != 0xa9 || fd_55B3_2A42[1] != 0x43 ||
        fd_55B3_2A42[2] != 0xc1 || fd_55B3_2A42[3] != 0x43 ||
        fd_55B3_2A42[4] != 0xba || fd_55B3_2A42[5] != 0x4a ||
        fd_55B3_2A42[6] != 0xa2 || fd_55B3_2A42[7] != 0x4a)
        return 2;
    return 0;
}
