#ifndef SIMANT_ENHANCED_ACTIONS_H
#define SIMANT_ENHANCED_ACTIONS_H
#include <stdint.h>
#include "portable/platform/host.h"

typedef struct EnhancedActionContract {
    const char *id;
    char route; /* approved L/E/T/H/U classification; L remains a candidate */
    const char *entry;
} EnhancedActionContract;
const EnhancedActionContract *enhanced_action_contract(const char *id);
unsigned enhanced_action_contract_count(void);

typedef struct EnhancedGestureSample {
    int16_t x, y; /* semantic tile/parameter units, never native pixels */
    uint16_t modifiers;
    uint8_t down;
} EnhancedGestureSample;
typedef struct EnhancedIntent {
    char id[4];
    int16_t parameter;
    uint64_t serial; /* caller-monotonic; duplicate submissions are refused */
    uint64_t generation, task_token;
    int16_t source_event, h, v, modifiers; /* audited alternate source path; canonical coordinates */
    unsigned sample_count;
    EnhancedGestureSample samples[64];
} EnhancedIntent;

typedef enum EnhancedActionResult {
    ENHANCED_QUEUED, ENHANCED_DISABLED, ENHANCED_BAD_PARAMETER,
    ENHANCED_DUPLICATE, ENHANCED_QUEUE_FULL, ENHANCED_NEEDS_ADAPTER,
    ENHANCED_HOST_ONLY
} EnhancedActionResult;
typedef struct EnhancedActionLedger {
    uint64_t submitted, delivered, last_serial;
    uint64_t prepared, flush_completed;
    uint64_t rejected;
    int16_t last_event, last_owner;
} EnhancedActionLedger;

/* UI callback surface: copy into durable native queue only. No game calls.
 * Discrete and live original tracker routes retain source event ownership.
 * Buffered sample transcripts and general task-result injection remain unavailable. */
EnhancedActionResult enhanced_submit(const EnhancedIntent *intent);
const EnhancedActionLedger *enhanced_action_ledger(void);
/* Shared native panel/menu/keyboard route. Only enumerated catalog events pass. */
int enhanced_event_binding(unsigned event,const char **id,int *parameter);
EnhancedActionResult enhanced_submit_event(unsigned event,int h,int v,int modifiers);
EnhancedActionResult enhanced_submit_pan(int dx,int dy);
int enhanced_allocation_values(int owner,int axis,uint8_t values[101]);
/* Engine-only completed editor draw; copies the source-reachable value set. */
void enhanced_allocation_catalog_refresh(void);
EnhancedActionResult enhanced_submit_allocation(int owner,int axis,int percent);
EnhancedActionResult enhanced_submit_pointer(unsigned event,int x,int y,int modifiers);
void enhanced_pointer_external_release(void);
void enhanced_pointer_update(int x,int y,int down);
void enhanced_pointer_poll(void);
int enhanced_transaction_wait(void);
int enhanced_queen_wait(void);
int enhanced_yard_wait(void);
int enhanced_pointer_tracking(int owner);
int enhanced_submit_wait_dismiss(void);
void enhanced_execute_wait_dismiss(void);
int enhanced_pointer_input(HostInputState *state);
int enhanced_submit_hit(int owner,int h,int v);


/* Engine-side only. Called once before outer DoEvent, never a nested wait. */
void enhanced_execute_next(void);
int enhanced_action_lease_active(void);
void enhanced_action_finish(void);

#endif
