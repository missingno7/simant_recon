#ifndef SIMANT_PARSE_STDDEF
#define SIMANT_PARSE_STDDEF
typedef unsigned long long size_t;
typedef signed long long ptrdiff_t;
#define NULL ((void *)0)
#define offsetof(type, member) __simant_parse_only_offsetof(#type, #member)
#endif
