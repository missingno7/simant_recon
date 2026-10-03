#ifndef SIMANT_WHOLE_STARTUP_PREFLIGHT_H
#define SIMANT_WHOLE_STARTUP_PREFLIGHT_H

#include <stdint.h>

/* Exercise the DOS startup's five simultaneous install.exe opens. On success,
 * optional_fd is either a separately opened, validated window-header file or
 * zero. On failure, return -1 and report the number of successful opens before
 * the failing attempt; the DOS error is available through dos_errno. */
int16_t dos_startup_preflight(char *path, int16_t *optional_fd,
                              int16_t *opened_before_failure);

/* Release only a retained, separately opened optional descriptor. */
void dos_startup_close_optional(int16_t *optional_fd);

/* Human-readable native diagnostic for the mapped DOS error number. */
char *dos_startup_error_text(int16_t error);

#endif
