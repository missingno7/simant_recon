/*
 * Defines the active map origin and the remembered surface, nest and yard view origins. The
 * scroll and world setup routines use signed coordinate pairs.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Consumers use signed 16-bit x/y pairs; SaveRec stores four bytes at each
 * registered base. Original COMMON order, padding and values remain unproven.
 */

typedef struct {
    int x;
    int y;
} Point;

Point far MapPnt;
Point far AMapPnt;
Point far BMapPnt;
Point far RMapPnt;
Point far YMapPnt;
