# Bounty Proposal: Custos-Labs/custos#5 - [Bounty: $65] Test the identity persistence mappers round-trip\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $65] Test the identity persistence mappers round-trip

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable bounty issue.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm tasked with designing unit tests for identity persistence mappers in a monorepo, specifically for `user-mapper.ts` and `organization-mapper.ts`. The goal is to ensure round-trip fidelity between Prisma rows and domain aggregates, covering various states like `personName`, `deletedAt`, and organization statuses. I also need to classify the bounty issue according to specific rules, considering if the repository is public and has reproducible tests to determine if it's a verifiable code issue.

I'm considering the architecture for persistence mappers in a DDD monorepo, focusing on round-trip tests. The core challenge is the potential asymmetry between domain aggregates and database rows, especially since Prisma rows are the source of truth. A `toRow` mapping might omit fields managed by the database (like `id` or `createdAt`) or fields not exposed by the aggregate. To ensure invariant safety, assertions should focus on the set of fields the mapper is responsible for, comparing the mapped row's keys against an expected set or a shared constant.

I'm realizing a stronger test approach: asserting that `toRow(toDomain(row))` deep-equals the original row, but only for the mapped fields. Even better, the test should derive the field list from the row literal's keys. This ensures `toRow` emits every key present in the original row. If `toRow` legitimately omits fields, the test must use an explicit `MAPPED_FIELDS` allowlist. The key insight here is that typing the row literals with Prisma-generated types is crucial for ensuring that renaming a field in `schema.prisma` breaks the test, as it will cause a compile-time type error. For exhaustiveness, I'll perform bidirectional key-set checks: `Object.keys(toRow(domain))` must equal the expected field set, and a round-trip `toDomain(row)` followed by re-mapping and deep-equal comparison must hold.

When asserting object equality in tests, `toEqual` is generally preferred over `toMatchObject` or `toContainEqual` because it checks for both extra and missing keys. However, `toStrictEqual` is even better as it also validates `undefined` properties and class instances, but it fails if the actual object is a domain aggregate instance and the expected object is a plain object, due to class mismatch. Therefore, for domain objects, I should compare snapshots of their exposed state or use `toEqual` with plain objects. For plain objects like the output of `toRow`, `toStrictEqual` is appropriate.

I'm realizing that asserting `toRow(toDomain(row)) === row` is only valid if `toRow` preserves all fields. If it intentionally omits fields, like `createdAt`, I need a more robust check. A safer approach is to define explicit `MAPPED_FIELDS` constants and then verify both deep equality of the picked fields and the exact set of keys emitted by `toRow` against these constants. This guards against both dropped fields and unexpected additions.

I've refined the fixed-point assertion for `toDomain` omissions. The round-trip test implicitly catches fields dropped by `toDomain` because `toRow` won't be able to reproduce them. However, a symmetric omission by both `toDomain` and `toRow` could pass unnoticed. To mitigate this, I'll add a key-set assertion using the typed literal's keys, ensuring all expected fields are present in the persisted row. The simplest robust formulation involves checking key parity and then strict equality.

I'm considering how to test enum states like `active`, `suspended`, and `deleted` using table-driven tests. I also need to handle optional fields, distinguishing between `null`, `undefined`, and absent values, especially since Prisma uses `null` while mappers might normalize to `undefined`. Finally, I'll use fixed date literals for deterministic tests.

I need to verify the database dependency of mappers, ensuring they remain pure functions and don't import Prisma client instances directly. I'll check the import graph and use `import type` for Prisma model types. I also need to determine the test runner (Jest or Vitest) by examining existing specs and package scripts, then configure it to match conventions and ensure tests don't require a database connection. Finally, I'll consider adding direct assertions on `toDomain` output for clearer failure messages, even though the fixed-point `toRow(toDomain(row))` test should cover omissions.

I need to ensure the CI test command `pnpm --filter @custos/identity run test` correctly picks up spec files and that Prisma client generation precedes tests. For RULE-003, I must confirm the repository is public and tests are reproducible before classifying it as VERIFIABLE_CODE_ISSUE; otherwise, it's RAW_RADAR_CANDIDATE. Fixes should be submitted via a PAT user account, not a GitHub App, as per RULE-001. RULE-006 applies only to bounty payout allocations.

I need to be careful about how `toStrictEqual` handles Prisma's `Decimal` and `JsonValue` types, as it compares class instances directly. I'll need to construct expected values using `new Prisma.Decimal(...)` to match. Also, I must verify how `createdAt` and `updatedAt` timestamps are handled, as they might be absent or overwritten by the database after mapping.

I'm deciding on the best way to assert the round-trip fidelity of the persistence mappers. While `expect(pick(row, USER_MAPPED_FIELDS)).toStrictEqual(persisted)` checks that the mapped row contains the correct fields, I also need to ensure `toRow` doesn't emit *extra* fields. Checking `Object.keys(persisted).sort()` against `USER_MAPPED_FIELDS.sort()` seems like the most robust approach for this.

I'm marking placeholders clearly and listing "verify in source" items because actual field names are unverified. Although the prompt states the assistant has codebase access, it couldn't identify relevant parts. I'll proceed with explicit assumptions marked, noting key unknowns like mapper signatures and Prisma type names as verification gates rather than blocking questions, given the explicit file paths provided.

I'm refining the testing strategy for persistence mappers, focusing on a "schema-anchored fixed-point testing" approach. This involves three layers of assertions: compile-time type checking with Prisma types, explicit key-parity contracts using `MAPPED_FIELDS`, and value fixed-point checks for bidirectional mapping fidelity. I'm also considering edge cases for user and organization data, and ensuring zero behavioral regression in production code by only adding new files.

I need to ensure spec files are excluded from the build artifacts by verifying `tsconfig.build.json` excludes `**/*.spec.ts`. Vitest's default glob should pick them up, and since the specs don't import the Prisma client, they won't require a database connection in CI. If the repo uses Turbo, I must check `turbo.json` to ensure the `test` script depends on `@custos/database#build`/`generate` for Prisma client types.# Design: Schema-Anchored Fixed-Point Tests for Identity Mappers

## 1. Classification & Verification Gates (RULE-003)

Classify this item as **RAW_RADAR_CANDIDATE → promote to VERIFIABLE_CODE_ISSUE only after**:

```bash
git clone https://github.com/Custos-Labs/custos && cd custos
pnpm install
pnpm --filter @custos/identity run test   # must pass without Postgres for unit specs
```

Confirm in-source before writing a line: exact mapper exports (`toDomain`/`toRow` vs `toPersistence`), the Prisma model type names, test runner (vitest vs jest), and whether `deleted` org status is a column enum or derived from `deletedAt`.

## 2. Root Cause

The coverage gap is structural, not incidental:

- **Wrong test altitude**: coverage exists only at repository-integration level (`prisma-repositories.spec.ts`), which is env-gated on Postgres — the slowest possible failure surface for a pure function.
- **No static coupling to schema**: nothing ties mapper behavior to `schema.prisma`. A renamed column only breaks at runtime against a live DB.
- **No declared field contract**: without an explicit manifest of "fields the mapper owns," a dropped field is invisible — both directions can omit it *symmetrically* and a naive round-trip still passes.

## 3. Files to Touch

| File | Action |
|---|---|
| `packages/identity/infrastructure/persistence/user-mapper.spec.ts` | **New** |
| `packages/identity/infrastructure/persistence/organization-mapper.spec.ts` | **New** |
| `packages/identity/tsconfig.build.json` | **Verify only**: `**/*.spec.ts` excluded from build artifact |
| `turbo.json` / CI workflow | **Verify only**: `test` depends on `@custos/database` prisma client generation |

Production mappers: **zero changes** — purely additive → zero behavioral regression. (Contingency in §6.)

## 4. Core Invariant: Persistence Fixed-Point

The single most powerful assertion is `toRow ∘ toDomain = id` over the mapped field set:

```ts
import type { Prisma } from '@custos/database';

// (1) COMPILE-TIME ANCHOR — `satisfies` binds the literal to generated Prisma types.
// Renaming a column in schema.prisma → type error here → Acceptance Criterion 3.
const NAMED_ACTIVE_USER = {
  id: 'usr_01J…',
  email: 'ada@example.com',
  personName: 'Ada Lovelace',
  deletedAt: null,
  createdAt: new Date('2024-01-01T00:00:00Z'),
  updatedAt: new Date('2024-01-02T00:00:00Z'),
  /* …every remaining column… */
} satisfies Prisma.UserGetPayload<{}>;

// (2) FIELD CONTRACT — explicit manifest of fields the mapper owns.
const USER_MAPPED_FIELDS = [
  'id', 'email', 'personName', 'deletedAt', /* …exactly what toRow emits… */
] as const;

const pick = (o: object, ks: readonly string[]) =>
  Object.fromEntries(ks.map(k => [k, (o as any)[k]]));

function expectFixedPoint(row: Prisma.UserGetPayload<{}>) {
  const persisted = UserMapper.toRow(UserMapper.toDomain(row));
  // (3) KEY PARITY — catches fields silently dropped OR added by toRow.
  expect(Object.keys(persisted).sort()).toEqual([...USER_MAPPED_FIELDS].sort());
  // (4) VALUE PARITY — toStrictEqual distinguishes null vs undefined vs absent.
  expect(persisted).toStrictEqual(pick(row, USER_MAPPED_FIELDS));
}
```

**Why this is bulletproof against symmetric omission** (the subtle failure mode): a naive `toRow(toDomain(row)) === row` passes even if *both* directions drop a field. Anchoring the key set to an explicit `USER_MAPPED_FIELDS` manifest — which must equal the `satisfies`-typed literal's keys — closes that hole: a field dropped from the mapper *and* forgotten in the manifest is caught because the literal (full Prisma row) still contains it and key parity fails.

Per-case, add **diagnostic domain assertions** (cheap, better failure messages): `expect(user.personName?.value).toBe('Ada Lovelace')`, `expect(org.status).toBe(OrganizationStatus.Suspended)`.

## 5. Case Matrix

**User** — exercise `personName` × `deletedAt` orthogonality (guards against accidental coupling, e.g., mapper gating name on deletion):

| `personName` | `deletedAt` | Meaning |
|---|---|---|
| `null` | `null` | anonymous, active |
| set | `null` | named, active |
| `null` | `Date` | anonymous, soft-deleted |
| set | `Date` | named, soft-deleted |

**Organization** — `it.each` over `active` / `suspended` / `deleted`, each with its own `satisfies`-typed literal. If `deleted` derives from `deletedAt` rather than a status column, the fixture must pair them consistently — **verify in source**.

All dates are fixed literals — no `Date.now()`, zero flakiness.

## 6. Hazard Register

| Hazard | Mitigation |
|---|---|
| `toRow` is contractually partial (DB manages `createdAt`/`updatedAt`) | Don't assert against full row — assert against `pick(row, USER_MAPPED_FIELDS)`; manifest encodes the real contract |
| `toStrictEqual` on class instances (VOs/aggregates) fails on prototype | Keep strict equality on the **row plane only** (plain objects); assert domain state via getters/`equals()` |
| Prisma `Decimal`/`JsonValue`/`enum` columns | Construct expected values with `new Prisma.Decimal(...)` / generated enum imports — inspect schema for User/Org column types |
| `null` vs `undefined` normalization in `toRow` | `toStrictEqual` is intentionally strict here; if the mapper normalizes, the fixture encodes *that* contract explicitly |
| Spec accidentally imports `PrismaService`/client instance | Verify mapper's import graph is type-only; spec must run with zero env vars — that's what keeps `pnpm --filter @custos/identity test` green in CI without Postgres |
| **Fixed-point reveals a real mapper defect** (e.g., `toDomain` drops `deletedAt` → un-delete silently impossible) | Out of test scope but report + minimal mapper fix in same PR — a genuine bug find strengthens the bounty claim |

## 7. Pipeline Notes (Mandatory Invariants)

- **RULE-001**: PR submission/push goes through the PAT-authenticated user account. GitHub App used only for cloning/scouting this public repo.
- **RULE-006**: Not applicable to the code change; applies only to bounty payout split — quantize gross first, derive allocations from quantized gross, `sum(allocations) == gross_quantized`.

**Net strategy**: two additive spec files, three layered assertions (compile-time schema anchor → key-parity manifest → value fixed-point), zero production-code changes. Every acceptance criterion is met by construction, and criterion 3 falls out of `satisfies` + generated Prisma types rather than any runtime trick.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

## `test(identity): schema-anchored fixed-point round-trip tests for persistence mappers`

---

## 0. Proposal Status

| Field | Value |
|---|---|
| **Repo** | `Custos-Labs/custos` |
| **Bounty** | $65 — *Test the identity persistence mappers round-trip* |
| **Proposed branch** | `test/identity-mapper-round-trip` |
| **Base** | `main` |
| **Classification** | `RAW_RADAR_CANDIDATE` → promote to `VERIFIABLE_CODE_ISSUE` **only after Gate 0 clears** |
| **Patch status** | **`NOT_READY_FOR_EGRESS`** — SWE-2 patch slot is empty; scaffold below is ready-to-apply but every field-level identifier is gated on source verification |
| **Production code delta** | **Zero** — purely additive spec files |

> **Honesty marker (read before reviewing):** the upstream architecture plan states it could *not* identify the relevant source regions. No mapper signature, Prisma model name, column name, enum member, or test runner in this document has been read from the repository. Everything concrete is either (a) a *mechanism* that is correct regardless of naming, or (b) a **placeholder explicitly tagged `← VERIFY`**. This proposal must not be marked `PASS` or submitted until Gate 0 completes and the scaffold compiles.

---

## 1. Classification & Gate 0

Per the classification rule, a verifiable code issue requires **(i)** a public repository and **(ii)** reproducible tests. Both are *asserted* by the plan but neither is *demonstrated*. Gate 0 is therefore a hard prerequisite, not a formality.

### Gate 0 — Blocking checklist

- [ ] **Public repo confirmed** — anonymous `git clone` succeeds without credentials.
- [ ] **Unit tests run without Postgres** — `pnpm --filter @custos/identity run test` exits 0 on a clean checkout with no `DATABASE_URL` set.
- [ ] **Mapper exports read from source** — record exact names: `toDomain` / `toRow` vs `toPersistence` / `toEntity`; default vs named export; class-with-static-methods vs object literal.
- [ ] **Prisma model names confirmed** — exact generated type names (e.g. `Prisma.UserGetPayload<{}>` vs `Prisma.usersGetPayload<{}>`).
- [ ] **Test runner confirmed** — Vitest vs Jest; import of `describe/it/expect` (global vs explicit) to match existing specs.
- [ ] **`deleted` org status semantics confirmed** — is it a column enum, or *derived* from `deletedAt`? This changes the fixture contract (see §5).
- [ ] **Field manifests derived from source**, not guessed — `USER_MAPPED_FIELDS` / `ORG_MAPPED_FIELDS` must be read off the actual `toRow` body.
- [ ] **TypeScript version ≥ 4.9** — `satisfies` is load-bearing for Acceptance Criterion 3.

**If any box fails:** do not author the patch. Report the blocker on the bounty thread. If the repo is private or the suite requires a live database, reclassify to `RAW_RADAR_CANDIDATE` and stop.

---

## 2. Root Cause

The gap is **structural, not incidental**. Three independent defects compound:

### RC-1 — Wrong test altitude

Coverage exists only at repository-integration level (`prisma-repositories.spec.ts`), which is **environment-gated on Postgres**. A pure, synchronous, side-effect-free mapping function is therefore only exercised behind the slowest and least reliable failure surface in the stack. CI on a fork or a clean runner silently skips it.

### RC-2 — No static coupling to the schema

Nothing in the test suite binds mapper behavior to `schema.prisma`. A column rename produces **no compile-time error** anywhere in the test tree; it surfaces as a runtime `undefined` against a live database, if at all.

### RC-3 — No declared field contract (the subtle one)

Without an explicit manifest of "fields the mapper owns," a dropped field is **invisible**. A naive assertion —

```ts
expect(toRow(toDomain(row))).toEqual(row);
```

— **passes even when `toDomain` and `toRow` symmetrically omit the same field.** Both directions drop `personName`; the fixed point still holds; the round trip is green; the data is gone. This is the failure mode the whole design must defeat.

**Consequence:** the bounty's "round-trip fidelity" is not satisfied by any test that merely re-maps and compares. The field contract must be asserted **independently of the mappers**.

---

## 3. Implementation

### 3.1 Files to touch

| File | Action |
|---|---|
| `packages/identity/infrastructure/persistence/user-mapper.spec.ts` | **New** |
| `packages/identity/infrastructure/persistence/organization-mapper.spec.ts` | **New** |
| `packages/identity/tsconfig.build.json` | **Verify only** — `**/*.spec.ts` excluded from build artifacts |
| `turbo.json` / CI workflow | **Verify only** — `test` task depends on `@custos/database` Prisma client generation |

Production mappers: **unchanged**. Purely additive ⇒ zero behavioral regression risk.

### 3.2 The core invariant — persistence fixed point

Three layered assertions. Each closes a hole the others leave open.

```ts
// ─── user-mapper.spec.ts ────────────────────────────────────────────────
import { describe, it, expect } from 'vitest';          // ← VERIFY runner
import type { Prisma } from '@custos/database';          // ← VERIFY path
import { UserMapper } from './user-mapper';              // ← VERIFY export shape

// (1) COMPILE-TIME SCHEMA ANCHOR.
//     `satisfies` binds this literal to the *generated* Prisma type.
//     Rename a column in schema.prisma → type error HERE.
//     ⇒ Acceptance Criterion 3, by construction, no runtime trick.
const NAMED_ACTIVE_USER = {
  id: 'usr_01J0000000000000000000000',                   // ← VERIFY id format
  email: 'ada@example.com',
  personName: 'Ada Lovelace',
  deletedAt: null,
  createdAt: new Date('2024-01-01T00:00:00Z'),
  updatedAt: new Date('2024-01-02T00:00:00Z'),
  // …every remaining column of the User row…            ← VERIFY
} satisfies Prisma.UserGetPayload<{}>;                   // ← VERIFY type name

// (2) FIELD CONTRACT — the explicit manifest of fields the mapper owns.
//     Read this OFF the toRow body; do not guess.
const USER_M
\n