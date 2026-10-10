# Bounty Proposal: Perenna-Labs/perenna-contracts#90 - [Bounty: $65] Deduplicate the two identical TTL constant pairs in `storage.rs`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $65] Deduplicate the two identical TTL constant pairs in `storage.rs`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Classified as RAW_RADAR_CANDIDATE, this issue is actionable and codeable with a clear scope to collapse four identical TTL constants into one shared pair in `storage.rs`. The target functions, unchanged values, and verification via `make test` and CI are explicitly specified with no missing dependencies.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
I need to design an architecture for deduplicating TTL constants in `storage.rs`. Since I can't access the codebase directly, I'll base the design on the issue description, clearly stating my assumptions and what needs verification. I must also ensure the strategy adheres to the invariant rules, particularly regarding GitHub App boundaries and the verification gate for RAW_RADAR_CANDIDATE issues, which requires confirming a public Git repo with reproducible tests before proceeding.

Regarding RULE-006, the financial rounding rule, I'll apply it to the bounty amount ($65) by quantizing it to cents upfront and deriving any allocations from that. This satisfies the rule's invariant without overcomplicating the code refactor itself, as the TTL constants are integers. For the technical refactor, I'm considering whether to collapse the TTL constants into two shared ones or derive the instance TTL from the persistent TTL.

I'm weighing the trade-offs between collapsing TTL constants and deriving them. Collapsing to two constants directly satisfies the acceptance criterion's literal wording, but deriving preserves semantic names and avoids potential churn if the TTLs diverge later. The ambiguity in the acceptance criterion ("only one pair" vs. "or derive") makes the safer bet a literal collapse, but I need to verify if external references to these constants exist via a `grep` to assess the impact of aliasing versus collapsing.

I'm leaning towards collapsing the TTL constants to two shared ones, as this directly satisfies the acceptance criterion's literal wording. However, I need to verify if aliasing them while keeping descriptive names like `PERSISTENT_TTL_*` would be better if there's any chance of future divergence. I'll check for external usages of these constants to assess the impact of renaming or collapsing, and also look into codebase conventions for naming and testing.

I'm confirming the existence of `make test` and the CI `check` job as part of the RULE-003 verification gate. The Soroban SDK version and `no_std` status don't affect the constants. I've also noted the ledger counts for context, though they aren't strictly necessary for the refactor. For the architecture, I'll proceed with cloning the repo, verifying files and tests, and then elevating the issue. Impact analysis will involve grepping for usages, and I'll use a decision matrix for the collapse vs. alias choice.

I'm enforcing the "values unchanged" invariant at compile time and guarding ordering, which adds safety though it could be optional. AC ruled out deprecated aliases for original names, as only one pair is allowed. I'm keeping the `extend_ttl` threshold < extend assert, as Soroban semantics require this. Since I can't see the file, I'll present a representative diff sketch and ask for confirmation or state my assumptions, aiming for a thorough but crisp response with markdown, code blocks, headers, and a potential invariants table.# Architecture Review: TTL Constant Deduplication — `contracts/stream/src/storage.rs`

## 1. Verification Gate (RULE-003) — before any code

The issue is still `RAW_RADAR_CANDIDATE`. Elevate to `VERIFIABLE_CODE_ISSUE` only after confirming, via a read-only clone (GitHub App, per RULE-001):

- `contracts/stream/src/storage.rs` exists and contains exactly the four constants with values `17_280` / `518_400`.
- `Makefile` has a `test` target; `.github/workflows/ci.yml` has a `check` job.
- No hidden fifth constant or conditional `#[cfg]` variant exists.

If any check fails → keep as `RAW_RADAR_CANDIDATE`, halt.

## 2. Root Cause & Impact Surface

**Root cause:** coincidental duplication — two TTL domains (instance vs. persistent) happen to share values, expressed as four independent literals. The failure mode is *silent divergence* on the next tuning change, which on Soroban means premature archival of instance or persistent entries — a liveness bug, not a style nit.

**Files to touch (minimal blast radius):**

| File | Action |
|---|---|
| `contracts/stream/src/storage.rs` | Collapse constants; update `extend_instance_ttl` + `extend_stream_ttl` |
| Tests / `lib.rs` / other modules | **Only if** grep shows imports of the old names — check `pub`/`pub(crate)` visibility first |

Run: `grep -rn "TTL_THRESHOLD\|TTL_EXTEND" contracts/` — renaming a `pub` constant is a breaking API change outside the module.

## 3. Design Decision: Collapse vs. Alias

Two legal readings of the spec:

```rust
// Option A — collapse (recommended: literal AC satisfaction)
// Shared TTL window applied to both instance and persistent storage:
// ~1 day threshold (17_280 ledgers), ~30 day extension (518_400 ledgers).
const TTL_THRESHOLD: u32 = 17_280;
const TTL_EXTEND: u32 = 518_400;
```

```rust
// Option B — single-source via aliasing (keeps semantic names as
// extension points, but arguably violates "only one pair remains")
const INSTANCE_TTL_THRESHOLD: u32 = PERSISTENT_TTL_THRESHOLD;
```

**Decision rule:** the issue's stated motivation is "these must move together." Option A encodes that coupling structurally — divergence becomes impossible rather than merely unlikely. Choose A unless grep reveals the domain-specific names are referenced externally (docs, other contracts, off-chain keeper config), in which case B with a comment preserving the constraint.

## 4. Bulletproofing Invariants

Add a compile-time lock on the "values unchanged" acceptance criterion — costs nothing at runtime under `no_std`:

```rust
const _: () = {
    assert!(TTL_THRESHOLD == 17_280);
    assert!(TTL_EXTEND == 518_400);
    // Soroban requires threshold < extend_to for extend_ttl semantics.
    assert!(TTL_THRESHOLD < TTL_EXTEND);
};
```

**Regression invariants:**
- Byte-identical TTL arguments reach both `storage().instance().extend_ttl(...)` and `storage().persistent().extend_ttl(&key, ...)` calls — this is a pure rename, zero semantic delta.
- `cargo fmt --check`, `clippy`, `make test`, CI `check` job all green.
- No float/arithmetic derivation of TTLs — keep integer literals (consistent with RULE-006 spirit: exact values, no implicit conversion).

## 5. Write-Path Governance (RULE-001)

This is an **external public repo** (`Perenna-Labs/perenna-contracts`):

- **GitHub App:** clone, scout, CI status polling only (quota shielding).
- **PAT user account:** fork, branch push, PR open — all writes.

## 6. Bounty Ledger (RULE-006)

If the $65 bounty is split (platform fee, contributor payout):

```python
gross = Decimal("65")
gross_q = gross.quantize(Decimal("0.01"))        # quantize first
fee     = (gross_q * fee_rate).quantize(Decimal("0.01"), ROUND_DOWN)
payout  = gross_q - fee                           # residual, never independent rounding
assert fee + payout == gross_q                    # zero-leak invariant
```

Never round sub-allocations independently — derive the last leg as `gross_quantized - sum(prior_legs)`.

## 7. Risks & Rollback

- **Risk:** reviewer prefers semantic names (Option B). → Trivial re-review; keep commit atomic (one commit = collapse only).
- **Risk:** stale doc references. → grep markdown/comments for constant names.
- **Rollback:** pure revert; no state migration since TTLs are call-time arguments, not stored values.

Confirm the actual `storage.rs` contents (visibility, exact comments, call sites) and I'll produce the precise diff — the sketch above assumes the canonical layout described in the issue.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — Deduplicate TTL Constant Pairs in `contracts/stream/src/storage.rs`

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $65] Deduplicate the two identical TTL constant pairs in `storage.rs`
**Author:** Claude — Delivery & Quality Verification Lead
**Status:** ⚠️ **PROPOSAL — BLOCKED ON VERIFICATION GATE (RULE-003)**

---

## 0. Verification Status Banner (read first)

This document is a **proposal package**, not a submitted PR. It packages an architecture plan whose own author states: *"Since I can't access the codebase directly, I'll base the design on the issue description"* and *"Code Patch (SWE-2): **None**."*

Therefore, **honest status**:

| Item | Status |
|---|---|
| Root cause analysis | Derived from issue text — **plausible, unconfirmed** |
| Exact constant names / values / visibility | **ASSUMED** (`17_280` / `518_400`) — not read from repo |
| Diff | **SKETCH** — not compiled, not applied |
| `make test` / CI results | **NOT EXECUTED** — no test output exists to report |
| Radar classification | Remains **RAW_RADAR_CANDIDATE** |

Nothing below should be represented to a maintainer as verified until the clone checks in §2 pass. **Do not open the PR before then.**

---

## 1. Root Cause

The issue describes two TTL constant *pairs* (a threshold + an extend window), each pair duplicated across two TTL domains — instance storage and persistent storage — with identical values.

**Mechanism:** coincidental duplication, not intentional coupling. Four independent literals encode a relationship the code never declares.

**Failure mode (why this is a liveness bug, not a style nit):** Soroban evicts entries when their live-until ledger passes. TTL constants are the only thing preventing archival. If a future tuning change updates one pair and misses the other, the untouched domain silently archives early — loss of contract state or instance data, with no compile error and no failing test unless one specifically pins both call sites.

**Why dedup fixes it structurally:** collapsing to a single pair makes divergence *impossible* rather than *unlikely*. That is the real acceptance criterion, beyond the literal "one pair remains" wording.

---

## 2. Verification Gate (RULE-003) — MUST PASS BEFORE WRITING CODE

Read-only clone via **GitHub App** (quota shielding, per RULE-001). Confirm all four:

1. `contracts/stream/src/storage.rs` exists and contains exactly **four** TTL constants with values `17_280` / `518_400`.
2. The names are as assumed (`INSTANCE_TTL_*` / `PERSISTENT_TTL_*` or similar) — record exact identifiers.
3. `Makefile` has a `test` target; `.github/workflows/ci.yml` has a `check` job.
4. No hidden fifth constant, no `#[cfg]`-gated variant, no second `storage.rs` under another contract.

**Visibility check:** `grep -rn "TTL_THRESHOLD\|TTL_EXTEND" contracts/` — if any constant is `pub` or `pub(crate)` and referenced outside the module, renaming is a breaking change and Option B (§4) applies.

**Gate result:**
- All pass → elevate to **VERIFIABLE_CODE_ISSUE**, proceed to §3.
- Any fail → **remain RAW_RADAR_CANDIDATE, halt.**

---

## 3. Proposed Implementation

### 3.1 Files touched

| File | Action |
|---|---|
| `contracts/stream/src/storage.rs` | Collapse four constants → two; update both `extend_ttl` call sites |
| Any module importing the old names | **Only if** §2 visibility check shows external references |

### 3.2 Diff sketch — Option A (recommended)

```rust
// Shared TTL window applied to both instance and persistent storage.
// Instance and persistent entries must move together: these values are the
// only guard against Soroban archival.
//
// ~1 day threshold (17_280 ledgers @ 5s), ~30 day extension (518_400 ledgers).
const TTL_THRESHOLD: u32 = 17_280;
const TTL_EXTEND: u32 = 518_400;
```

```rust
// call sites — pure rename, byte-identical arguments
storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTEND);
storage().persistent().extend_ttl(&key, TTL_THRESHOLD, TTL_EXTEND);
```

### 3.3 Compile-time lock on the "values unchanged" criterion

```rust
const _: () = {
    assert!(TTL_THRESHOLD == 17_280);
    assert!(TTL_EXTEND == 518_400);
    // Soroban semantics: threshold must be < extend_to.
    assert!(TTL_THRESHOLD < TTL_EXTEND);
};
```

**MSRV caveat:** const-context `assert!` requires Rust ≥ 1.57. If the workspace MSRV is lower, either drop this block or use `static_assertions` (no_std compatible). Do **not** silently raise MSRV.

### 3.4 Explicit non-goals

- No change to TTL **values** — this is a rename/collapse only.
- No arithmetic or float derivation of TTLs; keep integer literals.
- No deprecated aliases for the removed names (AC permits only one pair).

---

## 4. Design Decision: Collapse vs. Alias

| | Option A — Collapse | Option B — Alias |
|---|---|---|
| Shape | `const TTL_THRESHOLD = 17_280;` | `const INSTANCE_TTL_THRESHOLD = PERSISTENT_TTL_THRESHOLD;` |
| Coupling | Structural — divergence impossible | Declared, but re-introducible |
| AC "only one pair" | Satisfied literally | Arguably violates |
| Semantic names | Lost | Preserved as extension points |

**Decision rule:** choose **A** by default. Choose **B** *only if* §2 grep shows the domain-specific names are referenced externally (docs, off-chain keeper config, another contract). If B, add a comment stating the values must remain equal, and note in the PR body that AC was interpreted permissively.

---

## 5. Test Verification Plan

**Nothing here has been executed.** These are the commands the PR author must run and paste into the PR body, with real output:

| Step | Command | Expected |
|---|---|---|
| Format | `cargo fmt --all -- --check` | exit 0 |
| Lint | `cargo clippy --all-targets -- -D warnings` | exit 0 |
| Unit/integration | `make test` | all pass |
| CI parity | `check` job in `.github/workflows/ci.yml` | green |
| Build | `cargo build --target wasm32-unknown-unknown --release` | exit 0 |

**Required regression evidence** (beyond green tests):

1. The existing TTL tests, if any, still pass **unmodified** — do not adjust a test to accommodate the refactor.
2. If no test pins TTL behavior, state that plainly in the PR. Do **not** claim behavioral coverage that does not exist.
3. Confirm the const-assert block actually fires by temporarily setting `TTL
\n