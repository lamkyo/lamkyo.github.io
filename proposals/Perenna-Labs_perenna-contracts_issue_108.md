# Bounty Proposal: Perenna-Labs/perenna-contracts#108 - [Bounty: $55] Document and guard the zero `rate_per_second` when the deposit is under the duration\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $55] Document and guard the zero `rate_per_second` when the deposit is under the duration

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is actionable and codeable as RAW_RADAR_CANDIDATE, with a $55 bounty passing the $25 gate and clear targets in `types.rs`, `docs/CONTRACT_SPEC.md`, and `contracts/stream/src/test.rs` for the floored zero `rate_per_second` case. Scope is tightly bounded to documentation plus a pinning test for `deposit_amount < duration` while keeping the accrual formula authoritative, verified by `make test` and CI.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I'm analyzing this bounty issue for Perenna-Labs/perenna-contracts, role-playing as a Senior Systems Architect. The triage classifies this as RAW_RADAR_CANDIDATE, and I must maintain that classification because I cannot clone the repo to confirm it has reproducible tests, per RULE-003. This means the issue remains actionable but unverified for now.

I've identified the root cause of the issue in the `rate_per_second` calculation: integer division causes it to floor to 0 when the deposit amount is less than the duration. The fix involves updating documentation and adding a test case, rather than altering the core accrual formula, which remains the authoritative source. I'll need to adjust the test code to fit the repository's conventions, as I can't access the actual codebase.

I'm adding regression guardrails to ensure the accrual logic remains correct, specifically checking that the claimable amount equals the deposit when the rate is zero and that the accrual formula is independent of `rate_per_second`. I'll also verify edge cases like `deposit_amount == duration` and ensure existing validations for zero deposit or duration are still enforced, preventing division by zero. The documentation and test sketch reflect these checks.

I'm noting that the `client.create_stream` signature is unknown and must match existing tests in `test.rs`. I also need to validate edge cases like `duration == 0`, which results in `checked_div` returning `None`. The current handling, likely an `unwrap` or `expect`, should be left as is to avoid changing behavior, as per the rules. Finally, I'll confirm that standard verification commands (`cargo fmt --check`, `cargo clippy -- -D warnings`, `make test`) and the CI `check` job all pass.## Status Gate (per invariants)

- **RULE-003**: Holding classification at `RAW_RADAR_CANDIDATE`. Elevation to `VERIFIABLE_CODE_ISSUE` requires confirming the public repo exists and `make test` reproduces locally — I can't verify that from here, so all patches below are **design-stage, not READY_FOR_EGRESS**.
- **RULE-002**: Nothing is marked PASS until it survives `cargo check`/`clippy` + `make test` in a sandbox.
- **RULE-001**: Clone/scout via GitHub App; any branch push/PR to the public repo goes through a PAT-authenticated user account.

## Root Cause

Not a bug in math — a **contract ambiguity**:

1. `rate_per_second = deposit_amount.checked_div(duration)` floors to `0` when `deposit_amount < duration`.
2. The field is documented as *informational*, but nothing states the floor-to-zero case, so downstream consumers can reasonably treat `rate_per_second == 0` as "stream accrues nothing."
3. The **accrual formula is authoritative** (it computes `deposit_amount × elapsed / duration`, not `rate_per_second × elapsed`), so actual payouts are unaffected. The defect is purely a **spec/documentation gap** — meaning the fix is docs + a pinning test, and *zero* changes to arithmetic.

## Files to Touch / Not Touch

| Action | File |
|---|---|
| ✏️ Doc-comment `rate_per_second` field | `contracts/stream/src/types.rs` |
| ✏️ Spec §1: state floored-int semantics, `0` case, accrual authoritative | `docs/CONTRACT_SPEC.md` |
| ✏️ New pinning test | `contracts/stream/src/test.rs` |
| 🚫 `lib.rs` `create_stream` / accrual | **Do not modify** — changing the formula or the field type is a regression vector and exceeds bounty scope |

## Patch Design

**`types.rs`** — doc comment:

```rust
/// Floored integer result of `deposit_amount / duration`.
///
/// Informational only — accrual derives from `deposit_amount`
/// directly, NOT from this field. When `deposit_amount < duration`
/// this value is `0`; a zero rate does NOT mean the stream
/// accrues nothing.
pub rate_per_second: i128, // type unchanged
```

**`test.rs`** — pinning test (skeleton — adapt names/signature to the existing harness; I don't have the repo's test helpers):

```rust
#[test]
fn rate_per_second_floors_to_zero_when_deposit_lt_duration() {
    // 100 / 1_000 floors to 0
    let stream_id = create_default_stream(&ctx, /* deposit */ 100, /* duration */ 1_000);
    let stream = client.get_stream(&stream_id);
    assert_eq!(stream.rate_per_second, 0);

    // Regression pin: accrual unaffected by floored informational field
    advance_time(&ctx, 500); // half of duration
    assert_eq!(client.claimable(&stream_id), 50); // deposit * elapsed / duration
}
```

The second assertion is the important one — it proves `rate_per_second` is decoupled from payouts, which is the claim the docs make.

**Spec §1** — one paragraph mirroring the doc comment, explicitly naming accrual as the authoritative source.

## Regression Guardrails

- **Boundary cases to leave intact**: `deposit == duration → rate == 1`; `duration == 0` handling via `checked_div` (whatever exists today stays — don't touch).
- **No type change** on `rate_per_second` (e.g., switching to a ratio struct would break ABI/storage layout if this is a Soroban contract — out of scope).
- **Test-only diff invariant**: `lib.rs` diff must be empty in the final PR; if it isn't, the patch is wrong by construction.

## Verification Sequence

1. `cargo fmt --check && cargo clippy -- -D warnings`
2. `make test` (full suite — confirms no existing test assumed nonzero rate)
3. Diff audit: confirm only the three listed files changed
4. Confirm CI `check` job in `.github/workflows/ci.yml` runs the same commands (no new toolchain deps introduced — docs + test only, so risk is ~zero)

**Recommended final state**: `VERIFIABLE_CODE_ISSUE` only after step 2 passes in sandbox; then `READY_FOR_EGRESS` via PAT account with label `bug`.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $55] Document and guard the zero `rate_per_second` when the deposit is under the duration
**Prepared by:** Delivery & Quality Verification Lead
**Target branch:** `main` ← `docs/rate-per-second-floor-zero`
**Labels:** `bug`, `documentation`, `tests`

---

## 0. Status Gate (binding)

| Invariant | State |
|---|---|
| [RULE-003-RADAR-UNCERTAINTY] | **Held at `RAW_RADAR_CANDIDATE`.** No repository clone, no test execution in this session. Elevation to `VERIFIABLE_CODE_ISSUE` requires a confirmed public Git repo with a reproducible test suite. |
| [RULE-002-SYNTAX-GROUNDING] | **Nothing marked PASS.** No `cargo check` / `clippy` / `make test` has been run. All code below is design-stage. |
| [RULE-001-GH-APP-BOUNDARY] | Scout/clone via GitHub App; the branch push and PR creation go through a PAT-authenticated user account. |

**This is not `READY_FOR_EGRESS`.** It becomes eligible only after the verification sequence in §6 passes in a sandbox.

**Also true, and stated plainly:** the SWE-2 patch payload is **`None`**. There is currently **no diff to submit**. Everything in §3 is a specification for a patch, not a patch. Shipping this as-is would be an empty PR.

---

## 1. Summary

`rate_per_second` is an informational, floored-integer field. When `deposit_amount < duration`, integer division floors it to `0`. Because the field is not documented as informational, a downstream integrator can reasonably read `rate_per_second == 0` as "this stream accrues nothing" — which is false.

**Fix:** documentation + one pinning regression test. **Zero changes to arithmetic.** The accrual path is the authoritative source of payout value and is out of scope.

---

## 2. Root Cause

| # | Finding | Confidence |
|---|---|---|
| 1 | `rate_per_second = deposit_amount.checked_div(duration)` floors to `0` when `deposit_amount < duration`. | **Inferred** — read from the issue text, not from source. |
| 2 | The field's doc-comment does not state the floor-to-zero case or its informational status. | **Inferred** |
| 3 | Accrual derives from `deposit_amount × elapsed / duration`, **not** `rate_per_second × elapsed`, so payouts are unaffected. | **UNVERIFIED assumption** — this is the load-bearing claim of the whole proposal, and §5's test is exactly what would falsify it. |
| 4 | Therefore the defect is a spec/documentation gap, not a math bug. | **Conditional on #3** |

> If #3 is false — i.e. any payout path multiplies by `rate_per_second` — then this is a **fund-loss-class bug**, not a docs bounty, and the classification must be escalated immediately and the bounty scope revisited. Confirm #3 *before* writing the PR body.

---

## 3. Implementation

### 3.1 Files

| Action | File | Note |
|---|---|---|
| ✏️ Doc-comment `rate_per_second` | `contracts/stream/src/types.rs` | Path inferred |
| ✏️ Spec §1 | `docs/CONTRACT_SPEC.md` | Path inferred |
| ✏️ New pinning test | `contracts/stream/src/test.rs` | Harness signature unknown |
| 🚫 No change | `lib.rs` (`create_stream`, accrual) | Out of scope; regression vector |
| 🚫 No change | `rate_per_second` type / storage layout | ABI/storage risk on Soroban |

**Invariant:** the final PR's `lib.rs` diff must be **empty**. A non-empty `lib.rs` diff means the patch is wrong by construction.

### 3.2 `types.rs` — doc comment

```rust
/// Floored integer result of `deposit_amount / duration`.
///
/// Informational only — accrual derives from `deposit_amount`
/// directly, NOT from this field. When `deposit_amount < duration`
/// this value is `0`; a zero rate does NOT mean the stream
/// accrues nothing.
pub rate_per_second: i128, // type unchanged
```

### 3.3 `docs/CONTRACT_SPEC.md` §1 — one paragraph

State explicitly: (a) the value is floored integer division; (b) the `0` case occurs when `deposit_amount < duration`; (c) accrual is computed from `deposit_amount` and `duration` and is the authoritative source; (d) `rate_per_second` must not be used to derive claimable balances.

### 3.4 `test.rs` — pinning test (skeleton)

Helper names (`create_default_stream`, `advance_time`, `get_stream`, `claimable`) are **placeholders**. They must be replaced with the existing harness in `test.rs`; I cannot see it.

```rust
#[test]
fn rate_per_second_floors_to_zero_when_deposit_lt_duration() {
    // 100 / 1_000 floors to 0
    let stream_id = create_default_stream(&ctx, /* deposit */ 100, /* duration */ 1_000);
    let stream =
\n