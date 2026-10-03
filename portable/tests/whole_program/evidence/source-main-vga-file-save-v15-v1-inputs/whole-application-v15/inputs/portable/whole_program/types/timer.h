#ifndef SIMANT_WHOLE_PROGRAM_TYPES_TIMER_H
#define SIMANT_WHOLE_PROGRAM_TYPES_TIMER_H

#include <stddef.h>
#include <stdint.h>

/* Native whole-program spelling of the root:m1FD2 source type.  The target
 * DOS build used 16-bit far pointers; this native type deliberately uses a
 * real host callback pointer.  Queue aliases below address named members and
 * never depend on the old 18-byte DOS record offsets. */
#pragma pack(push, 2)
#ifndef SIMANT_SOURCE_RECT_DEFINED
#define SIMANT_SOURCE_RECT_DEFINED 1
struct Rect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
};
#endif

struct Timer {
    struct Rect r;
    void (*fn)(void);
    int16_t ticks;
    char a;
    char b;
    char c;
    char d;
};
#pragma pack(pop)

_Static_assert(sizeof(struct Rect) == 8, "native whole-program Rect");
_Static_assert(offsetof(struct Timer, r.left) == 0,
               "Timer queue count aliases Rect.left");
_Static_assert(offsetof(struct Timer, r.top) == 2,
               "Timer queue write index aliases Rect.top");
_Static_assert(offsetof(struct Timer, r.right) == 4,
               "Timer queue read index aliases Rect.right");
_Static_assert(offsetof(struct Timer, fn) == 8,
               "native callback pointer follows Rect");
_Static_assert(offsetof(struct Timer, ticks) == 16,
               "native ticks follow widened callback pointer");
_Static_assert(offsetof(struct Timer, a) == 18 && sizeof(struct Timer) == 22,
               "native Timer keeps trailing source bytes after ticks");

#endif
