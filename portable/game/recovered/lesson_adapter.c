#include "lesson_adapter.h"

#include <limits.h>
#include <stddef.h>

static int16_t add_i16(int16_t left, int16_t right)
{
    uint16_t sum = (uint16_t)((uint16_t)left + (uint16_t)right);
    return sum <= INT16_MAX ? (int16_t)sum : (int16_t)((int32_t)sum - 65536);
}

static SimLessonStatus lesson_clock(const SimLessonServices *services,
                                    int32_t *value)
{
    if (services == NULL || services->mac_tick_count == NULL)
        return SIM_LESSON_SERVICE_UNAVAILABLE;
    *value = services->mac_tick_count(services->context);
    return SIM_LESSON_OK;
}

static SimLessonStatus lesson_window(const SimLessonServices *services,
                                     int16_t window_id, int16_t *value)
{
    if (services == NULL || services->window_is_in_front == NULL)
        return SIM_LESSON_SERVICE_UNAVAILABLE;
    *value = services->window_is_in_front(services->context, window_id);
    return SIM_LESSON_OK;
}

static int pass_clock_threshold(const SimGameWorld *world,
                                const SimLessonServices *services,
                                int *passed)
{
    int32_t now;
    if (lesson_clock(services, &now) != SIM_LESSON_OK) return 0;
    *passed = now > (int32_t)world->source_state_0204;
    return 1;
}

SimLessonStatus sim_lesson_done(SimGameWorld *world, SimTickState *tick_state,
                                SimNestRuntime *nest_runtime,
                                SimLessonState *lesson_state,
                                const SimLessonServices *services,
                                int16_t lesson, int16_t *done)
{
    int16_t sum;
    int16_t front;
    int threshold_passed;
    SimLessonStatus status;
    if (world == NULL || tick_state == NULL || nest_runtime == NULL ||
        lesson_state == NULL || done == NULL)
        return SIM_LESSON_INVALID_ARGUMENT;
    *done = 0;
    switch (lesson) {
    case 1: case 2: case 6: case 11: case 15: case 17: case 23:
    case 25: case 28: case 29: case 31: case 34: case 35: case 37:
    case 40: case 44: case 45: case 48: case 51: case 53: case 55:
    case 56:
        *done = 1;
        break;
    case 3:
        *done = nest_runtime->dug_b_count >= (int32_t)world->source_state_0204 &&
                lesson_state->fd_50F6_0AA0 == 0;
        break;
    case 4:
        *done = nest_runtime->dug_b_count > (int32_t)world->source_state_0204 &&
                lesson_state->fd_50F6_0AA0 == 0;
        break;
    case 5: case 20:
        *done = world->current_ant_plane == 1;
        break;
    case 7: case 26:
        sum = add_i16(world->me_y, world->me_x);
        if (sum != lesson_state->fd_50F6_1074 && lesson_state->fd_50F6_0B1E == 0) {
            if (!pass_clock_threshold(world, services, &threshold_passed))
                return SIM_LESSON_SERVICE_UNAVAILABLE;
            *done = threshold_passed;
        }
        break;
    case 8: case 43: case 46: case 50:
        *done = lesson_state->fd_50F6_1074 != 0;
        break;
    case 9:
        sum = add_i16(world->map_view_y, world->map_view_x);
        if (sum != lesson_state->fd_50F6_1074) {
            *done = 1;
        } else {
            if (!pass_clock_threshold(world, services, &threshold_passed))
                return SIM_LESSON_SERVICE_UNAVAILABLE;
            *done = threshold_passed;
        }
        break;
    case 10: case 32: case 42:
        status = lesson_window(services, 0x0100, &front);
        if (status != SIM_LESSON_OK) return status;
        *done = front != 0;
        break;
    case 12: case 49:
        status = lesson_window(services, 0, &front);
        if (status != SIM_LESSON_OK) return status;
        *done = front != 0;
        break;
    case 13:
        if (world->current_ant_plane == 1) {
            if (world->me_x < 0 || world->me_x >= SIM_WORLD_WIDTH ||
                world->me_y < 0 || world->me_y >= SIM_WORLD_HEIGHT)
                return SIM_LESSON_MAP_COORDINATE_UNAVAILABLE;
            *done = world->tiles.surface[world->me_x][world->me_y] > 0x47;
        }
        break;
    case 14:
        *done = world->me_health > 0x5a;
        break;
    case 16:
        *done = world->me_type == 0x18;
        break;
    case 18:
        *done = world->current_ant_plane == 2;
        break;
    case 19:
        *done = world->me_type == 0x10;
        break;
    case 21:
        *done = world->me_type == 0x28;
        break;
    case 22:
        *done = world->me_type == 0x10;
        break;
    case 24:
        *done = tick_state->history_black[5] > 1;
        break;
    case 27:
        sum = add_i16(world->me_y, world->me_x);
        *done = sum != lesson_state->fd_50F6_1074 &&
                nest_runtime->alarm_drop_state != 0 &&
                lesson_state->fd_50F6_0B1E == 0;
        break;
    case 30:
        if (nest_runtime->alarm_drop_state != 0) {
            if (services == NULL || services->set_alarm_drop_state == NULL)
                return SIM_LESSON_SERVICE_UNAVAILABLE;
            services->set_alarm_drop_state(services->context, 0, 1);
        }
        *done = lesson_state->fd_50F6_1074 != 0;
        break;
    case 33:
        *done = world->map_plane == 0;
        break;
    case 36:
        *done = lesson_state->fd_50F6_035C == 1;
        break;
    case 38:
        *done = world->map_plane == 1;
        break;
    case 39:
        status = lesson_window(services, 0x1200, &front);
        if (status != SIM_LESSON_OK) return status;
        *done = front != 0;
        break;
    case 41:
        sum = add_i16(lesson_state->modeLevels[1], lesson_state->modeLevels[0]);
        *done = sum != lesson_state->fd_50F6_1074;
        break;
    case 47:
        status = lesson_window(services, 0x1300, &front);
        if (status != SIM_LESSON_OK) return status;
        *done = front != 0;
        break;
    case 52:
        *done = tick_state->history_black[5] > 0x28;
        break;
    case 54:
        if (world->current_ant_plane == 3) {
            lesson_state->fd_50F6_1074 = 0;
            *done = 1;
        } else if (world->current_ant_plane == 2) {
            lesson_state->fd_50F6_1074 = 1;
            *done = 1;
        }
        break;
    default:
        break;
    }
    *done = (int16_t)(*done != 0);
    return SIM_LESSON_OK;
}

const char *sim_lesson_status_string(SimLessonStatus status)
{
    switch (status) {
    case SIM_LESSON_OK: return "ok";
    case SIM_LESSON_INVALID_ARGUMENT: return "invalid-argument";
    case SIM_LESSON_SERVICE_UNAVAILABLE: return "service-unavailable";
    case SIM_LESSON_MAP_COORDINATE_UNAVAILABLE: return "map-coordinate-unavailable";
    default: return "unknown";
    }
}
