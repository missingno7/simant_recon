/*
 * Bundles yard and balloon positions with pointers, a byte buffer and a tile invalidation array.
 * The file crosses several unrelated functional roles.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Pnt { int x; int y; };
struct Pnt far CurYardPnt;
struct Pnt far LastEggPnt;
struct Pnt far CurEggPnt;
struct Pnt far LastFightPnt;
struct Pnt far CurFightPnt;
/*
 * Up to four complemented keys being matched against cheat entries.
 */
char far cheat_key_prefix[4];
char far * far fd_50F6_0B22;
/*
 * Previous terrain tile byte for each visible cache slot.
 */
unsigned char far edit_cached_terrain_tiles[1200];
/*
 * Previous life tile words; negative sentinels force redraw.
 */
int far edit_cached_life_tiles[30][40];
