import itertools
D = "            DoDigOutR(x, y, attr);\n            break;\n"
OLD_SW_START = "        switch (t) {\n        case 0:"
def partitions(s):
    if not s:
        yield []
        return
    first, rest = s[0], s[1:]
    for p in partitions(rest):
        for i in range(len(p)):
            yield p[:i] + [[first] + p[i]] + p[i + 1:]
        yield [[first]] + p
others = {0: "            DoRandR(x, y, attr, caste);\n            break;\n",
          1: "            DoNestingR(x, y, attr, caste);\n            break;\n",
          3: "            DoFoodInR(x, y, attr);\n            break;\n",
          4: "            DoDigInR(x, y, attr, caste);\n            break;\n",
          8: "            SimEggR(x, y);\n            break;\n",
          9: "            SimQueenR(x, y, caste, attr);\n            break;\n",
          10: "            DoNestFightR(x, y);\n            break;\n",
          13: "            DoRestR(x, y, attr);\n            break;\n",
          14: "            DoRandR(x, y, attr, caste);\n            if (fd_50F6_08E8 > 100)\n                RlistM[Tindex] = 0xf;\n            break;\n",
          17: "            DoDrownR(x, y, attr);\n            break;\n"}
def switch(groups):
    items = [(k, "        case %d:\n" % k + v) for k, v in others.items()]
    for g in groups:
        g = sorted(g)
        items.append((g[0], "".join("        case %d:\n" % l for l in g) + D))
    items.sort()
    return "        switch (t) {\n" + "".join(v for _, v in items) + "        default:\n            DoRandR(x, y, attr, caste);\n            break;\n        }\n"
import re
V = {}
for p in partitions([2, 5, 6, 7, 11, 12]):
    for q in ([[15, 16]], [[15], [16]]):
        name = "_".join("".join("%x" % v for v in sorted(g)) for g in sorted(p + q))
        V[name] = [("SWITCH_RED", switch(p + q))]
