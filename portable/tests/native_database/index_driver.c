#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/types/database.h"

extern IndexEntry *FindIndex(int16_t db, int16_t id, int16_t kind);

static int read_exact(FILE *f, void *p, size_t n) { return fread(p, 1, n, f) == n; }

int main(int argc, char **argv)
{
    FILE *f;
    uint32_t magic;
    uint16_t datasets;
    unsigned d;
    if (argc != 2 || (f = fopen(argv[1], "rb")) == NULL) return 2;
    if (!read_exact(f, &magic, sizeof magic) || magic != 0x31424457u ||
        !read_exact(f, &datasets, sizeof datasets)) return 3;
    for (d = 0; d < datasets; ++d) {
        int16_t count;
        uint32_t query_count, i;
        uint8_t *wire;
        IndexEntry *entries;
        if (!read_exact(f, &count, sizeof count) || count <= 0) return 4;
        wire = (uint8_t *)malloc(((size_t)count + 1u) * 8u);
        entries = (IndexEntry *)malloc(((size_t)count + 1u) * sizeof *entries);
        if (!wire || !entries ||
            !read_exact(f, wire, ((size_t)count + 1u) * 8u) ||
            !read_exact(f, &query_count, sizeof query_count)) return 5;
        if (sizeof(IndexEntry) != 8 || offsetof(IndexEntry, id) != 4 ||
            offsetof(IndexEntry, kind) != 6 || offsetof(IndexEntry, flags) != 7) return 6;
        memcpy(entries, wire, ((size_t)count + 1u) * 8u);
        if (memcmp(entries, wire, ((size_t)count + 1u) * 8u) != 0) return 6;
        fd_50F6_3958[0].index = entries;
        fd_50F6_3958[0].indexHeader.count = count;
        for (i = 0; i < query_count; ++i) {
            int16_t id, kind;
            IndexEntry *got;
            ptrdiff_t result_rank, home_rank;
            if (!read_exact(f, &id, sizeof id) || !read_exact(f, &kind, sizeof kind)) return 7;
            got = FindIndex(0, id, kind);
            result_rank = got ? got - entries : -1;
            home_rank = fd_50F6_3952 ? fd_50F6_3952 - entries : -1;
            printf("%u,%u,%d,%d,%d,%td,%lld,%d,%u,%u,%td,%lld,%d,%u,%u\n",
                   d, i, fd_50F6_3956, (int)id, (int)kind, result_rank,
                   got ? (long long)(uint32_t)got->offset : -1LL,
                   got ? (int)got->id : -1, got ? (unsigned)got->kind : 0u,
                   got ? (unsigned)got->flags : 0u, home_rank,
                   fd_50F6_3952 ? (long long)(uint32_t)fd_50F6_3952->offset : -1LL,
                   fd_50F6_3952 ? (int)fd_50F6_3952->id : -1,
                   fd_50F6_3952 ? (unsigned)fd_50F6_3952->kind : 0u,
                   fd_50F6_3952 ? (unsigned)fd_50F6_3952->flags : 0u);
        }
        free(entries);
        free(wire);
    }
    if (fgetc(f) != EOF) return 8;
    fclose(f);
    return 0;
}
