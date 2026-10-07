struct stat { short st_dev, st_ino, st_mode, st_nlink, st_uid, st_gid, st_rdev; long st_size, st_atime, st_mtime, st_ctime; };
int stat(const char *, struct stat *);
#define S_IREAD 0400
#define S_IWRITE 0200
