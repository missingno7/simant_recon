#ifndef SIMANT_WHOLE_WILDCARD_H
#define SIMANT_WHOLE_WILDCARD_H
#include <stdint.h>

/* Source consumers use AX only as a found/not-found predicate. The native
 * result normalizes the DOS near-pointer token; it is never a host address. */
int16_t file_wildcard_match(char *pattern, char *name);
int16_t file_wildcard_search(char *pattern, char *name);

#endif
