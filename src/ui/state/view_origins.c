/*
 * Review-only source storage candidate for five source-bounded point objects.
 * The source consumers use signed 16-bit x/y pairs; SaveRec stores four bytes
 * at each exact base. This does not claim the historical compiler's original
 * owner module, COMMON order, padding, or values.
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
