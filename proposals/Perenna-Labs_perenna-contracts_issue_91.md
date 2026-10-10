# Bounty Proposal: Perenna-Labs/perenna-contracts#91 - [Bounty: $95] Derive `remaining_balance` instead of storing it\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $95] Derive `remaining_balance` instead of storing it

## Architecture (Opus 5.5)
The user wants me to act as a Senior Systems Architect for a specific repository and issue, but my system prompt identifies me as a Codeium assistant. Although I don't have direct repo access, the issue description provides file paths and details about maintaining `remaining_balance` versus deriving it. The core task seems to be updating the logic and documentation to reflect that `remaining_balance` should be calculated as `deposit_amount - recipient_withdrawn` when the stream is active, and ensuring tests pass.

Regarding GitHub interaction, I'll note that public repository writes should use PATs, while GitHub Apps are better for internal repos or quota management. For classifying this bounty issue, RULE-003 requires verification. While the issue mentions `make test` and CI, suggesting it's a VERIFIABLE_CODE_ISSUE, I cannot confirm the repo is public or cloneable from here. Therefore, I'll classify it as RAW_RADAR_CANDIDATE pending confirmation, or note that it could be VERIFIABLE_CODE_ISSUE if cloning and tests succeed.

RULE-006 applies because `remaining_balance` is a financial value. The rule mandates quantizing gross amounts upfront and deriving sub-allocations from that quantized gross, ensuring the sum of allocations equals the quantized gross. In Soroban's i128 integer arithmetic, this invariant is crucial if withdrawals are calculated using division. I need to ensure that any derived amounts maintain this exact balance, preventing rounding leaks.

The core issue is a dual source of truth for `remaining_balance`, which is stored and updated in multiple places (`create_stream`, `withdraw`, `cancel`). This denormalized state risks drift, especially with future functions like `clawback` or `top_up`. The root cause is the lack of an invariant enforcer for this denormalized state. I'll need to remove the field from the `Stream` struct, add a helper function to derive the balance, and update relevant functions and tests.

I need to be careful about ABI changes, especially when removing fields from structs like `Stream`. Removing a field breaks deserialization for existing ledger entries, which is a critical regression risk for upgradeable contracts with on-chain state. If the contract is already deployed, I must either keep the field and enforce an invariant or implement a storage migration. The CI workflow and Makefile likely won't need changes.

The spec mentions the stream is "live" in §6 H3, implying the `deposit_amount - recipient_withdrawn` formula for remaining balance might only apply then. I need to clarify how to handle terminal states like cancellation or completion. If cancellation refunds unvested funds to the sender, the simple formula breaks. I should propose adding a `sender_refunded` field or deriving the remaining balance as `deposit_amount - recipient_withdrawn - sender_refunded`. Alternatively, a method could calculate the balance, accounting for terminal states and potentially returning 0 or the vested amount owed after cancellation.

I'm implementing the `remaining_balance` getter using `checked_sub` and adding a `debug_assert` for the non-negative invariant. RULE-006 dictates deriving this value from the gross upfront amount, not recomputing it independently. This ensures consistency across `cancel` refunds and `withdraw` events. I'll also add tests for invariants, overflow, and various cancellation scenarios, and use `debug_assert` as a safeguard during the transition.

I'm considering how to handle the cancellation edge case: should the `Stream` struct gain a `sender_refunded` field, or should the `remaining_balance` calculation method itself account for refunds and terminal states? The latter seems cleaner, but I need to ensure the event emitted at cancellation explicitly details the refunded amount. Also, I'll need to bump the schema version if I modify the `Stream` struct.

I'm considering the cancellation semantics, as the issue only guarantees the `deposit_amount - recipient_withdrawn` formula while a stream is live. I'll present a decision point for cancel semantics and mention `debug_assert` as a fallback if ABI preservation is critical, though recomputing and overwriting or panicking in release mode is better. I'll also note potential test locations and include a section on invariant checks.

I'm noting that RULE-003 requires `git clone` and `make test` to confirm the issue's status, classifying it as RAW_RADAR_CANDIDATE for now. RULE-006's invariant for `deposit_amount` and derived balances is key, especially in `cancel` where sub-allocations must sum to the remaining balance; I'll add an assertion for this. The plan is to structure the response with classification, root cause, design decisions, and files to touch, using Markdown and code blocks.

I'm considering two main strategies for implementing `remaining_balance`: Option A, which uses a single method, and Option B, a fallback. I need to ensure invariants are enforced, specifically mapping RULE-006 to the cancellation logic to prevent rounding errors. A test and regression plan will follow, along with PR logistics noting RULE-001. The length will be medium-long but justified.## Classification (RULE-003)

**RAW_RADAR_CANDIDATE** pending confirmation that `Perenna-Labs/perenna-contracts` is public and `make test` reproduces. The issue body strongly suggests it will elevate to **VERIFIABLE_CODE_ISSUE** — it names concrete symbols, spec sections, and a CI gate — but elevation requires a confirmed clone + green test run before I treat the cited file layout as ground truth.

## Root Cause

`remaining_balance` is **denormalized state with no invariant enforcer**. Three writers (`create_stream`, `withdraw`, `cancel`) each must remember to keep it in sync with `recipient_withdrawn`. The drift vectors are structural, not incidental:

- Any future mutator (top-up, clawback, pause/resume, fee skim) can update one field and forget the other.
- Ordering bugs: if the `TokensWithdrawn` event is emitted before the decrement, or reads the stored field after a partial update, the event carries a stale value.
- `cancel` is the most dangerous path: it likely splits remaining balance into vested payout + sender refund, which is the exact place where a hand-maintained mirror field gets out of sync (see RULE-006 below).

## Two Gating Questions (pick strategy before writing code)

1. **Is the contract deployed / upgradeable with live ledger state?** Removing a field from a `#[contracttype]` struct changes serialized layout — existing `Stream` entries may fail to deserialize after upgrade. If there is deployed state, you need Option B (or a migration), not Option A.
2. **Does any view function return `Stream` directly?** If `get_stream`/`balance` leaks the struct, removing the field is an ABI break. Mitigation: keep a response DTO that still exposes `remaining_balance` as a *derived* value — external shape preserved, internal truth deduplicated.
3. **Cancel semantics:** spec §6 H3 says the formula holds "while a stream is live." After cancel, `deposit_amount - recipient_withdrawn` equals the *refunded* amount, not zero. Decide whether `remaining_balance()` is defined only for `Active` status, or whether a `sender_refunded` / status field must enter the derivation.

## Files to Touch

| File | Change |
|---|---|
| `contracts/stream/src/types.rs` | Remove `remaining_balance` from `Stream`; add `impl Stream { pub fn remaining_balance(&self) -> i128 }` |
| `contracts/stream/src/lib.rs` | Update `create_stream` (drop init), `withdraw` (emit derived value), `cancel` (derive split from single source) |
| `contracts/stream/src/events.rs` *(if events live there — verify)* | `TokensWithdrawn` payload source |
| `contracts/stream/src/test.rs` or `tests/` | Update field reads; add invariant tests |
| `docs/CONTRACT_SPEC.md` | §1/§3 representation note; mark §6 H3 resolved |
| `.github/workflows/ci.yml`, `Makefile` | No changes — must stay green |

## Strategy — Option A (preferred, if no deployed-state constraint)

```rust
// types.rs — the ONLY place the quantity is defined
impl Stream {
    /// Spec §6 H3: single source of truth.
    pub fn remaining_balance(&self) -> i128 {
        self.deposit_amount
            .checked_sub(self.recipient_withdrawn)
            .expect("invariant violated: recipient_withdrawn > deposit_amount")
    }
}
```

```rust
// lib.rs — withdraw: payload derived AFTER mutation, never stored
stream.recipient_withdrawn = stream.recipient_withdrawn
    .checked_add(payout)
    .expect("withdraw overflow");
storage.set(&stream_key, &stream);
events::tokens_withdrawn(&env, stream_id, payout, stream.remaining_balance());
```

**RULE-006 mapping on `cancel`:** treat `remaining = stream.remaining_balance()` as the quantized gross; derive both sub-allocations from it and enforce the zero-leak invariant:

```rust
let gross = stream.remaining_balance();      // quantize/derive gross ONCE
let vested_due = vested_unpaid(&stream);     // sub-allocation 1
let sender_refund = gross - vested_due;      // sub-allocation 2, derived — not computed independently
assert!(vested_due + sender_refund == gross); // zero-leak invariant
```

Both allocations derive from `gross`; `sender_refund` is computed as the remainder rather than re-derived from a second formula — this is what makes drift structurally impossible.

## Strategy — Option B (fallback: ABI/storage must be preserved)

Keep the field, but make it **self-healing rather than asserted**: on every write, recompute and overwrite from the derived formula (not `debug_assert` — it's compiled out in release, so it cannot "enforce" anything in prod). Add a release-mode `assert_eq!` only if the cost is acceptable; otherwise write-derived is strictly better than assert-stored.

## Regression Prevention

- **Invariant test:** after every op, `stream.remaining_balance() == deposit_amount - recipient_withdrawn` — tautological under Option A, which is the point; it protects Option B.
- **Sequence test:** fuzz interleaved `withdraw`/`cancel` orderings, including cancel-before-start, cancel-mid-stream, cancel-after-end, and withdraw-to-zero.
- **Event assertions:** verify `TokensWithdrawn.remaining_balance` equals the post-mutation derived value (this catches emit-before-write ordering bugs).
- **Boundary tests:** `payout == remaining` (full drain), `payout` exceeding vested entitlement, `deposit_amount` at `i128` extremes.
- **Storage check:** if upgrading a deployed contract, add a deserialization test against a ledger entry serialized with the *old* struct.

## Execution Note (RULE-001)

Scouting/cloning/CI reads for `Perenna-Labs/perenna-contracts` may run under the GitHub App, but the PR branch push and PR creation against the public repo must go through the PAT-authenticated user account — the App credential must not perform external public-repo writes.

**Bottom line:** Option A with a single `remaining_balance()` method, `cancel` splitting via gross-first remainder derivation, and a compatibility DTO if the struct leaks through a view function. Confirm the two gating questions (deployed state, direct struct return) before committing to field removal.

## Code Fix (SWE-2)
None\n