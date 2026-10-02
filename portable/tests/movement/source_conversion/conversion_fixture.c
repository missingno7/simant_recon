#include "conversion_fixture.h"
#include "recovered_state.h"
#include "portable/game/simulation/movement.h"

#include <string.h>

int16_t fd_50F6_0A8E;
int16_t fd_50F6_0AF8;
int16_t fd_50F6_0AD6;
int16_t fd_50F6_0AE8;
int16_t fd_50F6_0AB6;
int16_t fd_50F6_0AC6;
int8_t fd_3D57_0000[8];
int8_t fd_3D57_0008[8];

static SourceConversionWorld active_world;
static SourceConversionResult *active_result;

int16_t o25_3BA4_1686(int16_t *rot, int16_t *dir, int16_t plane,
                      int16_t x, int16_t y, int16_t a, int16_t b);
int16_t GetDir(int16_t x1, int16_t y1, int16_t x2, int16_t y2);
int32_t GetDis(int16_t x1, int16_t y1, int16_t x2, int16_t y2);

static void record_call(int16_t kind, const int16_t *args, int count)
{
    SourceConversionCall *call;
    int i;
    if (active_result == NULL || active_result->call_count >= 32) return;
    call = &active_result->calls[active_result->call_count++];
    call->kind = kind;
    for (i = 0; i < 7; ++i) call->args[i] = i < count ? args[i] : 0;
}

int16_t f_0BE8_0B21(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    const int16_t args[4] = {x1, y1, x2, y2};
    record_call(1, args, 4);
    return GetDir(x1, y1, x2, y2);
}

int32_t f_0BE8_0B83(int16_t x1, int16_t y1, int16_t x2, int16_t y2)
{
    const int16_t args[4] = {x1, y1, x2, y2};
    record_call(2, args, 4);
    return GetDis(x1, y1, x2, y2);
}

int16_t TileCanBeMovedOn(int16_t plane, int16_t x, int16_t y,
                         int16_t from_plane, int16_t from_x, int16_t from_y,
                         int16_t digging)
{
    const int16_t args[7] = {plane, x, y, from_plane, from_x, from_y, digging};
    record_call(3, args, 7);
    return sim_tile_can_be_moved_on(&active_world,
                                    plane, x, y, from_plane, from_x, from_y,
                                    digging);
}

void source_conversion_run(const SourceConversionWorld *world,
                           const int8_t *dx, const int8_t *dy,
                           int16_t mode, int16_t from_plane,
                           int16_t from_x, int16_t from_y,
                           int16_t previous_x, int16_t previous_y,
                           int16_t plane, int16_t x, int16_t y,
                           int16_t target_x, int16_t target_y,
                           int16_t initial_rot, int16_t initial_direction,
                           SourceConversionResult *result)
{
    int16_t rot = initial_rot;
    int16_t dir = initial_direction;

    memset(result, 0, sizeof(*result));
    active_result = result;
    memcpy(&active_world, world, sizeof(active_world));
    memcpy(fd_3D57_0000, dx, sizeof(fd_3D57_0000));
    memcpy(fd_3D57_0008, dy, sizeof(fd_3D57_0008));
    fd_50F6_0A8E = mode;
    fd_50F6_0AF8 = from_plane;
    fd_50F6_0AD6 = from_x;
    fd_50F6_0AE8 = from_y;
    fd_50F6_0AB6 = previous_x;
    fd_50F6_0AC6 = previous_y;

    result->result = o25_3BA4_1686(&rot, &dir, plane, x, y, target_x, target_y);
    result->rot = rot;
    result->direction = dir;
    active_result = NULL;
}
