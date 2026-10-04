#include <malloc.h>
#include <stdio.h>

typedef struct heap_list_desc {
    void far *startseg;
    void far *roverseg;
    void far *lastseg;
    unsigned int segflags;
} HeapListDesc;

/* C spelling _fheap decorates to the pinned LLIBCR public __fheap. */
extern HeapListDesc _fheap;

static HeapListDesc heap_snapshots[5];

static void capture_heap(unsigned int slot)
{
    heap_snapshots[slot].startseg = _fheap.startseg;
    heap_snapshots[slot].roverseg = _fheap.roverseg;
    heap_snapshots[slot].lastseg = _fheap.lastseg;
    heap_snapshots[slot].segflags = _fheap.segflags;
}

static void report_heap(char *phase, unsigned int slot)
{
    HeapListDesc far *now = &heap_snapshots[slot];
    HeapListDesc far *entry = &heap_snapshots[0];
    printf("%s flags=%u links=%u%u%u changed=%u\n", phase, now->segflags,
           now->startseg != 0, now->roverseg != 0, now->lastseg != 0,
           now->startseg != entry->startseg || now->roverseg != entry->roverseg ||
           now->lastseg != entry->lastseg || now->segflags != entry->segflags);
}

void far main(void)
{
    void far *near_block;
    void far *far_block;
    void far *resized;
    unsigned frealloc_ok;

    capture_heap(0);
    near_block = malloc(32);
    capture_heap(1);
    free(near_block);
    capture_heap(2);

    far_block = _fmalloc(32);
    capture_heap(3);
    frealloc_ok = 0;
    if (far_block != 0) {
        resized = _frealloc(far_block, 64);
        if (resized != 0) {
            frealloc_ok = 1;
            far_block = resized;
        }
        _ffree(far_block);
    }
    capture_heap(4);

    report_heap("entry", 0);
    report_heap("near-allocated", 1);
    report_heap("near-freed", 2);
    report_heap("far-allocated", 3);
    report_heap("far-freed", 4);
    printf("malloc=%u fmalloc=%u frealloc=%u\n", near_block != 0,
           far_block != 0, frealloc_ok);
}
