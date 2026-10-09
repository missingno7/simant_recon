#ifndef SIMANT_MODERN_CAMERA_H
#define SIMANT_MODERN_CAMERA_H

/* Modern Game Window camera: presentation state only. Coordinates:
 *
 *   world pixels   tile (x, y) covers [16x, 16x+16) x [16y, 16y+16)
 *   view pixels    the Game Window's map area, origin at its top-left
 *
 * view = (world - center) * zoom + size / 2. The canonical camera (MapPnt and
 * the edit view, see world_view.h) stays the game's; modern_camera_follow /
 * modern_camera_canonical_origin are the only rules relating the two. */

typedef struct ModernCamera {
    double center_x, center_y;     /* world pixels at the view centre */
    double zoom;                   /* view pixels per world pixel */
    int width, height;             /* view size in pixels */
} ModernCamera;

void modern_camera_to_world(const ModernCamera *camera, double vx, double vy,
                            double *wx, double *wy);
void modern_camera_to_view(const ModernCamera *camera, double wx, double wy,
                           double *vx, double *vy);
/* Visible world rectangle (may extend past the world). */
void modern_camera_visible(const ModernCamera *camera, double *left, double *top,
                           double *right, double *bottom);
/* Keep the view on a world of `width` x `height` world pixels: a view
 * larger than the world centres it, otherwise no area outside it shows. */
void modern_camera_clamp(ModernCamera *camera, double width, double height);
/* Change zoom keeping the world point under view pixel (vx, vy) fixed. */
void modern_camera_zoom_at(ModernCamera *camera, double vx, double vy, double zoom);

/* Canonical edit view centre in world pixels: MapPnt plus half of the edit
 * tile rectangle (its pixel extent, not editHeight's partial row). */
void modern_camera_canonical_center(int origin_x, int origin_y, int rect_width,
                                    int rect_height, int tile, double *x, double *y);
/* MapPnt that centres the canonical edit view on the camera centre (unclamped;
 * the game's own scroll clamps it). */
void modern_camera_canonical_origin(const ModernCamera *camera, int rect_width,
                                    int rect_height, int tile, int *x, int *y);

#endif
