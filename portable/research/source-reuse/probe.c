#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "clr_mode_pop.generated.c"

int main(void)
{
    SimTickState state;
    unsigned i;
    memset(&state, 0xa5, sizeof state);
    state.population_counter_08dc = 2;
    state.population_counter_08e8 = 0;

    sim_source_clr_mode_pop(&state);

    for (i = 0; i < 20; ++i) {
        assert(state.population_black[i] == 0);
        assert(state.population_red[i] == 0);
    }
    assert(state.population_counter_08dc == 1);
    assert(state.population_counter_08e8 == 0);
    return 0;
}
