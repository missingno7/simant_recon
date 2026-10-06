#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_SOURCE_GLOBALS_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_SOURCE_GLOBALS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    SIM_WINDOW_SOURCE_SLOT_COUNT = 45
};

/* Source globals consumed by mechanically converted window TUs. */
typedef void (*SimWindowSourceDrawHook)(int16_t phase);

extern char g_5A97;
extern int16_t win_numOfWindows;
extern int16_t win_numOfColors;
extern int16_t win_numOfGroups;
extern SimWindowSourceDrawHook win_drawHooks[SIM_WINDOW_SOURCE_SLOT_COUNT];

/* Host startup configures the profile before the source loader is entered.
 * The source IBMInitStuff path may subsequently replace it as usual. */
void sim_window_source_set_profile(char profile);
void sim_window_source_clear_draw_hooks(SimWindowSourceDrawHook *hooks,
                                        size_t count);

#ifdef __cplusplus
}
#endif

#endif
