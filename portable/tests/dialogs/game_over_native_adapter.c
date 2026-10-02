#include "../../ui_model/dialogs/game_over.h"

#if defined(_WIN32)
#define SIM_EXPORT __declspec(dllexport)
#else
#define SIM_EXPORT
#endif

SIM_EXPORT int sim_game_over_native_calculate(const SimGameOverInput *input,
                                               SimGameOverResult *result)
{
    return (int)sim_game_over_calculate(input, result);
}
