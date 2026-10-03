#include "portable/whole_program/types/database.h"
IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind)
{
    int mid;
    int top;

    fd_50F6_3956 = 0;
    top = fd_50F6_3958[db].indexHeader.count - 1;
    if (top == -1)
        return 0L;
    while (fd_50F6_3956 <= top) {
        mid = (fd_50F6_3956 + top) / 2;
        fd_50F6_3952 = &fd_50F6_3958[db].index[mid];
        if (!(fd_50F6_3952->kind < kind || (fd_50F6_3952->kind == kind && fd_50F6_3952->id < id)))
            top = mid - 1;
        else
            fd_50F6_3956 = mid + 1;
    }
    fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];
    if (fd_50F6_3956 == fd_50F6_3958[db].indexHeader.count) return 0L;
    if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)
        return fd_50F6_3952;
    return 0L;
}
