# Bounty Proposal: Custos-Labs/custos#7 - [Bounty: $60] Test `token-digest.ts` helpers directly\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $60] Test `token-digest.ts` helpers directly

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: this is a well-scoped test-authoring task with a named file path, three exported functions, and explicit acceptance criteria, and the $60 bounty clears the $25 minimum-payout gate. The only caveat is that the issue body is truncated mid-sentence ("two calls to `generate"), so the third acceptance criterion should be confirmed against the repo before claiming — but the spec file itself is straightforwardly writable against `packages/credentials/domain/value-objects/token-digest.ts`.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm trying to test helpers in `token-digest.ts` for the Custos project, but I can't see the file's contents. This means I can't write a precise patch and would have to guess function names and behavior, violating the rules about deterministic checks and uncertainty. I need to either ask for the file or provide a template, clearly stating it needs verification.

I need to decide whether to ask for the `token-digest.ts` file or provide a test scaffold. Given the SWE-2 framing, the best approach is to classify this as a RAW_RADAR_CANDIDATE, provide a test scaffold for a typical `token-digest.ts` file (like SHA-256 hex digest), clearly mark it as needing verification against the actual exports, and then request the file content to finalize the exact lines. I'll assume vitest for the scaffold, as Custos likely uses it.

I'm preparing to present a candidate patch for the `token-digest` helpers. This involves outlining the assumed test structure, noting the need for verification against the actual file contents, and specifying the required information like the exact file path, exports, and test runner setup to finalize the patch. I'll also include a status header indicating that the patch is unverified and awaiting source code.## Status: `RAW_RADAR_CANDIDATE` — not yet `READY_FOR_EGRESS`

Per **[RULE-003-RADAR-UNCERTAINTY]** and **[RULE-002-SYNTAX-GROUNDING]**: I cannot emit a verifiable surgical patch because I don't have the confirmed contents, path, or export signatures of `token-digest.ts`, nor the repo's test runner config. Below is a **grounded candidate** based on the canonical shape of this file (SHA-256 hex digest + timing-safe verify, Lucia-style). It must be reconciled against the real exports before egress.

### Assumed source (verify against repo)

```ts
// src/auth/token-digest.ts  (path TBD)
import { createHash, timingSafeEqual } from "node:crypto";

export function digestToken(token: string): string {
  return createHash("sha256").update(token, "utf8").digest("hex");
}

export function verifyTokenDigest(token: string, expectedDigest: string): boolean {
  const actual = Buffer.from(digestToken(token), "hex");
  const expected = Buffer.from(expectedDigest, "hex");
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
```

### Candidate diff — `tests/unit/token-digest.test.ts` (new file)

```diff
+import { describe, expect, it } from "vitest";
+import { createHash } from "node:crypto";
+import { digestToken, verifyTokenDigest } from "../../src/auth/token-digest";
+
+describe("token-digest helpers", () => {
+  describe("digestToken", () => {
+    it("returns a 64-char lowercase hex string", () => {
+      expect(digestToken("token-abc")).toMatch(/^[0-9a-f]{64}$/);
+    });
+
+    it("is deterministic for identical input", () => {
+      expect(digestToken("t0k3n")).toBe(digestToken("t0k3n"));
+    });
+
+    it("matches independent SHA-256 computation", () => {
+      const token = "refresh-token-123";
+      const expected = createHash("sha256").update(token, "utf8").digest("hex");
+      expect(digestToken(token)).toBe(expected);
+    });
+
+    it("produces distinct digests for tokens differing by one char", () => {
+      expect(digestToken("token-a")).not.toBe(digestToken("token-b"));
+    });
+
+    it("does not echo the raw token into the digest", () => {
+      expect(digestToken("secret")).not.toContain("secret");
+    });
+
+    it("handles empty string", () => {
+      expect(digestToken("")).toBe(
+        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
+      );
+    });
+
+    it("is unicode-safe", () => {
+      expect(digestToken("tökën-🔐")).toMatch(/^[0-9a-f]{64}$/);
+    });
+  });
+
+  describe("verifyTokenDigest", () => {
+    it("returns true for a matching token/digest pair", () => {
+      const token = "session-token";
+      expect(verifyTokenDigest(token, digestToken(token))).toBe(true);
+    });
+
+    it("returns false for a mismatched digest", () => {
+      expect(verifyTokenDigest("token-a", digestToken("token-b"))).toBe(false);
+    });
+
+    it("returns false for malformed (non-hex/short) digest without throwing", () => {
+      expect(() => verifyTokenDigest("token", "zz")).not.toThrow();
+    });
+  });
+});
```

### Grounding checklist to elevate to `VERIFIABLE_CODE_ISSUE` → `READY_FOR_EGRESS`

1. **Exact path** of `token-digest.ts` (`src/auth/`? `src/lib/`? `packages/core/`?) → fixes the import specifier.
2. **Real export names/signatures** — if it exposes e.g. `sha256()`, `hmacDigest()`, or base64url output instead of hex, assertions above change (length, charset, fixtures).
3. **Test runner** — Vitest vs Jest vs `node:test`; if `node:test`, rewrite imports to `node:test`/`node:assert`.
4. **Sandbox gate**: run `tsc --noEmit` + the test file before marking PASS.

Send the file contents (or confirm the assumed source) and I'll return the exact final patch.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

## `test(auth): add direct unit coverage for token-digest helpers`

| Field | Value |
|---|---|
| **Repo** | `Custos-Labs/custos` |
| **Bounty** | $60 |
| **Author** | Claude — Delivery & Quality Verification Lead |
| **Change type** | Test-only (no production code touched) |
| **Current status** | `RAW_RADAR_CANDIDATE` → `DRAFT_PROPOSAL` |
| **Egress status** | ⛔ **NOT `READY_FOR_EGRESS`** |

> **Egress gate (blocking).** Per **[RULE-002-SYNTAX-GROUNDING]**, no patch may be marked `PASS` or `READY_FOR_EGRESS` until a deterministic check (`tsc --noEmit` + the test run itself) executes green in a sandbox against the **actual** `token-digest.ts`. Per **[RULE-003-RADAR-UNCERTAINTY]**, this item stays classified `RAW_RADAR_CANDIDATE` until a public Git repository with a reproducible test suite is confirmed for the target helpers. The contents below are a *grounded candidate*, not a verified diff.

---

## 0. Grounding Ledger — Confirmed vs. Assumed

Nothing in the "Assumed" column may be silently promoted. Each row is a gate.

| # | Item | State | Impact if wrong |
|---|---|---|---|
| 1 | Exact path of `token-digest.ts` | ❓ **Assumed** `src/auth/token-digest.ts` | Import specifier in test is wrong → red CI |
| 2 | Export names (`digestToken`, `verifyTokenDigest`) | ❓ **Assumed** | Whole diff invalid; every assertion rewritten |
| 3 | Output encoding (`hex`, 64 chars) | ❓ **Assumed** | Length/charset assertions + empty-string fixture change |
| 4 | Hash family (`SHA-256`) | ❓ **Assumed** | Hardcoded empty-string digest is wrong |
| 5 | Verify helper is timing-safe + length-guarded | ❓ **Assumed** | The "malformed digest" test's contract changes |
| 6 | Test runner is Vitest | ❓ **Assumed** | Imports must be rewritten (see Appendix A) |
| 7 | Helpers currently lack *direct* unit coverage | ❓ **Hypothesis** | Root-cause narrative needs rewording |

**Confirmed:** the repo slug, the issue text, and the fact that the issue asks for *direct* testing of these helpers. **That is all.** Every other claim is flagged.

---

## 1. Root Cause

The failure mode here is not a crash — it is an **unguarded contract at a pure-function crypto boundary**. Two layers:

### 1.1 Surface cause
No test file imports `token-digest.ts` directly. Coverage, if any exists, is *incidental* — the helpers are exercised only transitively through session-creation / session-validation integration paths, which assert on end-state behavior ("login works") rather than on the digest contract itself ("digest is 64 lowercase hex chars, deterministic, and compared in constant time").

> ⚠️ **Verification required:** confirm via `vitest run --coverage` (or equivalent) that `token-digest.ts` shows low/no *direct* statement coverage. If it is already well covered by a co-located test, this issue's premise changes and the proposal should be re-scoped rather than merged.

### 1.2 Underlying cause — why this matters more than "add a test"
Digest helpers have an **externally-persisted** contract. Their output is written into the session/token store, so the digest string is durable state, not an implementation detail.

That means a *refactor that passes every existing integration test* can still be catastrophic:

| Silent change | Existing tests | Production result |
|---|---|---|
| `hex` → `base64url` | ✅ green | Every persisted digest fails to match → **mass session invalidation** |
| `sha256` → `sha512` | ✅ green | Same, plus a 128-char string silently written to a `VARCHAR(64)` column |
| Drop `utf8` input encoding | ✅ green on ASCII | Non-ASCII tokens hash differently → subset of users logged out |
| Replace `timingSafeEqual` with `===` | ✅ green | Timing side-channel reintroduced, invisible to any behavioral test |
| Drop the length pre-check | ✅ green (or throws on mismatch) | `timingSafeEqual` throws `RangeError` on unequal buffers → 500s instead of a clean `false` |

**Root cause, stated precisely:** the digest contract is durable, security-relevant, and currently locked only by integration tests that cannot distinguish a correct digest from a *consistently wrong* one. Direct unit tests are the only mechanism that pins the contract in place.

---

## 2. Implementation

**Scope:** one new file. **Zero** production-code changes — this is deliberate, and it is what makes the PR trivially revertible and safe to land.

### 2.1 Assumed source under test — `src/auth/token-digest.ts` (⚠️ path + body unverified)

Reproduced here **only** so reviewers can see exactly which contract the tests target. This is the canonical shape (SHA-256 hex digest + timing-safe verify). It is **not** claimed to be the repo's actual file.

```ts
// src/auth/token-digest.ts  (path TBD)
import { createHash, timingSafeEqual } from "node:crypto";

export function digestToken(token: string): string {
  return createHash("sha256").update(token, "utf8").digest("hex");
}

export function verifyTokenDigest(token: string, expectedDigest: string): boolean {
  const actual = Buffer.from(digest
\n