#include "camera.h"

#include <math.h>

void modern_camera_to_world(const ModernCamera *camera, double vx, double vy,
                            double *wx, double *wy)
{
    *wx = camera->center_x + (vx - camera->width / 2.0) / camera->zoom;
    *wy = camera->center_y + (vy - camera->height / 2.0) / camera->zoom;
}

void modern_camera_to_view(const ModernCamera *camera, double wx, double wy,
                           double *vx, double *vy)
{
    *vx = (wx - camera->center_x) * camera->zoom + camera->width / 2.0;
    *vy = (wy - camera->center_y) * camera->zoom + camera->height / 2.0;
}

void modern_camera_visible(const ModernCamera *camera, double *left, double *top,
                           double *right, double *bottom)
{
    modern_camera_to_world(camera, 0, 0, left, top);
    modern_camera_to_world(camera, camera->width, camera->height, right, bottom);
}

static double clamp_axis(double center, double half, double extent)
{
    if (2 * half >= extent) return extent / 2;
    if (center < half) return half;
    if (center > extent - half) return extent - half;
    return center;
}

void modern_camera_clamp(ModernCamera *camera, double width, double height)
{
    camera->center_x = clamp_axis(camera->center_x, camera->width / (2 * camera->zoom), width);
    camera->center_y = clamp_axis(camera->center_y, camera->height / (2 * camera->zoom), height);
}

void modern_camera_zoom_at(ModernCamera *camera, double vx, double vy, double zoom)
{
    double wx, wy;
    modern_camera_to_world(camera, vx, vy, &wx, &wy);
    camera->zoom = zoom;
    camera->center_x = wx - (vx - camera->width / 2.0) / zoom;
    camera->center_y = wy - (vy - camera->height / 2.0) / zoom;
}

void modern_camera_canonical_center(int origin_x, int origin_y, int rect_width,
                                    int rect_height, int tile, double *x, double *y)
{
    *x = (double)origin_x * tile + rect_width / 2.0;
    *y = (double)origin_y * tile + rect_height / 2.0;
}

void modern_camera_canonical_origin(const ModernCamera *camera, int rect_width,
                                    int rect_height, int tile, int *x, int *y)
{
    *x = (int)floor((camera->center_x - rect_width / 2.0) / tile + 0.5);
    *y = (int)floor((camera->center_y - rect_height / 2.0) / tile + 0.5);
}
