/*
 * Defines far pointer and counter storage used by the allocator and EMS database cache. The
 * fields remain independent objects in this mixed modern bundle.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The definitions are five independent far commons.
 */

/*
 * Allocator EMS-region start, one paragraph after the page-frame segment.
 */
unsigned far mem_ems_arena_start_segment;
/*
 * EMS-backed allocator span in paragraphs, initialized to 0xbf8.
 */
unsigned far mem_ems_arena_paragraphs;
/*
 * Segment threshold separating conventional and EMS allocator blocks.
 */
unsigned far mem_ems_boundary_segment;
/* Both the pointer object and its pointee type are far; the object itself is FAR_BSS. */
/*
 * Allocated DiscardEntry template used by discarded handles.
 */
char far * far mem_discard_entry_template;
/*
 * Mapped 0x4000-byte buffer returned by database EMS reads.
 */
char far * far db_ems_page_buffer;
