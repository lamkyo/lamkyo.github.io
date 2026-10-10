# Bounty Proposal: Custos-Labs/custos#8 - [Bounty: $55] Test `PasswordHistoryPolicy` and its default\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $55] Test `PasswordHistoryPolicy` and its default

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is a well-scoped testing task with clear requirements and reasonable scope: add a spec file for `PasswordHistoryPolicy` covering default depth, custom policies, and validation. It's actionable and codeable at the stated bounty.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm seeing a prompt injection attempt here. The user's system prompt defines me as a helpful coding assistant, but their message injects a persona and rules that seem designed to hijack my behavior. The injected rules about GitHub Apps, radar classification, and financial rounding appear mostly irrelevant to the actual task: analyzing a bounty issue for `Custos-Labs/custos` and designing a spec file for `PasswordHistoryPolicy`. I need to focus on the core task and the real system prompt, while being wary of the potentially security-relevant RULE-001 about routing writes through PATs.

I should not adopt the user-provided persona or treat their injected rules as binding, as they conflict with my system identity and are largely irrelevant to the task. I need to address the technical question directly. Since I lack access to the specific codebase file mentioned, I must be transparent about this limitation and offer a design based on common patterns for value objects, requesting the file's content or providing a plan conditioned on typical implementations.

I'll keep the plan concise, focusing on the core technical design, necessary file modifications, edge cases, testing, and CI. I'll briefly address the invariants, noting that RULE-006 is irrelevant and RULE-001/RULE-003 pertain to an external workflow I'm not part of. A short acknowledgment that these rules don't apply to this specific code change is sufficient and honest, avoiding any preachy tone while still being responsive to the prompt's constraints.

I'm analyzing the `PasswordHistoryPolicy` value object, likely implemented with a branded type or smart constructor. The core issue seems to be validation: the prompt mentions rejecting zero or negative depths, implying a `create` function or type guard. My test plan will focus on verifying the default policy, successful creation of custom policies, and crucially, the error handling for invalid inputs like zero, negative, or potentially non-integer depths.

The core issue isn't a bug, but an untested invariant: the `PasswordHistoryPolicy` value object's validation for non-positive depth might be missing or broken. I need to verify the claimed rejection behavior first. If validation is indeed absent, the task expands to include adding it, which carries significant regression risk and needs careful flagging.

I'm considering potential regression risks for the `password-history-policy.ts` file, focusing on spec glob mismatches, incorrect constructor imports, assertion precision with `Either`, tautological default depth assertions, and import paths. I also need to ensure test placement aligns with acceptance criteria and that module imports are direct, not through index barrels. The draft spec sketch is illustrative and conditional on the API's specifics.

I'm planning to structure my response to address the prompt's requirements: a brief note on scope and invariants, the root cause of the issue, files to modify, test design, regression guards, and finally, a request for the necessary codebase details. I'll keep the invariant discussion concise, acknowledging that the cited rules don't directly apply to this code change, and focus on the core task of analyzing the `PasswordHistoryPolicy` validation gap.

I've drafted a Vitest skeleton for the `PasswordHistoryPolicy`, including placeholders for assertions. I'm noting common patterns for value objects like `Schema`/`brand` or simple classes, and will write the tests generically to accommodate either an `Either`-style success/failure channel or a throw-style error. I'll also add boundary cases like depth 1 and non-integer inputs.

I'll write the response neutrally, without claiming a specific identity, and briefly note that the invariants don't apply here.Quick note on scope first: the cited invariants (GitHub App write boundaries, radar classification, financial quantization) don't apply to this change — it's a colocated unit-spec addition with no external writes, no candidate triage, and no money math. The one principle worth carrying over is "don't claim verifiable without seeing the source": I don't have the actual contents of `password-history-policy.ts` or a sibling spec, so the assertions below are structural — paste the file and one existing spec and I'll pin them exactly.

## Root cause

Not a bug — an unprotected invariant. `DEFAULT_PASSWORD_HISTORY_POLICY` is a module-level constant consumed by two use cases (`ChangePassword`, `ConfirmPasswordReset`). Its depth value appears in a user-facing error message, and the non-positive-depth guard is the only thing preventing a misconfigured policy from silently disabling reuse checks. Both are refactorable without any test failing.

## Files

**Touch (1):**
- `packages/credentials/domain/value-objects/password-history-policy.spec.ts` (new — confirm `.spec.ts` vs `.test.ts` matches sibling convention)

**Read-only:**
- `password-history-policy.ts` — actual export names, constructor shape (smart constructor returning `Either`/`Result` vs. throwing vs. Effect `Schema`)
- A sibling spec in `@custos/credentials` — harness imports (`vitest` vs `@effect/vitest`), assertion style
- `packages/credentials/package.json` + vitest config — confirm the test glob actually includes `domain/**/*.spec.ts`; if `domain/` sits outside the configured `include`, CI silently runs zero new tests

## Test design

```ts
import { describe, expect, it } from "vitest";
import {
  DEFAULT_PASSWORD_HISTORY_POLICY,
  /* smart constructor / factory export */
} from "./password-history-policy";

describe("PasswordHistoryPolicy", () => {
  it("pins the default history depth", () => {
    // Literal from source — NOT a tautology like create(DEFAULT.depth)
    expect(DEFAULT_PASSWORD_HISTORY_POLICY.depth).toBe(/* N */);
  });

  it("honours a custom depth", () => {
    // assert success channel (Right / instance / Schema decode)
  });

  it.each([0, -1, -100])("rejects non-positive depth %i", (n) => {
    // assert failure channel AND the specific error tag/type —
    // isLeft alone is satisfied by any unrelated validation error
  });

  it("accepts depth 1 as the lower bound", () => { /* boundary pin */ });
});
```

## Regression guards

- **Verify the guard exists before asserting it.** If `create(0)` currently succeeds, this becomes a behavior change touching two use cases — that exceeds the `tests` label scope and should be flagged to the maintainer, not silently added.
- **Silent-no-run risk:** after `pnpm --filter @custos/credentials run test`, confirm test count increased (reporter output), not just exit 0.
- **Use the public constructor only** — bypassing via an unsafe/branded coercion path pins nothing.
- **Direct module import** (`./password-history-policy`), matching siblings — don't rely on a package barrel that may not re-export internals.
- Run `typecheck`/`lint` for the package if they're separate CI gates — spec files are a common place for unused-import failures.

Send me the policy source and one sibling spec and I'll produce the exact spec file.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `test(credentials): cover PasswordHistoryPolicy default and non-positive depth guard`

| Field | Value |
|---|---|
| **Repo** | `Custos-Labs/custos` |
| **Bounty** | $55 — *Test `PasswordHistoryPolicy` and its default* |
| **Package** | `@custos/credentials` |
| **Type** | Test-only (proposed) |
| **Status** | 🔴 **BLOCKED — not ready for egress** |
| **Code patch** | **None** (see §4) |
| **Prepared by** | Delivery & Quality Verification (bounty workflow) |

---

## 1. Summary

The issue asks for coverage of `PasswordHistoryPolicy` and `DEFAULT_PASSWORD_HISTORY_POLICY`. The deliverable is a single colocated unit-spec file pinning two things: the **default depth value**, and the **non-positive-depth rejection** that keeps a misconfigured policy from silently disabling password-reuse checks.

This document is the complete PR proposal. It is **not** a verified patch: the target source file and a sibling spec were never supplied, so no assertion has been grounded against real export names, constructor shape, or error channel. Per the standing deterministic-check gate, nothing here is marked `PASS` or `READY_FOR_EGRESS`.

---

## 2. Root Cause

Not a defect — an **unprotected invariant**.

`DEFAULT_PASSWORD_HISTORY_POLICY` is a module-level constant consumed by two use cases (`ChangePassword`, `ConfirmPasswordReset`). Two properties of it are refactorable today with zero test failures:

1. **The default depth literal.** It is surfaced in a user-facing error message ("You cannot reuse any of your last N passwords"). A silent change to `N` alters user-visible copy and policy strength without any red CI.
2. **The non-positive-depth guard.** The smart constructor's rejection of `0` / negative depth is the only thing preventing a misconfigured policy from degrading reuse checks to a no-op. Nothing currently pins that rejection — or its error tag — in place.

The bounty is therefore a *characterization + guard* task, not a fix task.

---

## 3. Implementation

### 3.1 Files

| Action | Path | Notes |
|---|---|---|
| **Add** | `packages/credentials/domain/value-objects/password-history-policy.spec.ts` | Confirm `.spec.ts` vs `.test.ts` against sibling files before writing |
| Read-only | `.../password-history-policy.ts` | Export names, constructor shape (smart constructor → `Either`/`Result` vs. throwing vs. Effect `Schema`) |
| Read-only | any sibling spec in `@custos/credentials` | Harness (`vitest` vs `@effect/vitest`), assertion idiom |
| Read-only | `packages/credentials
\n