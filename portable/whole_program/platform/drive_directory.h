/* Native implementation of the source root:m1F66 drive-CWD service.
 * DOS drive numbers are 1=A through 26=Z; zero means the process current drive.
 */
#ifndef SIMANT_WHOLE_DRIVE_DIRECTORY_H
#define SIMANT_WHOLE_DRIVE_DIRECTORY_H

#include <stddef.h>
#include <stdint.h>

/* Bounded host API. Success writes an absolute X:\\ path and returns 1.
 * Failure returns 0 and leaves the caller's buffer unchanged. */
int16_t sim_drive_getcwd(int16_t drive, char *path, size_t capacity);

/* Exact source-level ABI used by S09 FileSelect; source paths are 67 bytes. */
int16_t f_1F66_00AF(int16_t drive, char *path);

#endif
