#ifndef SIMANT_WHOLE_PROGRAM_DOS_FORMAT_H
#define SIMANT_WHOLE_PROGRAM_DOS_FORMAT_H

#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

/*
 * Native formatting boundary for mechanically converted DOS source.
 * Unqualified d/i/u/o/x/X operands are consumed as DOS 16-bit words;
 * l-qualified integer operands are consumed as DOS 32-bit values. Pointers
 * use the native host pointer representation and are intended for diagnostics.
 * Unsupported conversions and fields over DOS_FORMAT_FIELD_LIMIT fail with -1.
 */
#define DOS_FORMAT_FIELD_LIMIT 4096

int dos_vsnprintf(char *dst, size_t capacity, const char *format, va_list args);
int16_t dos_vsprintf(char *dst, const char *format, va_list args);
int16_t dos_sprintf(char *dst, const char *format, ...);
int16_t dos_printf(const char *format, ...);

#endif
