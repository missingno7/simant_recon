/*
 * Defines the Ralloc manager counters and near pointers to its block lists. The Block type
 * records the header view used by the allocator.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 55B3. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * These are five uninitialized DGROUP objects; the Block type is a view.
 * Their source and storage controls do not establish original placement or
 * translation-unit order. The former relative probe path belonged to scratch.
 */

typedef struct Block {
    int handle;
    long size;
    unsigned paras;
    unsigned char type;
    unsigned char lock;
    long age;
    unsigned next;
    unsigned prev;
    unsigned char attr;
    char name[13];
} Block;

/*
 * Conventional allocator arena length in sixteen-byte paragraphs.
 */
unsigned near mem_conventional_paragraphs;
/*
 * Segment of the first allocator block after reserved metadata.
 */
unsigned near mem_arena_start_segment;
/*
 * Pointer to the first allocator block.
 */
Block far * near mem_arena_first_block;
/*
 * One-past-end pointer bounding allocator arena walks.
 */
Block far * near mem_arena_end_pointer;
/*
 * Current free-list block used as a search starting point.
 */
Block far * near mem_free_list_cursor;
