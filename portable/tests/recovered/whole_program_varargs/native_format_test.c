#include "dos_format.h"

#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int expect(const char *name, const char *actual, const char *wanted)
{
    if (strcmp(actual, wanted) == 0) return 0;
    fprintf(stderr, "%s: wanted <%s>, got <%s>\n", name, wanted, actual);
    return 1;
}

int bounded_format(char *out, size_t cap, const char *fmt, ...);

static int replay_format(char *out, const char *fmt, ...)
{
    char scratch[64];
    va_list args;
    va_list copy;
    int first;
    int second;
    va_start(args, fmt);
    va_copy(copy, args);
    first = dos_vsprintf(scratch, fmt, copy);
    va_end(copy);
    va_copy(copy, args);
    second = dos_vsprintf(out, fmt, copy);
    va_end(copy);
    va_end(args);
    return first == second ? second : -1;
}

int main(void)
{
    char buf[256];
    int failures = 0;
    int n;

    n = dos_sprintf(buf, "%d %u %x %ld %-5s %.3s %c %%",
                    (int16_t)-32768, (uint16_t)65535, (uint16_t)0xbeef,
                    (int32_t)-2147483647, "ant", "queen", (int16_t)'Q');
    if (n != 43) { fprintf(stderr, "mixed result length: %d\n", n); ++failures; }
    failures += expect("mixed DOS widths", buf,
                       "-32768 65535 beef -2147483647 ant   que Q %");

    n = dos_sprintf(buf, "%*.*d", (int16_t)-6, (int16_t)3, (int16_t)12);
    if (n != 6) { fprintf(stderr, "dynamic width result length: %d\n", n); ++failures; }
    failures += expect("DOS dynamic width/precision", buf, "012   ");

    n = dos_sprintf(buf, "%ld %lx", (int32_t)INT32_MIN, (uint32_t)UINT32_C(0xdeadbeef));
    failures += expect("DOS signed/unsigned long", buf, "-2147483648 deadbeef");
    if (n != (int)strlen(buf)) { fprintf(stderr, "long result length mismatch\n"); ++failures; }

    n = dos_sprintf(buf, "%d %u %x", 0x12345, 0x12345, 0x12345);
    failures += expect("DOS word truncation", buf, "9029 9029 2345");
    if (n != (int)strlen(buf)) { fprintf(stderr, "word result length mismatch\n"); ++failures; }

    n = replay_format(buf, "%u/%ld", (int16_t)65535, (int32_t)-1234567);
    if (n != 14) { fprintf(stderr, "replay result length: %d\n", n); ++failures; }
    failures += expect("va_copy argument replay", buf, "65535/-1234567");
    n = replay_format(buf, "%s", "direct va_list string");
    if (n != (int)strlen("direct va_list string")) { fprintf(stderr, "string replay length: %d\n", n); ++failures; }
    failures += expect("va_list string", buf, "direct va_list string");

    /* The bounded proof is exercised through a correctly constructed list. */
    n = bounded_format(buf, 5, "%u", (int16_t)65535);
    if (n != 5) { fprintf(stderr, "bounded return: %d\n", n); ++failures; }
    failures += expect("bounded truncation", buf, "6553");

    if (dos_sprintf(buf, "%f", 1.0) != -1 || buf[0] != '\0') {
        fprintf(stderr, "unsupported float was not rejected cleanly\n"); ++failures;
    }
    if (dos_sprintf(buf, "%n", (int *)buf) != -1 || buf[0] != '\0') {
        fprintf(stderr, "unsupported %%n was not rejected cleanly\n"); ++failures;
    }
    if (dos_sprintf(buf, "%q", 1) != -1 || buf[0] != '\0') {
        fprintf(stderr, "unknown conversion was not rejected cleanly\n"); ++failures;
    }
    if (dos_sprintf(buf, "%4097d", 1) != -1 || buf[0] != '\0') {
        fprintf(stderr, "oversized field was not rejected cleanly\n"); ++failures;
    }
    if (dos_sprintf(buf, "%p", (void *)buf) <= 0 || buf[0] == '\0') {
        fprintf(stderr, "native diagnostic pointer output missing\n"); ++failures;
    }
    if (dos_printf("") != 0) { fprintf(stderr, "empty printf return mismatch\n"); ++failures; }
    if (failures != 0) return 1;
    puts("native DOS-format boundary controls passed");
    return 0;
}

int bounded_format(char *out, size_t cap, const char *fmt, ...)
{
    va_list args;
    int result;
    va_start(args, fmt);
    result = dos_vsnprintf(out, cap, fmt, args);
    va_end(args);
    return result;
}
