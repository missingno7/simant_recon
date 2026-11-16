#include "runtime.h"
#include "actions.h"

/* The typed conversion transports DOS saved SI explicitly through both
 * entries (event-omitted-word/caller-frames.json). Preserve that native ABI,
 * including when the enhanced preview is disabled. */
extern int16_t __real_DoEvent(int16_t incoming_si);
extern void __real_ui_pump_events_edge_scroll(int16_t incoming_si);
extern int16_t clip_window_z_order[32];
static unsigned depth;

/* The source calls DoEvent only if guest input is pending. The outer pump
 * is therefore the seam that can admit a new semantic intent while idle. */
void __wrap_ui_pump_events_edge_scroll(int16_t incoming_si)
{
    int outer=depth++==0;
    if (outer) {
        enhanced_publish(ENHANCED_OUTER_BEFORE);
        enhanced_execute_next();
    }
    __real_ui_pump_events_edge_scroll(incoming_si);
    if (outer) {
        enhanced_action_finish();
        enhanced_publish(ENHANCED_OUTER_AFTER);
    }
    --depth;
}

int16_t __wrap_DoEvent(int16_t incoming_si)
{
    int outer=depth++==0;
    if (outer) {
        enhanced_publish(ENHANCED_OUTER_BEFORE);
        enhanced_execute_next();
    }
    int16_t result=__real_DoEvent(incoming_si);
    if (outer) {
        enhanced_action_finish();
        enhanced_publish(ENHANCED_OUTER_AFTER);
    }
    --depth;
    return result;
}

/* Called by the existing source event-poll stub, after previous source
 * operations have completed. Only publish at an established modal owner;
 * never dispatch a new gameplay action from a nested source tracker. */
void enhanced_source_poll(void)
{
    if (!enhanced_contracts_enabled()) return;
    int16_t top=clip_window_z_order[0];
    if ((enhanced_window_flags(top)&0x40) || top==0x1a00 || top==0x1e00 || top==0x2100 || enhanced_transaction_wait() || enhanced_queen_wait() || enhanced_pointer_tracking(0x1500))
        enhanced_publish(ENHANCED_MODAL_POLL);
    enhanced_execute_wait_dismiss();
}
