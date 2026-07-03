---
name: Bug report
about: Something Komainu got wrong (crash, false positive, missed detection)
title: "[bug] "
labels: bug
---

**What happened**
A clear description. If it's a detection issue, say whether it's a
false positive (flagged something safe) or a false negative (missed a threat).

**Repro**
- Command you ran (e.g. `komainu import <url>` or `komainu scan <dir>`)
- A minimal fixture or snippet that shows it, if possible

**Expected**
What the verdict / behavior should have been.

**Environment**
- OS:
- `python3 --version`:
- Komainu version / commit:

> For a *security* issue (a bypass, or a way to make Komainu execute inspected
> code), please use **Security → Report a vulnerability** instead of a public issue.
