# Bounty Proposal: Perenna-Labs/perenna-contracts#54 - [Bounty: $90] Reject `create_stream` when the sender is the stream contract itself\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $90] Reject `create_stream` when the sender is the stream contract itself

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: it's a small, well-scoped guard in `create_stream` (`contracts/stream/src/lib.rs`) that returns a typed error when `sender == env.current_contract_address()`, plus a spec note and tests, and the $90 bounty clears the $25 minimum gate with no scam indicators. The only caveat is that the "Suggested" section is truncated, so confirm the proposed error variant naming and the §5 invariant test location before starting.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
The user wants me to analyze a GitHub issue for a bounty task, roleplaying as a Senior Systems Architect, though I'm the Codeium assistant. I'll proceed with the technical analysis without claiming a false identity. The task involves analyzing root causes, identifying files, and designing an architectural strategy for a Soroban smart contract issue where `create_stream` should reject calls from the stream contract itself. I can't access the codebase directly, but I'll provide an analysis based on the issue description and Soroban patterns, noting this limitation.

The system prompt indicates I can access the codebase but might not find relevant parts. I need to be cautious, offering analysis while noting that specific details like error enum names might require file contents for confirmation. My analysis will focus on the `create_stream` function, specifically how it calls `sender.require_auth()` and handles token transfers when the sender is the contract itself, which could lead to issues like double-counting or misleading events.

I'm realizing that `sender.require_auth()` within a contract's own invocation in Soroban isn't trivially authorized. It requires explicit authorization via `__check_auth` or `authorize_as_current_contract`. This means a `cancel` operation on a self-initiated stream would likely fail or require complex authorization, potentially locking funds or corrupting accounting. This also seems to break the balance invariant mentioned later, as self-deposits and refunds could net strangely.

I'm realizing that a self-transfer, while a no-op for the token contract's balance, still triggers a deposit event in the stream ledger. This leads accounting to believe the contract holds escrowed funds it "owes" to itself. If a recipient then withdraws, the contract might pay out from other users' escrowed funds, violating the invariant that the contract's balance must cover all active streams. This corruption stems from the ledger incorrectly reflecting a deposit when the token balance remains unchanged.

I need to add a typed error variant like `SelfReferentialSender` to `contracts/stream/src/error.rs`, ensuring it's appended to maintain ABI compatibility. Documentation in `CONTRACT_SPEC.md` should be updated, and tests in `contracts/stream/src/test.rs` must verify that `create_stream` rejects self-calls while still allowing normal senders. No new events are required.

I'm considering the order of operations for authorization and input validation. While placing `require_auth` first prevents probing, validating inputs beforehand is standard practice and avoids unnecessary authorization checks. For tests, `env.mock_all_auths()` is common, but placing the guard before `require_auth` is cleaner and allows negative test cases without mocking. I'll recommend this order, noting the tradeoff. I also need to decide whether to reject `recipient == contract`, which seems out of scope based on the issue description.

I'm considering adding a `cancel`/`withdraw` defense-in-depth, but it seems unnecessary if creation is impossible due to self-sender issues. If existing streams are already deployed, storage migration is out of scope for this fix. I need to confirm the exact placement for the invariant test, likely in `contracts/stream/src/test.rs`, and flag this confirmation. For error naming, I'll check the existing enum and suggest a name like `SenderIsContract` or `InvalidSender`, flagging the choice in the PR.

I need to add a caveat that I haven't seen the actual files, so any file paths or symbol names are inferred and must be verified. I'll present the analysis as a plan with these inferred paths and flag verification points. The response should be in markdown, with headers, concise bullets, and Rust code sketches, structured as a medium-length response suitable for a design/analysis ask.## Triage Gate Check

- **Payout**: $90 ≥ $25 minimum → passes the zero-payout gate.
- **Scam scan**: no flagged keywords, legitimate repo + spec references → proceed.
- **Scope**: small, well-scoped, codeable. Two unknowns flagged from the truncated "Suggested" section: **error variant naming** and **§5 invariant test location** — resolve before coding (read the error enum + spec first; if ambiguous, comment on the issue rather than guess).

⚠️ Caveat: I don't have the repo contents in front of me — paths/symbols below are inferred from the issue and standard Soroban layout. Verify against the actual tree.

## Root Cause

`create_stream` accepts any `sender` that passes `require_auth`. If `sender == env.current_contract_address()`:

1. **Escrow deposit is a no-op.** The initial token `transfer` moves contract → contract, so the token balance doesn't change — but stream accounting records a funded stream.
2. **§5 invariant corrupts.** Recipient `withdraw` pays out *real* tokens against a deposit that never arrived, draining other streams' collateral → insolvency.
3. **`cancel` is uncallable or self-refunding.** `sender.require_auth()` on the contract's own address requires self-authorization (`authorize_as_current_contract`) that nothing provides → funds locked, or a contract→contract refund no-op while accounting decrements.

The fix belongs at the entry point — no existing stream can have a self-sender, so no migration or downstream guards needed.

## Files to Touch

| File | Change |
|---|---|
| `contracts/stream/src/lib.rs` | Guard in `create_stream` |
| `contracts/stream/src/error.rs` (or wherever `#[contracterror]` enum lives) | Append new variant — **append only, never reorder** (error codes are ABI-stable) |
| `docs/CONTRACT_SPEC.md` | One-line rule near the `create_stream` section / §5 |
| `contracts/stream/src/test.rs` | 3 tests (below) |
| `.github/workflows/ci.yml`, `Makefile` | Read-only — confirm `check` job steps so local runs match |

## Implementation Sketch

```rust
// In create_stream — BEFORE sender.require_auth().
// Rationale: fail-fast on invalid input before recording an auth
// footprint; also keeps the negative test free of auth mocking.
// (If codebase convention is auth-first, match it and use
//  env.mock_all_auths() in tests instead.)
if sender == env.current_contract_address() {
    return Err(Error::SelfReferentialSender); // name TBD — match convention
}
sender.require_auth();
```

If the codebase uses `panic_with_error!` instead of `Result`, mirror that idiom exactly.

## Test Plan

1. **Negative**: `create_stream(contract_address, …)` → expect the typed error. In Soroban tests: `let contract_addr = env.register_contract(None, StreamContract);` then pass it as `sender`.
2. **Regression**: normal externally-owned `sender` succeeds, stream state identical to pre-change behavior.
3. **Invariant**: re-run the §5 invariant test (e.g., `balance == sum(active stream liabilities)`) unchanged — must stay green. Confirm its location; if it doesn't exist as a discrete test, that's worth flagging in the PR description, not silently adding scope.

## Regression Checklist

- ✅ Error enum: append-only, preserve discriminants.
- ✅ No storage schema, event, or signature changes.
- ✅ Guard order vs. `require_auth`: check existing tests asserting `env.auths()` — ordering change could break them.
- ✅ `make test` + `cargo fmt --check` + `clippy` locally before pushing (mirror `check` job).
- 🚫 Out of scope (don't scope-creep a bounty): rejecting `recipient == contract`, rejecting other contract senders, custody-contract parity beyond what the issue asks. Note as follow-up if relevant.
- 🚫 Per boundary rules: all PR/issue write actions via authenticated user PAT; no GitHub App writes to the public repo.

## Open Questions to Resolve First

1. Error variant name — inferred candidates: `SelfReferentialSender`, `InvalidSender`, `SenderIsContract`. Check existing naming style; truncated suggestion may have specified one.
2. Exact location/name of the §5 invariant test.
3. Whether `create_stream` returns `Result` or panics — dictates guard idiom.

**Estimated effort**: ~1–2 hrs including spec read; 24h ETA is comfortable.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — `perenna-contracts` Bounty #<issue-number> ($90)

**Deliverable owner:** Claude — Delivery & Quality Verification Lead, Anthropic
**Repository:** `Perenna-Labs/perenna-contracts`
**Issue:** *Reject `create_stream` when the sender is the stream contract itself*

---

## 0. Gate Status Block (read first)

| Field | Value |
|---|---|
| Radar classification | **`RAW_RADAR_CANDIDATE`** |
| Elevation criterion | Confirm public repo access + reproducible test suite locally → then `VERIFIABLE_CODE_ISSUE` |
| Patch artifact | **None.** SWE-2 returned `Code Patch: None` |
| Egress gate | **`BLOCKED — NOT READY_FOR_EGRESS`** |
| Unblock condition | Patch exists **and** a deterministic compiler/linter run (`cargo fmt --check`, `clippy -D warnings`, `cargo test`) passes in a sandbox, with raw output captured |

This proposal is a **specification**, not a verified patch. Per the syntax-grounding invariant, nothing in this document may be flipped to `PASS` or `READY_FOR_EGRESS` on the strength of reasoning alone. Every code block below is a *candidate* that must survive a real compiler.

**Verification caveat:** I do not have the repository contents in this session. All paths, symbol names, and error-variant names are **inferred** from the issue text and standard Soroban layout. Each inferred item is marked `⟨VERIFY⟩` and must be confirmed against the actual tree before the PR is opened.

---

## 1. PR Metadata

```
Title:   fix(stream): reject self-referential sender in create_stream
Branch:  fix/stream-reject-self-sender
Base:    main
Labels:  bug, bounty, stream-contract, needs-review
Fork:    <user>/perenna-contracts  (branch pushed here — never to upstream)
Sign-off: Signed-off-by: <user> <email>   (if DCO is enforced)
```

**Commit message:**

```
fix(stream): reject self-referential sender in create_stream

Accepting the stream contract as its own sender records a funded stream
while the escrow transfer is a contract->contract no-op. Recipient
withdrawals then pay real tokens against collateral that never arrived,
draining other streams and breaking the solvency invariant.

Guard create_stream before authorization, append a typed error variant
(additive, discriminant-stable), document the rule, and cover it with
negative, regression, and invariant tests.

Refs: #<issue-number>
```

---

## 2. Root Cause Analysis

`create_stream` accepts any `sender` that satisfies `sender.require_auth()`. When `sender == env.current_contract_address()`, three distinct failure modes compound:

| # | Failure | Mechanism | Impact |
|---|---|---|---|
| 1 | **Escrow deposit is a no-op** | Initial token `transfer` is contract → contract; token balance is unchanged, but stream accounting records a fully funded stream | Ledger believes it holds escrowed collateral it does not hold |
| 2 | **Solvency invariant corrupts** | Recipient `withdraw` pays *real* tokens against a deposit that never arrived | Drains collateral backing *other* streams → protocol insolvency |
| 3 | **`cancel` is uncallable or self-refunding** | `sender.require_auth()` against the contract's own address needs self-authorization (`authorize_as_current_contract`) that nothing provides; or, if it does resolve, the refund is a contract → contract no-op while accounting decrements | Funds locked, or accounting diverges from token reality |

**Why the fix belongs at the entry point.** No pre-existing stream can have a self-referential sender under a correct prior implementation, and the guard is applied at creation, so:

- No storage migration required.
- No downstream guards in `withdraw` / `cancel` required (defense-in-depth there is explicitly **out of scope** for this bounty).
- No event schema change.
- No public function signature change.

**Rejected alternatives**

- *Guard at the token-transfer layer* — the token contract cannot know it is participating in a self-dealing stream; the check is meaningless there.
- *Guard only in `cancel`*
\n