#include "wildcard.h"
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

static uint8_t fold(uint8_t byte)
{
    return byte >= 'a' && byte <= 'z' ? (uint8_t)(byte ^ 0x20u) : byte;
}

/* Direct control-flow translation of root:m1F66 L0031..L00AA. A star changes
 * the source matching/search mode; this deliberately retains the source's
 * greedy first-match behavior rather than substituting a host glob routine. */
static int16_t match(char *pattern, char *name, int searching)
{
    const uint8_t *p = (const uint8_t *)pattern;
    const uint8_t *n = (const uint8_t *)name;
    size_t index;
    uint8_t a, b;
    if (!p || !n) abort();
restart:
    index = 0;
next:
    a = p[index];
    if (a == 0) {
        if (n[index] != 0 && !searching) return 0;
        return 1;
    }
    if (a == '*') {
        searching = 1;
        p += index + 1;
        n += index;
        goto restart;
    }
    a = fold(a);
compare:
    b = n[index];
    if (b == 0) return 0;
    if (a == '?' || fold(b) == a) {
        ++index;
        goto next;
    }
    if (!searching) return 0;
    ++n;
    if (index == 0) goto compare;
    goto restart;
}

int16_t f_1F66_002D(char *pattern, char *name) { return match(pattern, name, 0); }
int16_t f_1F66_0029(char *pattern, char *name) { return match(pattern, name, 1); }
