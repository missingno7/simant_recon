#include "../../whole_program/algorithms/asm_utilities.h"

#include <stdint.h>
#include <string.h>

int main(int argc, char **argv)
{
    uint8_t bytes[4];
    memset(bytes, 0x5a, sizeof(bytes));
    if (argc != 2)
        return 2;
    if (strcmp(argv[1], "search-zero") == 0)
        (void)f_24FA_0004(bytes, 0x5a, 0);
    else if (strcmp(argv[1], "search-null") == 0)
        (void)f_24FA_0004(0, 0x5a, 1);
    else if (strcmp(argv[1], "expand-zero-width") == 0)
        f_24FA_0029(bytes, bytes, 0, 1);
    else if (strcmp(argv[1], "expand-zero-height") == 0)
        f_24FA_0029(bytes, bytes, 1, 0);
    else if (strcmp(argv[1], "clear-zero") == 0)
        f_2650_0107(bytes, 0);
    else if (strcmp(argv[1], "clear-null") == 0)
        f_2650_0107(0, 1);
    else
        return 2;
    return 0;
}
