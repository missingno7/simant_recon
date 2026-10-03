#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Event {
    int16_t what, message, x4, x6, h, v, code, xE;
};

enum { EV_PRINT = 1, EV_YARD_TO_MAP, EV_ENQUEUE, EV_YELLOW_COMMAND,
       EV_YELLOW_KEY, EV_TAB };
typedef struct TraceEvent {
    int16_t kind;
    int16_t count;
    int16_t arg[5];
} TraceEvent;

extern void o19_384C_0383(struct Event *ev);
static TraceEvent s_trace[4];
static int s_count;

static void append_event(int kind, int count, const int16_t *args)
{
    int i;
    TraceEvent *e;
    if (s_count >= (int)(sizeof(s_trace) / sizeof(s_trace[0]))) return;
    e = &s_trace[s_count++];
    e->kind = (int16_t)kind;
    e->count = (int16_t)count;
    for (i = 0; i < count && i < 5; ++i) e->arg[i] = args[i];
}

int16_t WinPrintf(char *format, ...)
{
    va_list ap;
    int code, message;
    int16_t args[2];
    if (format == NULL || strcmp(format, "\nKEYEVENT=%x, %x") != 0) abort();
    va_start(ap, format);
    code = va_arg(ap, int);
    message = va_arg(ap, int);
    va_end(ap);
    args[0] = (int16_t)code;
    args[1] = (int16_t)message;
    append_event(EV_PRINT, 2, args);
    return 0;
}

void YardToMap(void) { append_event(EV_YARD_TO_MAP, 0, NULL); }
void YellowCommand(int16_t cmd) { append_event(EV_YELLOW_COMMAND, 1, &cmd); }
void YellowCommandKey(int16_t key) { append_event(EV_YELLOW_KEY, 1, &key); }
void DoTab(void) { append_event(EV_TAB, 0, NULL); }

void f_1B73_030F(int16_t a, int16_t b, int16_t c, int16_t d, int16_t e)
{
    int16_t args[5] = { a, b, c, d, e };
    append_event(EV_ENQUEUE, 5, args);
}

static int expected_extra(uint16_t code, uint16_t message, TraceEvent *out)
{
    int16_t arg;
    memset(out, 0, sizeof(*out));
    if ((message & 4u) != 0) {
        switch (code) {
        case 0xfa05: out->kind = EV_YARD_TO_MAP; return 1;
        case 0xfa06: arg = (int16_t)0xfd22; break;
        case 0xfa07: arg = (int16_t)0xfd23; break;
        case 0xfa08: arg = (int16_t)0xfd24; break;
        case 0xfa09: arg = (int16_t)0xfd26; break;
        case 0xfa0a: arg = (int16_t)0xfd27; break;
        case 0xfa0b: arg = (int16_t)0xfd28; break;
        case 0xfa17: arg = (int16_t)0xfd16; break;
        case 0xfa23: arg = (int16_t)0xfd15; break;
        default: return 0;
        }
        out->kind = EV_ENQUEUE;
        out->count = 5;
        out->arg[0] = arg;
        return 1;
    }
    if ((message & 8u) != 0) {
        if (code != 0xfa03) return 0;
        out->kind = EV_YELLOW_COMMAND;
        out->count = 1;
        out->arg[0] = 3;
        return 1;
    }
    if (code == 0xfa0e) {
        out->kind = EV_YELLOW_KEY;
        out->count = 1;
        out->arg[0] = 0x88;
        return 1;
    }
    if (code == 0xfa0f) {
        out->kind = EV_TAB;
        return 1;
    }
    return 0;
}

static int test_exhaustive(void)
{
    static const uint16_t messages[] = { 0, 4, 8 };
    uint32_t code;
    unsigned f;
    uint64_t cases = 0;
    uint64_t routed = 0;
    for (f = 0; f < sizeof(messages) / sizeof(messages[0]); ++f) {
        for (code = 0; code <= 0xffffu; ++code) {
            struct Event ev = { 0, (int16_t)messages[f], 0x1234, 0, 11, 22,
                                (int16_t)code, (int16_t)0xabcd };
            TraceEvent expected;
            int has_extra = expected_extra((uint16_t)code, messages[f], &expected);
            s_count = 0;
            memset(s_trace, 0, sizeof(s_trace));
            o19_384C_0383(&ev);
            if (s_count != 1 + has_extra || s_trace[0].kind != EV_PRINT ||
                s_trace[0].count != 2 || (uint16_t)s_trace[0].arg[0] != code ||
                (uint16_t)s_trace[0].arg[1] != messages[f]) {
                fprintf(stderr, "bad print/trace count: code=%04x message=%04x count=%d\n",
                        (unsigned)code, (unsigned)messages[f], s_count);
                return 1;
            }
            if (has_extra) {
                int i;
                TraceEvent *got = &s_trace[1];
                if (got->kind != expected.kind || got->count != expected.count) {
                    fprintf(stderr, "bad callback: code=%04x message=%04x kind=%d/%d count=%d/%d\n",
                            (unsigned)code, (unsigned)messages[f], got->kind,
                            expected.kind, got->count, expected.count);
                    return 1;
                }
                for (i = 0; i < expected.count; ++i) {
                    if (got->arg[i] != expected.arg[i]) {
                        fprintf(stderr, "bad callback arg: code=%04x message=%04x arg%d=%04x expected=%04x\n",
                                (unsigned)code, (unsigned)messages[f], i,
                                (unsigned)(uint16_t)got->arg[i],
                                (unsigned)(uint16_t)expected.arg[i]);
                        return 1;
                    }
                }
                ++routed;
            }
            ++cases;
        }
    }
    printf("exhaustive cases=%llu routed=%llu\n",
           (unsigned long long)cases, (unsigned long long)routed);
    return 0;
}

static int test_unadapted_negative(void)
{
    static const struct { uint16_t code, message; } cases[] = {
        { 0xfa05, 4 }, { 0xfa06, 4 }, { 0xfa03, 8 },
        { 0xfa0e, 0 }, { 0xfa0f, 0 }, { 0xffff, 4 }
    };
    unsigned i;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        struct Event ev = { 0, (int16_t)cases[i].message, 0, 0, 0, 0,
                            (int16_t)cases[i].code, 0 };
        s_count = 0;
        o19_384C_0383(&ev);
        if (s_count != 1 || s_trace[0].kind != EV_PRINT) {
            fprintf(stderr, "unadapted signed-switch negative failed for %04x/%04x\n",
                    cases[i].code, cases[i].message);
            return 1;
        }
    }
    puts("unadapted signed event switch misses all six high-key controls");
    return 0;
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--negative") == 0)
        return test_unadapted_negative();
    return test_exhaustive();
}
