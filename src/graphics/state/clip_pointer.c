/*
 * Defines the near pointer to the active clipping rectangle list. Drawing and dialog code
 * temporarily replace or traverse this list.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

#include "rect.h"
/*
 * Offset of the active clip rectangle list; its far segment follows.
 */
struct Rect far * near clip_active_list_offset;
