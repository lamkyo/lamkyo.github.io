# Bounty Proposal: Perenna-Labs/perenna-contracts#98 - [Bounty: $75] Stop `get_next_stream_id` from masking a missing `NextStreamId` key\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $75] Stop `get_next_stream_id` from masking a missing `NextStreamId` key

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
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm looking at the Perenna-Labs/perenna-contracts repo, specifically an issue about `get_next_stream_id` masking a missing `NextStreamId` key. This sounds like a Soroban smart contract, likely for payment streams. The problem seems to be that `unwrap_or(0)` is used when fetching the key, which hides the uninitialized state. A fix would involve returning a `Result` or checking `has` before getting the value.

I can't access the repository directly, so I can't write exact code changes. Given the invariants, I must classify this as RAW_RADAR_CANDIDATE. I'll provide a best-effort patch based on common patterns, but it needs verification and must pass `cargo check`/`cargo test` in a sandbox before being marked READY.

I'm considering how to fix the `get_next_stream_id` function in Soroban contracts. The current implementation uses `unwrap_or(0)`, which masks uninitialized states and could lead to collisions or hide bugs. The best fix is likely to return a `Result<u64, ContractError>` using `.ok_or(ContractError::NotInitialized)` or to use `.expect()` with a descriptive message if the function signature must remain `u64`. I'd also add a test case to ensure it panics correctly when the key is missing.

I'm considering two patch variants for `get_next_stream_id`: one using `.expect()` if the function returns `u64`, and another using `.ok_or()` if it returns `Result`. I'll also add a `has` check variant and ensure `initialize` sets `NextStreamId` appropriately, likely to 0 or 1, to avoid the "masking a missing key" issue by enforcing a hard error.

I'll initialize the `NextStreamId` to 0 in the storage, and I'll add a test case `next_stream_id_errors_when_uninitialized` to verify that fetching this ID before initialization correctly returns an error. I'll present this as a draft patch, noting that it requires compilation and testing, and I'll include the `Result` variant for error handling.## Status: `RAW_RADAR_CANDIDATE` — patch is `DRAFT`, not `READY_FOR_EGRESS`

Per **RULE-003**, I have not confirmed a public clone of `Perenna-Labs/perenna-contracts` or its test suite from this environment, so I can't verify exact line numbers or the real signature of `get_next_stream_id`. The patch below targets the canonical Soroban/Rust pattern for this bug (`DataKey::NextStreamId` read with a silent default). Ground it against the actual file before egress; per **RULE-002** it must pass `cargo test` in a sandbox first.

## Root cause (probable)

```rust
fn get_next_stream_id(env: &Env) -> u64 {
    env.storage()
        .instance()
        .get(&DataKey::NextStreamId)
        .unwrap_or(0) // or .unwrap_or_default() — masks uninitialized storage
}
```

A missing key silently yields `0`, colliding with a real stream ID and hiding a skipped `initialize`.

## Patch (panic variant — minimal diff, signature preserved)

```diff
--- a/contracts/stream/src/lib.rs
+++ b/contracts/stream/src/lib.rs
@@ fn get_next_stream_id
     fn get_next_stream_id(env: &Env) -> u64 {
         env.storage()
             .instance()
             .get(&DataKey::NextStreamId)
-            .unwrap_or(0)
+            .expect("NextStreamId key missing: contract not initialized")
     }
```

## Patch (typed-error variant — if the crate exposes an error enum)

```diff
-    fn get_next_stream_id(env: &Env) -> u64 {
-        env.storage()
-            .instance()
-            .get(&DataKey::NextStreamId)
-            .unwrap_or(0)
-    }
+    fn get_next_stream_id(env: &Env) -> Result<u64, ContractError> {
+        env.storage()
+            .instance()
+            .get(&DataKey::NextStreamId)
+            .ok_or(ContractError::NotInitialized)
+    }
```

Add `NotInitialized` to `ContractError` if absent, and update call sites (`let id = get_next_stream_id(&env)?;`).

Also confirm `initialize` seeds the counter (this is what the getter should *require*):

```rust
env.storage().instance().set(&DataKey::NextStreamId, &0u64);
```

## Unit tests

```rust
#[test]
#[should_panic(expected = "NextStreamId key missing")]
fn next_stream_id_panics_when_uninitialized() {
    let env = Env::default();
    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);
    client.create_stream(&recipient, &token, &amount, &start, &stop); // no initialize()
}

#[test]
fn next_stream_id_starts_at_zero_after_init() {
    let env = Env::default();
    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);
    client.initialize(&admin);
    assert_eq!(client.next_stream_id(), 0);
    client.create_stream(&recipient, &token, &amount, &start, &stop);
    assert_eq!(client.next_stream_id(), 1);
}
```

## Required validation before `READY_FOR_EGRESS` (RULE-002)

```bash
cargo fmt --check && cargo clippy -- -D warnings
cargo test next_stream_id
cargo build --target wasm32-unknown-unknown --release
```

## Egress note (RULE-001)

If this fix goes to a public upstream PR, push/PR via an authenticated user PAT — the GitHub App credential stays scoped to clone/scout/internal repos.

Want me to adapt this once you paste the actual `get_next_stream_id` body and `DataKey` enum? Exact context lines differ per storage layout (`instance` vs `persistent`, `Symbol` vs `#[contracttype]` key).

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $75] Stop `get_next_stream_id` from masking a missing `NextStreamId` key
**Proposed branch:** `fix/next-stream-id-missing-key`
**Labels:** `bounty`, `bug`, `soroban`, `needs-verification`

---

## 0. Status & Classification

| Field | Value |
|---|---|
| Classification | `RAW_RADAR_CANDIDATE` |
| Patch state | `DRAFT` — **not** `READY_FOR_EGRESS` |
| Verification state | **NOT RUN** — no sandbox execution performed in this environment |
| Confirmed against source | ❌ No (no verified clone / reproducible test suite confirmed) |

**Per RULE-003:** this remains `RAW_RADAR_CANDIDATE`. It may be elevated to `VERIFIABLE_CODE_ISSUE` only once a public Git repository with a reproducible test suite is confirmed and the patch compiles there.

**Per RULE-002:** no hunk below may be marked `PASS` until `cargo fmt` / `cargo clippy` / `cargo test` / `wasm32` build succeed in a sandbox.

**Per RULE-001:** any public upstream write (push, PR, comment) goes through an authenticated **user PAT**. The GitHub App credential is limited to quota shielding, scouting, cloning, and internal repos.

> **Honesty note:** every code block in this document is a *pattern-matched sketch*, not a verified diff. Line numbers, file paths, type names, and the existence of `ContractError` / `DataKey` variants are all unconfirmed. Nothing here should be pasted upstream before grounding.

---

## 1. Problem Statement

`get_next_stream_id` reads `DataKey::NextStreamId` from instance storage with a silent default (`unwrap_or(0)` or `unwrap_or_default()`). A missing key — i.e. an uninitialized or corrupted contract — therefore yields `0` instead of surfacing an error.

Two failure modes follow:

1. **ID collision.** `0` is a plausible legitimate first stream ID, so an uninitialized contract silently issues an ID that can collide with an already-issued stream.
2. **Masked initialization bug.** A skipped or failed `initialize` produces no observable signal at the point of failure; the defect surfaces later, somewhere unrelated.

---

## 2. Root Cause

```rust
fn get_next_stream_id(env: &Env) -> u64 {
    env.storage()
        .instance()
        .get(&DataKey::NextStreamId)
        .unwrap_or(0)          // <-- defect: absence of key == legitimate zero
}
```

The getter conflates *"counter is zero"* with *"counter does not exist"*. The type system offers no way to distinguish them because the return type is `u64`, not `Result`.

---

## 3. Design Decision — Panic vs. Typed Error

| Option | Diff size | ABI impact | Recommendation |
|---|---|---|---|
| **A. `.expect(...)`** | 1 line | None (internal fn) | Acceptable if `get_next_stream_id` is private and callers already panic-terminate |
| **B. `.ok_or(ContractError::NotInitialized)`** | Call sites + error enum | Internal signature change; external `try_` behavior changes if the getter is a public contract fn | **Preferred** — recoverable, testable, idiomatic Soroban |
| **C. `.has()` guard + explicit error** | 3–4 lines | Same as B | Equivalent to B; slightly more explicit |

**Recommendation:** Option B if the crate already exposes a `ContractError` enum — it makes the failure recoverable and assertable in tests. Fall back to A only if the function is private, non-`Result`-returning, and changing it would ripple through many call sites.

⚠️ **Blocking unknown:** if `get_next_stream_id` is itself an exported contract entry point, Option B is a **breaking ABI change** and requires a semver/migration decision. Confirm before choosing.

---

## 4. Implementation

### 4.1 Option A — minimal, signature-preserving

```diff
--- a/contracts/stream/src/lib.rs
+++ b/contracts/stream/src/lib.rs
@@ fn get_next_stream_id
     fn get_next_stream_id(env: &Env) -> u64 {
         env.storage()
             .instance()
             .get(&DataKey::NextStreamId)
-            .unwrap_or(0)
+            .expect("NextStreamId key missing: contract not initialized")
     }
```

### 4.2 Option B — typed error (preferred)

```diff
-    fn get_next_stream_id(env: &Env) -> u64 {
-        env.storage()
-            .instance()
-            .get(&DataKey::NextStreamId)
-            .unwrap_or(0)
-    }
+    fn get_next_stream_id(env: &Env) -> Result<u64, ContractError> {
+        env.storage()
+            .instance()
+            .get(&DataKey::NextStreamId)
+            .ok_or(ContractError::NotInitialized)
+    }
```

Follow-ups required:

```rust
// 1. Add the variant if absent.
#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum ContractError {
    // ...
    NotInitialized = 1,
}

// 2. Update every call site.
let id = get_next_stream_id(&env)?;

// 3. Ensure `initialize` seeds the counter — this is what the getter now *requires*.
env.storage().instance().set(&DataKey::NextStreamId, &0u64);
```

**Unconfirmed items to ground before writing the real patch:**
- Exact file path and the real body of `get_next_stream_id`.
- Whether storage is `instance()` or `persistent()`.
- Whether `DataKey` is `#[contracttype]` with a `NextStreamId` variant, and its spelling.
- Whether `initialize` already sets `NextStreamId`, and to `0` or `1` — the test assertion in §5.2 depends on this.
- All call sites of `get_next_stream_id`.

---

## 5. Test Verification

### 5.1 Missing-key behavior

```rust
#[test]
#[should_panic(expected = "NextStreamId key missing")]
fn next_stream_id_panics_when_uninitialized() {
    let env = Env::default();
    let contract_id = env.register_contract(None, StreamContract); // API varies by SDK version
    let client = StreamContractClient::new(&env, &contract_id);
    // deliberately skip initialize()
    client.create_stream(&recipient, &token, &amount, &start, &stop);
}
```

Caveats to resolve on grounding:
- The test must call the **actual** function that invokes `get_next_stream_id`. If `create_stream` is not that caller, this test asserts nothing relevant.
- `recipient` / `token` / `amount` / `start` / `stop` are placeholders — construct them from the repo's existing test fixtures.
- If the repo targets a newer `soroban-sdk`, `env.register_contract(None, …)` may need to be `env.register(StreamContract, ())`. Match the style already in the repo's test module.
- `should_panic` string matching is brittle; if the repo has a house style for error assertions, follow it.

### 5.2 Happy path / regression

```rust
#[test]
fn next_stream_id_starts_at_zero_after_init() {
    let env = Env::default();
    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);
   
\n