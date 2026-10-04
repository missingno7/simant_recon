/* Scratch-only natural provider candidate; its basename is intentionally UIGEO.
 * No runtime initializer, fixed address, or placement is supplied.
 */
struct Rect {
    int left;
    int top;
    int right;
    int bottom;
};

struct Bitmap {
    int width;
    int height;
    char far *bits;
};

struct Rect far fd_50F6_10D2;
struct Rect far fd_50F6_110C;
struct Rect far fd_50F6_1104;
struct Bitmap far fd_50F6_392C;
