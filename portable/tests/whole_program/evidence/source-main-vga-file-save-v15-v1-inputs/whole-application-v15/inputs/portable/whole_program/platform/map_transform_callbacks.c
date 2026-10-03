#include "map_transform_callbacks.h"

/* S12::InitMapFunctions is the producer for these source callback globals.
 * Zero initialization preserves their pre-initialization DGROUP state. */
SimS00MapTransformCallback fd_50F6_38B8 = NULL;
SimS00MapTransformCallback fd_50F6_38BC = NULL;

SimS00MapCallbackStatus sim_s00_map_callbacks_validate(int16_t source_profile)
{
    if (source_profile != 0 && source_profile != 8)
        return SIM_S00_MAP_CALLBACKS_UNSUPPORTED_PROFILE;
    if (fd_50F6_38B8 == NULL || fd_50F6_38BC == NULL)
        return SIM_S00_MAP_CALLBACKS_NOT_INITIALIZED;
    if (fd_50F6_38B8 != o00_3126_0000 ||
        fd_50F6_38BC != o00_3126_0137)
        return SIM_S00_MAP_CALLBACKS_WRONG_PROFILE_BINDING;
    return SIM_S00_MAP_CALLBACKS_OK;
}
