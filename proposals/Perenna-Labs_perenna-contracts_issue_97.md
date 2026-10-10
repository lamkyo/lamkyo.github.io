# Bounty Proposal: Perenna-Labs/perenna-contracts#97 - [Bounty: $90] Extend the instance TTL on stream reads so an active contract cannot archive\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $90] Extend the instance TTL on stream reads so an active contract cannot archive

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Verdict: ACTIONABLE**
The issue is clear and codeable: it identifies the missing TTL extension in `contracts/stream/src/lib.rs` (`balance_of`, `get_stream`, `withdraw`, `cancel`) and provides verifiable acceptance criteria, including a test that ages and asserts instance TTL extension after `get_stream`.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm tasked with extending instance TTL on stream reads for "Perenna-Labs/perenna-contracts" to prevent archiving. However, I don't have access to the user's codebase, and this appears to be an external repository. Based on RULE-003, since I cannot confirm a public Git repository with reproducible tests, I must classify this as RAW_RADAR_CANDIDATE.

I've identified that "Perenna" likely refers to a Soroban smart contract project on Stellar, possibly a streaming payments protocol. The core issue seems to be preventing contract archiving by extending the instance TTL on stream reads, a common pattern using `instance().extend_ttl()`. Since I lack the repository's source code, I can't provide exact code changes but can offer a generic Soroban fix pattern and a draft patch/test.

I'm drafting a generic Soroban patch to extend instance TTL on public read entrypoints, including typical constants and a test case. I'm unsure about the exact test utility method for checking TTL in newer SDK versions, but I'll proceed with the best available option and note the uncertainty. I need repository access and a reference implementation to adapt this template.**Classification (per mandatory invariants):** `RAW_RADAR_CANDIDATE` — I do not have the `Perenna-Labs/perenna-contracts` source in context, so I cannot confirm repo structure, file paths, line numbers, or a reproducible test suite. Per **RULE-002**, nothing below can be marked `PASS`/`READY_FOR_EGRESS` — no deterministic check (`cargo check` / `cargo test`) has run against the real code. Per **RULE-001**, any eventual push must go through an authenticated user PAT, not a GitHub App.

I can give you the canonical fix pattern for this issue (Soroban instance TTL bump on read paths), labeled **DRAFT/UNVERIFIED** until grounded in the actual source.

## Fix pattern

The contract instance storage archives when its TTL expires, which bricks even an "active" contract. The fix: call `instance().extend_ttl()` inside every public read/stream entrypoint so reads renew the instance.

```rust
// constants.rs (or top of lib.rs)
pub(crate) const DAY_IN_LEDGERS: u32 = 17_280;
pub(crate) const INSTANCE_TTL_THRESHOLD: u32 = DAY_IN_LEDGERS;       // bump when < ~1 day left
pub(crate) const INSTANCE_BUMP_TO: u32 = 30 * DAY_IN_LEDGERS;        // extend to ~30 days
```

```diff
  pub fn get_stream(env: Env, stream_id: u64) -> Stream {
+     env.storage()
+         .instance()
+         .extend_ttl(INSTANCE_TTL_THRESHOLD, INSTANCE_BUMP_TO);
      env.storage()
          .persistent()
          .get(&DataKey::Stream(stream_id))
          .unwrap_or_else(|| panic_with_error!(&env, Error::NotFound))
  }
```

Apply the same two lines to **every** read entrypoint (`get_stream`, `balance_of`/`withdrawable`, `list_streams`, `get_config`, etc.). Also bump TTL on the *persistent* stream entry itself if streams should stay live on read:

```rust
env.storage()
    .persistent()
    .extend_ttl(&DataKey::Stream(stream_id), STREAM_TTL_THRESHOLD, STREAM_BUMP_TO);
```

## Draft test

```rust
#[test]
fn read_extends_instance_ttl() {
    let env = Env::default();
    let contract_id = env.register_contract(None, PerennaContract);
    let client = PerennaContractClient::new(&env, &contract_id);

    env.ledger().set_sequence_number(10_000);
    let stream_id = client.create_stream(&/* args */);

    let ttl_before = env.as_contract(&contract_id, || {
        env.storage().instance().get_ttl()
    });

    // Advance ledger so remaining TTL < threshold
    env.ledger().set_sequence_number(10_000 + ttl_before - 100);

    let _stream = client.get_stream(&stream_id);

    let ttl_after = env.as_contract(&contract_id, || {
        env.storage().instance().get_ttl()
    });
    assert!(ttl_after >= INSTANCE_BUMP_TO - 200);
}
```

## To produce the exact surgical diff, I need:

1. The repo checked out (or paste `lib.rs` + the read-function file) — function names/signatures vary (`get_stream` vs `stream`, storage key enum name, error type).
2. Existing TTL constants, if any (many Soroban repos already define `BUMP_AMOUNT`/`LIFETIME_THRESHOLD` — reusing them avoids duplication).
3. The issue's definition of "stream reads" — does it mean *all* getters or only stream-specific ones?

Share the source tree or the file(s) containing the read entrypoints and I'll output line-exact diffs and tests, which can then be gated through `cargo test` before egress.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — [DRAFT / UNVERIFIED]

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $90] Extend the instance TTL on stream reads so an active contract cannot archive
**Classification:** `RAW_RADAR_CANDIDATE` — no repository source in context; no public repo + reproducible suite confirmed.
**Patch status:** `DRAFT` — **not** `PASS`, **not** `READY_FOR_EGRESS` (RULE-002: no deterministic compiler/test run against real source).
**Egress path:** authenticated **user PAT** only (RULE-001). GitHub App is used for scouting/clone/quota shielding, never for the public PR write.

---

## 1. Title

```
fix(storage): renew instance TTL on stream read paths to prevent instance archival
```

## 2. Summary

Soroban contract instances are archived when their instance-storage TTL reaches zero. A contract can be economically "active" (live streams, pending withdrawals, non-zero balances) yet still archive, because **read-only entrypoints never touch instance storage in a way that renews its TTL**. Once archived, every entrypoint — including reads — fails until an explicit restore, so integrators and indexers see a hard outage on a contract that was never idle.

This change extends the instance TTL on the read paths that constitute "stream activity," so any read traffic keeps the instance live. It does **not** change stream accounting, authorization, or economic semantics.

## 3. Root Cause

1. `instance().extend_ttl(...)` is (presumably) only invoked on **write** paths — `create_stream`, `withdraw`, `cancel`, admin setters. Instance TTL therefore advances only when someone mutates state.
2. Read entrypoints (`get_stream`, `balance_of`/`withdrawable`, `list_streams`, `get_config`, …) touch instance storage (config, counters, admin) but never renew its TTL. They are pure reads from the ledger's perspective.
3. Consequence: a contract with an open, funded stream but no writes for longer than the TTL window archives. The archive is invisible to callers until the first post-expiry invocation, at which point reads revert and the integrator has no signal that the stream is still valid.
4. Secondary: the **persistent** `DataKey::Stream(id)` entry has its own independent TTL. Extending only the instance does not keep an individual stream entry readable, so a "read the stream" fix is incomplete unless the per-stream entry is also bumped.

## 4. Implementation

> Paths, constant names, key-enum names, and function signatures below are **placeholders** derived from the canonical Soroban pattern. They must be reconciled against the actual source before egress.

### 4.1 Constants (new, or reuse existing bump constants if the repo already defines them)

```rust
// constants.rs (or top of lib.rs)
pub(crate) const DAY_IN_LEDGERS: u32 = 17_280; // 5s ledgers

// Bump the instance when less than ~1 day of life remains…
pub(crate) const INSTANCE_TTL_THRESHOLD: u32 = DAY_IN_LEDGERS;
// …extend it out to ~30 days.
pub(crate) const INSTANCE_BUMP_TO: u32 = 30 * DAY_IN_LEDGERS;

// Per-stream persistent entry, same policy.
pub(crate) const STREAM_TTL_THRESHOLD: u32 = DAY_IN_LEDGERS;
pub(crate) const STREAM_BUMP_TO: u32 = 30 * DAY_IN_LEDGERS;
```

### 4.2 Shared helper (avoids duplicating the bump in every getter)

```rust
fn touch_instance(env: &Env) {
    env.storage()
        .instance()
        .extend_ttl(INSTANCE_TTL_THRESHOLD, INSTANCE_BUMP_TO);
}

fn touch_stream(env: &Env, stream_id: u64) {
    env.storage().persistent().extend_ttl(
        &DataKey::Stream(stream_id),
        STREAM_TTL_THRESHOLD,
        STREAM_BUMP_TO,
    );
}
```

### 4.3 Read entrypoints

```diff
  pub fn get_stream(env: Env, stream_id: u64) -> Stream {
+     touch_instance(&env);
+     touch_stream(&env, stream_id);
      env.storage()
          .persistent()
          .get(&DataKey::Stream(stream_id))
          .unwrap_or_else(|| panic_with_error!(&env, Error::NotFound))
  }
```

Apply `touch_instance(&env)` to **every** public read entrypoint:

| Entrypoint | Instance bump | Persistent bump |
|---|---|---|
| `get_stream` | ✅ | ✅ (`DataKey::Stream(id)`) |
| `withdrawable` / `balance_of` | ✅ | ✅ |
| `list_streams` / `streams_of` | ✅ | — (no single key) |
| `get_config` | ✅ | — |
| `next_stream_id` / counters | ✅ | — |

**Ordering note:** call `touch_instance` *before* the storage read. If the read is the last thing that happens and the instance expires mid-instruction, the renewal must already be recorded.

### 4.4 Explicitly out of scope

- No change to write-path TTL logic (assumed already correct).
- No change to `extend_ttl` thresholds for auth/allowance entries.
- No new admin entrypoint for manual renewal.
- No change to stream math or error codes.

### 4.5 Design note — read-triggered renewal is intentionally permissionless

Any caller can extend the instance TTL by reading, and pays the rent for doing so. This is the desired property for "an active contract cannot archive," and the griefing surface is a *benefit* here, not a cost: the only thing an attacker can do is pay to keep your contract alive. If the repo's threat model treats unsolicited TTL extension as undesirable, the alternative is a permissioned `bump()` entrypoint plus an off-chain keeper — but that reintroduces the liveness dependency the issue is trying to remove. **Flag this in the PR description so the maintainers can choose.**

## 5. Test Verification Plan

> Not executed. These are the gates that must run green before this moves off `DRAFT`.

### 5.1 Deterministic gates (RULE-002)

```bash
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --target wasm32-unknown-unknown --release
```

The `wasm32-unknown-unknown` release build is the authoritative syntax/semantics gate for a Soroban contract; `cargo test` alone is not sufficient.

### 5.2 Primary behavioural test — survives without a TTL getter

Preferred assertion: prove the instance is still live after outliving its original TTL, rather than reading a TTL number back (the storage TTL getter surface has moved between SDK versions — see 5.4).

```rust
#[test]
fn read_extends_instance_ttl() {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register_contract(None, PerennaContract);
    let client = PerennaContractClient::new(&env, &contract_id);

    let stream_id = client.create_stream(&/* args */);

    // Instance TTL is now at most INSTANCE_BUMP_TO from here.
    // Jump past it and assert the contract is still usable.
    env.ledger().set_sequence_number(
        env.ledger
\n