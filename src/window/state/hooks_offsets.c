/*
 * Defines per-window draw hooks and rectangle offsets. Window loading initializes them and
 * drawing, unlocking and resizing use their entries.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

#include "rect.h"
void (far * far win_drawHooks[45])(int phase);
struct Rect far win_offsets[45];
