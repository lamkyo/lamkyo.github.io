# Bounty Proposal: Custos-Labs/custos#47 - [Bounty: $70] Restore a coverage gate for `@custos/mfa`\n\n## Classification

**VERIFIABLE_CODE_ISSUE** — public repo (`Custos-Labs/custos`), reproducible test suite (`vitest`), deterministic acceptance criteria. Payout $70 > $25 floor; no scam keywords. Proceed.

---

## Files to modify

1. `.github/workflows/ci.yml` — add the gate step (only change required to satisfy acceptance).
2. `packages/mfa/package.json` — verify (may need a fix) that `test:coverage` exists and coverage provider is a devDependency.
3. `packages/mfa/vitest.config.ts` — verify thresholds exist (fix only if missing).

---

## 1. The CI change (surgical diff)

Insert **immediately after the existing `audit` gate step** in the `ci` job, matching the surrounding comment style verbatim:

```diff
       - name: Audit coverage gate
         # Phase 02 coverage-gate pattern
         run: pnpm --filter @custos/audit run test:coverage
 
+      - name: MFA coverage gate
+        # Phase 02 coverage-gate pattern
+        run: pnpm --filter @custos/mfa run test:coverage
+
       # ... next step unchanged
```

Rationale for placement: the four existing gates are ordered by package, and `mfa` is the last package released from quarantine (per `docs/QUARANTINE.md`), so it belongs at the tail of the gate block. Do **not** reorder existing gates — keeps the diff reviewable and avoids merge conflicts.

---

## 2. Verify the gate actually exists and fails

The CI step is only meaningful if the underlying script enforces the floor. Check `packages/mfa/package.json`:

```json
{
  "name": "@custos/mfa",
  "scripts": {
    "test:coverage": "vitest run --coverage"
  },
  "devDependencies": {
    "@vitest/coverage-v8": "..."
  }
}
```

And `packages/mfa/vitest.config.ts` must define thresholds, e.g.:

```ts
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json', 'html'],
    thresholds: {
      statements: 95,   // matches QUARANTINE.md claim
      branches: 90,
      functions: 95,
      lines: 95,
    },
  },
},
```

If `thresholds` is absent, `vitest run --coverage` will **exit 0 regardless of coverage**, and the acceptance criterion "dropping a test that crosses the package floor fails the `ci` job" would be silently unmet. That is the highest-risk failure mode here.

---

## 3. Verification (run before opening the PR)

```bash
# Gate passes on current tree
pnpm --filter @custos/mfa run test:coverage

# Gate FAILS when a test is dropped below the floor
git stash list   # ensure clean baseline
mv packages/mfa/src/<some>.test.ts /tmp/  # temporarily remove a test file
pnpm --filter @custos/mfa run test:coverage; echo "exit=$?"   # expect non-zero
mv /tmp/<some>.test.ts packages/mfa/src/                       # restore
```

Record both outputs (pass + induced failure) in the PR description — this is the evidence the reviewer will look for, and it directly demonstrates acceptance criteria 2 and 3.

---

## Edge cases handled

- **Filter name mismatch**: `pnpm --filter` resolves against `name` in `package.json`, not the directory. Confirm it is exactly `@custos/mfa`.
- **Workspace membership**: ensure `packages/mfa` is matched by `pnpm-workspace.yaml` (`packages/*`). If the package isn't in the workspace, `--filter` errors out and fails CI for the wrong reason.
- **Coverage provider not installed**: `vitest --coverage` throws "Missing dependency @vitest/coverage-v8" → CI fails spuriously. Add it to the package's devDependencies if absent.
- **Install ordering**: the gate must run after the job's `pnpm install --frozen-lockfile` step; if the new step is inserted before install, it will fail on a missing `node_modules`. Insert it in the existing post-install gate block.
- **`run` keyword**: keep `run test:coverage` (matches sibling gates); `pnpm --filter @custos/mfa test:coverage` also works but diverges from house style.

---

## PR checklist

- [ ] One step added to `ci` job; comment matches `# Phase 02 coverage-gate pattern`.
- [ ] `test:coverage` script + thresholds confirmed present (or added).
- [ ] Local pass + induced-failure transcript included.
- [ ] Label: `ci`. Branch `ci/mfa-coverage-gate`. No other packages touched.

This is a ~3-line diff; the real work is the verification transcript proving the floor is enforced.\n