# Bounty Proposal: Custos-Labs/custos#48 - [Bounty: $70] Restore a coverage gate for `@custos/authorization`\n\n## Implementation

### 1. `.github/workflows/ci.yml` — add the gate

Insert into `jobs.ci.steps`, adjacent to the existing coverage gates (identity/credentials/audit/sessions), after install + any workspace `build` step:

```diff
       - name: Sessions coverage gate
         run: pnpm --filter @custos/sessions run test:coverage
+
+      - name: Authorization coverage gate
+        run: pnpm --filter @custos/authorization run test:coverage
```

Mirror the exact naming/style of the sibling steps — reviewers will diff against them.

### 2. `packages/authorization/package.json` — verify only

Confirm the script exists; if absent, copy the sibling packages' exact form (usually):

```json
"test:coverage": "vitest run --coverage"
```

`vitest run` (not `vitest`) so it exits in CI rather than watching.

### 3. `packages/authorization/vitest.config.ts` — do **not** touch unless upstream landed

JS object literals silently take last-key-wins, so the lower duplicate values are the *effective* floor today.

- If the separate dedup issue merged before you → rebase, the gate now enforces the corrected (higher) thresholds; verify coverage still passes.
- If not merged → leave the file alone. Fixing it here would raise the floor and risk violating "gate passes on the current tree." Deleting a spec satisfies acceptance #3 regardless of which values are effective.

If you do end up owning the dedup: drop the second occurrence of each duplicated key, keeping the values consistent with sibling packages' floor.

### 4. Verification

```bash
pnpm install
pnpm --filter @custos/authorization run test:coverage   # must exit 0 on current tree
```

Negative test for acceptance #3 — locally, don't commit:

```bash
# Option A: remove the spec covering the highest-line module (RBAC/ABAC decision spec)
mv packages/authorization/src/decision.spec.ts /tmp/
pnpm --filter @custos/authorization run test:coverage   # expect: non-zero + "does not meet threshold"
mv /tmp/decision.spec.ts packages/authorization/src/

# Option B (no file mutation, proves thresholds are evaluated):
pnpm --filter @custos/authorization exec vitest run --coverage --coverage.thresholds.lines=100
```

### Edge cases

- **`--filter` name** must equal `name` in `packages/authorization/package.json` exactly (`@custos/authorization`).
- **Step ordering**: if vitest resolves `@custos/*` workspace deps as built artifacts, the gate needs the repo's `build` step first — placing it next to the other gates handles this either way.
- **No `continue-on-error: true`** at job or step level — the gate must hard-fail.
- **Affected-only CI**: if the workflow filters by changed packages (turbo/`--filter ...[origin/main]`), ensure this step runs unconditionally — the issue requires it in the `ci` job.
- **Duplicate-key detection**: if CI type-checks configs (`tsc --noEmit`), literal duplicate keys already fail (TS1117). If the tree is green, the dupes are in non-literal positions (spreads/merge) — `grep -n "thresholds\|lines\|branches" packages/authorization/vitest.config.ts` before assuming.
- **Evidence in PR body**: paste the `test:coverage` summary table showing coverage ≥ effective thresholds — that's acceptance #2.

### Submission notes

- Single-commit PR: `ci.yml` (+ `package.json` only if script absent). Suggested label `ci` applies.
- Bounty hygiene: $70 ≥ $25 floor — clears payout gate. External PR push via authenticated user PAT per operating rules; App used only for clone/scout.

I can't see the repo tree from here — verify the sibling gate step names and whether `build` precedes them before opening the PR.\n