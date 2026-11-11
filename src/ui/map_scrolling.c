/* Root module 004A: map view scrolling (view origin MapPnt clamped to
 * 0..hScrollMax/0F38) and per-plane view centre bookkeeping. */

typedef struct {
    int x;
    int y;
} Point;

int far goStepRight(int n);
int far goStepLeft(int n);
int far goStepDown(int n);
int far goStepUp(int n);
int far goStepNE(int step);
int far goStepSE(int step);
int far goStepSW(int step);
int far goStepNW(int step);
void far FinishDiagStep(void);
void far FinishHorzStep(void);
void far FinishVertStep(void);

extern int far hScrollMax;
extern Point far MapPnt;
extern void far f_00F8_0385(void);

int far goStepRight(int n)
{
    register int moved;

    moved = 0;
    MapPnt.x += n;
    if (MapPnt.x > hScrollMax) {
        MapPnt.x = hScrollMax;
    } else {
        if (n == 1)
            f_00F8_0385();
        moved = 1;
    }
    FinishHorzStep();
    return moved;
}

extern void far f_00F8_039D(void);

int far goStepLeft(int n)
{
    register int moved;

    moved = 0;
    MapPnt.x -= n;
    if (MapPnt.x < 0) {
        MapPnt.x = 0;
    } else {
        if (n == 1)
            f_00F8_039D();
        moved = 1;
    }
    FinishHorzStep();
    return moved;
}

extern int far vScrollMax;
extern void far f_00F8_037D(void);

int far goStepDown(int n)
{
    register int moved;

    moved = 0;
    MapPnt.y += n;
    if (MapPnt.y > vScrollMax) {
        MapPnt.y = vScrollMax;
    } else {
        if (n == 1)
            f_00F8_037D();
        moved = 1;
    }
    FinishVertStep();
    return moved;
}

extern void far f_00F8_0375(void);

int far goStepUp(int n)
{
    register int moved;

    moved = 0;
    MapPnt.y -= n;
    if (MapPnt.y < 0) {
        MapPnt.y = 0;
    } else {
        if (n == 1)
            f_00F8_0375();
        moved = 1;
    }
    FinishVertStep();
    return moved;
}

extern void far f_00F8_036D(void);
extern void far f_00F8_038D(void);

int far goStepNE(int step)
{
    register int moved;

    moved = 0;
    if (--MapPnt.y < 0) {
        MapPnt.y = 0;
    } else {
        if (step == 1)
            f_00F8_036D();
        moved = 1;
    }
    MapPnt.x++;
    if (MapPnt.x > hScrollMax) {
        MapPnt.x = hScrollMax;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    FinishDiagStep();
    return moved;
}

extern void far f_00F8_0365(void);

int far goStepSE(int step)
{
    register int moved;

    moved = 0;
    MapPnt.y++;
    if (MapPnt.y > vScrollMax) {
        MapPnt.y = vScrollMax;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    MapPnt.x++;
    if (MapPnt.x > hScrollMax) {
        MapPnt.x = hScrollMax;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    FinishDiagStep();
    return moved;
}

int far goStepSW(int step)
{
    register int moved;

    moved = 0;
    MapPnt.y++;
    if (MapPnt.y > vScrollMax) {
        MapPnt.y = vScrollMax;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--MapPnt.x < 0) {
        MapPnt.x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    FinishDiagStep();
    return moved;
}

int far goStepNW(int step)
{
    register int moved;

    moved = 0;
    if (--MapPnt.y < 0) {
        MapPnt.y = 0;
    } else {
        if (step == 1)
            f_00F8_0365();
        moved = 1;
    }
    if (--MapPnt.x < 0) {
        MapPnt.x = 0;
    } else {
        if (step == 1)
            f_00F8_038D();
        moved = 1;
    }
    FinishDiagStep();
    return moved;
}

extern int far MapPlane;
extern int far EditColumns;
extern Point far AMapPnt;
extern int far EditRows;
extern Point far BMapPnt;
extern Point far RMapPnt;
extern void far UpdateEdit(void);
extern void far f_0250_0ED2(void);

void far FinishDiagStep(void)
{
    switch (MapPlane) {
    case 1:
        AMapPnt.x = EditColumns / 2 + MapPnt.x;
        AMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    case 2:
        BMapPnt.x = EditColumns / 2 + MapPnt.x;
        BMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    case 3:
        RMapPnt.x = EditColumns / 2 + MapPnt.x;
        RMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

void far FinishHorzStep(void)
{
    switch (MapPlane) {
    case 1:
        AMapPnt.x = EditColumns / 2 + MapPnt.x;
        break;
    case 2:
        BMapPnt.x = EditColumns / 2 + MapPnt.x;
        break;
    case 3:
        RMapPnt.x = EditColumns / 2 + MapPnt.x;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

void far FinishVertStep(void)
{
    switch (MapPlane) {
    case 1:
        AMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    case 2:
        BMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    case 3:
        RMapPnt.y = EditRows / 2 + MapPnt.y;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}

int (far *g_1832[8])(int step) = {
    goStepUp, goStepNE, goStepRight, goStepSE,
    goStepDown, goStepSW, goStepLeft, goStepNW
};
