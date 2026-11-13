/*
 * Loads mouse cursor pictures and masks from the resource database. It installs or changes the
 * selected cursor shape.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 1B28; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs.
 */

typedef char far * far *Handle;

Handle g_3D02 = 0;
Handle g_3D06 = 0;
int g_3D0A = -1;
int g_3D0C = 0;
int g_3D0E = 0;
Handle cursor_custom_image_handle = 0;
Handle cursor_custom_mask_handle = 0;
Handle cursor_alternate_image_handle = 0;
Handle cursor_alternate_mask_handle = 0;

Handle near cursor_mask_handles[6];
Handle near cursor_image_handles[6];

extern Handle far db_LoadObject(int object, int kind);
extern void far db_UnhookObject(int object, int kind);

void far mouse_load_builtin_cursor_pairs(void)
{
    int i;

    if (g_3D0C == 0) {
        for (i = 0; i < 6; i++) {
            cursor_image_handles[i] = db_LoadObject(i, 8);
            cursor_mask_handles[i] = db_LoadObject(i, 7);
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

extern int far gfx_driver_initialized;
int near cursor_nonwait_shape;
extern void far mouse_set_cursor_bitmaps(char far *image, char far *mask);
extern void far mouse_show_cursor(void);

int far mouse_select_cursor_shape(int shape)
{
    Handle mask;
    Handle image;

    if (g_3D0E != 0 || gfx_driver_initialized == 0)
        return 0;
    g_3D0E = 1;
    if (g_3D0A != shape) {
        if (shape != 1)
            cursor_nonwait_shape = shape;
        if (shape != -1) {
            mask = cursor_mask_handles[shape];
            image = cursor_image_handles[shape];
            if (image == 0 || mask == 0) {
                g_3D0E = 0;
                return 0;
            }
            g_3D0A = shape;
            g_3D02 = image;
            g_3D06 = mask;
        }
        mouse_set_cursor_bitmaps(*g_3D02, *g_3D06);
        mouse_show_cursor();
    }
    g_3D0E = 0;
    return 1;
}

extern void far RallocFree(Handle h);

int far mouse_load_cursor_resources(int object)
{
    Handle image;
    Handle mask;

    image = db_LoadObject(object, 8);
    mask = db_LoadObject(object, 7);
    if (image == 0 || mask == 0)
        return 0;
    db_UnhookObject(object, 8);
    db_UnhookObject(object, 7);
    if (cursor_custom_image_handle != 0) {
        RallocFree(cursor_custom_image_handle);
        RallocFree(cursor_custom_mask_handle);
    }
    cursor_custom_image_handle = image;
    cursor_custom_mask_handle = mask;
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
    if (cursor_alternate_image_handle != 0) {
        RallocFree(cursor_alternate_image_handle);
        RallocFree(cursor_alternate_mask_handle);
    }
    cursor_alternate_image_handle = image;
    cursor_alternate_mask_handle = mask;
    return 1;
}
