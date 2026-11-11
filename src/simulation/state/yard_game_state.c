/*
 * Defines yard mode, current game tool, colony setup and outcome state. RandYard initializes the
 * words and the yard simulation updates them during play.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far CurGameTool;
int far HouseColonies;
int far JustToBeMean;
int far LastThemeSong;
int far MapPlane;
int far YardMode;
int far BlackWon;
int far IsGameOver;
