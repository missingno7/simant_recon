#include <stddef.h>

struct Rect { int left; int top; int right; int bottom; };
struct Point { int x; int y; };
struct Bitmap { int width; int height; char far *bits; };

extern struct Rect far fd_50F6_10D2;
extern struct Rect far fd_50F6_110C;
extern struct Rect far fd_50F6_1104;
extern struct Bitmap far fd_50F6_392C;
extern int far puts(char far *text);


static void dump32(char far *tag, unsigned char far *bytes)
{
    char line[80];
    char far *digits;
    int i;
    int k;

    digits = "0123456789ABCDEF";
    k = 0;
    while (tag[k]) {
        line[k] = tag[k];
        k++;
    }
    for (i = 0; i < 32; i++) {
        line[k++] = digits[bytes[i] >> 4];
        line[k++] = digits[bytes[i] & 15];
    }
    line[k] = 0;
    puts(line);
}

int far main(void)
{
    struct Rect a;
    struct Rect b;
    struct Rect c;
    struct Point far *p;
    int far *words;
    unsigned char far *objects[4];
    unsigned char raw[32];
    unsigned char far *ptrBytes;
    unsigned char far *mirrorBytes;
    int i;
    int j;
    int n;
    char far *mirrorBits;

    objects[0] = (unsigned char far *)&fd_50F6_10D2;
    objects[1] = (unsigned char far *)&fd_50F6_110C;
    objects[2] = (unsigned char far *)&fd_50F6_1104;
    objects[3] = (unsigned char far *)&fd_50F6_392C;
    if (sizeof(struct Rect) != 8 || sizeof(struct Point) != 4 ||
        offsetof(struct Rect, left) != 0 || offsetof(struct Rect, top) != 2 ||
        offsetof(struct Rect, right) != 4 || offsetof(struct Rect, bottom) != 6 ||
        sizeof(struct Bitmap) != 8 || offsetof(struct Bitmap, width) != 0 ||
        offsetof(struct Bitmap, height) != 2 || offsetof(struct Bitmap, bits) != 4 ||
        sizeof(((struct Bitmap far *)0)->bits) != 4) {
        puts("FAIL type size/offset");
        return 1;
    }
    puts("LAYOUT R=8/0,2,4,6 P=4/0,2 B=8/0,2,4/PTR4");

    if (fd_50F6_10D2.left || fd_50F6_10D2.top || fd_50F6_10D2.right || fd_50F6_10D2.bottom ||
        fd_50F6_110C.left || fd_50F6_110C.top || fd_50F6_110C.right || fd_50F6_110C.bottom ||
        fd_50F6_1104.left || fd_50F6_1104.top || fd_50F6_1104.right || fd_50F6_1104.bottom ||
        fd_50F6_392C.width || fd_50F6_392C.height || fd_50F6_392C.bits != 0) {
        puts("FAIL typed startup zero");
        return 2;
    }
    n = 0;
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 8; j++) {
            raw[n] = objects[i][j];
            if (raw[n] != 0) {
                puts("FAIL raw startup zero");
                return 3;
            }
            n++;
        }
    }
    dump32("ZERO32=", raw);

    a.left = -1; a.top = 0x1122; a.right = 0x3344; a.bottom = -2;
    b.left = -3; b.top = 0x2233; b.right = 0x4455; b.bottom = -4;
    c.left = -5; c.top = 0x3344; c.right = 0x5566; c.bottom = -6;
    fd_50F6_10D2 = a;
    fd_50F6_110C = b;
    fd_50F6_1104 = c;
    if (fd_50F6_10D2.left != -1 || fd_50F6_10D2.top != 0x1122 ||
        fd_50F6_10D2.right != 0x3344 || fd_50F6_10D2.bottom != -2 ||
        fd_50F6_110C.left != -3 || fd_50F6_110C.top != 0x2233 ||
        fd_50F6_110C.right != 0x4455 || fd_50F6_110C.bottom != -4 ||
        fd_50F6_1104.left != -5 || fd_50F6_1104.top != 0x3344 ||
        fd_50F6_1104.right != 0x5566 || fd_50F6_1104.bottom != -6) {
        puts("FAIL whole Rect assignment");
        return 4;
    }

    p = (struct Point far *)&fd_50F6_10D2;
    p->x = -11; p->y = 12;
    if (fd_50F6_10D2.left != -11 || fd_50F6_10D2.top != 12 ||
        fd_50F6_10D2.right != 0x3344 || fd_50F6_10D2.bottom != -2) {
        puts("FAIL Rect/Point prefix 10D2");
        return 5;
    }
    p = (struct Point far *)&fd_50F6_110C;
    p->x = -13; p->y = 14;
    words = (int far *)&fd_50F6_110C;
    if (fd_50F6_110C.left != -13 || fd_50F6_110C.top != 14 ||
        words[0] != -13 || words[1] != 14 ||
        fd_50F6_110C.right != 0x4455 || fd_50F6_110C.bottom != -4) {
        puts("FAIL Rect/Point/int[2] prefix 110C");
        return 6;
    }
    p = (struct Point far *)&fd_50F6_1104;
    p->x = -15; p->y = 16;
    if (fd_50F6_1104.left != -15 || fd_50F6_1104.top != 16 ||
        fd_50F6_1104.right != 0x5566 || fd_50F6_1104.bottom != -6) {
        puts("FAIL Rect/Point prefix 1104");
        return 7;
    }
    if (fd_50F6_10D2.left >= 0 || fd_50F6_110C.left >= 0 ||
        fd_50F6_1104.left >= 0) {
        puts("FAIL signed Rect int semantics");
        return 8;
    }

    mirrorBits = "UIGEO far bitmap payload";
    fd_50F6_392C.width = -17;
    fd_50F6_392C.height = 18;
    fd_50F6_392C.bits = mirrorBits;
    if (fd_50F6_392C.width != -17 || fd_50F6_392C.width >= 0 ||
        fd_50F6_392C.height != 18 || fd_50F6_392C.bits != mirrorBits) {
        puts("FAIL Bitmap typed values");
        return 9;
    }
    ptrBytes = (unsigned char far *)&fd_50F6_392C.bits;
    mirrorBytes = (unsigned char far *)&mirrorBits;
    for (i = 0; i < 4; i++) {
        if (ptrBytes[i] != mirrorBytes[i]) {
            puts("FAIL Bitmap far pointer bytes");
            return 10;
        }
    }

    n = 0;
    for (i = 0; i < 4; i++)
        for (j = 0; j < 8; j++)
            raw[n++] = objects[i][j];
    dump32("POST32=", raw);
    puts("PASS");
    return 0;
}

