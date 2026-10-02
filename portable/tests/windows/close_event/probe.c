#include "close_event_contract.h"

#include <stdio.h>

int main(void)
{
    unsigned front, code, now, last, prev_code, prev_mod, cur_mod;
    while (scanf("%x %x %u %u %x %x %x", &front, &code, &now, &last,
                 &prev_code, &prev_mod, &cur_mod) == 7) {
        SimantCloseEventPlan p = simant_close_event_plan((uint16_t)front,
                                                        (uint16_t)code);
        SimantClickHistory h = {last, {0, 0, 0, (uint16_t)prev_mod,
                                       0, 0, (uint16_t)prev_code, 0}};
        SimantClickEvent e = {0, 0, 0, (uint16_t)cur_mod, 0, 0,
                              (uint16_t)code, 0};
        int doubled = simant_object_click_history(&h, &e, now);
        printf("%u %u %u %u %u %u %u\n", (unsigned)p.route,
               p.flush_queue, p.event_remains_pending,
               p.enters_object_click_history, p.object_index,
               doubled, e.modifiers);
    }
    return 0;
}
