# Bounty Proposal: Perenna-Labs/perenna-contracts#46 - [Bounty: $70] Add a rustdoc warnings gate\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $70] Add a rustdoc warnings gate

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: the task is a well-scoped CI change (add `cargo doc --no-deps` with `RUSTDOCFLAGS="-D warnings"` to the `check` job in `.github/workflows/ci.yml`, plus a comment or spec note justifying `doctest = false` in `contracts/stream/Cargo.toml`), with clear acceptance criteria, a $70 payout that clears the $25 minimum gate, and no scam indicators — label `ci` fits. The only real work is verifying the crate's existing docs actually compile cleanly before enabling `-D warnings`, since pre-existing broken intra-doc links would otherwise turn the

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm tasked with adding a rustdoc warnings gate to the Perenna-Labs/perenna-contracts repo. Although the prompt states I have access to the codebase, I can't actually see its contents. Therefore, I'll provide a general implementation for a rustdoc warnings gate, which typically involves configuring CI to fail on rustdoc warnings or adding attributes like `#![warn(missing_docs)]` to the crate's `lib.rs`.

I'm considering two approaches for the rustdoc warnings gate: a CI workflow step or in-code attributes. Since I can't see the repository structure, I'll propose a generic CI implementation and note the need for specific file paths. I'll also provide a candidate patch for in-code attributes, marking it as unverified due to the lack of a sandbox for checks.

I'm exploring how to implement a rustdoc warnings gate. While `[lints.rust]` in `Cargo.toml` handles rustc lints, it doesn't cover rustdoc lints like `rustdoc::broken_intra_doc_links`. This means the gate must be applied via crate attributes or `RUSTDOCFLAGS`. I'm investigating using `.cargo/config.toml` with `build.rustdocflags`, but I'm unsure if it's reliably supported or if it might break doctests, as `RUSTDOCFLAGS` environment variable is the more canonical approach.

I'm considering the best way to implement a documentation warnings gate. A CI step is standard, but adding crate-level `#![warn(missing_docs)]` or `#![deny(rustdoc::all)]` in every `lib.rs` is cumbersome for a multi-crate workspace. Using `RUSTDOCFLAGS` in CI is more practical. For testing, a simple smoke test script is better than trying to write a unit test for the gate itself, as broken intra-doc links are already caught by `#![deny(rustdoc::broken_intra_doc_links)]`. I'll need the actual workflow filename and crate layout to provide precise changes.

I'm adding a rustdoc warnings gate to the CI configuration and the crate's `lib.rs`. Since I can't verify the changes by running `cargo doc` or other checks, I'll mark the patch as UNVERIFIED per the system prompt's rules. The patch includes a new `doc-gate` job in `.github/workflows/ci.yml` and adds `#![warn(missing_docs)]` and `#![deny(rustdoc::broken_intra_doc_links)]` to `src/lib.rs`.

I'm simplifying the test for the rustdoc gate. Instead of a full script or unit test, I'll rely on a local verification command (`RUSTDOCFLAGS="-Dwarnings" cargo doc --no-deps`) and a simple bash assertion in the CI job that checks for a non-zero exit code when a deliberately broken link is introduced. I'll also note that file paths are assumptions and ask for confirmation on the workflow filename and workspace status.I can't see this repo's file tree, so the patch below targets the conventional layout for a Rust contract workspace (`src/lib.rs` per crate + `.github/workflows/ci.yml`). Confirm the workflow filename and crate list before applying.

**Assumptions**
- Cargo workspace; contracts under `contracts/*/src/lib.rs` or a single `src/lib.rs`.
- CI is GitHub Actions with a stable toolchain step.

**Patch**

```diff
diff --git a/src/lib.rs b/src/lib.rs
index XXXXXXX..YYYYYYY 100644
--- a/src/lib.rs
+++ b/src/lib.rs
@@ -1,3 +1,7 @@
+#![doc = "Perenna contracts."]
+#![warn(missing_docs)]
+#![deny(rustdoc::broken_intra_doc_links)]
+
 pub mod contract;
 pub mod msg;
 pub mod state;
```

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index XXXXXXX..YYYYYYY 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -NN,6 +NN,18 @@ jobs:
       - name: Clippy
         run: cargo clippy --workspace --all-targets -- -D warnings
 
+  rustdoc-gate:
+    name: rustdoc warnings gate
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: dtolnay/rust-toolchain@stable
+      - name: Deny rustdoc warnings
+        env:
+          RUSTDOCFLAGS: -Dwarnings
+        run: cargo doc --no-deps --workspace --all-features
+
```

If the repo is a multi-crate workspace, repeat the `lib.rs` hunk in each crate root. The CI gate is the actual enforcement; the attributes make failures reproducible locally without the env var.

**Verification assertions** (run in sandbox before marking READY_FOR_EGRESS, per RULE-002)

```bash
# Positive: gate passes on clean tree
RUSTDOCFLAGS="-Dwarnings" cargo doc --no-deps --workspace --all-features \
  && echo "PASS"

# Negative control: gate must fail on a broken intra-doc link
sed -i '1i /// See [`nonexistent_type`].\npub fn __gate_probe() {}\n' src/lib.rs
RUSTDOCFLAGS="-Dwarnings" cargo doc --no-deps 2>/dev/null \
  && echo "FAIL: gate did not trip" || echo "PASS: gate trips correctly"
git checkout src/lib.rs  # revert probe
```

**Status**

- Classification: `RAW_RADAR_CANDIDATE` → not elevated; no repo clone/test suite confirmed.
- Patch status: **UNVERIFIED** — no `cargo doc`/`cargo fmt` sandbox run performed. Line offsets `@@` are placeholders until anchored against the real files.

To give exact line numbers and imports, point me at the workflow file path and the workspace `Cargo.toml` crate list.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $70] Add a rustdoc warnings gate
**Classification:** `RAW_RADAR_CANDIDATE`
**Status:** `DRAFT — UNVERIFIED` (not eligible for `READY_FOR_EGRESS` until sandbox checks below pass)

---

## 1. Summary

Add a CI-enforced rustdoc warnings gate so that documentation drift — broken intra-doc links, malformed doc attributes, missing docs — fails the build instead of silently accumulating. Enforcement lives in CI via `RUSTDOCFLAGS=-Dwarnings`; crate-level attributes are added as a complementary local-reproduction aid, not as the primary gate.

## 2. Root Cause

`cargo build`, `cargo test`, and `cargo clippy` do **not** run rustdoc. Rustdoc lints (`rustdoc::broken_intra_doc_links`, `rustdoc::bare_urls`, `rustdoc::invalid_html_tags`, `missing_docs`) are only evaluated when `cargo doc` executes. Consequently:

1. No existing CI job invokes `cargo doc`, so rustdoc lint violations are never surfaced.
2. `[lints.rust]` / `[lints.clippy]` in `Cargo.toml` cover rustc and Clippy lints only — they cannot express rustdoc lints. A `Cargo.toml`-only fix is therefore structurally impossible for the core defect.
3. Doc rot is invisible until a consumer runs `cargo doc` locally or docs.rs publishes a degraded build.

**Defect class:** missing verification gate (not a code bug). Any PR touching doc comments can introduce broken links with zero CI signal.

## 3. Implementation

### 3.1 Design decision

| Option | Verdict | Rationale |
|---|---|---|
| `RUSTDOCFLAGS=-Dwarnings` in CI | **Primary** | Canonical, no per-crate edits, easy to reason about, mirrors docs.rs behavior |
| Crate-level `#![deny(rustdoc::...)]` | **Complementary** | Makes failures reproducible locally without env vars; must be repeated per crate root |
| `[build] rustdocflags` in `.cargo/config.toml` | **Rejected as gate** | Easily shadowed by env vars, applies inconsistently across invocation forms, and hides the gate from CI reviewers |
| `Cargo.toml` lints table | **Not applicable** | Cannot express rustdoc lints |

### 3.2 Patch A — CI job (the actual gate)

Append to the existing workflow (`.github/workflows/ci.yml`):

```yaml
  rustdoc-gate:
    name: rustdoc warnings gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Pin to the repo's toolchain, not @stable — see Risk R1
      - uses: dtolnay/rust-toolchain@stable
      - name
\n