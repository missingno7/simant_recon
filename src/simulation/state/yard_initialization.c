/*
 * Defines the scalar state initialized by InitSimYard. It includes boy, bird, dog and foot
 * positions, animation values and counters alongside address named fields.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

long far CatDelay;
long far BirdDelay;
long far BoyMsgCnt;
int far BoyIsMowing;
int far CatCycle;
int far BoyPy;
int far CatFrame;
int far BoyPx;
int far LastColonyPopB;
int far LastColonyPopR;
int far FootY;
int far MowX;
int far MowY;
int far DogX;
int far DogY;
int far DogFrame;
int far DogDir;
int far DogTurnCnt;
int far YardCycle;
int far SwarmDelayB;
int far SwarmDelayR;
int far BirdFrame;
int far BirdOn;
int far BoyMessOn;
int far BoyMsgOffset;
