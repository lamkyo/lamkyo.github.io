# Bounty Proposal: Perenna-Labs/perenna-contracts#80 - [Bounty: $70] Document the reserved error codes' ABI status in the spec\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $70] Document the reserved error codes' ABI status in the spec

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This issue is actionable and codeable because it scopes a documentation-only update to the section 2 error table with explicit consistency and CI checks. It remains RAW_RADAR_CANDIDATE until the public repository and reproducible checks are confirmed.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm analyzing the user's request, which frames me as a specific architect but I'm actually the assistant. The core task is to triage a bounty issue for a contract repository, focusing on root causes, affected files, and a robust strategy. I need to consider mandatory invariants like GitHub App boundaries and uncertainty classification. Crucially, I don't have direct access to the specified repository, so I must be upfront about this limitation and frame my plan contingent on verification steps, aligning with the uncertainty rule.

I've identified the root cause: not a code bug, but ambiguity in the contract specification regarding reserved error codes (5 and 9). This ambiguity risks spec drift and requires careful documentation updates, specifically in CONTRACT_SPEC.md, to reflect their current unreachability and potential pre-v1.0 changes, without altering the existing error codes in the Rust files. I'll also check if CI needs adjustments to lint these spec files.

I'm refining the spec language for reserved codes, ensuring it clarifies their unreachability, fixed numeric values, and integrator guidance, while referencing the H4 lifecycle and acknowledging potential pre-v1.0 changes. I'll explicitly state the numeric value freeze as a compatibility guarantee, as required by the acceptance criteria, and confirm this aligns with ABI stability. My regression-avoidance strategy focuses on a documentation-only diff, verifying that no generated specs are overwritten and that edits are made to source templates if CONTRACT_SPEC.md is codegenerated.

I'm structuring the PR to ensure CI parity and avoid refactoring coupling, adhering to rules about PAT usage and idempotency. My cross-checks will verify error code alignment with table numbers and confirm zero construction sites for specific errors. I'll also address the bounty allocation rule, ensuring gross amounts are quantized upfront. The PR will include a commit message, labels, issue linking, and a description of performed checks, formatted in Markdown with headers and code blocks for clarity, aiming for a thorough yet concise design document.

I'm proposing a table addition and explanatory notes to the contract specification to clarify the status of reserved error codes 5 (StreamEnded) and 9 (AmountMismatch). These codes are currently unreachable but must remain fixed in value for ABI stability, even if activated or removed before v1.0. Integrators should treat them as generic errors. I've also prepared verification commands to confirm these points and ensure the `make check` target passes.

I'm checking the Makefile and scripts for "CONTRACT_SPEC" to see if it's codegenerated, which would require editing the generator source instead of the spec file directly. My risk register covers potential issues like over-promising permanence, overwriting generated specs, CI failures, scope creep, and incorrect PAT usage, with mitigations in place. The execution pipeline is defined in stages from scouting to publishing, and I've considered an optional local consistency check script to maintain scope. The overall response will be medium-long, structured with headers and a table, and will acknowledge its conditional status.# Architecture & Execution Plan — Reserved Error Code ABI Documentation

**Status gate (RULE-003):** This stays `RAW_RADAR_CANDIDATE` until Stage 0 confirms the public repo, the referenced files, and a reproducible `make check`. Everything below is conditional on that confirmation — I don't have verified visibility into `Perenna-Labs/perenna-contracts` contents.

---

## 1. Root Cause Analysis

This is not a code defect — it's a **spec semantics gap** on an ABI surface:

- `error.rs` exports `StreamEnded = 5` and `AmountMismatch = 9` as part of the contract's error enum. The discriminants are ABI-relevant even if unreachable.
- §2 labels them "Reserved" but defines no semantics for that label: Is the value stable? Can it be repurposed? What should an integrator's `match` arm do?
- §6 H4 defers a keep/remove decision to pre-v1.0 — so the spec **must not over-promise permanence** of the variants, only the freeze of the numeric values and a defined integrator posture.

**Latent risk if left undocumented:** an integrator either (a) assumes the codes are impossible and panics/UB on receipt, or (b) assumes "Reserved" means the slot can be recycled — and a future activation/repurpose becomes a silent breaking change.

**Contributing factor:** nothing mechanically ties the spec table to `error.rs`. The fix is documentation-only; the drift risk is noted but out of scope.

---

## 2. Files to Touch

| File | Change | Rationale |
|---|---|---|
| `docs/CONTRACT_SPEC.md` | **Only content edit** — expand §2 reserved-code semantics | Issue scope |
| `contracts/stream/src/error.rs` | **None** | Removing/renumbering variants is an ABI change — forbidden |
| `contracts/stream/src/lib.rs` | **None** | Doc-only issue |
| `.github/workflows/ci.yml`, `Makefile` | **None** | `check` must stay green as-is |

**Explicit non-goals:** no enum cleanup, no new CI steps, no spec-codegen harness. Scope discipline is the regression guard.

---

## 3. Stage 0 — Verification (read-only, RULE-003 gate)

Clone/scout via **GitHub App** (allowed: cloning, scouting, quota shielding — RULE-001). Confirm:

```bash
# 1. Variants and discriminants
grep -n "StreamEnded\|AmountMismatch" contracts/stream/src/error.rs

# 2. Zero construction sites (expect no hits in lib.rs)
grep -rn "StreamEnded\|AmountMismatch" contracts/stream/src/lib.rs

# 3. §2 table and §6 H4 exist as described
grep -n "Reserved\|H4" docs/CONTRACT_SPEC.md

# 4. Reproducible checks exist
grep -n "^check:" Makefile
grep -n "check" .github/workflows/ci.yml

# 5. CRITICAL: is CONTRACT_SPEC.md generated?
grep -rn "CONTRACT_SPEC" Makefile scripts/ xtask/ .github/workflows/ 2>/dev/null
```

Item 5 is the trap: if the spec is codegen'd, the edit target is the **generator source**, not the markdown. Abort-and-report if the layout diverges materially.

---

## 4. Proposed Spec Delta (§2)

Add a status column (or footnote block) plus a normative "Reserved code semantics" paragraph:

```markdown
| Code | Name           | Status                 |
|------|----------------|------------------------|
| 5    | StreamEnded    | Reserved (unreachable) |
| 9    | AmountMismatch | Reserved (unreachable) |

**Reserved code semantics.** Codes 5 and 9 are defined in
`contracts/stream/src/error.rs` but have no construction sites in
`contracts/stream/src/lib.rs`; the contract cannot currently emit them.

- Their numeric values are frozen for ABI stability. A reserved value is
  never reassigned to a different error meaning.
- Per §6 item H4, each reserved variant will be activated or removed
  before v1.0. Removal never renumbers other codes.
- Integrators MUST treat a received reserved code as a generic/unknown
  error (catch-all arm). Do not ignore it and do not rely on its
  continued unreachability — a future release may activate a reserved
  code without changing its numeric value.
```

**Acceptance criteria mapping:**

- AC1 → "Reserved (unreachable)" + no-construction-site statement
- AC2 → "frozen… never reassigned"
- AC3 → explicit §6 H4 deference; wording promises the *value* freeze, not the *variant's* survival — consistent with keep-or-remove
- AC4 → enforced in Stage 5

---

## 5. Stage 1–3 — Execution & Publication Boundary

1. **Author locally** — single commit, minimal diff, no adjacent reflow.
2. **Verify locally** — `make check`; re-run the §2-vs-`error.rs` grep to confirm numbers match; check markdownlint/line-length rules if `check` lints docs.
3. **Publish** — branch + PR via an **authenticated user PAT**, never the GitHub App (RULE-001). App stays read-only for CI-status scouting. PR body: links issue, lists the four ACs, includes the grep evidence output.

---

## 6. Risk Register

| Risk | Mitigation |
|---|---|
| Spec promises variant permanence → contradicts H4 | Freeze scoped to numeric value only; lifecycle deferred to H4 |
| Spec is codegen'd → edit silently overwritten | Stage 0 item 5 gate |
| `make check` lints docs (line length, tables, anchors) | Run before push; match existing table style |
| §-numbering/anchor drift breaks cross-reference | Use §-reference as written; verify heading text in Stage 0 |
| Scope creep into `error.rs` | Out of scope; file a separate issue if enum cleanup is desired |

**RULE-006 note:** the $70 bounty itself is a single allocation — no-op here — but if any downstream payout split occurs, quantize gross upfront and derive sub-allocations so `sum(allocations) == gross_quantized`.

---

## Decision

Documentation-only, single-file, single-commit change. Zero ABI/runtime surface delta. The only real architectural decision is the wording invariant: **freeze the number, not the variant** — that's what keeps §2 and §6 H4 mutually consistent.

Want me to proceed to Stage 0 verification, or do you have repo access details to confirm the file layout first?

---

## 3. Production Code Patch (`swe-2`)
The user wants exact code changes, but I haven't verified the repository's contents. My plan explicitly stated only documentation would change and that I lacked verified visibility. Producing a fabricated diff would violate my own rules and honesty.

I've decided Option B is the best approach: provide a patch template with placeholders and optional assertions, explicitly stating that exact context requires Stage 0 verification. This ensures honesty and usefulness, adhering to RULE-002 by allowing deterministic checks. For documentation-only changes, inserting a new paragraph block anchored to a grep-verifiable line is the cleanest method, minimizing reliance on unknown context.

I'm considering adding Rust unit tests to assert error enum discriminants, which mechanically ties spec claims to code and aligns with the issue's spirit. However, I don't know the exact error enum name or its representation, so I'll provide a template with placeholders. I'll also document that compile-time unreachability can't be tested directly. Finally, I'll ensure the patch follows commit structure rules and includes deterministic check commands.

I've drafted the diff to insert a new paragraph into `docs/CONTRACT_SPEC.md` explaining reserved error codes. This paragraph is anchored to the line following the §2 error table, ensuring it's placed correctly relative to existing content. The diff also includes a note about the `AmountMismatch` and `StreamEnded` error codes being currently unconstructible.

I need to be explicit about how I'm presenting diffs that only involve insertions, as I lack context. I'll offer a patch template with placeholders for context lines, or an `ed`-style instruction alongside a `git apply`-able snippet. Alternatively, I can show the final inserted text, a diff skeleton with placeholders, a fallback diff variant, a test template, and verification gates. For the unit test, I'll provide a template asserting enum discriminant values, noting that `as` casting might fail if the enum isn't fieldless and `#[repr(u32)]`, suggesting safer alternatives like `TryFrom` or `Into` if available.

I'm deciding where to place the new test code: ideally within the existing `#[cfg(test)] mod tests` block at the end of `error.rs`, or appended as a new conditional module if the block isn't present. I'll also include a variant-B patch for the "Reserved" column, using placeholders since I can't verify the table's existence in that form. The response structure will prioritize the code changes, followed by deterministic verification commands and a commit message.Per RULE-003, I can't fabricate exact context lines for a file I haven't read — that would produce a `git apply` failure, not a patch. So below: the **inserted content is final/production-ready** (it's new text, fully deterministic), and every context-dependent token is marked `<VERIFY-…>` with the exact Stage-0 command that resolves it.

## Patch A — §2 insertion (primary, minimal blast radius)

Insertion needs only one anchor line, so it survives table-format uncertainty:

```diff
diff --git a/docs/CONTRACT_SPEC.md b/docs/CONTRACT_SPEC.md
index <OLD>..<NEW> 100644
--- a/docs/CONTRACT_SPEC.md
+++ b/docs/CONTRACT_SPEC.md
@@ -<L>,3 +<L>,17 @@
 <CTX: last row of §2 error-code table>
 <CTX: first blank line after table>
+**Reserved code semantics.** Codes 5 (`StreamEnded`) and 9
+(`AmountMismatch`) are defined in `contracts/stream/src/error.rs` but
+have no construction sites in `contracts/stream/src/lib.rs`; the
+contract cannot currently emit them.
+
+- **Value freeze.** The numeric values of reserved codes are frozen for
+  ABI stability. A reserved value is never reassigned to a different
+  error meaning.
+- **Lifecycle.** Per §6 item H4, each reserved variant will be activated
+  or removed before v1.0. Removal never renumbers other codes.
+- **Integrator contract.** A received reserved code MUST be handled as a
+  generic/unknown error (catch-all arm). Integrators MUST NOT rely on
+  its continued unreachability — a future release may activate a
+  reserved code without changing its numeric value.
+
 <CTX: next existing paragraph/heading>
```

Resolve the three placeholders:

```bash
grep -n "AmountMismatch" docs/CONTRACT_SPEC.md   # last table row → <CTX>/<L>
```

## Patch B — alternative: `Status` column (only if the table matches the issue's described shape)

```diff
-| Code | Name           |
-|------|----------------|
-| 5    | StreamEnded    |
-| 9    | AmountMismatch |
+| Code | Name           | Status                 |
+|------|----------------|------------------------|
+| 5    | StreamEnded    | Reserved (unreachable) |
+| 9    | AmountMismatch | Reserved (unreachable) |
```

Use **A or B for the label**, plus the paragraph block from A either way. Do not apply both label mechanisms.

## Unit test — pin the ABI freeze mechanically

This is the only code-file touch, and it's additive — no ABI/runtime delta. Append inside the existing `#[cfg(test)] mod tests` in `contracts/stream/src/error.rs` if present, else append the whole module:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Pins reserved discriminants per docs/CONTRACT_SPEC.md §2.
    /// These values are ABI-frozen: a change here is a spec violation,
    /// not a refactor.
    #[test]
    fn reserved_error_codes_are_abi_frozen() {
        assert_eq!(<ENUM>::StreamEnded as u32, 5);
        assert_eq!(<ENUM>::AmountMismatch as u32, 9);
    }
}
```

`<ENUM>` = the actual error enum name (`Error`/`ContractError`) — resolve via `grep -n "pub enum" contracts/stream/src/error.rs`. If `as u32` fails to compile (e.g., non-`repr` enum), use the generated conversion — Soroban `#[contracterror]` typically supports `u32::from(<ENUM>::StreamEnded)` — and let `cargo test` be the grounding check, per RULE-002. No test can assert "zero construction sites"; that remains the grep evidence in the PR body.

## Deterministic verification (RULE-002 gate — required before READY_FOR_EGRESS)

```bash
git apply --check docs-spec-reserved-codes.patch   # hunk validity
cargo test -p <crate> reserved_error_codes         # test compiles + passes
grep -rn "StreamEnded\|AmountMismatch" contracts/stream/src/lib.rs  # expect: zero hits
make check                                          # CI parity
```

## Commit / PR

```text
docs(spec): define ABI semantics for reserved error codes 5 and 9

- Mark codes 5 (StreamEnded) and 9 (AmountMismatch) as reserved and
  currently unreachable: no construction sites in lib.rs
- Freeze numeric values; removal per §6 H4 never renumbers other codes
- Specify integrator contract: handle as generic/unknown error
- Pin discriminants with a unit test in error.rs
```

One flag: the issue's ACs are doc-only, so the `error.rs` test is technically additive scope — it's justified because it mechanically prevents the exact regression the spec now forbids, but if the maintainer wants a strictly-single-file diff, drop it and keep Patch A/B only. I'd ship it with the test and call that out in the PR description.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Document Reserved Error Codes' ABI Status in the Spec

**Repo:** `Perenna-Labs/perenna-contracts` · **Issue:** [Bounty: $70] Document the reserved error codes' ABI status in the spec
**Proposed branch:** `docs/spec-reserved-error-codes` → `main` (verify default branch in Stage 0)
**PR title:** `docs(spec): define ABI semantics for reserved error codes 5 and 9`
**Labels:** `documentation`, `spec`, `bounty` (confirm label set exists)
**Document status:** `DRAFT — PENDING_STAGE_0_VERIFICATION`
**Gate (RULE-002):** No artifact in this proposal is `PASS` or `READY_FOR_EGRESS` until the compiler/linter gates in §3 execute green in a sandbox. Nothing below is reported as already-executed.

> **Uncertainty disclosure (RULE-003).** I do not have verified read access to `perenna-contracts`. Every context-dependent token is marked `<VERIFY-…>` and paired with the exact command that resolves it. The *inserted* text is final; the *surrounding* context is not asserted.

---

## 1. Root Cause

**Classification:** specification-semantics gap on an ABI-relevant surface — not a runtime defect.

`contracts/stream/src/error.rs` declares `StreamEnded = 5` and `AmountMismatch = 9` as part of the contract's error enum. Those discriminants are ABI-relevant regardless of whether the contract can construct them. §2 of `docs/CONTRACT_SPEC.md` labels them "Reserved" without defining what that label obligates:

| Undefined question | Consequence |
|---|---|
| Are the numeric values stable across releases? | Integrator assumes a slot can be recycled → silent breaking change |
| Can the variant be removed or repurposed? | §6 H4 defers this decision, but §2 implies permanence — the two sections contradict |
| What must an integrator's `match` arm do? | Integrator treats a received reserved code as impossible → panic / undefined handling |

**Contributing factor:** nothing mechanically ties the §2 table to `error.rs`. The table can drift from the enum with no CI signal. Documenting the drift risk is in scope; building a codegen/lint harness for it is not.

**Impact if unaddressed:** an integrator either (a) treats codes 5/9 as unreachable and fails hard on receipt, or (b) treats "Reserved" as "recyclable," converting a future activation into an unannounced breaking ABI change.

**Fix shape:** documentation-only. The only architectural decision is the wording invariant — **freeze the number, not the variant.**

---

## 2. Implementation

### 2.1 File matrix

| File | Action | Justification |
|---|---|---|
| `docs/CONTRACT_SPEC.md` | **Modify** — expand §2 reserved-code semantics | Issue scope |
| `contracts/stream/src/error.rs` | **Additive test only** — `#[cfg(test)]` block pinning discriminants | Mechanical regression guard for the new normative text |
| `contracts/stream/src/lib.rs` | **No change** | Doc-only issue; also the grep target proving unreachability |
| `Makefile`, `.github/workflows/ci.yml` | **No change** | `check` must remain green unmodified |

**Explicit non-goals:** no enum cleanup, no renumbering, no new CI steps, no spec-codegen harness, no changes to adjacent table formatting.

**Scope flag for the maintainer:** the `error.rs` unit test is technically additive to a doc-only issue. It is included because it mechanically prevents the exact regression the spec text now forbids. If a strictly single-file diff is required, drop §2.3 and retain Patch A/B only — state the choice in the PR description either way.

### 2.2 Patch A — §2 insertion (primary)

Insertion requires only one anchor line, so it survives table-format uncertainty:

```diff
diff --git a/docs/CONTRACT_SPEC.md b/docs/CONTRACT_SPEC.md
index <VERIFY-OLD>..<VERIFY-NEW> 100644
--- a/docs/CONTRACT_SPEC.md
+++ b/docs/CONTRACT_SPEC.md
@@ -<VERIFY-L>,3 +<VERIFY-L>,17 @@
 <CTX: last row of §2 error-code table>
 <CTX: first blank line after table>
+**Reserved code semantics.** Codes 5 (`StreamEnded`) and 9
+(`AmountMismatch`) are defined in `contracts/stream/src/error.rs` but
+have no construction sites in `contracts/stream/src/lib.rs`; the
+contract cannot currently emit them.
+
+- **Value freeze.** The numeric values of reserved codes are frozen for
+  ABI stability. A reserved value is never reassigned to a different
+  error meaning.
+- **Lifecycle.** Per §6 item H4, each reserved variant will be activated
+  or removed before v1.0. Removal never renumbers other codes.
+- **Integrator contract.** A received reserved code MUST be handled as a
+  generic/unknown error (catch-all arm). Integrators MUST NOT rely on
+  its continued unreachability — a future release may activate a
+  reserved code without changing its numeric value.
+
 <CTX: next existing paragraph/heading>
```

Resolve the placeholders:

```bash
grep -n "AmountMismatch" docs/CONTRACT_SPEC.md     # → <CTX> anchor and <VERIFY-L>
grep -n "Reserved\|H4" docs/CONTRACT_SPEC.md       # confirm §2 table + §6 H4 exist as described
```

### 2.3 Patch B — optional `Status` column

Apply **A or B for the label**, plus the paragraph block from A in both cases. Never both label mechanisms.

```diff
-| Code | Name           |
-|------|----------------|
-| 5    | StreamEnded    |
-| 9    | AmountMismatch |
+| Code | Name           | Status                 |
+|------|----------------|------------------------|
+| 5    | StreamEnded    | Reserved (unreachable) |
+| 9    | AmountMismatch | Reserved (unreachable) |
```

### 2.4 Additive test — pin the ABI freeze

Append inside the existing `#[cfg(test)] mod tests` in `contracts/stream/src/error.rs` if present; otherwise append the whole module:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// Pins reserved discriminants per docs/CONTRACT_SPEC.md §2.
    /// These values are ABI-frozen: a change here is a spec violation,
    /// not a refactor.
    #[test]
    fn reserved_error_codes_are_abi_frozen() {
        assert_eq!(<VERIFY-ENUM>::StreamEnded as u32, 5);
        assert_eq!(<VERIFY-ENUM>::AmountMismatch as u32, 9);
    }
}
```

`<VERIFY-ENUM>` resolves via `grep -n "pub enum" contracts/stream/src/error.rs`. If `as u32` does not compile (non-`repr` enum), use the generated conversion — Soroban `#[contracterror]` typically supports `u32::from(<VERIFY-ENUM>::StreamEnded)` — and let `cargo test` be the grounding authority. **No test can assert "zero construction sites"**; that remains grep evidence in the PR body.

### 2.5 Acceptance-criteria mapping

| AC | Satisfied by |
|---|---|
| Reserved codes marked unreachable | Patch A paragraph sentence 1; Patch B `Status` column |
| Numeric values frozen | "Value freeze" bullet; §2.4 test |
| Consistent with §6 H4 lifecycle | "Lifecycle" bullet — promises *value* freeze, not *variant* survival |
| Integrator guidance | "Integrator contract" bullet |
| No ABI/runtime delta | Non-goals; `error.rs` diff is test-only |

### 2.6 Commit message

```text
docs(spec): define ABI semantics for reserved error codes 5 and 9

- Mark codes 5 (StreamEnded) and 9 (AmountMismatch) as reserved and
  currently unreachable: no construction sites in lib.rs
- Freeze numeric values; removal per §6 H4 never renumbers other codes
- Specify integrator
\n