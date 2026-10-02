#ifndef SIMANT_GAME_RECOVERED_CONTROL_ADAPTER_H
#define SIMANT_GAME_RECOVERED_CONTROL_ADAPTER_H

#include "../../ui_model/windows/control_events.h"

/* Called only while recovered TLS is bound. Read the active shared triangle
 * geometry, then write only the chosen event's source control fields. */
SimControlEventStatus sim_recovered_source_control_event(
    SimSetupControls *controls, SimControlEventPrivateState *private_state,
    SimSetupControlKind kind, const SimControlEventMessage *message,
    const SimControlEventProvider *provider);

#endif
