#ifndef SIMANT_WHOLE_STARTUP_PREFLIGHT_H
#define SIMANT_WHOLE_STARTUP_PREFLIGHT_H

#include <stdint.h>

/* Reproduce the five simultaneous INSTALL.EXE opens and closes made by DOS
 * main. On success, closed_fd_slot receives the now-closed number of fh[0].
 * The virtual DOS descriptor allocator must reuse that lowest free number for
 * the first retained data file (language.dat when present, otherwise SHARED).
 * On failure, return -1 and report successful opens; dos_errno retains error. */
int16_t dos_startup_preflight(char *path, int16_t *closed_fd_slot,
                              int16_t *opened_before_failure);

/* Human-readable native diagnostic for the mapped DOS error number. */
char *dos_startup_error_text(int16_t error);

#endif
