/* The isolated storage test has no presentation runtime. The complete
 * application's enhanced startup/catalog path is tested by tests/enhanced.
 * Fail if this storage-only executable attempts to decode presentation art. */
#include <stdlib.h>
int enhanced_contracts_enabled(void) { return 0; }
int enhanced_assets_load(const char *root) { (void)root; abort(); }
const char *enhanced_assets_error(void) { abort(); }
