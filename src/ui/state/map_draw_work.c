/*
 * Defines two small map drawing words and two detailed view rendering values. The mini map
 * renderer and tile drawing helper use these independent scalars.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

/*
 * Horizontal pixels per map cell in the miniature map.
 */
int near minimap_x_scale;
/*
 * Vertical pixels per map cell in the miniature map.
 */
int near minimap_y_scale;
/*
 * Life-tile identifier used by the editor tile drawing paths.
 */
unsigned near edit_current_life_tile;
/*
 * Terrain-tile identifier used by the editor tile drawing paths.
 */
unsigned char near edit_current_terrain_tile;
