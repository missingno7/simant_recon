/* Native scalar ABI only; DOS packed records require explicit conversion. */
#ifndef SIMANT_WHOLE_DOS_TYPES_H
#define SIMANT_WHOLE_DOS_TYPES_H
#include <stdint.h>
#include <stddef.h>
_Static_assert(sizeof(int16_t)==2, "DOS int");
_Static_assert(sizeof(int32_t)==4, "DOS long");
_Static_assert((char)-1<0, "MSC signed char");
#endif
