/*
 * Bundles tile drawing state, display callbacks, colony control resources, map cursor geometry
 * and dialog handles. Its address named fields cover more than the generic window library.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Rect { int left; int top; int right; int bottom; };
typedef char far * far *Handle;
int far fd_50F6_37D2;
int far fd_50F6_37D4;
struct Rect far spider_composite_rect;
Handle far edit_uploaded_tiles_handle;
void (far * far gfx_scratch_to_buffer_hook)();
void (far * far gfx_mask_to_buffer_hook)();
void (far * far gfx_buffer_intersection_hook)();
Handle far casteAnimHandle;
Handle far modeAnimHandle;
int far fd_50F6_37FA;
int far mode_knob_anim_index;
Handle far fd_50F6_3836;
long far main_iteration_count;
struct Rect far miniMapRect;
struct Rect far miniMapCursorRect;
int far fd_50F6_3852;
int far multiplier;
int far mapXsize;
int far mapYsize;
char far * far startup_working_directory;
int far startup_drive_letter;
void (far * far map_wide_row_converter)();
void (far * far map_narrow_row_converter)();
int far map_side_margin_pixels;
struct Rect far mapCursorRect;
Handle far fd_50F6_3934;
Handle far fd_50F6_3938;
struct Rect far menu_bar_rect;
long far startup_free_memory_bytes;
