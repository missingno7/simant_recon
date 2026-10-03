#include "../../whole_program/platform/sdl3/host_modes.h"
#include <SDL3/SDL.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

static void frame(Host *host, int height, const char *path)
{
    const size_t stride = 648;
    uint8_t *pixels = malloc(stride * (size_t)height);
    HostPalette palette = {{{0}}};
    SDL_Surface *image;
    int width, actual_height;
    assert(pixels);
    memset(pixels, 15, stride * (size_t)height);
    palette.rgb[15][0] = 217;
    palette.rgb[15][1] = 19;
    palette.rgb[15][2] = 53;
    assert(host_get_logical_size(host, &width, &actual_height));
    assert(width == 640 && actual_height == height);
    assert(host_present(host, pixels, stride, &palette));
    assert(host_save_frame(host, path));
    image = SDL_LoadBMP(path);
    assert(image && image->w == 640 && image->h == height);
    assert(host_present(host, pixels, 639, &palette) == 0);
    pixels[(size_t)(height - 1) * stride + 639] = 16;
    assert(host_present(host, pixels, stride, &palette) == 0);
    SDL_DestroySurface(image);
    free(pixels);
}

int main(int argc, char **argv)
{
    Host *host;
    int width, height;
    assert(argc == 3);
    assert(host_create_dimensions("invalid", 0, 320, 200) == NULL);
    host = host_create_dimensions("whole source VGA", 0, 640, 480);
    assert(host);
    frame(host, 480, argv[1]);
    assert(host_set_logical_size(host, 640, 350));
    frame(host, 350, argv[2]);
    assert(host_set_logical_size(host, 640, 480));
    assert(host_set_logical_size(host, 640, 400) == 0);
    assert(host_get_logical_size(host, &width, &height));
    assert(width == 640 && height == 480);
    host_destroy(host);
    host = host_create("existing API default", 1);
    assert(host_get_logical_size(host, &width, &height));
    assert(width == 640 && height == 350);
    host_destroy(host);
    return 0;
}
