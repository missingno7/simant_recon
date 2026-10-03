#include "ems_host.h"

EmsHostStatus ems_host_probe(EmsHostInfo *out_info)
{
    if (!out_info) return EMS_HOST_INVALID_ARGUMENT;
    out_info->version = 0;
    out_info->total_pages = 0;
    out_info->free_pages = 0;
    out_info->page_frame_segment = 0;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_query_pages(uint16_t *out_free, uint16_t *out_total)
{
    if (!out_free || !out_total) return EMS_HOST_INVALID_ARGUMENT;
    *out_free = 0;
    *out_total = 0;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_page_frame(uint16_t *out_segment)
{
    if (!out_segment) return EMS_HOST_INVALID_ARGUMENT;
    *out_segment = 0;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_allocate(uint16_t pages, uint16_t *out_handle)
{
    if (!out_handle || pages == 0) return EMS_HOST_INVALID_ARGUMENT;
    *out_handle = 0;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_map(uint16_t handle, uint16_t logical_page,
                           uint16_t physical_page)
{
    (void)logical_page;
    (void)physical_page;
    if (handle == 0) return EMS_HOST_INVALID_HANDLE;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_free(uint16_t handle)
{
    if (handle == 0) return EMS_HOST_INVALID_HANDLE;
    return EMS_HOST_UNAVAILABLE;
}

EmsHostStatus ems_host_set_name(uint16_t handle, const char *name)
{
    if (handle == 0) return EMS_HOST_INVALID_HANDLE;
    if (!name) return EMS_HOST_INVALID_ARGUMENT;
    return EMS_HOST_UNAVAILABLE;
}
