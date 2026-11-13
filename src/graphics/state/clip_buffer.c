/*
 * Defines the functional rectangle buffer used by window clipping. clip_SetWin selects and fills
 * this working storage.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * clip_SetWin selects this active list before the first Punt.
 */

struct Rect { int left; int top; int right; int bottom; };
struct Rect far clip_rectangle_workspace[256];
