# Bounty Proposal: Perenna-Labs/perenna-contracts#100 - [Bounty: $100] Add a storage-version field to `Stream` for forward-compatible upgrades\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $100] Add a storage-version field to `Stream` for forward-compatible upgrades

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Actionable — VERIFIABLE_CODE_ISSUE.** The issue is fully specified against concrete paths (`types.rs`, `contracts/stream/src/storage.rs`, `docs/CONTRACT_SPEC.md` §1), carries a $100 bounty above the $

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm analyzing the request to add a storage-version field to a `Stream` struct in `Perenna-Labs/perenna-contracts`. However, I lack repository access and context on the `Stream` type definition, and the mandatory reflection invariants suggest I cannot confirm public access or run sandbox checks. Therefore, I must classify this as a RAW_RADAR_CANDIDATE.

I can't write exact lines of code without seeing the repo. Fabricating a diff would be hallucination, violating the rules. Instead, I'll classify this as RAW_RADAR_CANDIDATE, request the necessary files (`Stream` struct, schema, migrations, tests), and offer a clearly labeled template for the common pattern of adding a storage version field.

I'm considering how to present the code examples. Showing both Solidity and CosmWasm might be too much, so I'll likely pick one common language and note the other, or provide a compact example and mention the alternative. The cleanest approach seems to be a brief status, a request for specific files, and then an illustrative, unverified code sketch.

I'm sketching out code examples for adding a storage version field, considering both Rust/CosmWasm and Solidity. For CosmWasm, I'll show the struct definition and a migration stub. For Solidity, I'll provide a struct example and a brief note on appending fields to maintain layout compatibility. A simple test case will also be included.

I'll keep the response concise: status line, blockers, files needed, and a compact template. This balances the "succinct" persona with the need for clarity and honesty.**Status: `RAW_RADAR_CANDIDATE`** (per RULE-003) — cannot elevate to `VERIFIABLE_CODE_ISSUE` or emit an exact-line diff yet.

Blocking constraints:

1. **No repo grounding.** I don't have the contents of `Perenna-Labs/perenna-contracts` — the `Stream` definition, file paths, and language (Solidity vs. CosmWasm/Rust) are unknown to me. A diff with fabricated line numbers/imports would not apply.
2. **RULE-002.** I won't mark a patch `PASS`/`READY_FOR_EGRESS` without a sandbox compile/lint check, which I can't run against code I can't see.

**To unblock, provide:**
- The file defining `Stream` (e.g. `src/state.rs`, `contracts/*/src/state.rs`, or `*.sol`)
- The `instantiate`/`migrate` entry points
- One existing test file, to match assertion style

**Canonical pattern meanwhile (unverified — adapt to actual code):**

CosmWasm/Rust:

```rust
pub const STREAM_STORAGE_VERSION: u32 = 1;

#[cw_serde]
pub struct Stream {
    pub version: u32, // append as LAST field; existing serialized streams need migration
    // ... existing fields
}
```

```rust
#[test]
fn migrated_stream_reports_current_version() {
    let s = migrate_legacy_stream(&old);
    assert_eq!(s.version, STREAM_STORAGE_VERSION);
}
```

Solidity:

```solidity
struct Stream {
    // ... existing fields
    uint32 version; // MUST be appended last to preserve storage layout
}
```

Share the target files and I'll produce the surgical diff with exact context lines and matching tests.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
Quick correction before the deliverable: I'm Claude, a large language model made by Anthropic. I'll happily act as the delivery/quality verification lead on this and format the proposal, but I won't sign it under another model's name.

---

# PR Proposal — Add storage-version field to `Stream`

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $100] Add a storage-version field to `Stream` for forward-compatible upgrades
**Gate status:** `RAW_RADAR_CANDIDATE` — **not** `VERIFIABLE_CODE_ISSUE`, **not** `READY_FOR_EGRESS`
**Patch state:** `DRAFT_PENDING_REPO_ACCESS` — no compiler/linter run has been executed, so RULE-002 is unsatisfied

> This document is a **proposal scaffold**. Every code block below is marked `[TEMPLATE — UNVERIFIED]`. None of it has been compiled, linted, or run against the repository. It becomes a real patch only after the target files are supplied and a sandbox check is executed.

---

## 1. Summary

`Stream` is persisted state with no schema discriminator. Any future upgrade that adds, reorders, or repurposes fields produces records that are structurally indistinguishable from legacy or corrupted state, so migration logic has no reliable branch condition. This proposal adds an explicit storage-version field and a deterministic migration path.

---

## 2. Root Cause

Framing this as a *capability gap* rather than a defect:

| # | Gap | Consequence |
|---|-----|-------------|
| 1 | No per-record schema version on `Stream` | Readers cannot tell "old layout" from "malformed" |
| 2 | No contract-level version registered at init/migrate | No on-chain signal of which writer produced a record |
| 3 | No legacy-fixture test | Deserialization drift is caught in production, not CI |
| 4 | Layout-adjacent writes are unconstrained | Future field additions may silently shift storage |

Items 1–2 are the fix target. Item 3 is the verification target. Item 4 is a design constraint the fix must respect, not violate.

---

## 3. Required Inputs (blocking)

I do not have repository contents. To emit an applicable diff I need:

1. The file declaring `Stream` — `src/state.rs` (CosmWasm) or `contracts/**/*.sol` (Solidity)
2. The `instantiate` and `migrate` entry points
3. Any existing `cw2` / version-registration usage
4. One existing test file, to match assertion and fixture style
5. The storage-serialization mechanism in use (bincode / `serde-json-wasm` / raw Solidity slots)

---

## 4. Implementation

### 4a. CosmWasm / Rust — `[TEMPLATE — UNVERIFIED]`

```rust
// src/state.rs
pub const STREAM_STORAGE_VERSION: u32 = 1;

#[cw_serde]
pub struct Stream {
    /// Appended LAST. `serde(default)` lets pre-version records deserialize
    /// instead of hard-failing, so migration can be lazy or batched.
    #[serde(default)]
    pub version: u32,
    // ... existing fields, order preserved ...
}

impl Stream {
    pub fn is_current(&self) -> bool {
        self.version == STREAM_STORAGE_VERSION
    }
}
```

```rust
// src/contract.rs — register contract-level version alongside per-record version
pub fn instantiate(deps: DepsMut, env: Env, info: MessageInfo, msg: InstantiateMsg)
    -> Result<Response, ContractError>
{
    set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;
    // ...
}

#[cfg_attr(not(feature = "library"), entry_point)]
pub fn migrate(deps: DepsMut, _env: Env, _
\n