# Bounty Proposal: Perenna-Labs/perenna-contracts#109 - [Bounty: $70] Validate `token_addr != env.current_contract_address()` in `create_stream`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $70] Validate `token_addr != env.current_contract_address()` in `create_stream`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: `contracts/stream/src/lib.rs::create_stream` needs a guard rejecting `token_addr == env.current_contract_address()` with typed error + spec doc update, acceptance criteria are clear (self-address fails, normal SAC succeeds, `contract balance >= Σ remaining_balance` preserved, `make test`/`check` job green).

Per [RULE-003-RADAR-UNCERTAINTY] classify as **RAW_RADAR_CANDIDATE** until public repo `Perenna-Labs/perenna-contracts` and reproducible test suite are confirmed - not yet **VERIFIABLE_CODE_ISSUE**; patch must still pass [RULE-002-SYNTAX-GROUNDING] sandbox check before READY_FOR_EGRESS.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm working on the Perenna-Labs/perenna-contracts repo, which seems to be a Soroban/Stellar smart contract project. The issue is to validate `token_addr != env.current_contract_address()` in `create_stream`. I don't have direct access to the codebase, so I'll need to provide a patch based on typical Soroban structures and clearly state that it requires verification. I also can't run sandbox compilation checks, so I'll note that limitation as well.

I need to add a check to prevent the contract from streaming its own token, which could cause reentrancy or accounting issues. Since I don't have the actual codebase, I'll provide a generic patch based on typical Soroban structures and request the specific file containing the `create_stream` function for an accurate fix.

I've drafted a patch to add validation in `create_stream` to prevent the token address from being the contract address itself, which is idiomatic in Soroban using `panic_with_error!`. I'll include a unit test and a git diff, but I must note that the diff requires manual adjustment for line numbers and context, and the code is unverified as I cannot run it in a sandbox.

I've added a new `StreamError::TokenIsContract` variant and a check within `create_stream` to prevent the contract from using its own address as the token address. I've also included a unit test using the `try_create_stream` method to verify this rejection, noting the specific return type `Result<Ok(T), Err(Ok(E))>` for Soroban tests.**Status: DRAFT — UNVERIFIED (per RULE-002, not yet compiled in sandbox).** I don't have visibility into the actual `perenna-contracts` file contents, so paths/hunk headers below are based on the standard Soroban workspace layout (`contracts/*/src/lib.rs`). Provide the file containing `create_stream` and I'll re-anchor the diff exactly.

## Change

Reject streams where the streamed token is the contract itself — prevents self-referential accounting/reentrancy issues.

```rust
// contracts/stream/src/lib.rs (or wherever create_stream lives)

// 1. Extend the contract error enum (append, don't renumber existing variants):
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum StreamError {
    // ... existing variants ...
    TokenIsContract = 12, // next free discriminant
}

// 2. In create_stream, alongside existing input validation:
if token_addr == env.current_contract_address() {
    panic_with_error!(&env, StreamError::TokenIsContract);
}
```

## Patch

```diff
diff --git a/contracts/stream/src/lib.rs b/contracts/stream/src/lib.rs
--- a/contracts/stream/src/lib.rs
+++ b/contracts/stream/src/lib.rs
@@ enum StreamError @@
     // ... existing variants ...
+    TokenIsContract = 12,
 }
 
@@ fn create_stream @@
         // existing checks (amount > 0, end_time > start_time, etc.)
+        if token_addr == env.current_contract_address() {
+            panic_with_error!(&env, StreamError::TokenIsContract);
+        }
+
         // ... rest of stream creation
```

No new imports needed — `panic_with_error!` and `env.current_contract_address()` are already available via `soroban_sdk` prelude in any contractimpl module.

## Test

```rust
#[test]
fn test_create_stream_rejects_contract_token() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);

    let sender = Address::generate(&env);
    let recipient = Address::generate(&env);

    let res = client.try_create_stream(
        &sender,
        &recipient,
        &contract_id, // token_addr == contract address
        &1_000,
        &0,
        &100,
    );

    assert_eq!(res, Err(Ok(StreamError::TokenIsContract)));
}
```

## To finalize

1. Paste `create_stream`'s actual signature + the error enum (or point me at the file) so I can fix identifiers, arg order, and discriminant numbering.
2. Run `cargo test -p <crate>` and `cargo clippy` in your sandbox — only then mark READY_FOR_EGRESS per RULE-002.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Validate `token_addr != env.current_contract_address()` in `create_stream`

**Status: `DRAFT — UNVERIFIED`. Not `READY_FOR_EGRESS`.**

> **Gating disclosure (RULE-002-SYNTAX-GROUNDING):** No deterministic compiler/linter pass (`cargo check`, `cargo clippy`, `cargo test`) has been executed against this patch. No sandbox was available in this session, and no file contents from `Perenna-Labs/perenna-contracts` were retrieved. Every path, identifier, argument order, and discriminant below is **inferred from standard Soroban workspace conventions**, not read from the repository. This proposal must not be marked PASS or submitted upstream until the gates in §7 are cleared.

---

## 1. PR Metadata

| Field | Value |
|---|---|
| Repo | `Perenna-Labs/perenna-contracts` |
| Bounty | $70 — *Validate `token_addr != env.current_contract_address()` in `create_stream`* |
| Type | Security hardening / input validation |
| Severity | Medium (self-referential token → accounting corruption, potential reentrancy surface) |
| Branch (proposed) | `fix/create-stream-reject-self-token` |
| Labels (proposed) | `security`, `soroban`, `needs-verification` |
| Author of record | Claude — Delivery & Quality Verification Lead |
| Base commit | **UNKNOWN — requires pinning** |

---

## 2. Radar Classification

Per **RULE-003-RADAR-UNCERTAINTY**:

```
classification: RAW_RADAR_CANDIDATE
reason:         Repository existence, visibility, and presence of a reproducible
                test suite (cargo test) were NOT confirmed in this session.
                No clone, no manifest read, no CI signal observed.
promotion_path: Confirm public git remote + `Cargo.toml` workspace + runnable
                test target for the crate containing `create_stream`.
                On confirmation → VERIFIABLE_CODE_ISSUE.
```

This item is **not** currently a `VERIFIABLE_CODE_ISSUE`. It is a candidate derived from the issue text alone.

---

## 3. Root Cause

`create_stream` accepts a `token_addr: Address` parameter and proceeds to construct a stream without asserting that the token being streamed is not the stream contract itself.

**Why this matters:**

1. **Self-referential accounting.** If `token_addr == env.current_contract_address()`, the contract's own token balance becomes both the escrow asset and the accounting subject. Any internal bookkeeping that reads "token balance of this contract" now reads the balance that the stream itself is mutating — a classic aliasing bug that can make `total_streamed` / `total_withdrawable` invariants unsatisfiable.
2. **Reentrancy / callback surface.** Depending on how token transfers are dispatched (SEP-41 token client `transfer` calls), routing a transfer to the contract's own address re-enters the contract through the token interface, or at minimum creates a path where an outbound transfer credits the caller-controlled accounting state.
3. **Defensive boundary.** Even if no *currently reachable* exploit exists, `create_stream` is a permissionless entry point. The invariant "a stream cannot be denominated in the stream contract's own address" is cheap to enforce and eliminates an entire class of future regressions.
4. **Failure mode today is silent.** Absent the check, a caller passing the contract address gets either a confusing downstream panic (deep in token logic) or, worse, a successfully created stream with corrupted state. Neither is diagnosable by an integrator.

**Fix:** fail fast, at the top of the validation block, with a typed contract error.

---

## 4. Implementation

### 4.1 Error enum extension

```rust
// Append to the existing #[contracterror] enum. Do NOT renumber existing variants —
// discriminants are part of the on-chain ABI and renumbering silently breaks
// off-chain decoders.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum StreamError {
    // ... existing variants unchanged ...
    TokenIsContract = 12, // <-- VERIFY: must be exactly max(existing) + 1
}
```

> **⚠ Blocker:** `12` is a placeholder. If the existing enum is declared without explicit discriminants (implicit `0,1,2,…`), appending a bare `TokenIsContract,` is safer than guessing a literal. If it uses explicit literals, the next free value must be read from source.

### 4.2 Guard in `create_stream`

```rust
// Insert into the existing input-validation block, before any state write
// and before any token transfer.
if token_addr == env.current_contract_address() {
    panic_with_error!(&env, StreamError::TokenIsContract);
}
```

**No new imports required.** `panic_with_error!` is exported from the `soroban_sdk` prelude, and `current_contract_address()` is available on `Env` inside any `#[contractimpl]` module. `Address` implements `PartialEq`, so `==` is valid.

### 4.3 Diff (placeholder-anchored)

```diff
diff --git a/contracts/stream/src/lib.rs b/contracts/stream/src/lib.rs
--- a/contracts/stream/src/lib.rs
+++ b/contracts/stream/src/lib.rs
@@ enum StreamError @@
     // ... existing variants ...
+    TokenIsContract = 12,
 }
 
@@ fn create_stream @@
         // existing checks (amount > 0, end_time > start_time, ...)
+        if token_addr == env.current_contract_address() {
+            panic_with_error!(&env, StreamError::TokenIsContract);
+        }
+
         // ... rest of stream creation
```

> **⚠ Blocker:** The `@@` hunk headers are **not valid unified diff** and will be rejected by `git apply`. This must be re-anchored against real line numbers with ≥3 lines of real context before the PR can be opened. A diff that does not apply is a hard failure under RULE-002.

---

## 5. Test Verification

### 5.1 Proposed unit test

```rust
#[test]
fn test_create_stream_rejects_contract_token() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register_contract(None, StreamContract); // VERIFY: SDK deprecation
    let client = StreamContractClient::new(&env, &contract_id);

    let sender = Address::generate(&env);
    let recipient = Address::generate(&env);

    let res = client.try_create_stream(
        &sender,
        &recipient,
        &contract_id, // token_addr == contract address
        &1_000,
        &0,
        &100,
    );

    assert_eq!(res, Err(Ok(StreamError::TokenIsContract)));
}
```

### 5.2 Test caveats — each is a hard gate, not a note

| # | Caveat | Why it blocks |
|---|---|---|
| T1 | `env.register_contract(None, C)` is deprecated in current Soroban SDK in favour of `env.register(C, ())`. | Will not compile on modern SDK. Must confirm pinned `soroban-sdk` version. |
| T2 | `try_*` return shape differs
\n