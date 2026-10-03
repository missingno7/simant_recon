#ifndef SIMANT_WHOLE_PROGRAM_TRI_CONTROL_STATE_H
#define SIMANT_WHOLE_PROGRAM_TRI_CONTROL_STATE_H

/* Include after the source TU's struct Pt and struct TriPoints definitions. */
struct Pt;
struct TriPoints;

struct Pt *sim_source_tri_control_point(unsigned int index);
struct TriPoints *sim_source_tri_control_triangle(unsigned int index);

#define fd_50F6_022E (*sim_source_tri_control_point(0u))
#define fd_50F6_0358 (*sim_source_tri_control_point(1u))
#define knobSize (*sim_source_tri_control_point(2u))
#define fd_50F6_3816 (*sim_source_tri_control_triangle(0u))
#define fd_50F6_3822 (*sim_source_tri_control_triangle(1u))

#endif
