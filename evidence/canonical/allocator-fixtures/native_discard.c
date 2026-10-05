/* Bounded contrast for the current whole native handle provider. */
#include "portable/whole_program/platform/handles.h"
#include <stdio.h>

int main(void)
{
    char **first, **second, **resized;
    int status;
    if (sim_handles_global_configure(4096, 64) != SIM_HANDLE_OK)
        return 1;
    first = f_171C_13CA(160, 3, "first-soft");
    second = f_171C_13CA(32, 3, "second-soft");
    if (!first || !second)
        return 2;
    f_171C_1804(first);
    f_171C_1804(second);
    printf("discarded,%d,%d,%ld,%ld\n", f_171C_1686(first),
           f_171C_1686(second), (long)f_171C_1C1C(first), (long)f_171C_1C1C(second));
    resized = f_171C_18A6(first, 100, 1);
    status = (int)sim_handles_global_last_status();
    printf("resize,%d,%d,%d,%d\n", resized == first, resized == NULL,
           status, f_171C_1686(second));
    return 0;
}
