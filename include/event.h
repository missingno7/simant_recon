/* 16-byte DOS input queue record (input_timer.asm:input_enqueue_event/input_pop_event).
 * It is NOT Macintosh EventRecord: DOS stores BIOS flags/time at +02/+04,
 * horizontal before vertical, event bits at +06 and a BX/ES payload at +0C/+0E.
 * Macintosh what/message/when/where/modifiers are not a layout specification for DOS.
 * Unsigned code is tested across consumers; raw bit-pattern codes include F0xx..FFxx.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef EVENT_H
#define EVENT_H

struct Event {
    int pad00; /* Queue producer does not write this word; purpose/initial value unknown. */
    int bios_shift_flags; /* +02: BIOS 0040:0017 word, with emulated button/shift bit ORed in. */
    int bios_tick_low; /* +04: low word of BIOS 0040:006C ticks when enqueued; wraps at 65536. */
    int modifiers; /* +06: producer AX; pointer transitions and window click-classification bits. */
    int h; /* +08: producer CX, horizontal screen pixels for pointer events. */
    int v; /* +0A: producer DX, vertical screen pixels for pointer events. */
    unsigned code; /* +0C: producer BX, object/menu id or synthetic keyboard/action code. */
    int payload_segment; /* +0E: producer ES, high half of caller payload; meaning is event-dependent. */
};

#endif
