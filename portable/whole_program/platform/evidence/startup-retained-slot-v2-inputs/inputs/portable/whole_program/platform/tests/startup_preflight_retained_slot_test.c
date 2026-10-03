#include "../dos_io.h"
#include "../startup_preflight.h"

#include <stdint.h>
#include <stdio.h>

static uint32_t read_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint32_t fnv1a(const uint8_t *p, size_t n)
{
    uint32_t h = 2166136261u;
    size_t i;
    for (i = 0; i < n; ++i) h = (h ^ p[i]) * 16777619u;
    return h;
}

int main(int argc, char **argv)
{
    int16_t closed_slot = -1, opened = -1;
    int16_t data_fd, index_fd;
    uint8_t header[14];
    uint8_t index_header[20];
    uint8_t block[256];
    uint32_t offset, end;

    if (argc != 3) return 2;
    if (dos_startup_preflight(argv[1], &closed_slot, &opened) != 0 ||
        opened != 5 || closed_slot <= 0)
        return 10;

    /* This proves fd_50F6_10D0 is a closed DOS-number slot before any
     * subsequent source database open, not an INSTALL.EXE file identity. */
    if (dos_read(closed_slot, header, 1) != -1 || dos_errno != 9)
        return 11;

    data_fd = dos_open(argv[2], DOS_O_RDWR | DOS_O_BINARY);
    if (data_fd <= 0 || data_fd != closed_slot)
        return 12;
    if (dos_read(data_fd, header, sizeof header) != (int16_t)sizeof header)
        return 13;
    offset = read_le32(header + 6);
    end = (uint32_t)dos_lseek(data_fd, 0, 2);
    if (offset != 95847u || end != 96117u)
        return 14;

    /* OpenDB keeps the .DAT handle; OpenIndex then opens and closes .NDX. */
    {
        static char index_path[] = "assets/SHARED.NDX";
        index_fd = dos_open(index_path, DOS_O_RDWR | DOS_O_BINARY);
    }
    if (index_fd <= 0 || index_fd == data_fd ||
        dos_read(index_fd, index_header, sizeof index_header) !=
            (int16_t)sizeof index_header || dos_close(index_fd) != 0)
        return 15;

    if (dos_lseek(data_fd, (int32_t)(offset + sizeof header), 0) !=
            (int32_t)(offset + sizeof header) ||
        dos_read(data_fd, block, sizeof block) != (int16_t)sizeof block ||
        dos_read(data_fd, header, 1) != 0)
        return 16;
    if (dos_close(data_fd) != 0)
        return 17;
    printf("PASS closed_slot=%d shared_dat_fd=%d header_offset=%u tail_bytes=256 tail_fnv1a=%08x\n",
           closed_slot, data_fd, offset, fnv1a(block, sizeof block));
    return 0;
}
