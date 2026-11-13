/*
 * Defines two event records for the window input layer. The event conversion helper fills their
 * message, position and modifier fields.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};
/*
 * Event popped from the input queue and processed by the window dispatcher.
 */
struct Event far window_current_event;
/*
 * Prior dispatched event used for rapid-repeat detection.
 */
struct Event far window_previous_event;
