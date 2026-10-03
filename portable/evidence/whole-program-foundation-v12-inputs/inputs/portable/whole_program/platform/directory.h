/* Native provider lifecycle hook for the packed MSC _dos_findfirst API.
 * Representable results use ASCII DOS 8.3 names; wildcard searches skip host
 * long names, while an exact unrepresentable name returns DOS error 206. */
#ifndef SIMANT_WHOLE_DIRECTORY_H
#define SIMANT_WHOLE_DIRECTORY_H

#include "dos_files.h"

/* Close an active search explicitly. Copies of the same find_t share one
 * iterator cookie; closing through any copy invalidates the other copies. */
void dos_findclose(struct find_t *result);

#endif
