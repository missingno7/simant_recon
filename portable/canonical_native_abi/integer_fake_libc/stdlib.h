#ifndef SIMANT_PARSE_STDLIB
#define SIMANT_PARSE_STDLIB
#include <stddef.h>
void *malloc(size_t);
void free(void *);
void *realloc(void *, size_t);
int abs(int);
long labs(long);
int atoi(const char *);
void exit(int);
void abort(void);
int atexit(void (*)(void));
#endif
