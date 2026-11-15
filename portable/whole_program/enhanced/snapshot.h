#ifndef SIMANT_ENHANCED_SNAPSHOT_H
#define SIMANT_ENHANCED_SNAPSHOT_H

#include <stdint.h>

/* Presentation-owned copies. No canonical pointers, raster planes, cache
 * handles, clock reads or game calls. Coordinates retain source units/order.
 * One engine/UI thread in phase 0; a reader may copy a frame for a repaint,
 * but inspectors always advance to the newest publication (no Freeze). */
typedef struct EnhancedPoint { int16_t x, y; } EnhancedPoint;
typedef struct EnhancedRect { int16_t left, top, right, bottom; } EnhancedRect;
typedef struct EnhancedWorldSnapshot {
    uint8_t surface[128][64], life_surface[128][64];
    uint8_t black[64][64], life_black[64][64];
    uint8_t red[64][64], life_red[64][64];
    /* Alarm, food, black nest/trail, red nest/trail; half resolution. */
    uint8_t scent[6][64][32];
    int16_t plane, terrain_set, world_layer;
    EnhancedPoint origin;
    EnhancedRect hidden_viewport;
    int16_t player_plane, player_x, player_y, player_type, player_dir;
    int16_t player_base, player_egg, player_mode;
    int16_t spider_on, spider_x, spider_y;
    /* Source-selected overlay poses/balloons need phase 1 production hooks. */
    uint8_t overlays_available;
} EnhancedWorldSnapshot;

typedef struct EnhancedOverviewSnapshot {
    int16_t map_mode, yard_mode;
    EnhancedRect tiles;
    int16_t cell_width, cell_height, pad, multiplier;
    EnhancedPoint yard_selection, current_patch;
    uint8_t population_black[12][16], population_red[12][16];
    int16_t stored_queens, placement_auto, colonies_black, colonies_red;
} EnhancedOverviewSnapshot;

typedef struct EnhancedAllocationSnapshot {
    int16_t automatic, preset, percent;
    uint16_t frac, mid, weight;
    int16_t population[6];
} EnhancedAllocationSnapshot;
typedef struct EnhancedPanelsSnapshot {
    EnhancedAllocationSnapshot behavior, caste;
    int16_t game_type, tool, paused, speed, options[6];
    int16_t health_yellow, health_black, health_red, warning_yellow, warning_black;
    int16_t population_black, population_red;
} EnhancedPanelsSnapshot;

typedef struct EnhancedCardsSnapshot {
    int16_t card, previous[16], previous_index;
    /* Draw-private link tables and immutable text catalog are phase 1 work.
     * Unavailable means unavailable, never an empty successfully decoded card. */
    uint8_t content_available, links_available;
    int16_t help_owner;
} EnhancedCardsSnapshot;

typedef struct EnhancedHistorySnapshot {
    int16_t samples[10][64]; /* data order: BPop/RPop/BFood/RFood/BHeal/RHeal/Food/ADead/PDead/FDead */
    int16_t start, count;
    int32_t last_overall_score; /* Copy only; never calls CalcScore/ScoreDialog. */
    uint8_t score_metrics_available, selection_available;
    char status[160];
    uint8_t status_truncated;
} EnhancedHistorySnapshot;

typedef struct EnhancedObjectSnapshot {
    int16_t id;
    uint8_t type;
    uint16_t flags;
    EnhancedRect rect;
    int16_t bitmap; /* type 6 only; -1 otherwise */
    char text[160];
    uint8_t text_truncated;
} EnhancedObjectSnapshot;
typedef struct EnhancedDialogsSnapshot {
    uint64_t task_token; /* changes when observed owner/modal identity changes */
    int16_t owner; /* -32768 when no front window */
    uint16_t flags;
    uint8_t modal, request_schema_available;
    unsigned object_count;
    EnhancedObjectSnapshot objects[32];
    /* No guessed Return/Escape/default/timeout. Per-wait result adapters must
     * establish request_schema_available before accepting task actions. */
} EnhancedDialogsSnapshot;

typedef enum EnhancedSeam {
    ENHANCED_OUTER_BEFORE, ENHANCED_OUTER_AFTER, ENHANCED_MODAL_POLL
} EnhancedSeam;
typedef struct EnhancedSnapshot {
    uint64_t generation;
    EnhancedSeam seam;
    EnhancedWorldSnapshot world;
    EnhancedOverviewSnapshot overview;
    EnhancedPanelsSnapshot panels;
    EnhancedCardsSnapshot cards;
    EnhancedHistorySnapshot history;
    EnhancedDialogsSnapshot dialogs;
    int16_t logical_order[32];
} EnhancedSnapshot;

/* NULL until the first safe source publication. Valid until the next source
 * seam, on the same thread. Repaints only read/copy this object. */
const EnhancedSnapshot *enhanced_snapshot(void);
int enhanced_snapshot_copy(EnhancedSnapshot *out);

#endif
