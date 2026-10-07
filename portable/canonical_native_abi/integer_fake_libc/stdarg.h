#ifndef SIMANT_PARSE_STDARG
#define SIMANT_PARSE_STDARG
typedef void *va_list;
void va_start(va_list, ...);
void va_copy(va_list, va_list);
void va_end(va_list);
#endif
