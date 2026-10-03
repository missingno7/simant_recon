#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_DATABASE_HOST_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_AUDIO_DATABASE_HOST_H

#include "../../game/resources/database.h"

#include <stddef.h>
#include <stdint.h>

typedef int16_t (*PortableWholeAudioResourceHook)(char **handle,
                                                   int16_t *size,
                                                   int16_t object,
                                                   int16_t kind);

typedef enum PortableWholeAudioDatabaseHostStatus {
    PORTABLE_WHOLE_AUDIO_DBHOST_OK = 0,
    PORTABLE_WHOLE_AUDIO_DBHOST_NOT_BOUND,
    PORTABLE_WHOLE_AUDIO_DBHOST_DB_ERROR,
    PORTABLE_WHOLE_AUDIO_DBHOST_BAD_SIZE,
    PORTABLE_WHOLE_AUDIO_DBHOST_HANDLE_ERROR,
    PORTABLE_WHOLE_AUDIO_DBHOST_KIND5_HOOK_MISSING,
    PORTABLE_WHOLE_AUDIO_DBHOST_HOOK_REJECTED
} PortableWholeAudioDatabaseHostStatus;

typedef struct PortableWholeAudioDatabaseHost {
    PortableDatabase *database; /* Borrowed, stable until unbind. */
    PortableWholeAudioResourceHook resource_hook;
    PortableWholeAudioDatabaseHostStatus status;
    PortableDbStatus last_database_status;
    uint64_t records_loaded;
    uint64_t kind5_hook_calls;
} PortableWholeAudioDatabaseHost;

/* Bind the source m1A53/m0000 SOUND calls to the portable database and native
 * relocatable handles. This service only handles resource ownership/data;
 * it does not select or probe an audio device.
 */
int portable_whole_audio_database_host_bind(PortableWholeAudioDatabaseHost *host,
                                             PortableDatabase *database);
void portable_whole_audio_database_host_unbind(
    PortableWholeAudioDatabaseHost *host);

PortableWholeAudioDatabaseHostStatus portable_whole_audio_database_host_status(
    const PortableWholeAudioDatabaseHost *host);

/* Source service symbols implemented by this host boundary. The loader
 * deliberately has no cache: db_UnhookObject therefore has no cached entry
 * to remove, and independently loaded handles retain normal handle-manager
 * lifetime/type semantics.
 */
char **f_1A53_00BA(int16_t object, int16_t kind);
void f_19A9_000B(PortableWholeAudioResourceHook hook);
void db_ReleaseHandle(char **handle);
void db_UnhookObject(int16_t object, int16_t kind);

/* Source m0000 reads the big-endian words in SOUND kind-18 headers through
 * this one-word helper. */
uint16_t f_1959_0002(uint16_t value);

#endif
