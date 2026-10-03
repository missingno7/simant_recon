#include "crt_abi.h"

#include <stdio.h>
#include <stdlib.h>

char *sim_sys_errlist[38] = {
    "Error 0", "", "No such file or directory", "", "", "", "",
    "Arg list too long", "Exec format error", "Bad file number", "", "",
    "Not enough core", "Permission denied", "", "", "", "File exists",
    "Cross-device link", "", "", "", "Invalid argument", "",
    "Too many open files", "", "", "", "No space left on device", "",
    "", "", "", "Math argument", "Result too large", "",
    "Resource deadlock would occur", "Unknown error"
};
int16_t sim_sys_nerr = 37;

static SimCrtHardErrorHandler harderr_handler;

void sim_crt_harderr_install(SimCrtHardErrorHandler handler)
{
    harderr_handler = handler;
}

SimCrtHardErrorHandler sim_crt_harderr_registered(void)
{
    return harderr_handler;
}

int16_t sim_crt_harderr_retired_result(void)
{
    /* There is no native DOS INT 24 interrupt. Expose the installed policy
     * only for diagnostics/tests; the host I/O boundary returns mapped errors. */
    if (!harderr_handler) {
        fputs("simant: DOS INT 24 policy requested before _harderr registration\n", stderr);
        fflush(stderr);
        exit(79);
    }
    return harderr_handler();
}

int sim_msc_ctype_is_lower_ascii(int value)
{
    if (value < 0 || value > 0x7f) {
        fputs("simant: non-ASCII byte reached the admitted MSC _ctype adapter\n", stderr);
        fflush(stderr);
        exit(79);
    }
    return value >= 'a' && value <= 'z';
}
