#include "bios_fonts.h"

PortableBiosFontsStatus portable_bios_font_provider_init(
    PortableBiosFontProvider *provider,
    const uint8_t *font_8x8, size_t font_8x8_size,
    const uint8_t *font_8x14, size_t font_8x14_size,
    const char *provider_id)
{
    if (provider == NULL || provider_id == NULL || provider_id[0] == '\0')
        return PORTABLE_BIOS_FONTS_INVALID_ARGUMENT;
    if (font_8x8 == NULL || font_8x8_size != 256u * 8u ||
        font_8x14 == NULL || font_8x14_size != 256u * 14u)
        return PORTABLE_BIOS_FONTS_SIZE_MISMATCH;
    provider->font_8x8 = (PortableBiosFontBitmap){
        font_8x8, font_8x8_size, 8, 8, provider_id};
    provider->font_8x14 = (PortableBiosFontBitmap){
        font_8x14, font_8x14_size, 8, 14, provider_id};
    return PORTABLE_BIOS_FONTS_OK;
}


#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BIOS_FONT8_BYTES 2048u
#define BIOS_FONT14_BYTES 3584u
#define BIOS_PROVIDER_ID "DOSBox-X/v2026.08.31/C0000-capture-0e5c2f9"
#define BIOS_MANIFEST_SHA256 "1089b9535b8f053739e6ace4111dee062b385b67444cac559adbd8717c2cf20d"
#define BIOS_FONT8_SHA256 "637bb841600ab50977197f81e27092037bc88e7a1a601cffaec286fcd18d9619"
#define BIOS_FONT14_SHA256 "bc20c247736ab20ef8b536a7fd51830cec78b4fa5779064df7349e14803b613d"

static const char default_directory[] =
    "build/bios-reference/dosbox-x-v2026.08.31";

static void set_error(PortableBiosFonts *fonts, const char *message)
{
    if (fonts == NULL) return;
    (void)snprintf(fonts->error, sizeof(fonts->error), "%s",
                   message == NULL ? "" : message);
}

static int hex_value(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static void sha256_transform(uint32_t state[8], const uint8_t block[64]);

/* Small self-contained SHA-256 used only to verify fixed-size generated files. */
static void sha256(const uint8_t *data, size_t size, uint8_t digest[32])
{
    static const uint32_t initial[8] = {
        0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u
    };
    uint32_t state[8];
    uint8_t block[64];
    size_t offset = 0;
    unsigned i;
    uint64_t bit_length = (uint64_t)size * 8u;
    memcpy(state, initial, sizeof(state));
    while (size - offset >= sizeof(block)) {
        sha256_transform(state, data + offset);
        offset += sizeof(block);
    }
    memset(block, 0, sizeof(block));
    if (size != offset) memcpy(block, data + offset, size - offset);
    block[size - offset] = 0x80u;
    if (size - offset >= 56u) {
        sha256_transform(state, block);
        memset(block, 0, sizeof(block));
    }
    for (i = 0; i < 8; ++i)
        block[63u - i] = (uint8_t)(bit_length >> (i * 8u));
    sha256_transform(state, block);
    for (i = 0; i < 8; ++i) {
        digest[i * 4u] = (uint8_t)(state[i] >> 24);
        digest[i * 4u + 1u] = (uint8_t)(state[i] >> 16);
        digest[i * 4u + 2u] = (uint8_t)(state[i] >> 8);
        digest[i * 4u + 3u] = (uint8_t)state[i];
    }
}

static uint32_t rotate_right(uint32_t value, unsigned count)
{
    return (value >> count) | (value << (32u - count));
}

static void sha256_transform(uint32_t state[8], const uint8_t block[64])
{
    static const uint32_t constants[64] = {
        0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
        0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
        0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
        0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
        0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
        0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
        0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
        0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
    };
    uint32_t words[64];
    uint32_t a,b,c,d,e,f,g,h;
    unsigned i;
    for (i = 0; i < 16; ++i) {
        const uint8_t *p = block + i * 4u;
        words[i] = ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
                   ((uint32_t)p[2] << 8) | p[3];
    }
    for (i = 16; i < 64; ++i) {
        uint32_t s0 = rotate_right(words[i-15],7) ^ rotate_right(words[i-15],18) ^ (words[i-15] >> 3);
        uint32_t s1 = rotate_right(words[i-2],17) ^ rotate_right(words[i-2],19) ^ (words[i-2] >> 10);
        words[i] = words[i-16] + s0 + words[i-7] + s1;
    }
    a=state[0]; b=state[1]; c=state[2]; d=state[3];
    e=state[4]; f=state[5]; g=state[6]; h=state[7];
    for (i = 0; i < 64; ++i) {
        uint32_t s1=rotate_right(e,6)^rotate_right(e,11)^rotate_right(e,25);
        uint32_t choice=(e&f)^((~e)&g);
        uint32_t t1=h+s1+choice+constants[i]+words[i];
        uint32_t s0=rotate_right(a,2)^rotate_right(a,13)^rotate_right(a,22);
        uint32_t majority=(a&b)^(a&c)^(b&c);
        uint32_t t2=s0+majority;
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    state[0]+=a; state[1]+=b; state[2]+=c; state[3]+=d;
    state[4]+=e; state[5]+=f; state[6]+=g; state[7]+=h;
}

static int hash_matches(const uint8_t *bytes, size_t size, const char *expected)
{
    uint8_t digest[32];
    unsigned i;
    sha256(bytes, size, digest);
    for (i = 0; i < 32; ++i) {
        int high = hex_value(expected[i * 2u]);
        int low = hex_value(expected[i * 2u + 1u]);
        if (high < 0 || low < 0 || digest[i] != (uint8_t)((high << 4) | low))
            return 0;
    }
    return expected[64] == '\0';
}

static PortableBiosFontsStatus read_exact(const char *path, size_t expected_size,
                                          const char *expected_hash,
                                          uint8_t **out)
{
    FILE *file;
    long length;
    uint8_t *bytes;
    *out = NULL;
    file = fopen(path, "rb");
    if (file == NULL) return PORTABLE_BIOS_FONTS_IO_ERROR;
    if (fseek(file, 0, SEEK_END) != 0 || (length = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0) {
        (void)fclose(file);
        return PORTABLE_BIOS_FONTS_IO_ERROR;
    }
    if ((uint64_t)length != (uint64_t)expected_size) {
        (void)fclose(file);
        return PORTABLE_BIOS_FONTS_SIZE_MISMATCH;
    }
    bytes = (uint8_t *)malloc(expected_size);
    if (bytes == NULL) {
        (void)fclose(file);
        return PORTABLE_BIOS_FONTS_IO_ERROR;
    }
    {
        int read_ok = fread(bytes, 1, expected_size, file) == expected_size;
        int close_ok = fclose(file) == 0;
        if (!read_ok || !close_ok) {
            free(bytes);
            return PORTABLE_BIOS_FONTS_IO_ERROR;
        }
    }
    if (!hash_matches(bytes, expected_size, expected_hash)) {
        free(bytes);
        return PORTABLE_BIOS_FONTS_HASH_MISMATCH;
    }
    *out = bytes;
    return PORTABLE_BIOS_FONTS_OK;
}

static PortableBiosFontsStatus read_manifest(const char *path)
{
    FILE *file = fopen(path, "rb");
    long length;
    uint8_t *bytes;
    int good;
    if (file == NULL) return PORTABLE_BIOS_FONTS_IO_ERROR;
    if (fseek(file, 0, SEEK_END) != 0 || (length = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0 || length <= 0 || length > 65536) {
        (void)fclose(file);
        return PORTABLE_BIOS_FONTS_IO_ERROR;
    }
    bytes = (uint8_t *)malloc((size_t)length);
    if (bytes == NULL) { (void)fclose(file); return PORTABLE_BIOS_FONTS_IO_ERROR; }
    good = fread(bytes, 1, (size_t)length, file) == (size_t)length;
    if (fclose(file) != 0) good = 0;
    if (!good) { free(bytes); return PORTABLE_BIOS_FONTS_IO_ERROR; }
    good = hash_matches(bytes, (size_t)length, BIOS_MANIFEST_SHA256);
    free(bytes);
    return good ? PORTABLE_BIOS_FONTS_OK : PORTABLE_BIOS_FONTS_HASH_MISMATCH;
}

static int make_path(char *out, size_t capacity, const char *directory,
                     const char *filename)
{
    int length = snprintf(out, capacity, "%s/%s", directory, filename);
    return length >= 0 && (size_t)length < capacity;
}

void portable_bios_fonts_free(PortableBiosFonts *fonts)
{
    if (fonts == NULL) return;
    free(fonts->font_8x8);
    free(fonts->font_8x14);
    memset(fonts, 0, sizeof(*fonts));
}

void portable_bios_fonts_init(PortableBiosFonts *fonts)
{
    if (fonts != NULL) memset(fonts, 0, sizeof(*fonts));
}

PortableBiosFontsStatus portable_bios_fonts_load(PortableBiosFonts *fonts,
                                                 const char *directory)
{
    char path[1024];
    PortableBiosFontsStatus status;
    if (fonts == NULL) return PORTABLE_BIOS_FONTS_INVALID_ARGUMENT;
    portable_bios_fonts_free(fonts);
    if (directory == NULL || directory[0] == '\0') directory = default_directory;
    if (!make_path(path, sizeof(path), directory, "manifest.json")) {
        set_error(fonts, "reference directory path is too long");
        return PORTABLE_BIOS_FONTS_INVALID_ARGUMENT;
    }
    status = read_manifest(path);
    if (status != PORTABLE_BIOS_FONTS_OK) {
        set_error(fonts, status == PORTABLE_BIOS_FONTS_HASH_MISMATCH ?
                  "reference manifest does not match the pinned identity" :
                  "cannot read reference manifest");
        return status;
    }
    if (!make_path(path, sizeof(path), directory, "font-8x8.bin")) {
        set_error(fonts, "reference directory path is too long");
        return PORTABLE_BIOS_FONTS_INVALID_ARGUMENT;
    }
    status = read_exact(path, BIOS_FONT8_BYTES, BIOS_FONT8_SHA256, &fonts->font_8x8);
    if (status != PORTABLE_BIOS_FONTS_OK) goto fail;
    if (!make_path(path, sizeof(path), directory, "font-8x14.bin")) {
        status = PORTABLE_BIOS_FONTS_INVALID_ARGUMENT;
        set_error(fonts, "reference directory path is too long");
        goto fail;
    }
    status = read_exact(path, BIOS_FONT14_BYTES, BIOS_FONT14_SHA256, &fonts->font_8x14);
    if (status != PORTABLE_BIOS_FONTS_OK) goto fail;
    fonts->font_8x8_size = BIOS_FONT8_BYTES;
    fonts->font_8x14_size = BIOS_FONT14_BYTES;
    (void)snprintf(fonts->provider_id, sizeof(fonts->provider_id), "%s", BIOS_PROVIDER_ID);
    if (portable_bios_font_provider_init(&fonts->provider,
                                        fonts->font_8x8, fonts->font_8x8_size,
                                        fonts->font_8x14, fonts->font_8x14_size,
                                        fonts->provider_id) != PORTABLE_BIOS_FONTS_OK) {
        status = PORTABLE_BIOS_FONTS_PROVIDER_ERROR;
        set_error(fonts, "font provider rejected verified reference tables");
        goto fail;
    }
    fonts->error[0] = '\0';
    return PORTABLE_BIOS_FONTS_OK;

fail:
    if (fonts->error[0] == '\0') {
        set_error(fonts, status == PORTABLE_BIOS_FONTS_SIZE_MISMATCH ?
                  "reference table has an unexpected byte length" :
                  status == PORTABLE_BIOS_FONTS_HASH_MISMATCH ?
                  "reference table hash does not match the pinned identity" :
                  "cannot read reference table");
    }
    free(fonts->font_8x8); fonts->font_8x8 = NULL; fonts->font_8x8_size = 0;
    free(fonts->font_8x14); fonts->font_8x14 = NULL; fonts->font_8x14_size = 0;
    memset(&fonts->provider, 0, sizeof(fonts->provider));
    fonts->provider_id[0] = '\0';
    return status;
}

const char *portable_bios_fonts_error(const PortableBiosFonts *fonts)
{
    return fonts == NULL ? "invalid BIOS font owner" : fonts->error;
}

const char *portable_bios_fonts_status_string(PortableBiosFontsStatus status)
{
    switch (status) {
    case PORTABLE_BIOS_FONTS_OK: return "ok";
    case PORTABLE_BIOS_FONTS_INVALID_ARGUMENT: return "invalid-argument";
    case PORTABLE_BIOS_FONTS_IO_ERROR: return "io-error";
    case PORTABLE_BIOS_FONTS_SIZE_MISMATCH: return "size-mismatch";
    case PORTABLE_BIOS_FONTS_HASH_MISMATCH: return "hash-mismatch";
    case PORTABLE_BIOS_FONTS_PROVIDER_ERROR: return "provider-error";
    default: return "unknown";
    }
}
