/* Root module 1B28: mouse cursor shapes (cursor image/mask objects from the database). */

typedef char far * far *Handle;

Handle g_3D02 = 0;
Handle g_3D06 = 0;
int g_3D0A = -1;
int g_3D0C = 0;
int g_3D0E = 0;
Handle g_3D10 = 0;
Handle g_3D14 = 0;
Handle g_3D18 = 0;
Handle g_3D1C = 0;

Handle near g_8C9C[6];
Handle near g_8C7C[6];

extern Handle far db_LoadObject(int object, int kind);
extern void far db_UnhookObject(int object, int kind);

void far f_1B28_0006(void)
{
    int i;

    if (g_3D0C == 0) {
        for (i = 0; i < 6; i++) {
            g_8C7C[i] = db_LoadObject(i, 8);
            g_8C9C[i] = db_LoadObject(i, 7);
            db_UnhookObject(i, 8);
            db_UnhookObject(i, 7);
        }
        g_3D0C = 1;
    }
}

void far f_1B28_0068(void)
{
}

void far f_1B28_0069(void)
{
}

extern int far fd_55B3_6262;
int near g_8CBC;
extern void far f_1B73_01E1(char far *image, char far *mask);
extern void far f_1B73_00D9(void);

int far f_1B28_006A(int shape)
{
    Handle mask;
    Handle image;

    if (g_3D0E != 0 || fd_55B3_6262 == 0)
        return 0;
    g_3D0E = 1;
    if (g_3D0A != shape) {
        if (shape != 1)
            g_8CBC = shape;
        if (shape != -1) {
            mask = g_8C9C[shape];
            image = g_8C7C[shape];
            if (image == 0 || mask == 0) {
                g_3D0E = 0;
                return 0;
            }
            g_3D0A = shape;
            g_3D02 = image;
            g_3D06 = mask;
        }
        f_1B73_01E1(*g_3D02, *g_3D06);
        f_1B73_00D9();
    }
    g_3D0E = 0;
    return 1;
}

extern void far f_171C_13E4(Handle h);

int far f_1B28_0129(int object)
{
    Handle image;
    Handle mask;

    image = db_LoadObject(object, 8);
    mask = db_LoadObject(object, 7);
    if (image == 0 || mask == 0)
        return 0;
    db_UnhookObject(object, 8);
    db_UnhookObject(object, 7);
    if (g_3D10 != 0) {
        f_171C_13E4(g_3D10);
        f_171C_13E4(g_3D14);
    }
    g_3D10 = image;
    g_3D14 = mask;
    return 1;
}

int far f_1B28_01CB(int object)
{
    Handle image;
    Handle mask;

    image = db_LoadObject(object, 8);
    mask = db_LoadObject(object, 7);
    db_UnhookObject(object, 8);
    db_UnhookObject(object, 7);
    if (image == 0 || mask == 0)
        return 0;
    if (g_3D18 != 0) {
        f_171C_13E4(g_3D18);
        f_171C_13E4(g_3D1C);
    }
    g_3D18 = image;
    g_3D1C = mask;
    return 1;
}
