#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_MAP_TRANSFORM_CALLBACKS_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_MAP_TRANSFORM_CALLBACKS_H

#include <stdint.h>

/* S12 source calls each callback with two far buffers and two 16-bit words.
 * The original S00 conversion procedures consume only the two buffer
 * pointers; the trailing words are retained in this ABI and intentionally
 * ignored by those procedures. */
typedef void (*SimS00MapTransformCallback)(char *source, char *destination,
                                          int16_t source_width,
                                          int16_t count);

typedef enum SimS00MapCallbackStatus {
    SIM_S00_MAP_CALLBACKS_OK = 0,
    SIM_S00_MAP_CALLBACKS_UNSUPPORTED_PROFILE,
    SIM_S00_MAP_CALLBACKS_NOT_INITIALIZED,
    SIM_S00_MAP_CALLBACKS_WRONG_PROFILE_BINDING
} SimS00MapCallbackStatus;

/* These two source-owned slots are assigned by the converted
 * S12::InitMapFunctions. Native storage uses real host function pointers;
 * it does not serialize them into a DOS four-byte pointer table. */
extern SimS00MapTransformCallback fd_50F6_38B8;
extern SimS00MapTransformCallback fd_50F6_38BC;

/* Check, but do not initialize or repair, the assignments made by the source
 * InitMapFunctions path. This accepts only source profiles 0 and 8. */
SimS00MapCallbackStatus sim_s00_map_callbacks_validate(int16_t source_profile);

/* Native ABI providers for the four transform entries selected by S12 for
 * source profiles 0, 4 and 8. The actual source initializer determines which
 * two entries are installed in the slots above. */
void o00_3126_0000(char *source, char *destination,
                   int16_t source_width, int16_t count);
void o00_3126_0137(char *source, char *destination,
                   int16_t source_width, int16_t count);
void o00_3126_026A(char *source, char *destination,
                   int16_t source_width, int16_t count);
void o00_3126_03A9(char *source, char *destination,
                   int16_t source_width, int16_t count);

#endif
