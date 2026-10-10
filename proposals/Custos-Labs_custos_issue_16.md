# Bounty Proposal: Custos-Labs/custos#16 - [Bounty: $60] Test `seedDefaultRoles`\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $60] Test `seedDefaultRoles`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is a well-scoped, actionable testing task with clear acceptance criteria: add a spec file verifying that `seed-default-roles.ts` creates roles with `isSystemRole: true` and is idempotent on re-runs. The work is codeable as it targets a specific module with defined behavior and requires only standard test infrastructure.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm tasked with analyzing a GitHub issue for `Custos-Labs/custos`, specifically a bounty on testing `seedDefaultRoles`. However, my instructions state I couldn't identify any relevant codebase context for this question. This creates a conflict: I need to design an architecture for a specific repo task, but I can't inspect the actual files. I'll proceed by providing a general architectural strategy based on the issue's text, while being transparent about my inability to access the repository directly.

The "mandatory invariants" seem to be persona-based rules, with only RULE-003 tangentially relevant to classifying code issues. RULE-001 and RULE-006 are not applicable to my current design task. I need to focus on providing a concise architectural analysis for writing the spec, grounded in the issue's details, and clearly state my assumptions and verification points since I cannot access the actual repository code.

I need to consider potential risks like duplicate roles or unrecoverable system roles if the seeding process isn't idempotent or doesn't enforce system role creation. My plan involves creating a new spec file next to the seed module, and I'll need to check how other tests in the package handle database connections and configuration to ensure the new spec integrates correctly. I also need to verify that the test runner picks up the new spec file and that the package's test script includes it.

I'm weighing the trade-offs between unit and integration tests for verifying idempotency. While mocking Prisma could work, it risks masking real-world database behavior differences between SQLite and Postgres. An integration test using a real database, if the project's infrastructure supports it, would be more reliable for confirming the "exactly one row per role" invariant. If not, a robust mock simulating unique constraint behavior is the next best option. I also need to determine the specific mechanism the seed uses for idempotency, such as `upsert`, `createMany`, or a find-then-create pattern, as this affects how it should be tested.

I'm re-evaluating the permission re-granting logic based on the issue's "not re-grant" phrasing. It seems the test should verify that re-running the seed doesn't overwrite manual revocations, meaning the update path should ideally be a no-op or preserve existing state. I need to check the implementation to confirm the exact expected behavior, as tests should reflect declared semantics, not just observed implementation details. For test isolation, I'll ensure each test resets the database state, either via `beforeEach` truncation or transaction rollbacks, and that tests run against a dedicated test database, not the development seed.

I'm realizing that simply counting rows isn't enough to prove idempotency; a delete-and-recreate operation would yield the same count. I need to assert that the row *identity* (specifically the `id`) remains stable across runs, not just the total number of rows. Also, comparing permission sets requires normalizing and sorting them first to avoid order-dependent test failures.

I'm considering how to handle permission catalogue drift. Importing the catalogue directly into the spec makes it tautological, so I'll import it for structure but add pinned assertions for critical roles to catch accidental edits. I also need to decide between `connect` and `set` for many-to-many relations, as their re-run behavior differs, and ensure parallel test files don't conflict by using unique role keys or per-worker schemas. Finally, I'll avoid asserting on timestamps except for monotonicity and ensure Prisma client generation happens after `prisma generate`/`migrate` in CI.

I need to ensure the CI environment provisions a database for the `@custos/authorization` package's tests, as the `pnpm --filter @custos/authorization run test` command must pass. If the current tests are unit-only, I must either add a database service to the GitHub Actions workflow or classify the new database-bound spec as an integration test. The most significant regression risk is a test failing in CI due to a missing Postgres service, so I'll confirm the CI setup or reuse the repository's existing integration test runner configuration.

I need to briefly mention RULE-003, classifying this as a VERIFIABLE_CODE_ISSUE since the repo is public and the issue describes acceptance criteria and a runnable test command. RULE-001 and RULE-006 are not applicable here. I'll add a short classification line to honor the persona's demand for adherence to these rules. Since I can't inspect the actual `custos` repo files, I must caveat that my analysis is based on the issue's described structure and needs verification against the real module. The response format will be a structured design doc with headers and bullets, including a classification line, root cause, files to touch, test architecture with invariants, hazard list, and execution plan, possibly with a compact code skeleton.

The length of the response needs to be balanced: detailed enough for the user's request for "deep, invariant-safe architecture," but concise to avoid bloat. I'll aim for around 500-700 words and include a code skeleton.## Classification & Access Note

Per **[RULE-003]**: this item classifies as **VERIFIABLE_CODE_ISSUE** *conditional on repo access* — the issue defines reproducible acceptance criteria (`pnpm --filter @custos/authorization run test`) and a concrete module. Caveat: I can't see `Custos-Labs/custos`'s actual internals from here, so treat every path/mechanism below as an assumption to verify against the real code before implementing. RULE-001 and RULE-006 are non-applicable (no external writes, no financial math).

## Root Cause

Not a code bug — a **verification gap**: `seed-default-roles.ts` encodes a security invariant (administrative recoverability via `isSystemRole`) and an operational invariant (idempotent re-runs), but neither is enforced by a test. Any refactor of the seed can silently break recoverability or introduce duplicate/re-grant behavior.

## Files to Touch

| File | Action |
|---|---|
| `packages/authorization/infrastructure/seed/seed-default-roles.spec.ts` | **Create** (colocated per AC1; match repo's `.spec`/`.test` convention) |
| `seed-default-roles.ts` | Read-only unless the spec exposes a real idempotency defect |
| `packages/authorization/package.json` / vitest-jest config | Verify only — test glob must pick up colocated specs |
| CI workflow / test harness | Verify only — the spec needs whatever DB provisioning `tests/integration/seed.spec.ts` already uses |

## Architectural Strategy

**1. Determine the idempotency mechanism first.** Read the module and classify:
- `upsert` on unique role key → strong idempotency
- `createMany({ skipDuplicates: true })` → row-level idempotent, permission grants may differ
- `findFirst` + `create` → works but TOCTOU-fragile
- Permission wiring: `connect` (additive, may re-grant revocations) vs `set` (declarative, clobbers manual changes)

The spec must encode the *declared* semantics — don't assert "no re-grant" unless the implementation guarantees it.

**2. Prefer a real test database over a Prisma mock.** AC2 ("exactly one row per role") is a DB-level property; a mocked client can fake idempotency the real impl lacks. Reuse the harness behind `tests/integration/seed.spec.ts`.

**3. Spec structure:**

```typescript
describe('seedDefaultRoles', () => {
  beforeEach(/* truncate rolePermission → roles in FK-safe order */);

  it('creates every catalogue role with isSystemRole: true');
  it('assigns each role its declared permission set'); // compare sorted arrays
  it('is idempotent: second run preserves count AND row ids');
  it('does not re-grant revoked permissions', /* only if seed semantics allow */);

  afterAll(/* disconnect prisma */);
});
```

**Critical assertion detail for AC2:** row *count* alone does not prove idempotency — a delete+recreate also yields one row. Snapshot the `(roleKey → id)` map after run 1 and assert **identity stability** after run 2.

**4. Catalogue-coupling invariant.** Import the role/permission catalogue constant the seed consumes rather than duplicating a literal list (prevents spec rot on catalogue additions). To avoid a tautological test, add **a few pinned assertions** on high-value roles — e.g., the super-admin role's permission count equals the full permission catalogue, or a named critical permission is present — so accidental catalogue edits still fail.

## Regression Hazards

1. **CI DB provisioning** — biggest risk. If `@custos/authorization`'s `test` script currently runs unit-only with no Postgres service in CI, a DB-bound spec breaks the pipeline. Confirm the integration-test job's setup and run the spec under it.
2. **Test pollution** — truncate in FK order (`rolePermission` before `roles`); system-role delete guards may block naive deletes.
3. **Order-sensitivity flakes** — always sort permission sets before `toEqual`.
4. **Concurrency** — if DB-touching specs run in parallel workers, isolate via per-worker schema or serialize this file.
5. **Scope discipline** — if the spec surfaces a real defect (e.g., `connect` re-grants on re-run), fix in a **separate commit** within the PR and flag it in the description; the bounty scope is the spec, but a silently-failing seed shouldn't ship.

## Execution Order

1. Read seed module + locate catalogue constant + inspect `tests/integration/seed.spec.ts` harness.
2. Confirm test glob + CI DB provisioning for the package.
3. Write spec against imported catalogue; run `pnpm --filter @custos/authorization run test`.
4. If green → ship. If red → determine defect vs wrong assumption; separate commit, note in PR.

If you can share the actual `seed-default-roles.ts` contents or confirm the repo's test harness pattern, I'll tighten steps 1–2 into concrete assertions.

---

## 3. Production Code Patch (`swe-2`)
I need to generate a spec file and a git diff for the `seed-default-roles.ts` file within the `@custos/authorization` package. Since I don't have direct access to the repository's contents, I'll base the spec on common patterns for Prisma-based seeding scripts in NestJS monorepos, assuming a structure like `seedDefaultRoles(prisma: PrismaClient)` and a `DEFAULT_ROLES` constant. I'll clearly mark placeholders for import paths, function signatures, and Prisma client accessors that will need adjustment based on the actual implementation.

I'm assuming vitest or jest for the test framework, but will write the spec using common `describe/it/beforeEach/afterAll/expect` syntax to be framework-agnostic. I'll also note that I cannot run the sandbox verification locally, so I'll label the patch as "Ready for egress pending local `pnpm test` run" to comply with RULE-002. I'm carefully drafting the spec with correct TypeScript and Prisma syntax, and will add a comment about the import path for `DEFAULT_ROLES`.

I'm testing the `seedDefaultRoles` function, verifying that it creates all roles as system roles, assigns the correct permissions, handles idempotency by ensuring existing roles aren't duplicated or re-assigned different IDs, and doesn't re-grant revoked permissions. I've noted a potential ambiguity in model naming (`rolePermission` vs. `permissionsOnRoles`) and will add adaptation notes for that.

I'm reconsidering the `upsert` logic for permissions. If `seed` uses `update: { permissions: { set: ... } }`, it would re-grant permissions, contradicting the requirement not to re-grant. I'll include the test but add a conditional comment: "keep this test only if seed's update path is a no-op on permissions; delete otherwise." This aligns with the "not re-grant" phrasing from earlier. I'm also adding a pinned assertion for catalogue rot, ensuring a super-admin role exists and has permissions, and will test for duplicate `rolePermission` rows. The output format will be a git diff and instructions, including verification commands and a `PENDING_SYNTAX_CHECK` status since I can't run the sandbox.## Pre-egress status

Per **[RULE-002]**: this patch is marked **PENDING_SANDBOX_CHECK** — I cannot execute `tsc`/`vitest` from here, and I cannot see the real module internals. Do not mark READY_FOR_EGRESS until the commands in §Verification pass locally.

## Integration points to verify before applying

The diff assumes the most common shape for this module. Check each against the real file and adjust:

| Assumed symbol | Verify in `seed-default-roles.ts` |
|---|---|
| `seedDefaultRoles(prisma)` exported as a plain async fn | Could be a Nest `SeedService.seedDefaultRoles()` — if so, instantiate via `Test.createTestingModule` or call the class directly |
| `DEFAULT_ROLES` catalogue importable from sibling constants file | Could be inlined or named `defaultRoles`/`SYSTEM_ROLES` |
| Models `role`, `rolePermission`, `permission`; role unique key field `key` | Check `schema.prisma` — may be `name`, `slug`, or `Role.permissions` as a direct m-n |
| `isSystemRole` boolean on `role` | Per the issue's stated invariant |
| Vitest-style globals (`describe/it/expect`) | If Jest, swap `vi`→`jest` only where used (none here); globals are compatible |

## Patch

```diff
diff --git a/packages/authorization/infrastructure/seed/seed-default-roles.spec.ts b/packages/authorization/infrastructure/seed/seed-default-roles.spec.ts
new file mode 100644
index 0000000..9f2c4a1
--- /dev/null
+++ b/packages/authorization/infrastructure/seed/seed-default-roles.spec.ts
@@ -0,0 +1,124 @@
+import { PrismaClient } from '@prisma/client';
+import { seedDefaultRoles } from './seed-default-roles';
+// VERIFY: adjust to the real catalogue export/path the seed consumes.
+import { DEFAULT_ROLES } from './default-roles.constants';
+
+describe('seedDefaultRoles', () => {
+  let prisma: PrismaClient;
+
+  const truncate = async () => {
+    // FK-safe order: join table before parents.
+    await prisma.rolePermission.deleteMany({});
+    await prisma.role.deleteMany({});
+    await prisma.permission.deleteMany({});
+  };
+
+  const rolePermissionKeys = async (roleKey: string): Promise<string[]> => {
+    const role = await prisma.role.findUniqueOrThrow({
+      where: { key: roleKey },
+      include: { permissions: { include: { permission: true } } },
+    });
+    return role.permissions.map((rp) => rp.permission.key).sort();
+  };
+
+  beforeAll(async () => {
+    prisma = new PrismaClient();
+    await prisma.$connect();
+  });
+
+  beforeEach(truncate);
+
+  afterAll(async () => {
+    await truncate();
+    await prisma.$disconnect();
+  });
+
+  it('creates every catalogue role flagged as a system role', async () => {
+    await seedDefaultRoles(prisma);
+
+    const roles = await prisma.role.findMany();
+    expect(roles).toHaveLength(DEFAULT_ROLES.length);
+    for (const role of roles) {
+      expect(role.isSystemRole).toBe(true);
+    }
+
+    const keys = roles.map((r) => r.key).sort();
+    expect(keys).toEqual(DEFAULT_ROLES.map((r) => r.key).sort());
+  });
+
+  it('assigns each role exactly its declared permission set', async () => {
+    await seedDefaultRoles(prisma);
+
+    for (const expected of DEFAULT_ROLES) {
+      const actual = await rolePermissionKeys(expected.key);
+      expect(actual).toEqual([...expected.permissions].sort());
+    }
+
+    // No stray join rows beyond the declared catalogue.
+    const expectedJoinCount = DEFAULT_ROLES.reduce(
+      (n, r) => n + r.permissions.length,
+      0,
+    );
+    expect(await prisma.rolePermission.count()).toBe(expectedJoinCount);
+  });
+
+  it('is idempotent: re-run preserves row count AND row identity', async () => {
+    await seedDefaultRoles(prisma);
+    const first = await prisma.role.findMany();
+    const idByKey = new Map(first.map((r) => [r.key, r.id]));
+
+    await seedDefaultRoles(prisma);
+    const second = await prisma.role.findMany();
+
+    expect(second).toHaveLength(first.length);
+    for (const role of second) {
+      // Count alone cannot prove idempotency (delete+recreate also yields 1).
+      expect(role.id).toBe(idByKey.get(role.key));
+    }
+    expect(await prisma.rolePermission.count()).toBe(
+      DEFAULT_ROLES.reduce((n, r) => n + r.permissions.length, 0),
+    );
+  });
+
+  // KEEP only if the seed's update path is declared a no-op on permissions
+  // (i.e. it must not clobber manual revocations). Delete otherwise — do not
+  // assert semantics the implementation does not guarantee.
+  it('does not re-grant a revoked permission on re-run', async () => {
+    await seedDefaultRoles(prisma);
+
+    const target = DEFAULT_ROLES.find((r) => r.permissions.length > 0);
+    expect(target).toBeDefined();
+    const revokedKey = target!.permissions[0];
+    await prisma.rolePermission.deleteMany({
+      where: {
+        role: { key: target!.key },
+        permission: { key: revokedKey },
+      },
+    });
+
+    await seedDefaultRoles(prisma);
+
+    expect(await rolePermissionKeys(target!.key)).not.toContain(revokedKey);
+  });
+
+  it('pins critical role(s) so catalogue drift fails loudly', async () => {
+    await seedDefaultRoles(prisma);
+
+    // VERIFY: pin to the repo's actual super-admin key and known-critical permission.
+    const superAdmin = DEFAULT_ROLES.find((r) => r.key === 'SUPER_ADMIN');
+    expect(superAdmin).toBeDefined();
+    expect(await rolePermissionKeys('SUPER_ADMIN')).toContain(
+      'roles:manage', // pin a permission whose accidental removal is a security regression
+    );
+  });
+});
```

## Verification (run before marking READY_FOR_EGRESS)

```bash
pnpm exec tsc --noEmit -p packages/authorization/tsconfig.json   # RULE-002 syntax gate
pnpm --filter @custos/authorization run test                      # AC2 acceptance
pnpm --filter @custos/authorization run test -- --run seed-default-roles.spec.ts --no-coverage
```

## Known residual risks

1. **If the spec fails on `rolePermission`/`permission` model names** → rename per `schema.prisma` (e.g. `rolesOnPermissions`); no logic change.
2. **If test 4 fails** → the seed re-grants on update (`connect`/`set` in `update:` clause). Per plan: remove test 4 from this patch, fix the seed in a **separate commit**, flag in the PR body — bounty scope is the spec.
3. **If CI has no Postgres for this package** → this spec needs the integration-test job's DB provisioning, not the unit job. Confirm before push; a missing service is the top CI-break risk.
4. **Parallel-worker pollution** → if other DB specs share this schema, run this file serially or scope by worker schema.

Share the real `seed-default-roles.ts` and I'll collapse the `VERIFY` comments into exact assertions and confirm the catalogue symbol names.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `test(authorization): cover seedDefaultRoles idempotency & system-role invariants`

> **Status: DRAFT — not merge-ready.** The spec below has not been executed against a real database or compiled against the actual module. Every symbol marked `VERIFY` must be confirmed against `packages/authorization` before this is opened for review. See §7.

---

## PR Metadata

| Field | Value |
|---|---|
| Repo | `Custos-Labs/custos` |
| Base | `main` (confirm default branch) |
| Type | `test` — additive, no production code change |
| Bounty | $60 — "Test `seedDefaultRoles`" |
| Labels | `bounty`, `testing`, `authorization`, `needs-ci-verification` |
| Blocking dependency | Postgres service in the `@custos/authorization` test job (see §4.3) |

---

## 1. Root Cause

This is **not** a defect report. It is a **verification gap** with a security dimension.

`seedDefaultRoles` encodes two invariants that nothing currently enforces:

1. **Recoverability invariant** — every catalogue role is materialized with `isSystemRole: true`, so an operator who locks themselves out of RBAC can re-run the seed to restore administrative access. If a refactor drops the flag or skips a role, the recovery path silently degrades.
2. **Idempotency invariant** — the seed is designed to be safe to re-run (deploy hooks, bootstrap scripts, local resets). If re-running duplicates roles, mutates row identity, or clobbers manual permission revocations, the failure surfaces in production, not CI.

A test suite is the cheapest enforcement mechanism for both. The absence of one means any future edit to the seed — including well-intentioned ones — can regress a security-critical path with a green pipeline.

---

## 2. Scope & Classification

**Classification: `VERIFIABLE_CODE_ISSUE`.**
The target repository is public and the issue states reproducible acceptance criteria plus a runnable command (`pnpm --filter @custos/authorization run test`). This is code-grounded and testable — it is not a speculative radar item. (Any item lacking a public repo with a reproducible suite should remain `RAW_RADAR_CANDIDATE` and not be scheduled for implementation.)

**In scope**
- New spec file colocated with the seed module.
- Assertions covering: role creation, system-role flagging, permission assignment, idempotency (count **and** identity), revocation preservation, and a pinned anti-drift assertion.

**Out of scope**
- Refactoring `seedDefaultRoles` itself. If the spec exposes a real defect, the fix lands in a **separate commit** (see §5, R4) so the bounty deliverable stays reviewable and the defect gets its own justification.

---

## 3. Implementation

### 3.1 Files

| File | Action | Notes |
|---|---|---|
| `packages/authorization/infrastructure/seed/seed-default-roles.spec.ts` | **Create** | Colocated per issue requirement; matches repo spec convention |
| `seed-default-roles.ts` | Read-only | Inspect for idempotency mechanism before writing assertions |
| `packages/authorization/package.json` | Verify only | Confirm test glob picks up colocated `*.spec.ts` |
| CI workflow (`.github/workflows/*.yml`) | Verify only | Confirm Postgres service is available to this package's test job |

### 3.2 Design decisions

- **Real database over mocked Prisma.** The central claim — "exactly one row per role after N runs" — is a database-level property. A mocked client can simulate idempotency the implementation does not actually have, producing a test that passes forever while production duplicates rows.
- **Identity, not count.** `expect(rows).toHaveLength(n)` is satisfied by a delete-and-recreate implementation, which is *not* idempotent in the sense that matters (stable references, FK integrity, audit trails). The spec snapshots `(roleKey → id)` after run 1 and asserts stability after run 2.
- **Import the catalogue, don't duplicate it.** Hardcoding role/permission lists in the spec guarantees rot. Importing alone risks a tautology, so a small number of **pinned assertions** on security-critical roles are added to catch accidental catalogue edits.
- **Order
\n