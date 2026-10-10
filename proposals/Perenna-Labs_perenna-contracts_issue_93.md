# Bounty Proposal: Perenna-Labs/perenna-contracts#93 - [Bounty: $80] Collapse the duplicated emit signatures behind a shared argument struct\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $80] Collapse the duplicated emit signatures behind a shared argument struct

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is a VERIFIABLE_CODE_ISSUE and is actionable and codeable since collapsing `emit_stream_created` to take the `StreamCreated` struct directly removes duplication and an allow while keeping the payload unchanged. The $80 bounty passes the $25 minimum gate with no scam signals and clear verification via `make test` and the CI `check` job.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm unable to proceed with the request to modify the `Perenna-Labs/perenna-contracts` repository. I don't have access to the codebase, which prevents me from generating a diff with exact lines as required. Furthermore, the provided rules (RULE-003 and RULE-002) explicitly state that I cannot confirm a public Git repo with reproducible tests or verify patches in a sandbox, meaning I cannot fulfill the conditions for a verified patch or mark the task as ready for egress.

Writing exact-line diffs for an unseen codebase would be fabrication, which these invariants are meant to prevent. The correct approach is to state I can't access the repo, explain what's needed, and offer an illustrative example or ask for the code. This aligns with the instruction to truthfully state when I don't know the answer.

I'm drafting an illustrative example for the "duplicated emit signatures" pattern in Solidity. The fix involves introducing a struct to consolidate parameter lists, reducing stack depth and code duplication. I'll present "before" and "after" code snippets, along with a Foundry-style test case. I need the actual files with these duplicated signatures to proceed, and I'll note that this task doesn't involve external write actions, thus avoiding boundary concerns.

I'm structuring the output as a short status header, explaining why exact-line diffs aren't possible, followed by an illustrative template with code fences, and a request for the actual code. This format will be succinct and include a before/after snippet with a compact test assertion, plus a checklist of needed items.**Classification: `RAW_RADAR_CANDIDATE`** — per RULE-003 I cannot elevate this to a verifiable code change: I don't have the contents of `Perenna-Labs/perenna-contracts`, and per RULE-002 I won't emit a diff with "exact lines" I can't compile-check against real source. Fabricating line numbers/imports for an unseen repo is precisely the failure mode those invariants guard against.

What I can do now: (a) give you the canonical shape of this refactor as a template, clearly marked as such, and (b) produce the real surgical patch once you paste the contract(s) containing the duplicated emit signatures (or the relevant file paths if the repo is mounted).

### Template — before

```solidity
function emitDeposit(address token, uint256 amount, address to, uint64 expiry) external {
    _validate(token, amount, to, expiry);
    emit Deposit(token, amount, to, expiry);
}

function emitWithdraw(address token, uint256 amount, address to, uint64 expiry) external {
    _validate(token, amount, to, expiry);
    emit Withdrawal(token, amount, to, expiry);
}
```

### Template — after

```solidity
struct EmitArgs {
    address token;
    uint256 amount;
    address to;
    uint64 expiry;
}

function emitDeposit(EmitArgs calldata args) external {
    _validate(args);
    emit Deposit(args.token, args.amount, args.to, args.expiry);
}

function emitWithdraw(EmitArgs calldata args) external {
    _validate(args);
    emit Withdrawal(args.token, args.amount, args.to, args.expiry);
}
```

### Template — Foundry test assertion

```solidity
function test_emitDeposit_acceptsSharedStruct() public {
    PerennaContracts.EmitArgs memory args = PerennaContracts.EmitArgs({
        token: address(token),
        amount: 1e18,
        to: alice,
        expiry: uint64(block.timestamp + 1 days)
    });
    vm.expectEmit(true, true, true, true);
    emit Deposit(args.token, args.amount, args.to, args.expiry);
    perenna.emitDeposit(args);
}
```

Typical surgical considerations for this refactor:
- All call sites (including other contracts in-repo and tests) must be updated to pass the struct — check for `emit*` invocations across the repo.
- Struct passed as `calldata` for external fns; ABI changes, so any interface (`I*.sol`) declaring the old signatures must be updated in the same diff.
- Verify `solc` doesn't complain about struct encoding if any arg is a dynamic type.

To get the real patch: paste the file(s) with the duplicated signatures (plus any interface files), or point me at the directory. I'll then produce exact-line diffs, updated imports/interfaces, and tests — and mark it `READY_FOR_EGRESS` only after a `forge build`/`solc` check.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Collapse duplicated `emit*` signatures behind a shared argument struct

**Repo:** `Perenna-Labs/perenna-contracts` · **Bounty:** $80
**Prepared by:** Claude, acting as Delivery & Quality Verification Lead
**Status:** `DRAFT — BLOCKED_ON_SOURCE` · **Classification:** `RAW_RADAR_CANDIDATE` (RULE-003) · **Egress:** `NOT_READY_FOR_EGRESS`

---

## 0. Verification ledger (read this first)

| Claim | Source | Status |
|---|---|---|
| Repo exists and is public | Issue text only | `UNCONFIRMED` |
| Public repo has a reproducible test suite | none | `UNCONFIRMED` |
| Duplicated `emit*` signatures exist, and how many | none | `UNCONFIRMED` |
| Exact files, lines, Solidity version, function visibility | none | `UNCONFIRMED` |
| Refactor shape (struct consolidation) | general Solidity practice | `PROPOSED` |
| Patch compiles | no sandbox run possible without source | `UNVERIFIED` |

Per **RULE-003**, this stays a `RAW_RADAR_CANDIDATE` until a public Git repository with a reproducible test suite is confirmed. Per **RULE-002**, no diff may be labelled `PASS` or `READY_FOR_EGRESS` without a deterministic compiler/linter run. This document is therefore a **proposal scaffold**, not a patch. Every line-numbered element below is a placeholder and is marked as such; none of it was invented from the repository.

---

## 1. Summary

Several helper functions in the codebase appear to emit distinct events through near-identical parameter lists, producing copy-paste duplication and repeated stack pressure. The proposed change introduces one shared argument struct, migrates all emit helpers and their call sites to it, and unifies validation.

**The actual diff cannot be written yet** — the repository contents were never supplied, and the patch stage correctly declined to fabricate line numbers for unseen source. That refusal is the correct behaviour and is preserved here.

---

## 2. Root Cause (analysis, conditional on source confirmation)

Duplicated emit signatures are a *structural* defect, not a typo:

1. **Parallel parameter lists.** Each `emitX(...)` repeats the same ordered tuple (`token, amount, to, expiry, …`). Ordering is implicit and enforced only by convention.
2. **Silent arg-order drift.** When one helper is edited, the others are not; a swapped `to`/`amount` compiles cleanly and only surfaces in an indexer or off-chain consumer.
3. **Stack-too-deep pressure.** Wide parameter lists push the compiler toward `stack too deep`, forcing `via-ir` or ad-hoc `unchecked` blocks that are unrelated to the real logic.
4. **Interface drift.** Any `I*.sol` declaring the old signatures must move in lockstep with the implementation; nothing in the toolchain enforces that today.
5. **Test churn.** Every call site (tests, scripts, mocks) repeats the full argument tuple.

**Falsifiable check to run before writing anything:** `grep -rn "emit[A-Z]" --include=*.sol` and `grep -rn "function emit" --include=*.sol` to count occurrences and confirm the duplication is real and how wide it is.

---

## 3. Decision point that must be resolved before implementation

The bounty says "collapse the duplicated **emit signatures**." Two readings, materially different ABI impact:

| Option | Change | External ABI | Risk |
|---|---|---|---|
| **A — Internal struct, public ABI preserved** | Keep existing `external` signatures; add a `private`/`internal` helper taking `EmitArgs`; each public fn builds the struct and delegates. | **Unchanged** | Low; non-breaking for integrators |
| **B — Public signature replaced by struct** | `emitDeposit(EmitArgs calldata)` replaces the flat-arg version. | **Breaking** | Requires integrator notice, interface updates, and a version bump |

**Recommendation:** Option A unless the bounty explicitly asks for an ABI change. It removes the duplication (the stated defect) without breaking downstream consumers. This is a question for the maintainers, not something to decide silently in a bounty PR.

---

## 4. Implementation (Option A shape — placeholders, not source)

```solidity
// <PATH>/<FILE>.sol — placement to be confirmed against the real file layout

/// @notice
\n