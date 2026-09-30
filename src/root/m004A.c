/* Root module 004A: map view scrolling (view origin fd_50F6_0508 clamped to
 * 0..fd_50F6_0F36/0F38) and per-plane view centre bookkeeping. */

typedef struct {
    int x;
    int y;
} Point;

int far f_004A_000A(int n);
int far f_004A_0052(int n);
int far f_004A_008A(int n);
int far f_004A_00D2(int n);
int far f_004A_010A(int step);
int far f_004A_0172(int step);
int far f_004A_01E9(int step);
int far f_004A_0253(int step);
void far f_004A_02AD(void);
void far f_004A_038B(void);
void far f_004A_040E(void);

extern int far fd_50F6_0F36;
extern Point far fd_50F6_0508;
extern void far f_00F8_0385(void);

int far f_004A_000A(int n)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.x += n;
    if (fd_50F6_0508.x > fd_50F6_0F36) {
        fd_50F6_0508.x = fd_50F6_0F36;
    } else {
        if (n == 1)
            f_00F8_0385();
        moved = 1;
    }
    f_004A_038B();
    return moved;
}

extern void far f_00F8_039D(void);

int far f_004A_0052(int n)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.x -= n;
    if (fd_50F6_0508.x < 0) {
        fd_50F6_0508.x = 0;
    } else {
        if (n == 1)
            f_00F8_039D();
        moved = 1;
    }
    f_004A_038B();
    return moved;
}

extern int far fd_50F6_0F38;
extern void far f_00F8_037D(void);

int far f_004A_008A(int n)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.y += n;
    if (fd_50F6_0508.y > fd_50F6_0F38) {
        fd_50F6_0508.y = fd_50F6_0F38;
    } else {
        if (n == 1)
            f_00F8_037D();
        moved = 1;
    }
    f_004A_040E();
    return moved;
}

extern void far f_00F8_0375(void);

int far f_004A_00D2(int n)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.y -= n;
    if (fd_50F6_0508.y < 0) {
        fd_50F6_0508.y = 0;
    } else {
        if (n == 1)
            f_00F8_0375();
        moved = 1;
    }
    f_004A_040E();
    return moved;
}

extern void far f_00F8_036D(void);
extern void far f_00F8_038D(void);

int far f_004A_010A(int step)
{
    register int moved;

    moved = 0;
    if (--fd_50F6_0508.y < 0) {
        fd_50F6_0508.y = 0;
    } else {
        if (step == 1)
            f_00F8_036D();
        moved = 1;
    }
    fd_50F6_0508.x++;
    if (fd_50F6_0508.x > fd_50F6_0F36) {
        fd_50F6_0508.x = fd_50F6_0F36;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

extern void far f_00F8_0365(void);

int far f_004A_0172(int step)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.y++;
    if (fd_50F6_0508.y > fd_50F6_0F38) {
        fd_50F6_0508.y = fd_50F6_0F38;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    fd_50F6_0508.x++;
    if (fd_50F6_0508.x > fd_50F6_0F36) {
        fd_50F6_0508.x = fd_50F6_0F36;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

int far f_004A_01E9(int step)
{
    register int moved;

    moved = 0;
    fd_50F6_0508.y++;
    if (fd_50F6_0508.y > fd_50F6_0F38) {
        fd_50F6_0508.y = fd_50F6_0F38;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--fd_50F6_0508.x < 0) {
        fd_50F6_0508.x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

int far f_004A_0253(int step)
{
    register int moved;

    moved = 0;
    if (--fd_50F6_0508.y < 0) {
        fd_50F6_0508.y = 0;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--fd_50F6_0508.x < 0) {
        fd_50F6_0508.x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    f_004A_02AD();
    return moved;
}

extern int far fd_50F6_032E;
extern int far fd_50F6_0FB6;
extern Point far fd_50F6_0596;
extern int far fd_50F6_0FFA;
extern Point far fd_50F6_06A6;
extern Point far fd_50F6_072E;
extern void far f_0250_0E9D(void);
extern void far f_0250_0ED2(void);

void far f_004A_02AD(void)
{
    switch (fd_50F6_032E) {
    case 1:
        fd_50F6_0596.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        fd_50F6_0596.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    case 2:
        fd_50F6_06A6.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        fd_50F6_06A6.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    case 3:
        fd_50F6_072E.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        fd_50F6_072E.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    }
    f_0250_0E9D();
    f_0250_0ED2();
}

void far f_004A_038B(void)
{
    switch (fd_50F6_032E) {
    case 1:
        fd_50F6_0596.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        break;
    case 2:
        fd_50F6_06A6.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        break;
    case 3:
        fd_50F6_072E.x = fd_50F6_0FB6 / 2 + fd_50F6_0508.x;
        break;
    }
    f_0250_0E9D();
    f_0250_0ED2();
}

void far f_004A_040E(void)
{
    switch (fd_50F6_032E) {
    case 1:
        fd_50F6_0596.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    case 2:
        fd_50F6_06A6.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    case 3:
        fd_50F6_072E.y = fd_50F6_0FFA / 2 + fd_50F6_0508.y;
        break;
    }
    f_0250_0E9D();
    f_0250_0ED2();
}

int (far *g_1832[8])(int step) = {
    f_004A_00D2, f_004A_010A, f_004A_000A, f_004A_0172,
    f_004A_008A, f_004A_01E9, f_004A_0052, f_004A_0253
};
