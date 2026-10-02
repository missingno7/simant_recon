#include "menu_adapter.h"

#include <stddef.h>
#include <string.h>

/* Identical to the Event declaration in the selected S11 source TU. Keeping
 * this bridge separate avoids sharing S22's differently shaped Event tag. */
struct Event {
    int16_t what;
    int16_t where[2];
    int16_t when[2];
    int16_t modifiers;
    int16_t message;
};

_Static_assert(sizeof(struct Event) == 14, "S11 event has seven DOS words");
_Static_assert(offsetof(struct Event, message) == 12,
               "S11 ProcMenu reads its command at byte twelve");

extern void ProcMenu(struct Event *event);

void sim_recovered_source_proc_menu_command(uint16_t command)
{
    struct Event event = {0};
    /* Retain the word's bit pattern without an out-of-range signed cast. */
    memcpy(&event.message, &command, sizeof(command));
    ProcMenu(&event);
}
