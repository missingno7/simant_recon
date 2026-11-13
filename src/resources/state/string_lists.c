/*
 * Defines advice, history and other prepared string list pointers. PrepareStrings binds them to
 * resources and the interface uses them for titles, scores and advice.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef char far * far *StrList;
StrList far AdviceStrs;
StrList far HistGraphStrs;
StrList far ScenarioNameStrs;
StrList far EndGameRatingStrs;
StrList far MiscStrs;
