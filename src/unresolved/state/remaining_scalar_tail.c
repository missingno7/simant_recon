/*
 * Bundles player, spider, dog, swarm and balloon state words with a long timer. Several fields
 * remain address named and no coherent historical grouping is established.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far RedDestX;
int far RedDestY;
int far MeEgg;
int far DogPx;
int far DogPy;
int far MeSMode;
long far DogBarkDelay;
int far FlyAwayB;
int far FlyAwayR;
int far CurRestPlane;
int far fd_50F6_0FF8;
int far SpidDir;
int far MeHealthCntDwn;
int far fd_50F6_103A;
int far SwarmCentX;
int far MeWantFood;
int far fd_50F6_1046;
int far SwarmCentY;
int far fd_50F6_104A;
