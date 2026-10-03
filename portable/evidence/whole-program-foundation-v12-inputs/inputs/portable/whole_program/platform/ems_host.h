#ifndef SIMANT_WHOLE_EMS_HOST_H
#define SIMANT_WHOLE_EMS_HOST_H

#include <stdint.h>

/* The native game uses ordinary host memory and never owns EMS pages. */
typedef enum EmsHostStatus {
    EMS_HOST_OK = 0,
    EMS_HOST_UNAVAILABLE = 1,
    EMS_HOST_INVALID_ARGUMENT = 2,
    EMS_HOST_INVALID_HANDLE = 3
} EmsHostStatus;

typedef struct EmsHostInfo {
    uint8_t version;
    uint16_t total_pages;
    uint16_t free_pages;
    uint16_t page_frame_segment;
} EmsHostInfo;

/* Source anchors: m195A.asm f_195A_0260 (probe/version/page-frame setup),
 * f_195A_0035 (page counts), and f_195A_001D (page-frame segment). */
EmsHostStatus ems_host_probe(EmsHostInfo *out_info);
EmsHostStatus ems_host_query_pages(uint16_t *out_free, uint16_t *out_total);
EmsHostStatus ems_host_page_frame(uint16_t *out_segment);

/* Source anchors: f_195A_004B allocate, f_195A_0062 map logical page,
 * f_195A_007D free handle, and f_195A_01CB set handle name. These fail
 * explicitly on a host with no EMS; none can create a fake successful handle. */
EmsHostStatus ems_host_allocate(uint16_t pages, uint16_t *out_handle);
EmsHostStatus ems_host_map(uint16_t handle, uint16_t logical_page,
                           uint16_t physical_page);
EmsHostStatus ems_host_free(uint16_t handle);
EmsHostStatus ems_host_set_name(uint16_t handle, const char *name);

#endif
