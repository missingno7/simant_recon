#ifndef SIMANT_WHOLE_PROGRAM_UI_STRING_LISTS_H
#define SIMANT_WHOLE_PROGRAM_UI_STRING_LISTS_H

/* Native owners for the StrList globals assigned by root:m075B::PrepareStrings.
 * Each table is an array of host-width pointers into its live kind-4 resource
 * payload; the allocation itself remains a source Ralloc handle. */
extern char **fd_50F6_046C; /* SHARED kind 4, object 1000 */
extern char **fd_50F6_0324; /* SHARED kind 4, object 1001 */
extern char **fd_50F6_034C; /* SHARED kind 4, object 1010 */
extern char **AdviceStrs;   /* SHARED kind 4, object 1020 */
extern char **fd_50F6_02BA; /* SHARED kind 4, object 1050 */
extern char **fd_50F6_106E; /* SHARED kind 4, object 1100 */
extern char **fd_50F6_1078; /* SHARED kind 4, object 1101 */
extern char **fd_50F6_1086; /* SHARED kind 4, object 1102 */
extern char **fd_50F6_1096; /* SHARED kind 4, object 1103 */
extern char **fd_50F6_10A8; /* SHARED kind 4, object 1200 */
extern char **fd_50F6_10B4; /* SHARED kind 4, object 1210 */
extern char **fd_50F6_020A; /* SHARED kind 4, object 1220 */
extern char **fd_50F6_0218; /* SHARED kind 4, object 1230 */
extern char **fd_50F6_021C; /* SHARED kind 4, object 1240 */
extern char **fd_50F6_0234; /* SHARED kind 4, object 1250 */
extern char **fd_50F6_023A; /* SHARED kind 4, object 1260 */
extern char **fd_50F6_0328; /* SHARED kind 4, object 1900 */
extern char **fd_50F6_0368; /* SHARED kind 4, object 1800 */

/* initStuff assigns *db_LoadObject(1000,9) after source f_0244_0022 has
 * processed the retained startup image payload. This is a borrowed payload
 * pointer; neither the image bytes nor their owning DB handle live here. */
extern char *fd_50F6_0B22;

#endif
