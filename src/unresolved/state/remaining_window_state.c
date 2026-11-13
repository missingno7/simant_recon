/*
 * Bundles tile drawing state, display callbacks, colony control resources, map cursor geometry
 * and dialog handles. Its address named fields cover more than the generic window library.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

#include "rect.h"
typedef char far * far *Handle;
int far fd_50F6_37D2;
int far fd_50F6_37D4;
/*
 * Screen rectangle occupied by the spider composite bitmap.
 */
struct Rect far spider_composite_rect;
/*
 * Tile resource handle used when uploading planar graphics to video memory.
 */
Handle far edit_uploaded_tiles_handle;
void (far * far gfx_scratch_to_buffer_hook)();
void (far * far gfx_mask_to_buffer_hook)();
void (far * far gfx_buffer_intersection_hook)();
Handle far casteAnimHandle;
Handle far modeAnimHandle;
int far fd_50F6_37FA;
/*
 * Animation object index used to move the mode triangle knob.
 */
int far mode_knob_anim_index;
Handle far fd_50F6_3836;
/*
 * Main-loop counter used as the bird animation timebase.
 */
long far main_iteration_count;
struct Rect far miniMapRect;
struct Rect far miniMapCursorRect;
int far fd_50F6_3852;
int far multiplier;
int far mapXsize;
int far mapYsize;
/*
 * Allocated startup working-directory string used to restore the path.
 */
char far * far startup_working_directory;
/*
 * First character of the startup working-directory pathname.
 */
int far startup_drive_letter;
void (far * far map_wide_row_converter)();
void (far * far map_narrow_row_converter)();
/*
 * Horizontal pixel margin added to main-map drawing and cursor positions.
 */
int far map_side_margin_pixels;
struct Rect far mapCursorRect;
Handle far fd_50F6_3934;
Handle far fd_50F6_3938;
/*
 * Menu-bar pixel bounds used when drawing and constraining windows.
 */
struct Rect far menu_bar_rect;
/*
 * Free-memory byte count captured during configuration.
 */
long far startup_free_memory_bytes;
