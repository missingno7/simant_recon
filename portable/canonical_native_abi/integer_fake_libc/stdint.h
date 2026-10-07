#ifndef SIMANT_PARSE_STDINT
#define SIMANT_PARSE_STDINT
typedef signed char int8_t;
typedef unsigned char uint8_t;
typedef signed short int16_t;
typedef unsigned short uint16_t;
typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef signed long long int64_t;
typedef unsigned long long uint64_t;
typedef unsigned long long uintptr_t;
typedef signed long long intptr_t;
#define INT16_MIN (-32767-1)
#define INT16_MAX 32767
#define UINT16_MAX 65535
#define INT32_MAX 2147483647
#define UINT32_MAX 4294967295U
#define UINT64_C(x) x##ULL
#define INT64_C(x) x##LL
#define UINT16_C(x) x
#define INT16_C(x) x
#define UINT32_C(x) x##U
#define INT32_C(x) x
#endif
