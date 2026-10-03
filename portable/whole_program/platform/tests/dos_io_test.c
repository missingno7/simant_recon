#include "../dos_io.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#undef assert
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "check failed: %s (%s:%d)\n", #condition, __FILE__, __LINE__); \
        exit(2); \
    } \
} while (0)

static void expect_bytes(const char *path, const unsigned char *want, size_t n)
{
    FILE *f = fopen(path, "rb");
    unsigned char got[128];
    assert(f != NULL && n <= sizeof got);
    assert(fread(got, 1, n, f) == n);
    assert(memcmp(got, want, n) == 0);
    {
        int extra = fgetc(f);
        if (extra != EOF) {
            fprintf(stderr, "%s: unexpected trailing byte 0x%02x after %lu expected bytes\n",
                    path, (unsigned)extra, (unsigned long)n);
            exit(3);
        }
    }
    fclose(f);
}

int main(int argc, char **argv)
{
    static const unsigned char raw[] = {'A', '\r', '\n', 'B', 0x1a, 'C'};
    static const unsigned char append_want[] = {'o','n','e','t','w','o'};
    char pathbuf[512];
    char *allocated_cwd;
    unsigned char buf[32];
    unsigned font_index;
    int16_t fd;
    int n;
    assert(argc == 10);
    assert(dos_files_set_root(argv[1]) == 0);
    assert(dos_errno == 0);

    fd = dos_open("MiXeD.DAT", (int16_t)0x8101, 0x0180);
    assert(fd >= 3);
    assert(dos_write(fd, (void *)raw, (uint16_t)sizeof raw) == (int16_t)sizeof raw);
    assert(dos_close(fd) == 0);
    expect_bytes("MiXeD.DAT", raw, sizeof raw);

    /* Case-insensitive file lookup and explicit DOS binary mode retain CR/LF/Ctrl-Z. */
    assert(dos_access("mixed.dat", 0) == 0);
    fd = dos_open("mixed.dat", (int16_t)0x8000);
    assert(fd >= 3);
    n = dos_read(fd, buf, sizeof buf);
    assert(n == (int)sizeof raw && memcmp(buf, raw, sizeof raw) == 0);
    assert(dos_read(fd, buf, sizeof buf) == 0);
    assert(dos_close(fd) == 0);

    /* MSC's default text mode translates CRLF and treats Ctrl-Z as EOF on Win32. */
    dos_fmode = DOS_O_TEXT;
    fd = dos_open("MiXeD.DAT", 0);
    assert(fd >= 3);
    n = dos_read(fd, buf, sizeof buf);
    assert(n == 3 && memcmp(buf, "A\nB", 3) == 0);
    assert(dos_read(fd, buf, sizeof buf) == 0);
    assert(dos_close(fd) == 0);

    /* 0x8102 is binary read/write + create without truncate. */
    fd = dos_open("MIXED.dat", (int16_t)0x8102, 0x0180);
    assert(fd >= 3);
    assert(dos_read(fd, buf, 1) == 1 && buf[0] == 'A');
    assert(dos_close(fd) == 0);
    expect_bytes("mixed.dat", raw, sizeof raw);

    /* 0x8302 requests binary read/write, create and truncate. */
    fd = dos_open("MiXeD.DAT", (int16_t)0x8302, 0x0180);
    assert(fd >= 3);
    assert(dos_write(fd, "x", 1) == 1);
    assert(dos_close(fd) == 0);
    expect_bytes("mixed.dat", (const unsigned char *)"x", 1);

    fd = dos_open("append.bin", (int16_t)0x0109, 0x0180);
    assert(fd >= 3 && dos_write(fd, "one", 3) == 3 && dos_close(fd) == 0);
    fd = dos_open("append.bin", (int16_t)0x0109, 0x0180);
    assert(fd >= 3 && dos_write(fd, "two", 3) == 3 && dos_close(fd) == 0);
    expect_bytes("append.bin", append_want, sizeof append_want);

    fd = dos_open("seek.bin", (int16_t)0x8102, 0x0180);
    assert(fd >= 3 && dos_write(fd, "012345", 6) == 6);
    assert(dos_lseek(fd, 2, 0) == 2);
    assert(dos_read(fd, buf, 2) == 2 && memcmp(buf, "23", 2) == 0);
    assert(dos_lseek(fd, -1, 2) == 5);
    assert(dos_write(fd, "X", 1) == 1);
    assert(dos_close(fd) == 0);
    expect_bytes("seek.bin", (const unsigned char *)"01234X", 6);

    fd = dos_open("SubDir/child", (int16_t)0x8101, 0x0180);
    assert(fd >= 3 && dos_close(fd) == 0);
    assert(dos_chdir("subdir") == 0);
    assert(dos_getcwd(pathbuf, sizeof pathbuf) == pathbuf);
    assert(strstr(pathbuf, "SubDir") != NULL || strstr(pathbuf, "subdir") != NULL);
    allocated_cwd = dos_getcwd(NULL, 0);
    assert(allocated_cwd != NULL &&
           (strstr(allocated_cwd, "SubDir") != NULL || strstr(allocated_cwd, "subdir") != NULL));
    free(allocated_cwd);
    assert(dos_chdir("..") == 0);
    assert(dos_remove("SUBDIR/CHILD") == 0);

    assert(dos_stricmp("MSMOUSE", "msmouse") == 0);
    assert(dos_stricmp("a", "B") < 0);
    assert(dos_stricmp("B", "a") > 0);

    assert(dos_open("absent.dat", (int16_t)0x8000) == -1 && dos_errno == 2);
    assert(dos_read(0, buf, 1) == -1 && dos_errno == 9);
    assert(dos_open("badflags", 3) == -1 && dos_errno == 22);
    fd = dos_open("seek.bin", (int16_t)0x8000);
    assert(fd >= 3);
    assert(dos_lseek(fd, 0, 3) == -1 && dos_errno == 22);
    assert(dos_close(fd) == 0);
    assert(dos_close(fd) == -1 && dos_errno == 9);
    assert(dos_remove("missing.file") == -1 && dos_errno == 2);
    dos_files_close_all();

    /* DosFileStream is opaque to the port: DOS fread takes 16-bit size/count
     * and returns a 16-bit item count; host FILE stays inside the wrapper. */
    for (font_index = 0; font_index < 4; ++font_index) {
        const unsigned arg_path = 2 + font_index * 2;
        char lower_path[1024];
        size_t path_len = strlen(argv[arg_path]);
        size_t path_pos;
        DosFileStream *stream;
        uint16_t words[13];
        unsigned char chunk[1024];
        unsigned long total;
        unsigned expected_size;
        int got;
        assert(path_len < sizeof lower_path);
        for (path_pos = 0; path_pos <= path_len; ++path_pos) {
            unsigned char ch = (unsigned char)argv[arg_path][path_pos];
            lower_path[path_pos] = (char)(ch >= 'A' && ch <= 'Z' ? ch + ('a' - 'A') : ch);
        }
        stream = dos_fopen(lower_path, "rb");
        assert(stream != NULL);
        assert(dos_fread(words, 2, 13, stream) == 13);
        total = sizeof words;
        expected_size = (unsigned)strtoul(argv[arg_path + 1], NULL, 10);
        while ((got = dos_fread(chunk, 1, sizeof chunk, stream)) > 0)
            total += (unsigned)got;
        assert(total == expected_size);
        assert(dos_fclose(stream) == 0);
    }

    puts("DOS I/O native contract tests: PASS");
    return 0;
}
