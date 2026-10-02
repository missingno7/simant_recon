#ifndef SIMANT_GAME_RECOVERED_NEST_ADAPTER_H
#define SIMANT_GAME_RECOVERED_NEST_ADAPTER_H

#include "recovered_state.h"
#include "../simulation/nest.h"

typedef struct SimRecoveredNestBinding {
    SimRng *rng;
    const SimNestRequest *request;
    SimNestTickCountProvider tick_count_provider;
    void *tick_count_context;
    SimNestTrace *trace;
    SimNestEventSink event_sink;
    void *event_context;
    SimNestStatus status;
    unsigned calls;
} SimRecoveredNestBinding;

/* Bind this service around a recovered DoAntSim call, while the matching
 * RecoveredState is active through recovered_bind_begin/end. The recovered
 * source calls the historical void entry `o25_3BA4_1035`; this adapter maps
 * source globals into the typed nest transition and records its status. */
void sim_recovered_nest_bind(SimRecoveredNestBinding *binding);
SimNestStatus sim_recovered_nest_unbind(SimRecoveredNestBinding *binding);

/* Source-compatible generated-core entry. Fails hard when no host binding is
 * active so the recovered core cannot silently skip a gameplay transition. */
void o25_3BA4_1035(void);

/* Convenient direct harness entry: bind RecoveredState and RNG, invoke the
 * same source-compatible entry, then export every changed recovered global. */
SimNestStatus sim_recovered_nest_apply(RecoveredState *state, SimRng *rng,
                                       const SimNestRequest *request,
                                       SimNestTrace *trace);
SimNestStatus sim_recovered_nest_apply_with_tick_provider(
    RecoveredState *state, SimRng *rng, const SimNestRequest *request,
    SimNestTrace *trace, SimNestTickCountProvider tick_count_provider,
    void *tick_count_context);

#endif
