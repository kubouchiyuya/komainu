## What & why

<!-- What does this change, and why? Every changed line should trace to this. -->

## Type

- [ ] New / improved detection
- [ ] New adapter or runtime support
- [ ] Bug fix (false positive / false negative / crash)
- [ ] Docs
- [ ] Other

## Checklist

- [ ] `sh skills/komainu/tests/smoke.sh` is green
- [ ] The engine still **never executes** inspected repo code
- [ ] Sterilization still **quarantines, never deletes**
- [ ] New detection has a fixture under `skills/komainu/fixtures/`
- [ ] Docs / threat-model updated if behavior changed
- [ ] No overclaiming — `SAFE` semantics preserved
