#include "dos_memory.h"
#include "../../platform/memory.h"
#include <string.h>

void *_fmemcpy(void *dst, const void *src, uint16_t n)
{
    return portable_fmemcpy(dst, src, n);
}

void *_fmemmove(void *dst, const void *src, uint16_t n)
{
    return portable_fmemmove(dst, src, n);
}

void *_fmemset(void *dst, int16_t value, uint16_t n)
{
    if (!n) return dst;
    return memset(dst, (uint8_t)value, n);
}

int16_t _fmemcmp(const void *a, const void *b, uint16_t n)
{
    const uint8_t *x = a, *y = b;
    while (n--) {
        int16_t difference = (int16_t)*x++ - (int16_t)*y++;
        if (difference) return difference;
    }
    return 0;
}

void *_fmemchr(const void *src, int16_t value, uint16_t n)
{
    if (!n) return NULL;
    return memchr(src, (uint8_t)value, n);
}

uint16_t _fstrlen(const char *s)
{
    return (uint16_t)strlen(s);
}

char *_fstrcpy(char *dst, const char *src)
{
    return strcpy(dst, src);
}

char *_fstrncpy(char *dst, const char *src, uint16_t n)
{
    return strncpy(dst, src, n);
}

char *_fstrcat(char *dst, const char *src)
{
    return strcat(dst, src);
}

int16_t _fstrcmp(const char *a, const char *b)
{
    for (;;) {
        uint8_t x = (uint8_t)*a++, y = (uint8_t)*b++;
        if (x != y) return (int16_t)x - (int16_t)y;
        if (!x) return 0;
    }
}

int16_t _fstrncmp(const char *a, const char *b, uint16_t n)
{
    while (n--) {
        uint8_t x = (uint8_t)*a++, y = (uint8_t)*b++;
        if (x != y) return (int16_t)x - (int16_t)y;
        if (!x) return 0;
    }
    return 0;
}

char *_fstrchr(const char *s, int16_t value)
{
    return strchr(s, (uint8_t)value);
}

char *_fstrrchr(const char *s, int16_t value)
{
    return strrchr(s, (uint8_t)value);
}
