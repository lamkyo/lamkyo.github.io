# Bounty Proposal: Perenna-Labs/perenna-contracts#110 - [Bounty: $90] Bound the `withdraw` transfer by `remaining_balance`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $90] Bound the `withdraw` transfer by `remaining_balance`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
RAW_RADAR_CANDIDATE: This `withdraw` guard request is actionable and codeable with a clear file, bound, and acceptance criteria. It remains un-elevated to VERIFIABLE_CODE_ISSUE pending confirmation of the public repo and reproducible `make test` suite.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
The user wants me to fix a bounty issue in `Perenna-Labs/perenna-contracts` by bounding the `withdraw` transfer by `remaining_balance`. However, I cannot access the codebase, so I don't know the specifics of the `withdraw` function or the `remaining_balance` variable. I'll need to ask for more information about the relevant files and their contents.

The embedded rules require classifying radar items as RAW_RADAR_CANDIDATE unless a public Git repo with reproducible test suites is confirmed, and all generated patches must pass a sandbox check. Since I cannot access the repository or run sandbox checks, I cannot generate a diff with exact lines, as that would be fabrication. I must explain this limitation and ask for the relevant files or code snippets, while offering a speculative generic pattern as a RAW_RADAR_CANDIDATE.

Given the invariants, I must classify this as RAW_RADAR_CANDIDATE because I lack repo access and reproducible tests to create a verified patch. I'll plainly state this limitation and request the necessary information. I can offer a generic, illustrative code sketch, clearly marked as unverified, to be helpful. I also need to acknowledge the ambiguity in the programming language and variable naming conventions, as `remaining_balance` suggests Rust but could appear in Solidity.

I can't access the repository, so I can't provide exact-line diffs. Per the invariants, I must mark this as unverified and ask for the file path containing `withdraw`, its current body, the `remaining_balance` field, the framework/language, and the test setup. I'll also provide a minimal, generic illustrative pattern for both Solidity and Rust/Anchor, clearly labeled as speculative.I can't produce this patch yet — I don't have access to the `Perenna-Labs/perenna-contracts` repository, and I wasn't able to locate the `withdraw` function or a `remaining_balance` field in the codebase available to me. Writing a diff with "exact lines and imports" without the actual source would be fabricated context lines, which violates **[RULE-002-SYNTAX-GROUNDING]** (can't be sandbox-verified) and **[RULE-003-RADAR-UNCERTAINTY]** (this stays a `RAW_RADAR_CANDIDATE` until the repo + reproducible tests are confirmed — I can't verify that `Perenna-Labs/perenna-contracts` is a public repo with a test suite).

To generate a real surgical diff, please provide:

1. **File path and full body** of the contract/module containing `withdraw`
2. **Language/framework** — the name suggests Solidity, but `remaining_balance` (snake_case) hints at Rust (Anchor/CosmWasm) or Move
3. **How `remaining_balance` is derived** — a state field, a computed view, or a token balance check
4. **Existing test file** for `withdraw` so assertions match your test harness

Generically, the fix is one of these two patterns — pick whichever matches the issue intent:

```rust
// Clamp (bound) — transfer min(requested, remaining)
let payout = amount.min(remaining_balance);
require!(payout > 0, ErrorCode::NothingToWithdraw);
// ... transfer payout, decrement remaining_balance
```

```rust
// Reject — revert if requested exceeds remaining
require!(amount <= remaining_balance, ErrorCode::ExceedsRemainingBalance);
// ... transfer amount, decrement remaining_balance
```

"Bound by" most likely means clamp, but whether the bounty expects `min()` or a hard revert depends on the issue spec — share the file and I'll write the exact diff plus tests.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Bound `withdraw` transfer by `remaining_balance`

**Repository:** Perenna-Labs/perenna-contracts
**Bounty:** $90
**Proposal status:** `RAW_RADAR_CANDIDATE` → `BLOCKED_ON_SOURCE`
**Egress state:** `NOT_AUTHORIZED` — no diff, branch, or PR may be opened from this document

---

## 0. Verification Ledger

Per **[RULE-003-RADAR-UNCERTAINTY]**, every claim below is tagged by evidence class. Nothing in this proposal is `VERIFIABLE_CODE_ISSUE` yet.

| Artifact | State | Evidence required to elevate |
|---|---|---|
| Repo is public + has reproducible test suite | `UNCONFIRMED` | `git ls-remote` success + CI config or `tests/` tree |
| `withdraw` source located | `UNCONFIRMED` | Full file body supplied |
| `remaining_balance` is a state field vs. computed view | `UNCONFIRMED` | Struct/state declaration + getter |
| Root cause hypothesis | `HYPOTHESIS` | Failing test reproducing the unbounded transfer |
| Patch compiles/lints | `NOT_RUN` | **[RULE-002]** sandbox `go vet` / `tsc` / `ast.parse` / `solc` / `cargo check` |
| Patch marked `PASS` / `READY_FOR_EGRESS` | `FORBIDDEN` until above two pass | — |

**Why no diff is included:** producing "exact lines and imports" without the source means fabricating context lines and hunk headers. That is unverifiable by construction and violates **[RULE-002-SYNTAX-GROUNDING]**. The code blocks in §4 are illustrative patterns, explicitly not a patch.

---

## 1. Problem Statement

`withdraw` performs an outward transfer whose size is not constrained by the account's `remaining_balance`. The intended invariant is:

```
transferred_amount <= remaining_balance   (pre-transfer, per caller)
```

If the transfer amount is caller-controlled and unchecked against `remaining_balance`, the function can over-disburse relative to the accounting ledger.

---

## 2. Root Cause — Ranked Hypotheses (not confirmed)

| # | Hypothesis | Signature in source | Fix shape |
|---|---|---|---|
| H1 | **Missing clamp** — `amount` transferred directly, no comparison to `remaining_balance` | `transfer(to, amount)?;` with no guard above | Add bound (§4-A/B) |
| H2 | **Stale read** — `remaining_balance` read before mutation or decremented after an early return | balance fetched, then transfer, then decrement | Reorder; single read at top |
| H3 | **Unit/scale mismatch** — `amount` and `remaining_balance` in different decimals or bases | one uses `decimals()`, other a raw field | Normalize to one unit |
| H4 | **Second path** — batch/emergency/`withdraw_all` variant bypasses the bound | second `transfer` call site | Apply bound in shared internal helper |

H4 is the most common reason a "surgical fix" fails review: the guard is added to one entry point and the sibling entry point remains unbounded. Any accepted patch should route both through one internal function.

---

## 3. Decision Required: Clamp vs. Revert

"Bound by" is ambiguous and the two semantics are not interchangeable. This must be resolved by the issue text or maintainer, **not guessed**.

| | Clamp (`min`) | Revert |
|---|---|---|
| Semantics | Silently pay `min(requested, remaining)` | Fail if `requested > remaining` |
| Caller experience | Partial fill, no signal | Explicit error |
| Accounting | Ledger drains exactly to zero | Ledger unchanged on failure |
| Risk if wrong choice | Under-disbursement; no user signal; hard to audit | DoS if `remaining_balance` is transiently stale |
| Typical intent | Vault "withdraw up to" | Strict share/position accounting |

**Recommendation:** if `remaining_balance` is a strict accounting invariant, choose **revert** — clamping hides a caller bug and complicates reconciliation. If it is a soft cap, choose **clamp** and emit an event recording the requested vs. paid delta.

---

## 4. Implementation (Illustrative — not a patch)

### 4-A. Rust / Anchor / CosmWasm variant

```rust
// <<PATH_UNRESOLVED>>
let remaining_balance = ctx.accounts.account.remaining_balance;

// Revert semantics
require!(
    amount <= remaining_balance,
    ErrorCode::ExceedsRemainingBalance
);
let payout = amount;

// -- or -- Clamp semantics
// let payout = amount.min(remaining_balance);
// require!(payout > 0, ErrorCode::NothingToWithdraw);

ctx.accounts.account.remaining_balance = remaining_balance
    .checked_sub(payout)
    .ok_or(ErrorCode::MathOverflow)?;

// transfer `payout` via the existing CPI / token program call
```

### 4-B. Solidity variant

```solidity
// <<PATH_UNRESOLVED>>
uint256 remaining = remainingBalance[msg.sender];

// Revert semantics
if (amount > remaining) revert ExceedsRemainingBalance(amount, remaining);
uint256 payout = amount;

// -- or -- Clamp semantics
// uint256 payout = amount < remaining ? amount : remaining;
// if (payout == 0) revert NothingToWithdraw();

remainingBalance[msg.sender] = remaining - payout;   // or unchecked-safe sub
emit Withdrawn(msg.sender, amount, payout);          // amount vs paid, if clamping
_send(msg.sender, payout);
```

**Both variants require:** the actual error-enum/error-name convention in use, the real transfer primitive, and the real field path. All three are unresolved.

---

## 5. Test Verification Plan

To be written against the real harness; command lines stay plain (configure any proxy/mir
\n