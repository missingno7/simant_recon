#ifndef SIMANT_ACCEPTANCE_EVENT_CONTEXT_RULE_H
#define SIMANT_ACCEPTANCE_EVENT_CONTEXT_RULE_H
/* Observer-only keyboard-context-v1, restricted to explicitly bound Event
 * objects. include/event.h fixes the 16-byte layout. DOS scan code in
 * input_timer.asm produces FAxx and F081..F087. Only h/v (+08..0B) are omitted.
 * Proof: evidence/canonical/native-input-irq/normal-words.md, supplied HCEGANT
 * 640-wide modes only. This never mutates the game or its raw observations. */
#include <stdint.h>
static inline int simant_event_context_includes(const uint8_t *data,
                                               unsigned records, unsigned at)
{
    unsigned record=at/16,byte=at%16;
    if(record>=records || byte<8 || byte>=12) return 1;
    const uint8_t *event=data+record*16;
    unsigned code=(unsigned)event[12] | ((unsigned)event[13]<<8);
    return !((code&0xff00)==0xfa00 || (code>=0xf081 && code<=0xf087));
}
#endif
