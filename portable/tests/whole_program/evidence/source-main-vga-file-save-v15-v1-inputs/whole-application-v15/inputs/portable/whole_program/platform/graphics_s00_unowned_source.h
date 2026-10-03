#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_S00_UNOWNED_SOURCE_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_GRAPHICS_S00_UNOWNED_SOURCE_H

#ifdef __cplusplus
extern "C" {
#endif

/* Exact empty far-return entry from S00:m35A6.asm. */
void o00_35A6_0006(void);

/* The original entry selects the 320x200 CGA mode and initializes CGA-only
 * memory. That complete video profile is unsupported by this native port. */
void o00_31AD_1AE7(void);

#ifdef __cplusplus
}
#endif
#endif
