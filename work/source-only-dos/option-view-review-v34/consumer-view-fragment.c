/* Explanatory consumer-view fragment only; not a whole TU and not a
 * compilable/admissible module or a search/promote input.
 * The DOS consumers and S09 serializer view this 12-byte range as six ints.
 * The accepted data:3D57 object defines neighboring publics at +2/+6/+8/+10
 * in the same far-data segment; the view has no cross-object order dependency.
 * The extra word at +12 (3D57:07B4) is present/zero; its semantic role is
 * unknown, but its storage is already part of fd_3D57_07B2[4].
 */
extern int far fd_3D57_07A8[6];
