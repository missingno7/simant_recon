#include "../../whole_program/algorithms/asm_utilities.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int test_swaps(void)
{
    uint32_t i;
    for (i = 0; i <= 0xffffu; ++i) {
        uint16_t v = (uint16_t)i;
        uint16_t want = (uint16_t)((i << 8) | (i >> 8));
        if (simant_dos_swap_word(v) != want)
            return 0;
    }
    if (simant_dos_swap_dword(0x01234567u) != 0x67452301u ||
        simant_dos_swap_dword(0x8001fe7fu) != 0x7ffe0180u ||
        simant_dos_swap_dword(0) != 0 ||
        simant_dos_swap_dword(UINT32_MAX) != UINT32_MAX ||
        f_1959_0002(0x1234u) != 0x3412u ||
        f_1959_000C(0x01234567u) != 0x67452301u)
        return 0;
    return 1;
}

static int test_reverse_search(void)
{
    static const uint8_t data[] = {0x10, 0x20, 0x30, 0x20, 0x40};
    if (simant_dos_reverse_find_byte(data + 4, 0x20, 5) != data + 3 ||
        f_24FA_0004((uint8_t *)data + 4, 0x20, 5) != data + 3)
        return 0;
    if (simant_dos_reverse_find_byte(data + 2, 0x20, 3) != data + 1)
        return 0;
    if (simant_dos_reverse_find_byte(data + 4, 0x99, 5) != 0)
        return 0;
    if (simant_dos_reverse_find_byte(data, 0x10, 1) != data)
        return 0;
    return 1;
}

static int test_mutation(void)
{
    uint8_t buf[65538];
    uint32_t i;
    for (i = 0; i < sizeof(buf); ++i)
        buf[i] = (uint8_t)(i * 37u + 11u);
    simant_dos_invert_bytes(buf + 1, 0);
    if (buf[0] != 11u || buf[1] != (uint8_t)~48u || buf[65536] != (uint8_t)~(uint8_t)(65536u * 37u + 11u) ||
        buf[65537] != (uint8_t)(65537u * 37u + 11u))
        return 0;
    simant_dos_invert_bytes(buf + 1, 3);
    if (buf[1] != 48u || buf[2] != 85u || buf[3] != 122u)
        return 0;
    simant_dos_clear_bytes(buf + 10, 5);
    for (i = 10; i < 15; ++i)
        if (buf[i] != 0)
            return 0;
    if (buf[9] == 0 || buf[15] == 0)
        return 0;
    f_24FA_00A0(buf + 20, 2);
    if (buf[20] != (uint8_t)(20u * 37u + 11u) ||
        buf[21] != (uint8_t)(21u * 37u + 11u))
        return 0;
    f_2650_0107(buf + 30, 2);
    if (buf[29] == 0 || buf[30] != 0 || buf[31] != 0 || buf[32] == 0)
        return 0;
    return 1;
}

static int test_packed_expansion(void)
{
    uint8_t src[8] = {0xe4u, 0x1bu, 0x39u, 0xc6u, 0x00u, 0xffu, 0x5au, 0xa5u};
    uint8_t guarded[14];
    static const uint8_t row0[] = {0x00u, 0x0fu, 0xf0u, 0xffu, 0xffu};
    static const uint8_t row1[] = {0xffu, 0x00u, 0x0fu, 0xf0u, 0x00u};
    memset(guarded, 0x5a, sizeof(guarded));
    f_24FA_0029(guarded + 2, src, 9, 2);
    if (guarded[0] != 0x5a || guarded[1] != 0x5a ||
        memcmp(guarded + 2, row0, sizeof(row0)) != 0 ||
        memcmp(guarded + 7, row1, sizeof(row1)) != 0 ||
        guarded[12] != 0x5a || guarded[13] != 0x5a)
        return 0;
    return 1;
}

int main(void)
{
    if (!test_swaps()) {
        fputs("swap controls failed\n", stderr);
        return 1;
    }
    if (!test_reverse_search()) {
        fputs("reverse-search controls failed\n", stderr);
        return 1;
    }
    if (!test_mutation()) {
        fputs("byte mutation controls failed\n", stderr);
        return 1;
    }
    if (!test_packed_expansion()) {
        fputs("packed expansion controls failed\n", stderr);
        return 1;
    }
    puts("PASS asm utility controls: 65536 word inputs; scalar dword controls; search, expansion, inversion and clear boundaries");
    return 0;
}
