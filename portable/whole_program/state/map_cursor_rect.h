#ifndef SIMANT_WHOLE_PROGRAM_MAP_CURSOR_RECT_H
#define SIMANT_WHOLE_PROGRAM_MAP_CURSOR_RECT_H

/* Include after the source TU's complete struct Rect declaration. */
struct Rect;
struct Rect *sim_source_map_cursor_rect(void);

#define fd_50F6_38C2 (*sim_source_map_cursor_rect())

#endif
