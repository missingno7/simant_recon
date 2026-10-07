#ifndef SIMANT_PARSE_STDIO
#define SIMANT_PARSE_STDIO
#include <stddef.h>
#include <stdarg.h>
typedef struct SIMANT_PARSE_FILE FILE;
int printf(const char *, ...);
int sprintf(char *, const char *, ...);
int snprintf(char *, size_t, const char *, ...);
int puts(const char *);
int putchar(int);
FILE *fopen(const char *, const char *);
int fclose(FILE *);
size_t fread(void *, size_t, size_t, FILE *);
size_t fwrite(const void *, size_t, size_t, FILE *);
extern FILE *stderr;
#endif
