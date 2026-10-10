# Bounty Proposal: Perenna-Labs/perenna-contracts#47 - [Bounty: $75] Add a release-profile test run to exercise `overflow-checks`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $75] Add a release-profile test run to exercise `overflow-checks`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: add a gated `cargo test --release` step to `.github/workflows/ci.yml` (e.g., wasm job on push to main) to exercise `overflow-checks=true` / `panic="abort"` release behavior for `compute_earned`/`withdraw`/`cancel`.

Verdict: RAW_RADAR_CANDIDATE per triage invariants — passes $75 > $25 payout gate with no scam signals, clearly scoped CI change with acceptance criteria, elevates to VERIFIABLE_CODE_ISSUE once `Perenna-Labs/perenna-contracts` public repo and reproducible test suite are confirmed (tools unavailable to verify in this run).

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm trying to address a bounty to add a release-profile test run for `overflow-checks` in the `Perenna-Labs/perenna-contracts` repo. However, I can't access the user's codebase or confirm access to this specific repository. This uncertainty prevents me from verifying the issue as a code issue or running deterministic checks, which are required before any patch can be marked as ready.

I suspect "perenna-contracts" is a Soroban/Stellar repo, and the issue asks for a common Rust pattern: running `cargo test --release` to enable overflow checks. Without the codebase, I can only propose a generic patch to modify CI or Makefiles and ensure `Cargo.toml` has `overflow-checks = true` in its release profile. I must classify this as RAW_RADAR_CANDIDATE because I cannot verify the repo structure or run sandbox checks.

I'm considering the typical structure of a Soroban contract repository to address the bounty. The fix likely involves ensuring `overflow-checks = true` is set in the release profile within `Cargo.toml`, adding a `cargo test --release` step to the CI configuration (like a GitHub Actions workflow), or including it in a Makefile. I'd also add a unit test to specifically verify that arithmetic overflows cause panics, confirming the checks are active.

I'm trying to determine the correct `cfg` flag to check for overflow checks being enabled in release builds. `cfg!(overflow_checks)` seems like the most direct option, but I'm unsure if it's universally recognized by `rustc` or if it was stabilized recently. A runtime test using `catch_unwind` might be a more robust, albeit less direct, approach to verify this behavior.

I'm using `black_box` to prevent the compiler from optimizing away runtime overflow checks, as it can otherwise perform constant evaluation and emit a compile error. This is necessary because `arithmetic_overflow` is a deny-by-default lint. Since I cannot verify the repository or run sandbox tests, I must classify this as RAW_RADAR_CANDIDATE and mark the patch as DRAFT/NEEDS_SANDBOX.

I'm drafting a concrete patch for the `Cargo.toml` file to enable overflow checks in the release profile. However, I need to confirm if the existing `Cargo.toml` in the user's repository already includes `overflow-checks = true`, as the Soroban example contracts' workspace `Cargo.toml` does. I'll need to inspect the root `Cargo.toml`'s `[profile.*]` sections, CI workflow files in `.github/workflows/`, and potentially a `Makefile` to provide a verified patch.

I've realized that `cargo test` in debug mode already enables overflow checks by default, making the initial premise of needing a release run *just* for overflow checks slightly off. However, a release build is still crucial because it uses different codegen and optimization levels (`opt-level = "z"`), and the bounty specifically requires testing under production arithmetic settings. The proposed solution remains to add `cargo test --release` to CI or a Makefile, and optionally include a unit test to assert overflow panic behavior.

The draft correctly identifies that `cargo test` in debug mode already enables overflow checks, but a release build is still necessary for the bounty. This is because release builds use different optimization levels and codegen, and the bounty specifically requires testing under production arithmetic settings. The proposed solution of adding `cargo test --release` to CI or a Makefile, along with a unit test for overflow panic behavior, remains valid.

I'm considering how to best integrate overflow checks. A dedicated CI job is cleaner, but I need to decide where to place the unit test: within an existing contract crate, as a workspace-level assertion, or as a new integration test file. For compatibility, I'll use the `#[inline(never)]` fallback for `std::hint::black_box` if the Soroban MSRV is older than Rust 1.66, though `black_box` is generally fine for recent toolchains.

`catch_unwind` won't work if `panic = "abort"` is set, which the Soroban template does in its release profile. Cargo documentation states `panic` is ignored for tests, but I'm unsure if `cargo test --release` respects this. If it doesn't, `catch_unwind` will fail. To be safe, I could avoid `catch_unwind` entirely.

I'm switching from `catch_unwind` to `#[should_panic]` for overflow checks, as it bypasses concerns about `panic = "abort"` and is immune to the test harness's unwind behavior. `black_box` prevents constant folding, ensuring runtime overflow checks are evaluated. This approach is cleaner and works even if overflow checks are off, causing the test to fail as intended.

I'm structuring the final patch as a single `git apply`-able diff, focusing on `Cargo.toml` to enable release overflow checks, adding a release test step to the GitHub Actions workflow, and including a new test module. I'll note that hunk contexts may need adjustment.## Classification & Verification Status

- **[RULE-003]** `RAW_RADAR_CANDIDATE` — I cannot confirm `Perenna-Labs/perenna-contracts` structure from my current context. The patch below assumes a standard Rust workspace (Soroban-style, where `[profile.release]` typically already carries `overflow-checks = true` but CI only runs debug `cargo test`). Confirm before egress.
- **[RULE-002]** `DRAFT — NOT READY_FOR_EGRESS`. No sandbox run performed. Required gate: `cargo test` && `cargo test --release` && `cargo check --release` in the repo sandbox.
- **[RULE-001]** Any push/PR must go through the authenticated user PAT account, not the GitHub App.

## Surgical Changes

**1. `Cargo.toml` (workspace root) — only if `overflow-checks` is absent from the release profile:**

```diff
 [profile.release]
+overflow-checks = true
```

**2. `.github/workflows/*.yml` — insert after the existing `cargo test` step** (or add as a dedicated job to keep debug/release signal separated):

```diff
       - name: Run tests
         run: cargo test
+
+      - name: Run tests (release profile, exercises overflow-checks)
+        run: cargo test --release --workspace
```

Equivalent Makefile change if the repo routes CI through `make test`:

```diff
 test:
 	cargo test --workspace
+	cargo test --release --workspace
```

**3. Tripwire test — add to an existing `#[cfg(test)]` module** (e.g. `src/test.rs` in any contract crate):

```rust
#[test]
#[should_panic]
fn arithmetic_overflow_panics_in_this_profile() {
    // black_box blocks const-folding so this is a real runtime check.
    // Without overflow-checks this wraps silently and the test FAILS.
    let _ = std::hint::black_box(u64::MAX) + std::hint::black_box(1u64);
}
```

Notes: `#[should_panic]` is used instead of `catch_unwind` so the test is immune to `panic = "abort"` in the release profile (Soroban templates set this). `std::hint::black_box` requires Rust ≥ 1.66; for older toolchains use an `#[inline(never)]` helper instead.

## What I need to mark this READY_FOR_EGRESS

1. Path/name of the CI workflow file and its current `cargo test` step (exact context lines for the diff hunk).
2. Current `[profile.*]` block in root `Cargo.toml` (to confirm whether change 1 is needed).
3. Which contract crate's test module should host the tripwire test.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `Perenna-Labs/perenna-contracts`

## Add release-profile test run exercising `overflow-checks`

| Field | Value |
|---|---|
| **Bounty** | $75 — Add a release-profile test run to exercise `overflow-checks` |
| **Author role** | Delivery & Quality Verification Lead |
| **Status** | `DRAFT — NOT READY_FOR_EGRESS` |
| **Classification** | `RAW_RADAR_CANDIDATE` (per RULE-003) |
| **Egress route** | Authenticated user PAT only (per RULE-001) |
| **Base gate** | `cargo test --release --workspace` green in sandbox (per RULE-002) |

---

## 1. Root Cause

The repository's CI exercises only the default `dev` profile. Rust enables integer overflow checks in `dev` **by default** and disables them in `release` **by default**, so a debug-only `cargo test` run gives a false sense of arithmetic safety. Production artifacts are built with `--release` (different `opt-level`, different codegen, overflow checks off unless explicitly re-enabled), meaning:

1. Any overflow-dependent bug that is masked by debug-only checks ships untested.
2. If `overflow-checks = true` *is* declared in `[profile.release]`, nothing in CI currently proves that the declaration actually propagates to the test binary — a silent regression (e.g. a `[profile.bench]` override, or a refactor that drops the key) would go undetected.

**Root cause:** no CI path builds and runs tests under the release/bench profile, so the production arithmetic configuration is unverified.

---

## 2. Implementation

### 2.1 `Cargo.toml` (workspace root) — apply **only if** the key is absent

```diff
 [profile.release]
+overflow-checks = true
```

> Note: `cargo test --release` builds test targets with the `bench` profile, which inherits from `release`. Inheritance is what carries `overflow-checks` into the test binary — **unless** `[profile.bench]` sets the key explicitly. Verify with `cargo test --release -v` before merge.

### 2.2 `.github/workflows/*.yml` — new step after the existing debug test step

```diff
       - name: Run tests
         run: cargo test
+
+      - name: Run tests (release profile — exercises overflow-checks)
+        run: cargo test --release --workspace --locked
```

If CI routes through `make`, apply the equivalent instead:

```diff
 test:
 	cargo test --workspace
+	cargo test --release --workspace
```

### 2.3 Tripwire test — add to an existing `#[cfg(test)]` module

```rust
/// Fails if this build profile does NOT have overflow checks enabled.
/// Run under `cargo test --release` to assert production arithmetic settings.
#[test]
#[should_panic]
fn arithmetic_overflow_panics_in_this_profile() {
    // black_box prevents const-folding / const-eval, forcing a *runtime* check.
    let _ = std::hint::black_box(u64::MAX) + std::hint::black_box(1u64);
}
```

**Design notes:**

- `#[should_panic]` is deliberately chosen over `catch_unwind`: it is immune to `panic = "abort"` (the Soroban template sets this in `[profile.release]`) and to any unwind-behaviour differences in the test harness.
- `std::hint::black_box` requires Rust ≥ 1.66. If the workspace MSRV is lower, substitute an `#[inline(never)]` identity helper.
- The test is **self-verifying**: it fails on a profile without overflow checks and passes on a profile with them. That makes it the proof that 2.1/2.2 work, not just a smoke test.

---

## 3. Test Verification

### 3.1 Deterministic gates (all required before egress)

| # | Command | Expected | Purpose |
|---|---|---|---|
| G1 | `cargo fmt --check` | exit 0 | formatting |
| G2 | `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 | lint |
| G3 | `cargo test --workspace` | green | debug regression |
| G4 | `cargo test --release --workspace` | green, tripwire **passes** | new coverage |
| G5 | `cargo check --release --workspace` | exit 0 | release compile |

### 3.2 Negative control (proves the tripwire has teeth)

Temporarily set `overflow-checks = false` in the release profile, then:

```
cargo test --release arithmetic_overflow_panics_in_this_profile
```

**Must FAIL.** If it passes with checks disabled, the tripwire is being optimised away or const-evaluated — fix before merge. Revert the temporary edit and re-run G4.

### 3.3 Sandbox log (fill at execution time)

```
toolchain:  rustc <ver> / cargo <ver>
G1: <pass|fail>   G2: <pass|fail>   G3: <pass|fail>
G4: <pass|fail>   G5: <pass|fail>
negative control (3.2): <failed as expected | PASSED — INVESTIGATE>
```

> Per **RULE-002**, no patch in this proposal may be marked `PASS` or `READY_FOR_EGRESS` until 3.1–3.3 are recorded.

---

## 4. Acceptance Criteria Mapping (bounty $75)

| Criterion | Satisfied by |
|---|---|
| Release-profile test run exists in CI | 2.2 |
| Run actually exercises `overflow-checks` | 2.1 + 2.3 (tripwire) |
| Regression-proof | 3.2 negative control |
| No unrelated churn | surgical diffs only |

---

## 5. Risk & Rollback

- **Low risk.** CI-only + one test file; no contract logic touched.
- **CI duration** increases by one full release compile+test pass. Mitigation: keep as a separate job if wall-clock matters, or gate to PR + `main` only.
- **Rollback:** revert the workflow step and the test module; the `Cargo.toml` key is a one-line revert.

---

## 6. Blockers / Open Questions

1. Exact filename and current context lines of the CI workflow containing `cargo test` (needed for a clean `git apply`).
2. Current `[profile.*]` blocks in root `Cargo
\n