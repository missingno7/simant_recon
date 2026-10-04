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

Point far fd_50F6_0508;
Point far fd_50F6_0596;
Point far fd_50F6_06A6;
Point far fd_50F6_072E;
Point far fd_50F6_07BC;
