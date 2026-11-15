#ifndef SIMANT_ENHANCED_ACTIONS_H
#define SIMANT_ENHANCED_ACTIONS_H
#include <stdint.h>

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
 * Supported discrete actions require sample_count=task_token=0. All gesture
 * and wait-result adapters fail closed until their per-action proof exists. */
EnhancedActionResult enhanced_submit(const EnhancedIntent *intent);
const EnhancedActionLedger *enhanced_action_ledger(void);

/* Engine-side only. Called once before outer DoEvent, never a nested wait. */
void enhanced_execute_next(void);
int enhanced_action_lease_active(void);
void enhanced_action_finish(void);

#endif
