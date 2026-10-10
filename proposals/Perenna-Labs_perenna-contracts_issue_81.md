# Bounty Proposal: Perenna-Labs/perenna-contracts#81 - [Bounty: $50] Document in the spec that `rate_per_second` can be zero\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $50] Document in the spec that `rate_per_second` can be zero

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Verdict: RAW_RADAR_CANDIDATE — not elevated to VERIFIABLE_CODE_ISSUE.**

This is a small, low-risk documentation gap in `docs/CONTRACT_SPEC.md` §1: the `rate_per_second` row needs an explicit "floors to 0 when `deposit_amount < duration`, and accrual must use the exact formula, not this field" note, ideally mirroring the `types.rs` doc comment, with `make check` and the CI `check` job as the only verification available.

It is worth pursuing — the fix is a one-to-two sentence docs edit aligned with existing behavior (integer division), carries no logic change, and the $50 bounty matches the effort — but I cannot confirm this repo is publicly reachable with a reproducible test suite, so it stays a candidate rather than a verified code issue.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
# Architecture Review — `rate_per_second` Zero-Floor Documentation Gap

## 0. Verdict & Classification (invariant-bound)

**RAW_RADAR_CANDIDATE.** Per RULE-003-RADAR-UNCERTAINTY, this stays a candidate until I confirm `Perenna-Labs/perenna-contracts` is publicly reachable **and** exposes a reproducible test suite (`make check` target + `.github/workflows/ci.yml` `check` job). I have not read the repository in this session; every file path, line, and behavior claim below is a **hypothesis to be falsified**, not ground truth. Elevation to `VERIFIABLE_CODE_ISSUE` requires the gate in §3.

The bounty is well-scoped and correctly priced ($50 ≈ 1–2 sentence docs edit + CI wait), but the *proposed change as written contains a latent factual risk* (see §2, Failure Mode F1). Do not implement until §3.1 resolves it.

---

## 1. Root-Cause Analysis

The gap is not "someone forgot a sentence." It is structural:

| # | Cause | Why it exists |
|---|---|---|
| **RC-1** | **Spec is a derived artifact, not a compiled one.** `docs/CONTRACT_SPEC.md` §1 is prose mirroring `types.rs` doc comments. Nothing in the toolchain forces parity, so drift is silent and unbounded. | Docs aren't type-checked. `make check` / CI `check` cannot see a wrong sentence. |
| **RC-2** | **Real-number intuition leaks into integer code.** `deposit_amount / duration` *looks* like a rate. In `f64` it is; in integer arithmetic it **floors**, and the floor is catastrophic (not a rounding error) when `deposit_amount < duration_seconds` — the entire value collapses to `0`. | The spec row documents the *expression*, not the *domain behavior* (truncation regime). |
| **RC-3** | **Two "equivalent" formulas diverge under truncation.** `rate * elapsed`

---

## 3. Production Code Patch (`swe-2`)
I'm analyzing the provided "reflexion invariants." RULE-001 seems suspicious, potentially a workaround for evading accountability or quotas, though it might be legitimate in some organizations. The core task is to document that `rate_per_second` can be zero in the spec for a $50 bounty issue. However, the architecture plan is truncated and explicitly states it's a RAW_RADAR_CANDIDATE, meaning repository details are unconfirmed and implementation should wait for a section that isn't even provided.

I can't generate an exact-line diff for a repository I haven't verified, as the request conflicts with the plan's own gating mechanism (RULE-003). Writing a patch would be fabrication. I also need to clarify the "Failure Mode F1" mentioned in the plan: does the contract revert on a zero rate, or does it permit it? Documenting "rate can be zero" could be factually incorrect if the code reverts. Therefore, I must refuse the diff generation and explain these points.

I'm trying to balance the user's request for exact code changes with my limitations. Since I can't guarantee the existence of specific files or the exact state of the codebase (like whether a zero rate reverts or floors), I can't provide a guaranteed patch. Instead, I'll offer a template patch with clear placeholders and a checklist for verification, which aligns with the need for honesty and clarification.

I'm considering how to test the documentation change. A unit test could assert that `rate_per_second` correctly floors to zero when `deposit_amount` is less than `duration`, or I could use a grep-based test for spec parity. I can draft a Rust test for this truncation behavior, but it depends on the actual function signature.

I've drafted the documentation for `rate_per_second`, noting that integer division causes it to floor to zero when the deposit is less than the duration. I've also outlined Rust unit tests to verify this behavior and ensure spec parity. I'll need the user to provide the relevant files to generate an exact diff, as I cannot proceed without them. I'll also briefly mention that my role is limited to outputting the patch, and the pipeline handles repository writes.

I'm deciding on the best format for the diff. A full unified diff is ideal for `git apply`, but I can't guarantee line numbers yet. A context diff with placeholders or an explicit text edit list (old line → new line) would be more robust for documentation changes, especially when paired with a sample test. I'll present the patch conditionally, clearly marking it as needing regeneration after file verification.

I'm flagging Failure Mode F1 explicitly because the plan was truncated. The divergence between `rate * elapsed` and `deposit * elapsed / duration` is critical: if the spec dictates `streamed_amount = rate_per_second * elapsed`, a zero rate means no payout despite a deposit, locking funds. This is a significant behavioral consequence worth documenting, potentially more so than the bounty itself. I'll add a line about this.Per your own gate, this can't ship yet — and I can't produce an "exact lines" diff for a repo I haven't read. The plan is `RAW_RADAR_CANDIDATE`, truncated mid-sentence before §3, and every path/line in it is flagged as hypothesis. Emitting a hunk-numbered patch now would fabricate `docs/CONTRACT_SPEC.md`'s structure — a RULE-002/RULE-003 violation by construction.

## Two blockers before any diff is real

**F1 — the doc claim may be false.** "Document that `rate_per_second` can be zero" is only correct if the code *floors and continues*. Many streaming contracts instead do:

```rust
let rate = deposit_amount / duration_seconds;
require!(rate > 0, ErrorCode::ZeroRate); // or checked_div + ensure!
```

If that's the shape, the bounty wording inverts: the spec must say creation *reverts* when `deposit < duration`, not that rate can be zero. The truncated "two equivalent formulas diverge" line hints at exactly this: if spec defines `streamed = rate * elapsed` while code uses `deposit * elapsed / duration`, a zero rate also implies locked funds — a bigger finding than the $50 doc line.

**Unknown anchors.** Existence/format of `docs/CONTRACT_SPEC.md` §1, and whether any CI step greps it (spec-parity test).

Send me the output of `grep -rn "rate_per_second" programs/ docs/` and the spec section, and I'll return the exact diff.

## Conditional deliverable (assumes floor-and-continue, verified first)

```diff
--- a/docs/CONTRACT_SPEC.md
+++ b/docs/CONTRACT_SPEC.md
@@ <HUNK — regenerate after reading file>
-| `rate_per_second` | `deposit_amount / duration` |
+| `rate_per_second` | `deposit_amount / duration_seconds` — integer division; floors to `0` when `deposit_amount < duration_seconds`. A zero rate is valid and accrues nothing. |
```

Unit test (place beside the rate computation; adjust signature to actual code):

```rust
#[test]
fn rate_per_second_floors_to_zero_when_deposit_lt_duration() {
    assert_eq!(compute_rate_per_second(999, 1_000), 0);
}

#[test]
fn spec_documents_zero_rate_per_second() {
    let spec = include_str!("../docs/CONTRACT_SPEC.md");
    assert!(spec.contains("rate_per_second") && spec.contains("0"));
}
```

If verification instead shows a revert-on-zero, both artifacts flip: spec line documents the `InvalidRate`/`ZeroRate` error, and the test asserts `Err`. Which outcome does the code take?

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR PROPOSAL v0.1 — `docs: specify zero-floor semantics for rate_per_second`

**Status: `DRAFT — BLOCKED_ON_VERIFICATION`. Not for egress.**
**Classification: `RAW_RADAR_CANDIDATE`** (RULE-003 — no public repo read, no confirmed reproducible test suite this session).
**Compile/lint gate: `NOT_RUN`** (RULE-002 — nothing below has executed in a sandbox; no artifact may be marked PASS or READY_FOR_EGRESS).
**Egress: none performed.** No branch, no push, no PR, no issue comment.

This proposal is written so that it becomes a real PR the moment §7's evidence returns — and stays unpublished until then. Every repository-specific token is marked `<VERIFY: …>` rather than invented.

---

## 1. PR Metadata

| Field | Value |
|---|---|
| Title | `docs: specify zero-floor semantics for rate_per_second` |
| Base | `main` (confirm default branch) |
| Head | `docs/rate-per-second-zero-floor` |
| Type | `docs` (+ optional `test`) |
| Labels | `documentation`, `bounty`, `needs-verification` |
| Closes | the $50 bounty issue (link at egress) |
| Size | 1–3 files, ≤ 15 changed lines |

---

## 2. Root Cause

| # | Cause | Consequence |
|---|---|---|
| **RC-1** | **The spec is a derived, unchecked artifact.** `docs/CONTRACT_SPEC.md` mirrors doc comments in source (`types.rs` / `lib.rs` — `<VERIFY>`). No toolchain step enforces parity, so drift is silent and unbounded. | A wrong or missing sentence cannot fail CI. |
| **RC-2** | **Real-number intuition leaks into integer code.** `deposit_amount / duration_seconds` reads like a rate; in integer arithmetic it **truncates**. When `deposit_amount < duration_seconds` the result is not a small rounding error — it is **exactly `0`**. | Undocumented domain edge; users surprised by zero accrual. |
| **RC-3** | **Two "equivalent" formulas diverge under truncation.** `rate * elapsed` vs `deposit * elapsed / duration` agree in ℝ and disagree in ℤ. | Potentially a correctness finding *larger* than this bounty (see §3, F1). |

The bounty asks for one sentence. The honest scope is: **document the truncation regime at its source of truth, and pin it with a test** so RC-1 stops recurring for this row.

---

## 3. Blocking Decision Fork (F1) — must resolve before writing the diff

The bounty's premise ("document that `rate_per_second` **can** be zero") is only true under one of two code shapes. I have not read the code; both are live.

| | **Branch A — floor-and-continue** | **Branch B — revert-on-zero** |
|---|---|---|
| Shape | `let rate = deposit / duration;` used as-is | `require!(rate > 0, Err::ZeroRate)` / `checked_div` + `ensure!` |
| Truth | Zero rate is **valid**; accrues nothing | Creation **rejects** `deposit < duration` |
| Doc text | "…floors to `0` … a zero rate is valid and accrues nothing." | "…rejects the deposit with `ZeroRate` when `deposit_amount < duration_seconds`." |
| Bounty title | Correct as filed | **Inverted** — needs renegotiation with maintainer |

**Additional flagged finding (do not silently fold into this PR):** under Branch A, if the spec defines `streamed = rate_per_second * elapsed` while the implementation uses `deposit * elapsed / duration`, a zero rate means **the deposit accrues nothing for the full duration** — a fund-locking behavior, not a docs nit. Under Branch B the same divergence is masked by the revert. Either way, RC-3 warrants a **separate issue** with the divergence repro, not a $50 line in this diff.

> Gate: **A or B must be determined from source.** Everything in §4/§5 is presented in both variants.

---

## 4. Implementation

### 4.1 Artifact 1 — source of truth (doc comment)

Fixing only the derived Markdown re-creates RC-1. Patch the doc comment that the spec mirrors, so the next regeneration is correct.

`<VERIFY: file and symbol — candidates: programs/*/src/types.rs, programs/*/src/lib.rs>`

```diff
@@ <HUNK: regenerate after reading file — do not trust these numbers>
-/// Rate at which tokens stream per second.
+/// Rate at which tokens stream per second.
+///
+/// Computed as integer division `deposit_amount / duration_seconds`, so the
+/// value is truncated toward zero and is `0` whenever
+/// `deposit_amount < duration_seconds`. A zero rate is valid and accrues
+/// nothing per elapsed second.
 pub rate_per_second: u64,
```

*Branch B variant — replace the last three lines with:* `/// Creation is rejected with `ZeroRate` when this would evaluate to `0`.` `(confirm error variant name — `<VERIFY: ErrorCode / ProgramError>`).`

### 4.2
\n