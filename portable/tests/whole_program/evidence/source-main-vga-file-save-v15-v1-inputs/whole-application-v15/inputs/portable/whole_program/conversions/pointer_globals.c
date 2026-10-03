#include "pointer_globals.h"

/* Only source-used native pointer/slot counts are materialized. The source
 * pointer table and DB slot table begin in zeroed BSS; no pointer-width DOS
 * byte array is copied into these host-native objects. */
SimSourceWindowHandle win_handles[SIM_SOURCE_WINDOW_COUNT];
int16_t db_handles[SIM_SOURCE_DATABASE_COUNT];
struct Font *fd_50F6_4A1A[SIM_SOURCE_FONT_COUNT];
