#include "portable/whole_program/enhanced/assets.h"
#include "portable/whole_program/enhanced/runtime.h"
#include "desktop_files.h"
#include <SDL3/SDL.h>
#include <windows.h>
#include <wincrypt.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

/* Supported shipped resource identity, not game data. CFG is mutable and is
 * deliberately excluded. The same assets are prerequisites of the port gate. */
static const struct { const char *name, *hash; } resources[] = {
    {"FONT1", "bb9591cc742e39864722b9dab2a7e59c82c1a3804f00da684f8459912c993cc3"},
    {"FONT2", "f5a9f39e46ae7f789ae7b7c5339aff905d2675db8149a1c0c794e33b0f6dedbc"},
    {"FONT3", "56480958990bda60d7f798d1922ae40762261c7453cc9e99c0573e5f7a2286ff"},
    {"FONT4", "0d0ccb62f197213e6ea793913c0b68d194fefeed63d58f6b7e36dbe25347bc15"},
    {"HCEGANT.DAT", "9c98c0f110e901a2c2db65944e4ebdf6b26392181e9415a34eb7b29617eaa899"},
    {"HCEGANT.NDX", "077d8aecdad5e816f0828204f7ca500a68b3a4a3288740ac75e73e44eaa8efc4"},
    {"SHARED.DAT", "aa0d2342510f99abf57a685ea93178d9dd8d2d5be1e65b556c9b27f974012750"},
    {"SHARED.NDX", "e172f030c11f417af4b5be34dacbda9a63f157820827b40d62c08ca2c6ea7477"},
    {"SOUND.DAT", "6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629"},
    {"SOUND.NDX", "4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80"}
};
static int path(char *out, size_t size, const char *root, const char *name)
{
    int n = snprintf(out, size, "%s/%s", root, name);
    return n >= 0 && (size_t)n < size;
}
static int digest(const char *name, char hex[65])
{
    HCRYPTPROV provider = 0;
    HCRYPTHASH hash = 0;
    unsigned char data[16384], result[32];
    DWORD length = sizeof(result);
    size_t n;
    int okay = 0;
    FILE *f = fopen(name, "rb");
    if (!f) return 0;
    if (!CryptAcquireContextA(&provider, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT) ||
        !CryptCreateHash(provider, CALG_SHA_256, 0, 0, &hash)) goto done;
    while ((n = fread(data, 1, sizeof(data), f)))
        if (!CryptHashData(hash, data, (DWORD)n, 0)) goto done;
    if (ferror(f) || !CryptGetHashParam(hash, HP_HASHVAL, result, &length, 0)) goto done;
    for (unsigned i = 0; i < 32; ++i) snprintf(hex + i*2, 3, "%02x", result[i]);
    okay = 1;
done:
    if (hash) CryptDestroyHash(hash);
    if (provider) CryptReleaseContext(provider, 0);
    fclose(f);
    return okay;
}
static int config_safe(const char *name)
{
    FILE *f = fopen(name, "rb");
    unsigned words = 0, length = 0;
    char values[6][30] = {{0}};
    int c, okay = 0;
    if (!f) return 0;
    /* The DOS ReadWord uses a 30-byte local. Reject malformed input before
     * that original parser runs; do not replace its mode selection. */
    while ((c = fgetc(f)) != EOF) {
        if (isspace((unsigned char)c)) {
            if (length) { ++words; length = 0; }
        } else {
            if (words >= 6 || length >= 29) goto done;
            values[words][length++] = (char)c;
        }
    }
    if (length) ++words;
    okay = !ferror(f) && words == 6 && strlen(values[2]) == 1 &&
        strchr("?EHMTVem", values[2][0]) && strlen(values[5]) == 1;
done:
    fclose(f); return okay;
}
int simant_desktop_files(const char *assets, int in_place, const char *user_root,
                         char *volume, size_t capacity, char *error, size_t error_capacity)
{
    char source[2048], destination[2048], hash[65], absolute[2048], root[2048];
    char *pref = NULL;
    const char *bad = assets;
    unsigned i;
    DWORD n = GetFullPathNameA(assets, sizeof(absolute), absolute, NULL);
    if (!n || n >= sizeof(absolute)) goto failed;
    /* Fail before original OpenDB's create-on-open-failure branch can create a
     * replacement for a missing or damaged database. */
    for (i = 0; i < SDL_arraysize(resources); ++i) {
        bad = resources[i].name;
        if (!path(source, sizeof(source), absolute, bad) || !digest(source, hash) ||
            strcmp(hash, resources[i].hash)) goto failed;
    }
    bad = "SIMANT.CFG";
    if (!path(source, sizeof(source), absolute, bad)) goto failed;
    if (!config_safe(source)) goto failed;
    if (enhanced_contracts_enabled() && !enhanced_assets_load(absolute)) {
        bad = enhanced_assets_error(); goto failed;
    }
    if (in_place) {
        if (strlen(absolute) >= capacity) goto failed;
        strcpy(volume, absolute);
        return 1;
    }
    if (!user_root) {
        pref = SDL_GetPrefPath("SimAnt", "SDL3");
        user_root = pref;
    }
    bad = "per-user game directory (check permissions and free disk space)";
    if (!user_root) goto failed;
    /* Each installed resource location has its own saves/config. Stable
     * case-insensitive path identity; unrelated installations cannot collide
     * merely because their executables share a filename. */
    unsigned long long identity = 14695981039346656037ull;
    for (const unsigned char *p = (const unsigned char *)absolute; *p; ++p)
        identity = (identity ^ (unsigned char)tolower(*p == '\\' ? '/' : *p)) * 1099511628211ull;
    snprintf(root, sizeof(root), "%s/games/%016llx", user_root, identity);
    if (strlen(root) >= capacity || !SDL_CreateDirectory(root)) goto failed;
    strcpy(volume, root);
    /* Copy only missing files: an existing config and saves belong to the
     * player. Never truncate or overwrite one during startup. */
    for (i = 0; i <= SDL_arraysize(resources); ++i) {
        const char *name = i == SDL_arraysize(resources) ? "SIMANT.CFG" : resources[i].name;
        bad = name;
        if (!path(source, sizeof(source), absolute, name) ||
            !path(destination, sizeof(destination), root, name)) goto failed;
        if (!CopyFileA(source, destination, TRUE) && GetLastError() != ERROR_FILE_EXISTS) goto failed;
        /* Windows copies the distribution's read-only attribute. Native DOS
         * opens its resource databases read/write, even though it reads them. */
        DWORD attributes = GetFileAttributesA(destination);
        if (attributes == INVALID_FILE_ATTRIBUTES ||
            !SetFileAttributesA(destination, attributes & ~FILE_ATTRIBUTE_READONLY)) goto failed;
        if (i < SDL_arraysize(resources) && (!digest(destination, hash) || strcmp(hash, resources[i].hash))) goto failed;
        if (i == SDL_arraysize(resources) && !config_safe(destination)) goto failed;
    }
    bad = "INSTALL.EXE availability probe";
    if (!path(destination, sizeof(destination), root, "INSTALL.EXE")) goto failed;
    HANDLE probe = CreateFileA(destination, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ, NULL,
                               OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (probe == INVALID_HANDLE_VALUE) goto failed;
    CloseHandle(probe);
    SDL_free(pref);
    return 1;
failed:
    snprintf(error, error_capacity, "Cannot prepare SimAnt files: %s.\nResource folder: %s\n"
        "Check missing/corrupt files, permissions and free disk space. This build supports the shipped English VGA resource set.", bad, assets);
    SDL_free(pref);
    return 0;
}
