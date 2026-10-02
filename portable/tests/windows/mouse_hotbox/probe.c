#include "../../../ui_model/windows/window.h"

#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    unsigned count, i;
    int x, y;
    PortableWindowResource empty = {0};
    if (portable_window_mouse_hit_test(NULL, (PortableWindowPoint){0, 0}) != -1 ||
        portable_window_mouse_hit_test(&empty, (PortableWindowPoint){0, 0}) != -1)
        return 5;
    while (scanf("%u %d %d", &count, &x, &y) == 3) {
        PortableWindowResource window = {0};
        PortableWindowObject *objects;
        int hit;
        if (count > 256) return 2;
        objects = (PortableWindowObject *)calloc(count ? count : 1, sizeof(*objects));
        if (objects == NULL) return 3;
        window.count = (uint16_t)count;
        window.objects = objects;
        for (i = 0; i < count; ++i) {
            unsigned flags;
            int left, top, right, bottom;
            if (scanf("%d %d %d %d %u", &left, &top, &right, &bottom,
                      &flags) != 5) {
                free(objects);
                return 4;
            }
            objects[i].rect = (PortableWindowRect){(int16_t)left, (int16_t)top,
                                                   (int16_t)right, (int16_t)bottom};
            objects[i].flags = (uint16_t)flags;
        }
        hit = portable_window_mouse_hit_test(&window,
                                             (PortableWindowPoint){(int16_t)x,
                                                                   (int16_t)y});
        printf("%d\n", hit);
        free(objects);
    }
    return 0;
}
