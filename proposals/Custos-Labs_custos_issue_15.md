# Bounty Proposal: Custos-Labs/custos#15 - [Bounty: $85] Add specs for the permission and assignment Prisma adapters\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $85] Add specs for the permission and assignment Prisma adapters

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable — well-scoped request to wire `prisma-permission-repository.ts` and `prisma-user-role-assignment-repository.ts` into `repository-contract.spec.ts` to run existing `permission-repository.contract.ts` / `user-role-assignment-repository.contract.ts` suites plus add expired `expiresAt` filter assertion. Clear files and acceptance criteria provided, but without verified public repo/test access this remains **RAW_RADAR_CANDIDATE** (not yet VERIFIABLE_CODE_ISSUE).

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm analyzing the request, noting the roleplay setup and mandatory invariants. RULE-006 (Financial rounding quantization) seems irrelevant to the core task of adding specs and filters, though it could apply if bounty payouts were being handled. The main task involves analyzing root causes for the Custos-Labs/custos issue, identifying files, and designing an architecture to add permission and assignment Prisma adapters, wire them into repository-contract.spec.ts, and add an expired expiresAt filter assertion.

I'm proceeding without direct codebase access, relying on the file paths provided in the issue. My analysis indicates that while contract suites exist, they aren't being invoked, likely due to a process gap where new adapters are merged without updating the harness or spec files, or the CI check is failing silently. I'll focus on updating `repository-contract.spec.ts` to include factory functions for the Prisma adapters.

I'm considering whether to co-locate adapter-specific spec files or use a shared test fixture for Prisma adapters. The main decision is whether the expired `expiresAt` filtering is a repository contract invariant or an adapter-specific behavior. If it's a contract invariant, it belongs in `repository-contract.spec.ts`; otherwise, it should be in an adapter-level spec. The issue implies adapter-level filtering, so I'll add it to the contract only if it's part of the documented read-path semantics, otherwise, I'll create an adapter-level spec.

I'm realizing the `contributor-checks.yml` check for new repository adapters might be too weak. It seems to only catch new files, not retroactive coverage, which is why the issue was filed. I should strengthen this by making it a coverage manifest, ensuring every `prisma-*-repository.ts` file is referenced by a spec, enforced by a script. For architecture, I'll use a contract test pattern with a `describePermissionRepositoryContract` function, manage Testcontainers lifecycle per-suite or shared, and handle time control for `expiresAt` by injecting a Clock or using boundary-safe offsets to avoid flakiness.

I'm considering how to handle invariants for testing, specifically regarding resource cleanup and schema isolation in parallel tests. For regression avoidance, I'll avoid modifying adapter production code and instead focus on ensuring new tests fail if the adapter is missing functionality, like expired filter handling. I'll also need to ensure CI parity with local testcontainers and clarify PR/boundary notes per RULE-001, distinguishing between PAT and GitHub App usage. RULE-006 is noted as not applicable unless bounty splitting is implemented.

The current status is a candidate for elevation, requiring a checklist to be completed before proceeding. This checklist involves cloning the repository, confirming file existence, running a specific test command, and verifying contract signatures. Until these steps are done, all file paths will adhere strictly to the issue statement.

I'm refining the test strategy for the `expiresAt` filter, focusing on boundary conditions like `expiresAt <= now` and handling null values. I'll inject a clock for time source control to avoid flaky tests, and ensure test isolation by truncating between runs. For regression avoidance, I'll apply the invariant mindset of RULE-006 to resource lifecycle management, ensuring teardown symmetry, and will run the full filter locally to prevent breaking the in-memory adapter.## 1. Classification & Verification Gate (RULE-003)

Status remains **RAW_RADAR_CANDIDATE**. All file paths and contract signatures below are taken from the issue statement, not verified source. Elevation to `VERIFIABLE_CODE_ISSUE` requires:

- [ ] `git clone Custos-Labs/custos` succeeds (public repo confirmed)
- [ ] Both adapter files and both contract files exist at stated paths
- [ ] `pnpm install && pnpm --filter @custos/authorization run test` reproduces green
- [ ] Contract suite signatures confirmed (factory-injection vs. hardcoded adapter)

Per **RULE-001**: cloning/scouting/CI-log reading via GitHub App; the eventual branch push + PR goes through a user PAT, since `custos` is an external public repo.

## 2. Root Cause Analysis

| Layer | Root cause |
|---|---|
| **Structural** | Contract suites are *libraries*, not executable specs. Nothing at compile or runtime forces a new adapter to be wired — registration is manual → guaranteed drift. |
| **Process/CI** | `contributor-checks.yml`'s guard step is almost certainly **diff-scoped**: it fires on adapter files added *in that PR*. It has no retroactive coverage check, so adapters that predated the check (or slipped through a glob gap) are permanently invisible to it. |
| **Test-infra friction** | Prisma adapters need a live Postgres (testcontainers) + migrations + truncation. If no shared bootstrap fixture existed when the adapters landed, writing the spec was high-friction → deferred indefinitely. |

The fix must close all three layers, not just add the two `describe` blocks — otherwise the third unwired adapter is a matter of time.

## 3. Files to Touch

| File | Change | Risk |
|---|---|---|
| `infrastructure/testing/repository-contract.spec.ts` | Add contract invocations for both adapters | Low — additive |
| `infrastructure/testing/prisma-test-harness.ts` *(new, if absent)* | Shared container singleton, `migrate deploy`, `TRUNCATE ... CASCADE` helper | Low |
| `user-role-assignment-repository.contract.ts` | Add expired-`expiresAt` case **only if** expiry filtering is contract-level semantics | **Medium** — see §5 decision rule |
| `scripts/check-repository-contract-coverage.ts` + `contributor-checks.yml` | Replace diff-scoped check with repo-wide manifest check | Low, but touches CI |
| Production adapters | **None** — test-only scope | Contingency in §6 |

## 4. Wiring Design

Assumed contract pattern (verify at elevation gate):

```ts
// repository-contract.spec.ts
describe('PrismaPermissionRepository', () => {
  const harness = usePrismaHarness(); // container + migrate + truncate
  runPermissionRepositoryContract(() =>
    new PrismaPermissionRepository(harness.client));
});

describe('PrismaUserRoleAssignmentRepository', () => {
  const harness = usePrismaHarness();
  runUserRoleAssignmentRepositoryContract(() =>
    new PrismaUserRoleAssignmentRepository(harness.client));
});
```

**Harness invariants (zero-leak, resource analog of RULE-006):** the container is the quantized whole — *all* derived state (rows, sequences, schemas) is derived from and reconciled against it per test. `afterEach` truncates every table the suite touched; `sum(allocations) == gross` means no row survives a test boundary, no container survives the suite. One container per worker (Vitest/Jest `fileParallelism` safe) — never share a schema across parallel spec files.

## 5. The `expiresAt` Assertion — Decision Rule + Bulletproofing

**Where it lives:**
- If `user-role-assignment-repository.contract.ts` documents "read path excludes expired assignments" as adapter-agnostic semantics → add it **to the contract**, so the in-memory adapter is also bound.
- If it's Prisma-specific behavior → adapter-level spec only. *Verify the in-memory adapter passes before adding to the contract* — this is the #1 regression vector in this issue.

**Boundary safety — never use `now - 1ms`:**

```ts
const now = harness.clock.now(); // or Date.now() with wide margins
await seed({ expiresAt: new Date(now.getTime() - 3600_000) }); // clearly expired → excluded
await seed({ expiresAt: null });                               // never expires → included
await seed({ expiresAt: new Date(now.getTime() + 3600_000) }); // future → included
// + boundary case: expiresAt == now → assert documented semantics (<= vs <)
```

Prefer a `Clock` injected into the adapter if it accepts one; if the adapter delegates to DB-side `NOW()`, wide margins eliminate wall-clock flakes. Exactly-`now` behavior must be pinned to the documented comparison operator, not left implicit.

## 6. Regression Avoidance

1. **Contingency pre-commit:** if the new assertion fails because the read path *doesn't actually filter expiry*, that's a production bug surfaced by the test — the PR scope expands to a one-line `where: { OR: [{ expiresAt: null }, { expiresAt: { gt: now } }] }` fix, flagged explicitly in the PR body, not silently bundled.
2. **Contract changes are cross-adapter breaking:** any edit to a `.contract.ts` file runs against *every* wired adapter — run the full `--filter` suite, not just the new describe blocks.
3. **CI parity:** pin the testcontainers image tag; ensure `DATABASE_URL` indirection so local and CI execute identical code paths.
4. **Close the detection gap:** coverage check should be `glob(prisma-*-repository.ts)` minus `grep(specs)` == ∅ — repo-wide, not diff-scoped. This is the durable fix for the structural root cause.

## 7. RULE-006 Applicability

No monetary arithmetic in this change — the $85 bounty is metadata. The invariant **would** trigger if a payout-splitting feature is ever built (quantize gross upfront, derive allocations, `sum(allocations) == gross_quantized`). I've applied its *mindset* here to resource lifecycle accounting instead (§4).

## 8. Definition of Done

- [ ] Both adapters executed by their contract suites (visible in test output, not just present in source)
- [ ] Expired-`expiresAt` assertion green, boundary semantics pinned
- [ ] `pnpm --filter @custos/authorization run test` green locally and under testcontainers
- [ ] Coverage check made repo-wide; in-memory adapter still green if contract was modified
- [ ] Zero production-code changes, unless §6.1 contingency is documented

**Estimated effort:** 4–6h if harness exists; ~10h if building it (which amortizes across all future adapters).

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Title:** `test(authorization): wire Prisma permission & assignment adapters into contract suites + enforce repo-wide contract coverage`

**Repo:** `Custos-Labs/custos` · **Issue:** [Bounty: $85] Add specs for the permission and assignment Prisma adapters
**Author:** Delivery & Quality Verification Lead · **Base:** `main` · **Type:** test-only (+ CI)

---

## 0. Verification Gate — Read This First

**Classification: `RAW_RADAR_CANDIDATE`.** Everything below is derived from the issue text. No file has been cloned or read. Before this proposal is turned into a branch, the following must be executed and the results pasted into the PR body:

| # | Gate | Command | Expected |
|---|---|---|---|
| G1 | Repo public + cloneable | `git clone https://github.com/Custos-Labs/custos` | success |
| G2 | Adapter files exist | `ls **/prisma-*-repository.ts` | 2 files |
| G3 | Contract suites exist | `ls **/*-repository.contract.ts` | ≥2 files |
| G4 | Suite currently green | `pnpm install && pnpm --filter @custos/authorization run test` | pass (baseline) |
| G5 | Contract signatures | read `repository-contract.spec.ts` | factory-injection, not hardcoded |
| G6 | Harness presence | `ls infrastructure/testing/prisma-test-harness.ts` | exists / absent → effort fork |

If G5 shows the suite is **hardcoded** rather than factory-driven, §4 changes shape (see Open Question Q1) and this PR becomes a refactor, not an addition. Stop and re-plan.

**Boundary routing (RULE-001):** clone, scouting, CI-log reads, and any internal mirror pushes go through a **GitHub App**. The external branch push and PR open against `Custos-Labs/custos` go through a **user PAT**. Do not use the App token on the public repo write path.

**Financial (RULE-006):** no monetary arithmetic in scope. The $85 is issue metadata only. Applicability is addressed in §8.

---

## 1. Summary

The permission and assignment Prisma adapters exist in production but are **not executed by any test**. The contract suites that would exercise them are libraries, not specs — nothing forces a new adapter to be wired in. This PR:

1. Adds a shared Prisma test harness (container singleton + migration + derived truncation).
2. Wires both Prisma adapters into their existing contract suites.
3. Adds the missing expired-`expiresAt` filter assertion with pinned boundary semantics.
4. Replaces the diff-scoped contributor check with a **repo-wide coverage manifest** so the next unwired adapter fails CI instead of shipping.

**No production code changes** unless §6.1 contingency fires (documented separately, not silently bundled).

---

## 2. Root Cause Analysis

Three independent layers, all of which must be closed — fixing only layer 1 guarantees a recurrence.

| Layer | Root cause | Evidence to confirm |
|---|---|---|
| **Structural** | `.contract.ts` files are *libraries*. Contract registration is manual, so an adapter can be merged without ever being invoked. Drift is the default state, not an accident. | `repository-contract.spec.ts` imports only in-memory adapters |
| **Process / CI**
\n