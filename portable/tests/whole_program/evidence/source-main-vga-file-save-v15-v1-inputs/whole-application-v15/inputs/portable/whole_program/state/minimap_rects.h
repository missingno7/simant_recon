#ifndef SIMANT_WHOLE_PROGRAM_MINIMAP_RECTS_H
#define SIMANT_WHOLE_PROGRAM_MINIMAP_RECTS_H

/* Include after the source TU's complete struct Rect declaration. */
struct Rect;
struct Rect *sim_source_minimap_rect(unsigned int index);

#define fd_50F6_3842 (*sim_source_minimap_rect(0u))
#define fd_50F6_384A (*sim_source_minimap_rect(1u))

#endif
