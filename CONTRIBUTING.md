# Contributing to 狛犬 / Komainu

Thanks for helping guard the gate. Komainu is small on purpose — pure Python
stdlib, no build step — so contributing is quick.

## Ground rules

- **The engine never executes inspected code.** Any change that would run,
  import, or `eval` content from a scanned repo will be rejected. Scanners are
  read-only static analysis.
- **Quarantine, never delete.** Sterilization moves things to `_QUARANTINE/`;
  it does not remove user data.
- **Be honest in the docs.** No overclaiming. `SAFE` means "no static threat +
  nothing auto-runs," and the README/threat-model say so.

## Dev loop

```bash
git clone https://github.com/kubouchiyuya/komainu
cd komainu
python3 skills/komainu/bin/komainu selfcheck
sh skills/komainu/tests/smoke.sh      # must stay green
```

Everything is stdlib — if `python3` and `git` run, you're set. `ripgrep` is used
as an optional accelerator with a pure-Python fallback.

## Adding a detection

1. Add the pattern/rule in `skills/komainu/core/scan.py` under the right category.
2. Add a fixture that triggers it under `skills/komainu/fixtures/evil_repo/`.
3. Make sure `sh skills/komainu/tests/smoke.sh` still passes (add an assertion if
   it's a new category).
4. Update `references/threat-model.md` if it's a new class of threat.

## Pull requests

- Keep changes scoped; every changed line should trace to the PR's purpose.
- CI (`ci.yml`) runs the smoke suite — green before review.
- Explain *why*, not just *what*, in the description.

## Attribution

When Komainu imports third-party code, it preserves the source's LICENSE and
attribution. Contributions follow the same spirit.
