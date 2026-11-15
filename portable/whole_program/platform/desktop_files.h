#ifndef SIMANT_DESKTOP_FILES_H
#define SIMANT_DESKTOP_FILES_H
#include <stddef.h>
/* Native storage policy only. Explicit --assets and --portable mount in place;
 * ordinary play gets a private writable DOS volume under the user's prefs. */
int simant_desktop_files(const char *assets, int in_place, const char *user_root,
                         char *volume, size_t capacity, char *error, size_t error_capacity);
#endif
