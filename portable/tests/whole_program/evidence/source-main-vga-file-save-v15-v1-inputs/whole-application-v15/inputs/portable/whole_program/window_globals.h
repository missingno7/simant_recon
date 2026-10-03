#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_GLOBALS_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_GLOBALS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    SIM_WINDOW_GLOBALS_TABLE_SLOTS = 45,
    SIM_WINDOW_GLOBALS_PURGE_LIST_BYTES = 40,
    SIM_WINDOW_GLOBALS_COLOR_ENTRY_BYTES = 6,
    SIM_WINDOW_GLOBALS_OFFSET_COPY_BYTES = 0x140
};

typedef struct SimWindowGlobalRect {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
} SimWindowGlobalRect;

typedef void (*SimWindowDrawHook)(int16_t phase);

/* Native ownership for the independent 50F6 globals consumed by the window
 * TUs. Fixed source arrays have typed host representations; colors are sized
 * from resource 0x80 and are not adjacent to the other owner fields. */
typedef struct SimWindowGlobals {
    int8_t hardware_profile; /* source g_5A97, configured by IBMInitStuff */
    int16_t num_windows;      /* source resource 0x80 word 0 */
    int16_t num_colors;       /* source resource 0x80 word 1 */
    int16_t num_groups;       /* source resource 0x80 word 2 */
    uint8_t (*colors)[SIM_WINDOW_GLOBALS_COLOR_ENTRY_BYTES];
    size_t colors_size;
    SimWindowDrawHook draw_hooks[SIM_WINDOW_GLOBALS_TABLE_SLOTS];
    SimWindowGlobalRect offsets[SIM_WINDOW_GLOBALS_TABLE_SLOTS];
    uint8_t initialized;
} SimWindowGlobals;

typedef enum SimWindowGlobalsStatus {
    SIM_WINDOW_GLOBALS_OK = 0,
    SIM_WINDOW_GLOBALS_BAD_ARGUMENT,
    SIM_WINDOW_GLOBALS_RESOURCE_TRUNCATED,
    SIM_WINDOW_GLOBALS_INVALID_COUNT,
    SIM_WINDOW_GLOBALS_OUT_OF_MEMORY
} SimWindowGlobalsStatus;

void sim_window_globals_init_empty(SimWindowGlobals *globals,
                                   int8_t hardware_profile);
void sim_window_globals_destroy(SimWindowGlobals *globals);

/* Source-ordered data portion of win_LoadAllWindows:
 *   1. clear 45 draw hooks;
 *   2. sentinel-fill 45 offsets and optionally copy 0x140 bytes (40 Rects);
 *   3. read three little-endian resource-0x80 words;
 *   4. copy num_colors*6 bytes from resource 0x81.
 * Missing optional kind-9 offset data leaves all 45 sentinels. The caller
 * passes exact payload spans returned by its resource owner. */
SimWindowGlobalsStatus sim_window_globals_load(
    SimWindowGlobals *globals,
    const uint8_t *resource_80, size_t resource_80_size,
    const uint8_t *resource_81, size_t resource_81_size,
    const uint8_t *profile_kind9_offsets, size_t profile_kind9_size);

const uint8_t *sim_window_globals_color(const SimWindowGlobals *globals,
                                        int16_t color_index);
const char *sim_window_globals_status_string(SimWindowGlobalsStatus status);

#ifdef __cplusplus
}
#endif

#endif
