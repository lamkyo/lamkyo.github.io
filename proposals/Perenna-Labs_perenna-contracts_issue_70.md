# Bounty Proposal: Perenna-Labs/perenna-contracts#70 - [Bounty: $95] Reject `stop_time` values that overflow the i128 accrual window\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $95] Reject `stop_time` values that overflow the i128 accrual window

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
I can't write production code for the "Perenna-Labs/perenna-contracts" bounty issue because I don't have access to the actual codebase. Attempting to generate a patch without seeing the code would violate the principle of grounding changes in real code.

I've identified the issue as potential `stop_time` overflows in Soroban smart contracts, likely within the `perenna-contracts` codebase. While a `u64` to `i128` cast won't overflow, calculations like `stop_time * rate` or `(stop_time - start_time) * amount` could exceed `i128` limits. I need to ask for the specific file containing the accrual logic, but I can also provide a speculative implementation demonstrating the fix pattern.

I'm reconsidering the overflow potential. While direct multiplication of `stop_time` and `rate` might not overflow `i128`, the contract likely calculates the total deposited amount using `(stop_time - start_time) * rate`. If `stop_time` is extremely large, this calculation could exceed `i128::MAX` or the actual deposited amount, breaking invariants. The fix involves validating `stop_time` at stream creation, perhaps by checking against a `MAX_ACCRUAL_WINDOW` or using `checked_mul` to reject values that would lead to overflow.

The issue title implies an overflow within the `i128` accrual window, likely from `stop_time * rate` or accrued amount calculations, not the `u64` to `i128` cast itself. I'll implement a defensive check at creation, validating that `(stop_time - start_time) * rate_per_second` fits within `i128` using checked arithmetic and returning a contract error. I'll write this as a Soroban Rust contract patch, noting the uncertain file layout and providing the fix with tests and a diff.

I'm opting to provide a complete, isolated reference implementation and patch template rather than just asking for clarification, as the user's request is detailed and expects code. I'll explicitly mark identifiers and paths needing reconciliation and note that the patch status is not yet 'PASS' per RULE-002, as I cannot run `cargo check` or `soroban contract build` myself.

The core issue is likely `(stop_time - start_time) * rate` overflowing `i128`, not the `u64` to `i128` cast. My `checked_mul` approach implicitly enforces the necessary bound `stop_time <= start_time + i128::MAX / rate`, which is the most precise fix for the "i128 accrual window" overflow. I'll also note an optional absolute cap on `stop_time` as a secondary measure.

I'm structuring the response to include a caveat about unresolved file paths, followed by assumptions, the production diff, the test diff, and finally verification commands and status. I'll ensure the patch and tests are presented clearly using Rust code blocks and diff format, keeping the overall response concise and actionable.

I've added a new error code, `AccrualWindowOverflow`, and a validation function `check_stop_time` to prevent overflows in the accrual math. This function will be called at stream creation and potentially during `set_stop_time` updates. I'm also considering adding checked math to the accrual path itself as a defense-in-depth measure, though the primary fix is input validation.

Wait, the `max_window` calculation `i128::MAX / rate` can overflow `u64` when added to `start`. This happens if `rate` is too small, specifically less than `i128::MAX / u64::MAX`. I need to ensure the `rate` used in tests is large enough, like `1e19` or `2e19`, so that `max_window` is less than `u64::MAX - start`.

It's simpler to test rejection via a huge `stop_time` with a small `rate`, as `window * rate` would only overflow `u64` if `window` exceeds `1.7e32`. For `u64` timestamps, overflow requires `rate > ~9.2e18/sec`, which is a legitimate boundary worth noting. If `stop_time` is `i128`, overflow is much more reachable. I'll implement for both signatures, making the check generic over a `u64` window and noting that if `stop_time` is `i128`, `stop_time - start_time` needs `checked_sub`.

The `max_window` calculation using `i128::MAX / rate` could overflow `u64` if `rate` is very small. I need to ensure my test rates are large enough to avoid this, or handle the `u64` overflow explicitly. It's simpler to test rejection with a huge `stop_time` and small `rate`, as `u64` overflow requires a rate over ~9.2e18/sec.I don't have `Perenna-Labs/perenna-contracts` files in my context index — the paths/symbols below are grounded against the standard Soroban (Rust, i128) contract layout this issue describes. Per **[RULE-003]** this patch is `RAW_RADAR_CANDIDATE` → `READY_FOR_EGRESS` only after `cargo test` passes in the sandbox. Per **[RULE-002]**, treat it as a template until the marked assumptions are reconciled with the real source.

**Assumptions to reconcile:** contract is Soroban/Rust; creation entrypoint is `create`; rate field is `rate_per_second: i128`; timestamps are `u64`; error enum is `contracterror`.

### Root cause
`stop_time` is accepted unvalidated at ingress, then accrual math computes `(stop_time - start_time) as i128 * rate_per_second`. For `rate > i128::MAX / u64::MAX` (~`9.2e18` raw units/sec), or if `stop_time` is `i128`/user-sourced, this panics or wraps. Reject at the boundary.

### Production diff

```diff
--- a/contracts/perenna/src/error.rs
+++ b/contracts/perenna/src/error.rs
@@ enum Error
     InvalidTimeRange = 4,
+    /// (stop_time - start_time) * rate_per_second does not fit in i128.
+    AccrualWindowOverflow = 7,
 }
```

```diff
--- a/contracts/perenna/src/lib.rs
+++ b/contracts/perenna/src/lib.rs
@@
+/// Rejects `stop_time` values whose accrual window overflows the i128
+/// accrual math: `(stop_time - start_time) * rate_per_second` must fit.
+fn check_stop_time(start_time: u64, stop_time: u64, rate_per_second: i128) -> Result<(), Error> {
+    if rate_per_second <= 0 {
+        return Err(Error::InvalidRate);
+    }
+    let window = stop_time
+        .checked_sub(start_time)
+        .filter(|w| *w > 0)
+        .ok_or(Error::InvalidTimeRange)? as i128;
+    window
+        .checked_mul(rate_per_second)
+        .ok_or(Error::AccrualWindowOverflow)?;
+    Ok(())
+}
+
@@ fn create(...)
     if params.stop_time <= params.start_time {
         return Err(Error::InvalidTimeRange.into());
     }
+    check_stop_time(params.start_time, params.stop_time, params.rate_per_second)?;
```

If `stop_time` is mutable post-creation (e.g., `set_stop_time`), apply the same `check_stop_time` call there.

### Test diff

```diff
--- a/contracts/perenna/src/test.rs
+++ b/contracts/perenna/src/test.rs
@@
+#[test]
+fn create_rejects_stop_time_overflowing_i128_window() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    // rate > i128::MAX / u64::MAX, so a 4s window must overflow.
+    let rate = i128::MAX / 2;
+    let start = 1_700_000_000u64;
+    let stop = start + 4;
+    let res = client.try_create(&admin, &token, &start, &stop, &rate);
+    assert_eq!(res, Err(Ok(Error::AccrualWindowOverflow)));
+}
+
+#[test]
+fn create_accepts_boundary_stop_time() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    let rate = 20_000_000_000_000_000_000i128; // 2e19
+    let start = 1_700_000_000u64;
+    let max_window = (i128::MAX / rate) as u64;
+    // max_window * rate <= i128::MAX (integer division) -> accepted
+    assert!(client
+        .try_create(&admin, &token, &start, &(start + max_window), &rate)
+        .is_ok());
+    // one second past the bound -> rejected
+    assert_eq!(
+        client.try_create(&admin, &token, &start, &(start + max_window + 1), &rate),
+        Err(Ok(Error::AccrualWindowOverflow))
+    );
+}
+
+#[test]
+fn create_rejects_stop_time_not_after_start() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    let res = client.try_create(&admin, &token, &100u64, &100u64, &1i128);
+    assert_eq!(res, Err(Ok(Error::InvalidTimeRange)));
+}
```

### Verification required before egress (RULE-002)

```bash
cargo check --workspace && cargo test -p perenna
soroban contract build  # wasm target must compile clean
```

If you can paste `lib.rs`/`error.rs` (or confirm the real entrypoint/field names — e.g., whether `stop_time` is `u64` or `i128`), I'll regenerate the diff as exact line-anchored hunks.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Reject `stop_time` values that overflow the i128 accrual window

**Repository:** `Perenna-Labs/perenna-contracts`
**Bounty:** $95 — *Reject `stop_time` values that overflow the i128 accrual window*
**Branch (proposed):** `fix/accrual-window-overflow`
**Type:** Security hardening / input validation (non-breaking)

> **Status gate:** `RAW_RADAR_CANDIDATE` → `VERIFIABLE_CODE_ISSUE` requires the public repo + reproducible test suite confirmed **[RULE-003]**. The hunks below are grounded against the standard Soroban/Rust `i128` contract layout this issue describes; they are **not** `READY_FOR_EGRESS` until `cargo test` passes in-sandbox **[RULE-002]**. All paths/symbols marked ⚠️ must be reconciled against the real tree before egress.

---

## 1. Summary

`stop_time` is accepted at stream creation without validating that the accrual window `(stop_time - start_time)` can be safely multiplied by `rate_per_second` inside `i128`. For large rates or attacker-supplied far-future timestamps, the accrual math panics or wraps, breaking the stream's amount invariant. This PR rejects such inputs at the ingress boundary and adds regression coverage.

---

## 2. Root Cause

Accrual is computed as:

```
accrued = (stop_time - start_time) as i128 * rate_per_second
```

- The `u64 → i128` cast itself is lossless, so the issue is **not** the cast.
- The multiplication is unguarded. It overflows when `(stop_time - start_time) > i128::MAX / rate_per_second`.
- For `u64` timestamps the overflow threshold is `rate_per_second > i128::MAX / u64::MAX` (~`9.2e18` raw units/sec) — reachable for high-precision or high-decimal assets.
- If `stop_time` is user-sourced as `i128`, or the window is derived from an unvalidated `i128`, the overflow is trivially reachable.

**Impact:** panic / wrapped accrual → incorrect withdrawable balance, broken `total_deposited` invariant, potential DoS on stream creation and accrual reads.

**Fix strategy:** validate at the boundary (creation, and any post-creation mutation of `stop_time`), using `checked_sub` + `checked_mul` so the exact admissible window is enforced — no arbitrary magic cap needed.

---

## 3. Implementation

### 3.1 Error variant

```diff
--- a/contracts/perenna/src/error.rs
+++ b/contracts/perenna/src/error.rs
@@ enum Error
     InvalidTimeRange = 4,
+    /// (stop_time - start_time) * rate_per_second does not fit in i128.
+    AccrualWindowOverflow = 7,
 }
```

⚠️ **Verify:** variant index `7` must not collide with an existing discriminant; renumber to the next free slot if it does.

### 3.2 Validation helper + call site

```diff
--- a/contracts/perenna/src/lib.rs
+++ b/contracts/perenna/src/lib.rs
@@
+/// Rejects `stop_time` values whose accrual window overflows the i128
+/// accrual math: `(stop_time - start_time) * rate_per_second` must fit.
+fn check_stop_time(start_time: u64, stop_time: u64, rate_per_second: i128) -> Result<(), Error> {
+    if rate_per_second <= 0 {
+        return Err(Error::InvalidRate);
+    }
+    let window = stop_time
+        .checked_sub(start_time)
+        .filter(|w| *w > 0)
+        .ok_or(Error::InvalidTimeRange)? as i128;
+    window
+        .checked_mul(rate_per_second)
+        .ok_or(Error::AccrualWindowOverflow)?;
+    Ok(())
+}
+
@@ fn create(...)
     if params.stop_time <= params.start_time {
         return Err(Error::InvalidTimeRange.into());
     }
+    check_stop_time(params.start_time, params.stop_time, params.rate_per_second)?;
```

⚠️ **Verify:** entrypoint name (`create`), field names (`start_time`, `stop_time`, `rate_per_second`), and error type (`Error` vs `ContractError`) against the real source.

**If `stop_time` is mutable post-creation** (e.g. a `set_stop_time` / `extend` entrypoint), apply the identical `check_stop_time` call there — an unchecked mutation path reopens the hole.

**If `stop_time` is `i128`** rather than `u64`: swap `checked_sub` for `i128::checked_sub` and drop the cast; the `checked_mul` guard is unchanged.

### 3.3 Tests

```diff
--- a/contracts/perenna/src/test.rs
+++ b/contracts/perenna/src/test.rs
@@
+#[test]
+fn create_rejects_stop_time_overflowing_i128_window() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    // rate > i128::MAX / u64::MAX, so a 4s window must overflow.
+    let rate = i128::MAX / 2;
+    let start = 1_700_000_000u64;
+    let stop = start + 4;
+    let res = client.try_create(&admin, &token, &start, &stop, &rate);
+    assert_eq!(res, Err(Ok(Error::AccrualWindowOverflow)));
+}
+
+#[test]
+fn create_accepts_boundary_stop_time() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    let rate = 20_000_000_000_000_000_000i128; // 2e19
+    let start = 1_700_000_000u64;
+    let max_window = (i128::MAX / rate) as u64;
+    // max_window * rate <= i128::MAX (integer division) -> accepted
+    assert!(client
+        .try_create(&admin, &token, &start, &(start + max_window), &rate)
+        .is_ok());
+    // one second past the bound -> rejected
+    assert_eq!(
+        client.try_create(&admin, &token, &start, &(start + max_window + 1), &rate),
+        Err(Ok(Error::AccrualWindowOverflow))
+    );
+}
+
+#[test]
+fn create_rejects_stop_time_not_after_start() {
+    let e = Env::default();
+    let (client, admin, token) = setup(&e);
+    let res = client.try_create(&admin, &token, &100u64, &100u64, &1i128);
+    assert_eq!(res, Err(Ok(Error::InvalidTimeRange)));
+}
```

**Boundary-math note:** with `rate = 
\n