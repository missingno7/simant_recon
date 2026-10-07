/* Virtual DOS drive-CWD service. Host paths are private to this boundary. */
#ifndef SIMANT_WHOLE_DRIVE_DIRECTORY_H
#define SIMANT_WHOLE_DRIVE_DIRECTORY_H

#include <stddef.h>
#include <stdint.h>

/* The application supplies the host asset directory once at startup. */
int16_t sim_drive_set_root(const char *host_path);

/* DOS drive numbers are 1=A through 26=Z; zero means the current drive.
 * Only the oracle's mounted C: volume is present in this virtual machine. */
int16_t sim_drive_getdrive(void);
int16_t sim_drive_setdrive(int16_t drive);
int16_t sim_drive_getcwd(int16_t drive, char *path, size_t capacity);

/* Resolve a DOS path inside virtual C:. Return 1 on success; otherwise return
 * 0 and write the corresponding DOS error code. Wildcards are accepted only
 * when requested by the directory-enumeration service. */
int16_t sim_drive_resolve_path(const char *dos_path, char *host_path,
                               size_t capacity, int allow_wildcards,
                               uint16_t *dos_error);
uint16_t sim_drive_chdir(const char *dos_path);
int16_t sim_drive_error_to_errno(uint16_t dos_error);

/* Exact source ABI used by S09 FileSelect; path is a DOS CWD, never a host path. */
int16_t f_1F66_00AF(int16_t drive, char *path);

#endif
