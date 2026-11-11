/*
 * Defines yellow ant and red initiator positions and planes. Commands and movement use the two
 * location triples.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * These are six registered signed game words.
 */

int far MeLocX;
int far MeLocY;
int far MePlane;
int far RedLocX;
int far RedLocY;
int far RedPlane;
