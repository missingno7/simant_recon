/*
 * Defines arrays used for yard animation and drawing. The yard update and Draw_SimYard routines
 * index these work tables.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far GrassMap[12];
int far yard_rain_anim_indices[15];
int far yard_black_swarm_anim_indices[17];
int far yard_red_swarm_anim_indices[17];
