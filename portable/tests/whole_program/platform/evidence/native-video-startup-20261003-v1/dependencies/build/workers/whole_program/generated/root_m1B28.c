#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Root module 1B28: mouse cursor shapes (cursor image/mask objects from the database). */

typedef char  *  *Handle;

Handle g_3D02 = 0;
Handle g_3D06 = 0;
int16_t g_3D0A = -1;
int16_t g_3D0C = 0;
int16_t g_3D0E = 0;
Handle g_3D10 = 0;
Handle g_3D14 = 0;
Handle g_3D18 = 0;
Handle g_3D1C = 0;

Handle  g_8C9C[6];
Handle  g_8C7C[6];

extern Handle  db_LoadObject(int16_t object, int16_t kind);
extern void  db_UnhookObject(int16_t object, int16_t kind);

void  f_1B28_0006(void)
{
    int16_t i;

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

void  f_1B28_0068(void)
{
}

void  f_1B28_0069(void)
{
}

extern int16_t  fd_55B3_6262;
int16_t  g_8CBC;
extern void  f_1B73_01E1(char  *image, char  *mask);
extern void  f_1B73_00D9(void);

int16_t  f_1B28_006A(int16_t shape)
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

extern void  f_171C_13E4(Handle h);

int16_t  f_1B28_0129(int16_t object)
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

int16_t  f_1B28_01CB(int16_t object)
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

#pragma pack(pop)
