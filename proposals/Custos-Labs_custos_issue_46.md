# Bounty Proposal: Custos-Labs/custos#46 - [Bounty: $55] Check that changed source files have matching tests\n\n## Diagnosis

The current job builds two **global** lists and compares them:

```bash
src=$(... | grep -v '\.spec\.ts$')      # any non-spec .ts in diff
tests=$(... | grep '\.spec\.ts$')       # any spec .ts in diff
if [ -n "$src" ] && [ -z "$tests" ]; then warn; fi
```

The predicate is `tests != empty`, so **one** spec anywhere satisfies **all** changed sources. The fix is to make the predicate *per-package*: for each changed source file, look for a changed spec **in the same `packages/<pkg>/`**, and warn per unmatched file. The job must still `exit 0`.

## File to modify

`.github/workflows/contributor-checks.yml` → the `test-coverage` job.

\n