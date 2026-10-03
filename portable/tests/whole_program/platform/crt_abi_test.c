#include "portable/whole_program/platform/crt_abi.h"

#include <assert.h>
#include <string.h>

static int16_t source_policy(void)
{
    return 3;
}

int main(int argc, char **argv)
{
    static const char *const expected[38] = {
        "Error 0", "", "No such file or directory", "", "", "", "",
        "Arg list too long", "Exec format error", "Bad file number", "", "",
        "Not enough core", "Permission denied", "", "", "", "File exists",
        "Cross-device link", "", "", "", "Invalid argument", "",
        "Too many open files", "", "", "", "No space left on device", "",
        "", "", "", "Math argument", "Result too large", "",
        "Resource deadlock would occur", "Unknown error"
    };
    int value;

    if (argc == 2 && strcmp(argv[1], "unsupported-ctype") == 0)
        return sim_msc_ctype_is_lower_ascii(0x80);
    assert(sim_sys_nerr == 37);
    for (value = 0; value < 38; ++value)
        assert(strcmp(sim_sys_errlist[value], expected[value]) == 0);
    for (value = 0; value < 128; ++value)
        assert(sim_msc_ctype_is_lower_ascii(value) ==
               (value >= 'a' && value <= 'z'));
    assert(sim_crt_harderr_registered() == 0);
    sim_crt_harderr_install(source_policy);
    assert(sim_crt_harderr_registered() == source_policy);
    assert(sim_crt_harderr_retired_result() == 3);
    return 0;
}
