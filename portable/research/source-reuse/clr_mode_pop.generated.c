/* Diagnostic generated source; not accepted port code.
 * Input: src/root/m0894.c lines 237-249; sha256=57b40ad0a9ee74c501fbcb0d521b86b8158f206f44f4867e960bcb800b5e7484
 * Translation: explicit context field bindings + 16-bit loop index.
 */
#include <stdint.h>
#include "../../game/simulation/tick.h"

void sim_source_clr_mode_pop(SimTickState *state)
{
    int16_t i;

    for (i = 0; i < 20; i++) {
        state->population_black[i] = 0;
        state->population_red[i] = 0;
    }
    if (state->population_counter_08dc)
        --state->population_counter_08dc;
    if (state->population_counter_08e8)
        --state->population_counter_08e8;
}
