/* root:m2662's source-selected current animation object. This is a native
 * heap pointer, never a serialized resource field. AddAnimObject assigns it
 * before ChangeAnimObject reads it. The record stays owned by source 2662. */
struct AnimObj;
struct AnimObj *fd_50F6_4A42;
