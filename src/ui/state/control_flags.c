/*
 * Defines percentage display and the mode and caste button state words. initControls initializes
 * the flags used by the colony control windows.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

int far ShowPercentMode;
int far modeButtonState;
int far casteButtonState;
