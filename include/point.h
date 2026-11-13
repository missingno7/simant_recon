/* DOS horizontal-first pair; origins and valid ranges depend on the caller.
 * alerts.c does not use its former struct Point; no Macintosh vertical-first ABI inferred.
 * Organisation and descriptive field names are ours. Include where the local
 * struct was defined: this header contributes exactly one struct tag.
 */
#ifndef POINT_H
#define POINT_H

struct Point {
    int x; /* First coordinate: horizontal; pixels in graphics, map/caller units elsewhere. */
    int y; /* Second coordinate: vertical, same caller units; mouse/geometry/simulation write it. */
};

#endif
