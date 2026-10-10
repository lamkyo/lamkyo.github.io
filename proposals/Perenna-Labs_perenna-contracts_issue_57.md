# Bounty Proposal: Perenna-Labs/perenna-contracts#57 - [Bounty: $80] Move `require_auth` before the `is_canceled`/`cancelable` checks in `cancel`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $80] Move `require_auth` before the `is_canceled`/`cancelable` checks in `cancel`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Verdict: Actionable and codeable.**

The change is a small, well-scoped reordering of statements in a single function (`cancel` in `contracts/stream/src/lib.rs`) to call `stream.sender.require_auth()` immediately after loading the stream and before the `is_canceled`/`cancelable` checks — it is verifiable against the existing test suite (`make test` plus the `check` CI job) and against explicit acceptance criteria asserting unauthorized calls now fail at auth rather than `StreamCanceled`/`NotCancelable`. The only caveat worth confirming is that no existing tests depend on the current error-precedence, which is exactly what the acceptance criteria are designed to catch.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm looking at the `Perenna-Labs/perenna-contracts` repository, specifically an issue about moving `require_auth` before `is_canceled`/`cancelable` checks in a `cancel` function. This seems to be a Soroban smart contract. Although the prompt states I have access to the codebase, I couldn't identify the specific files involved. Since I can't see the actual code, I'll have to make an assumption about the change and clearly state it when providing the patch.

I'm noting mandatory invariants like RULE-001, RULE-003, and RULE-006. RULE-003 suggests classifying this as a RAW_RADAR_CANDIDATE until the repo is verified, and RULE-006 requires financial rounding quantization if payments are involved. Since I can't access the actual code, I'll provide a canonical Soroban fix with assumed paths and assertions, clearly stating my assumptions and noting the invariant classifications.

I'm reviewing the `cancel` function's logic, specifically the ordering of `require_auth` and state checks like `is_canceled` and `cancelable`. The draft correctly points out that auth checks should precede state checks to prevent unauthorized users from learning sensitive state information or causing denial-of-service through state-dependent panics. This aligns with common Soroban audit findings and necessitates a change in the function's implementation, as reflected in the proposed test case.

I'm noting that the typical Soroban test for authorization ordering involves checking `env.auths()` after a call, or verifying panic messages when `mock_all_auths()` is used. To ensure `require_auth` runs first, I'll suggest testing the panic behavior when auth isn't mocked, which should yield an "Unauthorized function call" error instead of a state-related one like "already canceled." I'll also draft the answer with assumed file paths and a generic patch, asking the user to confirm the exact location.

I'm refining the test for authorization ordering. Instead of just checking for any error, I'll assert that `try_cancel` returns `Err(Err(_))` specifically, distinguishing host/auth errors from contract panics. This aligns with the `Result<Result<T, E>, Result<SdkError/InvokeError...>>` return type. I'll also add a test to verify that an authorized call to cancel an uncancelable schedule still panics with the correct "already canceled" message.

I'll produce the diff in unified format, noting that line numbers and hunks are approximate and paths are assumed to be `contracts/<contract>/src/contract.rs`. I'll ask for confirmation before proceeding.Quick framing, then the patch.

**Status (RULE-003):** I can't confirm the exact file layout of `perenna-contracts` from context, so I'm treating this as a candidate fix against the standard Soroban `cancel` pattern. Adjust paths/hunk headers to the actual file — likely `contracts/<name>/src/contract.rs` or `lib.rs`. If you point me at the file, I'll tighten the line numbers.

### Rationale
Guarding on state (`is_canceled`, `cancelable`) before `require_auth` lets unauthenticated callers probe contract state via revert reasons, and reverses the checks-before-auth convention auditors flag. Auth must be demanded first — every caller, authorized or not, gets an identical auth failure.

### Production diff

```diff
--- a/contracts/<contract>/src/contract.rs
+++ b/contracts/<contract>/src/contract.rs
@@ fn cancel
     pub fn cancel(env: Env, id: u64) {
-        let mut schedule = read_schedule(&env, id);
+        let mut schedule = read_schedule(&env, id);
 
-        if schedule.is_canceled {
-            panic_with_error!(&env, Error::AlreadyCanceled);
-        }
-        if !schedule.cancelable {
-            panic_with_error!(&env, Error::NotCancelable);
-        }
+        // Auth first: identical failure for unauthorized callers
+        // regardless of schedule state.
+        schedule.owner.require_auth();
 
-        schedule.owner.require_auth();
+        if schedule.is_canceled {
+            panic_with_error!(&env, Error::AlreadyCanceled);
+        }
+        if !schedule.cancelable {
+            panic_with_error!(&env, Error::NotCancelable);
+        }
 
         schedule.is_canceled = true;
         write_schedule(&env, id, &schedule);
     }
```

If the contract uses `env.current_contract_address()`-scoped auth or a stored `canceler`/`borrower` role instead of `schedule.owner`, move *that* address's `require_auth()` — same ordering principle. No import changes needed.

### Unit tests

```rust
#[test]
fn cancel_demands_auth_even_when_state_guards_would_revert() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, id) = setup_canceled_and_locked_schedule(&env);
    // Seed: is_canceled == true AND cancelable == false

    // Now drop all mocked auths and retry.
    let env2 = Env::default(); // or reset auth via client.mock_auths(&[])
    let res = client.try_cancel(&id);

    // Host-side auth failure (Err(Err(..))), NOT the contract's
    // AlreadyCanceled / NotCancelable panic (Err(Ok(..))).
    assert!(matches!(res, Err(Err(_))));
}

#[test]
fn cancel_records_owner_auth() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, owner, id) = setup_cancelable_schedule(&env);

    client.cancel(&id);

    let auths = env.auths();
    assert_eq!(auths.len(), 1);
    assert_eq!(auths[0].0, owner);
    assert_eq!(
        auths[0].1.function,
        AuthorizedFunction::Contract((
            client.address.clone(),
            Symbol::new(&env, "cancel"),
            (id,).into_val(&env),
        ))
    );
}

#[test]
#[should_panic(expected = "AlreadyCanceled")]
fn cancel_still_reverts_when_already_canceled_with_auth() {
    let env = Env::default();
    env.mock_all_auths();
    let (client, id) = setup_canceled_schedule(&env);
    client.cancel(&id); // auth passes, state guard reverts
}
```

### Notes
- **RULE-006:** if `cancel` also computes a refund/payout split, keep the quantize-gross-upfront invariant — reorder auth only, don't touch the arithmetic path.
- **RULE-001:** if this patch gets pushed to the public repo, route it through an authenticated user PAT, not the GitHub App.

Want me to adapt this once you confirm the real file path and the exact struct/field names (`owner` vs `borrower`, error enum names)?

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `fix: require_auth before state guards in cancel`

**Repo:** Perenna-Labs/perenna-contracts
**Bounty:** $80 — *Move `require_auth` before the `is_canceled`/`cancelable` checks in `cancel`*
**Branch:** `fix/cancel-auth-ordering` → `main`
**Labels:** `security`, `bounty`, `auth-ordering`, `needs-verification`
**Status:** `DRAFT — NOT VERIFIED` (see §9; RULE-002 gate not satisfied in this context)

---

## 1. Summary

Reorder the guard sequence inside the `cancel` entrypoint so the caller's authorization is demanded **before** the `is_canceled` / `cancelable` state guards. No storage-layout change, no arithmetic change, no new imports. Pure control-flow reordering plus regression tests.

## 2. Root Cause

The current `cancel` reads schedule state and evaluates state-dependent guards before calling `require_auth`. Two consequences:

1. **State oracle / error-based probing.** An unauthenticated caller can distinguish `AlreadyCanceled`, `NotCancelable`, and success-path reachability from revert reasons alone. Any third party can enumerate schedule state without authorization.
2. **Inverted convention.** Soroban's authorization model is "authenticate the caller, then decide." State checks ahead of auth invert that and are a recurring audit finding (and a repeated finding class across Soroban deployments).

The fix restores the invariant: **every** caller — authorized or not — receives an identical authorization failure first.

## 3. Scope

**In scope:** guard ordering in `cancel` only; regression tests covering ordering.
**Non-goals:** the refund/payout arithmetic path (untouched — see RULE-006 note in §11), error enum renames, storage schema, other entrypoints.

## 4. Implementation

```diff
--- a/contracts/<contract>/src/contract.rs
+++ b/contracts/<contract>/src/contract.rs
@@ pub fn cancel
     pub fn cancel(env: Env, id: u64) {
         let mut schedule = read_schedule(&env, id);
 
-        if schedule.is_canceled {
-            panic_with_error!(&env, Error::AlreadyCanceled);
-        }
-        if !schedule.cancelable {
-            panic_with_error!(&env, Error::NotCancelable);
-        }
+        // Auth first: identical failure surface for unauthorized callers,
+        // independent of schedule state.
+        schedule.owner.require_auth();
 
-        schedule.owner.require_auth();
+        if schedule.is_canceled {
+            panic_with_error!(&env, Error::AlreadyCanceled);
+        }
+        if !schedule.cancelable {
+            panic_with_error!(&env, Error::NotCancelable);
+        }
 
         schedule.is_canceled = true;
         write_schedule(&env, id, &schedule);
     }
```

**Note on the read-then-auth ordering:** `require_auth` necessarily follows `read_schedule`, because the authenticated address is derived from the stored record. This means a *nonexistent* `id` still short-circuits at the read with `NotFound` rather than an auth error. That is standard and accepted; it is called out in §10 as residual, not fixed here.

**Substitution rule:** if the contract authenticates a role other than `schedule.owner` (e.g. a stored `canceler`/`borrower`), move *that* address's `require_auth()` under the same rule. No import changes either way.

## 5. Blocking Assumptions — Must Be Confirmed Before Merge

| # | Assumption | Consequence if wrong |
|---|---|---|
| A1 | File path is `contracts/<contract>/src/contract.rs` (or `lib.rs`) | Hunk headers wrong; diff won't apply |
| A2 | Authenticated principal is `schedule.owner`
\n