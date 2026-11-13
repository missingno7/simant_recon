/*
 * Bundles balloon, tutorial, bird, strategy and tile view state. Several resource handles and
 * dimensions are still identified only by address.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef char far * far *Handle;
int far WantQueenBalloon;
int far WantRFightBalloon;
unsigned char far fd_50F6_106C;
int far LessonTemp;
int far WantRestBalloon;
int far message_balloon_count;
int far StrategicModeR;
int far BirdX;
int far TutHowLong;
int far BirdY;
Handle far startup_info_block_handle;
int far startup_executable_fd;
Handle far yardAnimHandle;
int far fd_50F6_10DE;
int far fd_50F6_10E0;
char far * far * far fd_50F6_10E2;
Handle far edit_life_tiles_handle;
Handle far edit_life_alt_tiles_handle;
Handle far edit_terrain_tiles_handle;
int far edit_tile_renderer_kind;
