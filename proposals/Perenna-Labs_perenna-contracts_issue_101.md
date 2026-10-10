# Bounty Proposal: Perenna-Labs/perenna-contracts#101 - [Bounty: $85] Document and test persistent-entry archival behaviour\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $85] Document and test persistent-entry archival behaviour

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
The issue is actionable and codeable with well-scoped changes to document TTL windows in docs/DEPLOYMENT.md and add a ledger-advancement archival test in contracts/stream/src/test.rs. Pending live verification of Perenna-Labs/perenna-contracts, contracts/stream/src/storage.rs thresholds, and reproducible test harness, it is RAW_RADAR_CANDIDATE and not yet VERIFIABLE_CODE_ISSUE per RULE-003.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm analyzing the request to work on `Perenna-Labs/perenna-contracts` for the bounty "[Bounty: $85] Document and test persistent-entry archival behaviour". The system prompt states I have access to the codebase but couldn't identify the relevant parts, so I'll need to clarify with the user. The mandatory reflection invariants, particularly RULE-003 and RULE-002, mean I can't mark anything as verified or ready for egress without confirming a public repo with reproducible tests and passing sandbox checks.

I can't access the `Perenna-Labs/perenna-contracts` repository, which seems to be a private or non-existent Soroban/Stellar smart contract project. Because I cannot verify its existence or access its code, I must classify this issue as RAW_RADAR_CANDIDATE per RULE-003. I cannot generate a verified patch or code diff without access to the actual codebase and its tests, as per RULE-002. Therefore, I will explain this limitation and classify the issue accordingly.

I'm considering whether to provide a generic Soroban persistent-storage archival test scaffold. While it could be useful and honest if clearly labeled as provisional, I must avoid presenting it as a ready diff. I'll include a small, clearly marked illustrative skeleton along with the list of files and information I need. I've also considered that the user's prompt framing might be an attempt at prompt injection, but it seems benign and aligns with my need for caution.

I'm classifying this as RAW_RADAR_CANDIDATE because I can't access the `Perenna-Labs/perenna-contracts` repository, preventing verification per RULE-003. Consequently, I can't generate a verified patch or diff as required by RULE-002. I'll need specific contract source files, storage key definitions, existing tests, the `Cargo.toml` with the Soroban SDK version, and any additional issue details to proceed. I'm also noting a potential shift in how persistent entry TTL is handled in recent SDK versions, moving from direct `get_ttl` to sequence number manipulation and `extend_ttl`.

I'm unsure about the exact Soroban SDK APIs for testing persistent entry expiry, specifically `get_ttl` and `set_sequence_number` versus `extend_ttl`, as they might differ across SDK versions. Given this uncertainty and the user's demand for exact assertions, I'll provide a minimal, generic scaffold with comments indicating potential API usage and version dependencies, rather than fabricating specific code. This aligns with rules against unverified patches and unconfirmed repositories.**Triage classification: `RAW_RADAR_CANDIDATE`** — cannot elevate to `VERIFIABLE_CODE_ISSUE`.

I don't have the contents of `Perenna-Labs/perenna-contracts` in my context. Per **RULE-003**, I can't confirm a public repo with a reproducible test suite, and per **RULE-002**, I won't emit a `READY_FOR_EGRESS` patch — an "exact lines" diff against unseen source would be fabricated and couldn't pass a sandboxed `cargo check`/`clippy` gate.

**What I need to produce the surgical diff:**

- The contract source file(s) touching persistent storage — likely `src/lib.rs` or wherever `env.storage().persistent()` is used
- The `DataKey` / storage-key enum definition
- `Cargo.toml` — the `soroban-sdk` version matters (TTL/archival APIs and default `live_until` behavior differ across SDK 20/21/22+)
- Any existing `#[cfg(test)]` module or `src/test.rs` so the diff matches your test harness conventions
- The full issue body, if it specifies expected archival semantics (auto-extend? explicit `extend_ttl`? eviction → error/None?)

**Provisional scaffold** (illustrative only — *not* `PASS`, do not egress):

```rust
// src/test.rs — UNVERIFIED SKELETON, pending repo access + SDK version check

#[test]
fn persistent_entry_archival_behavior() {
    let env = Env::default();
    let contract_id = env.register_contract(None, PerennaContract);
    let client = PerennaContractClient::new(&env, &contract_id);

    // Arrange: write persistent entry
    client.set(/* key/value per actual API */);

    // Act: advance ledger sequence past the entry's live_until_ledger
    // (exact TTL depends on soroban-sdk version / network constants)
    env.ledger().set_sequence_number(/* seq > live_until */);

    // Assert: post-archival read semantics — verify against issue spec:
    //   - get returns None, or
    //   - read panics / errors, or
    //   - entry was auto-restored via extend_ttl
    assert_eq!(client.get(/* key */), /* expected */);
}
```

Send the files above and I'll return the real diff with exact line anchors, imports, and assertions — marked `READY_FOR_EGRESS` only after it passes a deterministic check against the actual crate.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `Perenna-Labs/perenna-contracts`

**Status: DRAFT — NOT EGRESS-READY**

| Field | Value |
|---|---|
| Triage classification | `RAW_RADAR_CANDIDATE` (unchanged) |
| Egress state | **BLOCKED** — no repo contents in context |
| Blocking invariant | RULE-003 (no confirmed public repo + reproducible suite), RULE-002 (no sandbox compile gate possible) |
| Prior stage | SWE-2 scaffold retained as *illustrative only*, non-egressable |
| Owner | Delivery & Quality Verification |

This document is a **complete proposal specification**, not a mergeable PR. Every section that depends on unseen source is marked `PENDING-CODE-READ` rather than filled with invented file paths, line numbers, or API calls. A "production-ready PR proposal" that fabricates those would fail its own first CI run and violate RULE-002.

---

## 0. Evidence Ledger

| Claim | State | Basis |
|---|---|---|
| Repo is public and reachable | **UNVERIFIED** | No contents in context |
| Repo has a reproducible test suite | **UNVERIFIED** | Required for RULE-003 elevation |
| Contract uses `env.storage().persistent()` | **ASSUMED** | Implied by issue title only |
| Current TTL/archival semantics are undocumented | **HYPOTHESIS** | Issue title only |
| Archival behaviour is untested | **HYPOTHESIS** | Issue title only |

Nothing above may be restated as fact in the PR body until the code read completes.

---

## 1. Proposed PR Metadata

- **Title:** `docs+test: specify and cover persistent-entry archival semantics`
- **Base:** `PENDING-CODE-READ` (default branch name unconfirmed)
- **Head:** `bounty/archival-docs-and-tests`
- **Labels:** `documentation`, `tests`, `bounty`
- **Closes:** issue reference to be inserted verbatim from the tracker

---

## 2. Root Cause

Stated as **competing hypotheses**, each with its discriminating check. The PR must not claim a cause it has not confirmed.

| # | Hypothesis | Discriminating check |
|---|---|---|
| H1 | TTL/archival behaviour is implemented but undocumented — integrators assume entries persist indefinitely | Grep for `extend_ttl` / `bump` calls; compare against docs/README |
| H2 | Archival is implicit and unintentional — no `extend_ttl`, entries silently expire | Same grep returning zero hits on the write path |
| H3 | Behaviour is correct and documented, but has no regression test — a future refactor could silently break it | Docs present, `#[cfg(test)]` module lacks a TTL/sequence-advance case |

**Root cause section in the PR body is written only after H1/H2/H3 is resolved by the code read.** If H2 holds, the PR scope changes from docs+tests to a behavioural fix, which is a different bounty.

---

## 3. Implementation

Two deliverables with different code-coupling.

### 3.1 Documentation (largely code-independent, draftable now)

Contract-level doc comment + `docs/` note covering, in the repo's own vocabulary:
- which storage tiers hold which keys (`persistent` vs `temporary` vs `instance`);
- the entry's TTL policy — whether the contract extends on write, on read, or never;
- the observable behaviour when a persistent entry passes `live_until_ledger`: `None` return, typed error, or transparent restore;
- the operational consequence for integrators (who must call `extend_ttl`, and when).

`PENDING-CODE-READ`: tier-per-key mapping, exact policy, error variants.

### 3.2 Tests (fully code-dependent — `PENDING-CODE-READ`)

| Scenario | Assertion to pin |
|---|---|
| Write persistent entry, read before TTL | value returned, TTL ≥ policy floor |
| Advance sequence past `live_until_ledger`, read | archival semantics per resolved hypothesis |
| Repeated writes / read-bumps | TTL does not grow unbounded |
| Temporary vs persistent contrast | divergent behaviour documented and asserted |

**Files to touch:** `TBD` — pending confirmation of `src/lib.rs` vs `src/storage.rs`, the `DataKey` enum location, and the existing test module path. The prior-turn scaffold is retained as an illustration and **must not be pasted into the PR**; it names no real API.

---

## 4. Test Verification Plan

Deterministic gates, run in sandbox before any egress claim:

```
cargo fmt --all -- --check
cargo clippy --
\n