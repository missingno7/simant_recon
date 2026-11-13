/* Merged object views; variable size and type-dependent overlapping payload. Requires rect.h.
 * This is an access view, NOT a universal 0x38-byte object: some types occupy only 0x28.
 * Only use text_handle/list_handle for the documented types. The +08 four-word
 * layout tuple is deliberately reinterpreted by existing Rect-copy accessors.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef OBJ_H
#define OBJ_H

struct Obj {
    struct Rect rect; /* +00 computed screen bounds; win_Recalc writes them. */
    int x; /* +08 layout horizontal base, pixels; also word 0 of a Rect-sized layout overlay. */
    int y; /* +0A layout vertical base, pixels; layout accessors/window dragging write it. */
    int width; /* +0C layout width/base term; also word 2 of the layout overlay. */
    int height; /* +0E layout height/base term; also word 3 of the layout overlay. */
    int operand[4]; /* +10 per-axis object/argument operand read by _win_CalcObjElement. */
    int mode[4]; /* +18 per-axis layout selector (0..5); helper dispatches, bad value reads a key. */
    unsigned char group; /* +20 resource group id, compared by the SetGroup* routines. */
    char type; /* +21 object type dispatch; resource supplies it, consumers select payload format. */
    int record_bytes; /* +22 byte stride to next object, read by RepointObjects. */
    unsigned flags; /* +24 visibility/selectability/selection/proximity bits, object_attributes writes. */
    char palette; /* +26 normal colour-table index, read by win_SetColorFromObj. */
    char selected_palette; /* +27 selected colour-table index, same reader; resource supplied. */
    int payload28; /* +28 type-dependent word: bitmap id, slider link, or low-byte font/line width. */
    char far * far *text_handle; /* +2A types 16..18 text handle; alloc/free by attributes/unlock. Types 4/10 overlay List.visible/count. */
    char pad2E[6]; /* +2E inline format for types 16..18; List.top/topOff/endOff words for 4/10. Common type unknown. */
    char far * far *list_handle; /* +34 types 4/10 text allocation handle; list drawing locks it and win_UnlockWin releases it. */
};

#endif
