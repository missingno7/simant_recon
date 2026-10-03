#ifndef SIMANT_WHOLE_PROGRAM_MENU_BAR_RECT_H
#define SIMANT_WHOLE_PROGRAM_MENU_BAR_RECT_H

/* Shared native owner for the source global used by menu/window layout.
 * Include after the source TU's complete struct Rect declaration. */
struct Rect;
struct Rect *sim_source_menu_bar_rect(void);

#define fd_50F6_393C (*sim_source_menu_bar_rect())

#endif
