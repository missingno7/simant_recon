/*
 * Defines prepared string list pointers for balloon messages, window prompts, menus and the boy.
 * PrepareStrings initializes each list before those interface routines use it.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

typedef char far * far *StrList;
StrList far BFightMsgs;
StrList far RFightMsgs;
StrList far EggMsgs;
StrList far QueenMsgs;
StrList far RestMsgs;
StrList far WindPromptStrs;
StrList far MwinTitle;
StrList far fd_50F6_106E;
StrList far CasteStr;
StrList far fd_50F6_1086;
StrList far fd_50F6_1096;
StrList far BoyMsgs;
StrList far fd_50F6_10B4;
