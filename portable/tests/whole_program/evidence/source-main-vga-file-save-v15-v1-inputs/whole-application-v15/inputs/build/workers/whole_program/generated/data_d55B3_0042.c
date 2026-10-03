#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#pragma pack(push, 2)
/* Version stamp: the first game contribution to DGROUP _DATA (55B3:0042, right after the
   runtime's BEGDATA segment), a file without code.  Its only reference is the far pointer
   fd_55B3_0064 at the start of the next object's _DATA; that pointer's relocation forms a
   target group of its own (an external symbol, not the pointer object's own _DATA), so the
   string is defined in another file.  The text has the shape of "Ver 1.00 " __TIMESTAMP__;
   the file time itself is not reconstructible, so the stamp is spelled out. */
char g_0042[] = "Ver 1.00 Fri Dec 06 14:51:14 1991";

#pragma pack(pop)
