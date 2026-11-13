/*
 * Bundles window resource counts, an EMS cache pointer, a sprite callback and a clip stack
 * handle. The contents cross the window, database and graphics interfaces.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * SOURCE_ONLY_DOS data owner candidate: closed scalar/pointer subfamily only.
 * UI resource arrays with unresolved caps are intentionally not defined here.
 */

typedef struct {
    unsigned int age;
    int file;
    int page;
} EmsSlot;

typedef char far * far *Handle;

int far win_numOfWindows;
int far win_numOfColors;
int far win_numOfGroups;
/*
 * Handle for database EMS page-cache slot records.
 */
EmsSlot far * far * far db_ems_slot_list_handle;
void (far * far gfx_copy_to_buffer_hook)(char far *, char far *, int, int);
/*
 * Head handle of the linked stack of saved clipping states.
 */
Handle far clip_saved_state_stack;
