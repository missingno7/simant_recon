/* Source-visible large-model string/memory ABI. Segment qualifiers become
 * ordinary pointers; word counts and byte comparison results stay DOS width.
 * This header does not convert packed pointer-bearing resource records. */
#ifndef SIMANT_DOS_MEMORY_H
#define SIMANT_DOS_MEMORY_H
#include <stdint.h>
#include <stddef.h>

void *_fmemcpy(void *dst, const void *src, uint16_t n);
void *_fmemmove(void *dst, const void *src, uint16_t n);
void *_fmemset(void *dst, int16_t value, uint16_t n);
int16_t _fmemcmp(const void *a, const void *b, uint16_t n);
void *_fmemchr(const void *src, int16_t value, uint16_t n);
uint16_t _fstrlen(const char *s);
char *_fstrcpy(char *dst, const char *src);
char *_fstrncpy(char *dst, const char *src, uint16_t n);
char *_fstrcat(char *dst, const char *src);
int16_t _fstrcmp(const char *a, const char *b);
int16_t _fstrncmp(const char *a, const char *b, uint16_t n);
char *_fstrchr(const char *s, int16_t value);
char *_fstrrchr(const char *s, int16_t value);
#endif
