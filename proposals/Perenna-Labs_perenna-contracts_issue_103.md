# Bounty Proposal: Perenna-Labs/perenna-contracts#103 - [Bounty: $70] Test that withdrawals are bounded by elapsed time (anti-drain)\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $70] Test that withdrawals are bounded by elapsed time (anti-drain)

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Yes, this is actionable and highly codeable — it requires only a new test in contracts/stream/src/test.rs that attempts a near-full-deposit withdraw shortly after start_time, asserts WithdrawAmountTooHigh and unchanged balance, then verifies a small accrued withdrawal succeeds. Per triage invariants it remains a RAW_RADAR_CANDIDATE until Perenna-Labs/perenna-contracts is confirmed public with a reproducible `make test` and CI check workflow, but no production logic changes are needed and risk is minimal.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm trying to address a bounty for testing withdrawals against elapsed time in the Perenna-Labs/perenna-contracts repo. However, I don't have access to the codebase, nor do I know the contract language or specific contract type. This prevents me from writing production code or unit tests as required.

I've identified the bounty as testing withdrawal rate limits based on elapsed time. However, I cannot create a verifiable patch without access to the codebase. According to the system prompt, I should clarify that I have access but need more specific information about the relevant contracts and test setup.

I must classify this issue as RAW_RADAR_CANDIDATE due to uncertainty about the repo and test suite, and avoid marking anything as PASS/READY_FOR_EGRESS without deterministic checks. I can still provide a generic anti-drain withdrawal test template, clearly labeled as needing adaptation, to be helpful without being misleading about providing exact code. I need to explain why I can't provide exact lines and list what information is required. The core logic for anti-drain withdrawals involves time elapsed, either linearly or as a fraction of a duration, and tests should verify partial and full withdrawals, as well as cumulative limits.

I've drafted a generic Foundry test skeleton for withdrawal time bounds, covering common anti-drain patterns like elapsed time and cumulative limits. However, I need to be cautious not to assume the repository's API or test setup. I'll classify this as RAW_RADAR_CANDIDATE because I can't confirm the repo structure or test suite context.

I can't provide an exact diff for the Perenna contracts because I don't have access to the repository's files. Fabricating code would violate the rule against non-verifiable changes. To proceed, I need to know the development framework (Foundry, Hardhat, etc.), the specific contract and function for withdrawals with time-bounding logic, and the location and conventions of existing tests. I'll offer a generic Foundry test skeleton as a starting point, clearly marked as a template.

I've drafted a generic Foundry test skeleton for withdrawal time bounds, including tests for zero elapsed time, bounded partial withdrawals, and cumulative withdrawal limits to prevent anti-drain exploits. This template needs to be adapted to the specific API of the target contract, as indicated by the commented-out sections and TODOs.

The draft includes comments on test cases for withdrawal logic, specifically focusing on elapsed time and cumulative limits. It also contains meta-commentary about the structure and content of the agent's own output, including decisions on headers, mentions, and potential framework assumptions. The agent is considering whether to mention a specific rule and whether to add a note about egress, ultimately deciding to keep it minimal. It also reflects on the possibility of the target repository being written in Rust/Solana or Move/Aptos, while noting the assumption of a Foundry template.**Status: `RAW_RADAR_CANDIDATE`** (per RULE-003 — no confirmed clone of `Perenna-Labs/perenna-contracts` with a reproducible test suite exists in my context).

I can't produce a diff with "exact lines" for this repo right now. I don't have its file layout, the withdrawal implementation, or the test framework in context — and any line-exact patch I fabricated would fail RULE-002, since it couldn't pass a deterministic `forge test` / `tsc` / `cargo test` check before egress.

**To elevate this to `VERIFIABLE_CODE_ISSUE` and write the real patch, I need:**

1. **Framework** — Foundry? Hardhat? Anchor/Rust? (Assuming Foundry below.)
2. **The withdrawal code** — path to the contract + function enforcing the elapsed-time bound (e.g., `src/Vault.sol::withdraw`), and the formula used (`rate * elapsed`, linear unlock, cliff?).
3. **Test conventions** — which existing test file to extend, and how time is manipulated (`vm.warp`, `evm_increaseTime`, clock mocking).

**Generic skeleton** (template only — `NOT READY_FOR_EGRESS`):

```solidity
// test/WithdrawalTimeBounds.t.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Test} from "forge-std/Test.sol";

contract WithdrawalTimeBoundsTest is Test {
    // TODO: adapt to actual contract API / setUp

    /// @dev Zero elapsed → zero withdrawable.
    function test_withdraw_noElapsedTime_yieldsZero() public {
        // assertEq(vault.withdrawable(alice), 0);
        // vm.expectRevert(); vault.withdraw(1);
    }

    /// @dev Partial elapsed → bound enforced.
    function test_withdraw_boundedByElapsedTime() public {
        // vm.warp(t0 + elapsed);
        // uint256 expected = RATE * elapsed;
        // vm.expectRevert(); vault.withdraw(expected + 1);
        // vault.withdraw(expected); // ok
    }

    /// @dev Anti-drain: cumulative withdrawals ≤ bound. Guards the classic
    ///      stale `lastWithdrawal` / missing cumulative accounting bug —
    ///      where most anti-drain vulnerabilities actually live.
    function test_withdraw_cumulativeCannotExceedElapsedBound() public {
        // vm.warp(t0 + half); vault.withdraw(max);
        // assertEq(vault.withdrawable(alice), 0);
        // vm.expectRevert(); vault.withdraw(1);
    }

    /// @dev Fully elapsed → no bound remains.
    function test_withdraw_fullElapsed_unbounded() public {
        // vm.warp(t0 + FULL_PERIOD);
        // vault.withdraw(ENTIRE_BALANCE);
    }

    /// @dev Fuzz: withdrawable ≤ rate * elapsed for all elapsed ≤ period.
    function testFuzz_withdraw_neverExceedsRateTimesElapsed(uint256 elapsed) public {
        // elapsed = bound(elapsed, 0, FULL_PERIOD);
        // vm.warp(t0 + elapsed);
        // assertLe(vault.withdrawable(alice), RATE * elapsed);
    }
}
```

The highest-value assertion here is `test_withdraw_cumulativeCannotExceedElapsedBound` — anti-drain failures are typically accounting bugs (per-call bound computed without tracking cumulative withdrawals), not formula bugs.

Point me at the relevant contract file and test directory and I'll produce the actual diff.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `test(withdrawals): bound withdrawal by elapsed time (anti-drain invariant)`

**Classification:** `RAW_RADAR_CANDIDATE` (RULE-003)
**Artifact status:** `NOT READY_FOR_EGRESS` (RULE-002 gate not yet satisfiable)
**Deliverable type:** test-only bounty — no production code change expected

> **Read this first.** This document is a *complete, submission-shaped PR proposal* with every section a reviewer will ask for. It is **not** a line-exact patch, because no clone of `Perenna-Labs/perenna-contracts` with a reproducible test suite exists in my context. The Implementation section is a **framework-parameterized template** with explicit `TODO(adapter)` markers. Section 7 lists exactly what unblocks the line-exact version. Any claim of `PASS` before the Section 5 gate runs would violate RULE-002.

---

## 0. Submission gates (must all be green before egress)

| # | Gate | Rule | Current |
|---|------|------|---------|
| G1 | Target repo cloned; framework + toolchain version pinned | RULE-003 | ⛔ blocked |
| G2 | Test file compiles/lints in sandbox (`forge build` + `forge test`) | RULE-002 | ⛔ blocked |
| G3 | Tests **fail** against a bound-removed mutant (falsification) | RULE-002 | ⛔ blocked |
| G4 | PR opened from a **PAT-authenticated user account**, not the GitHub App | RULE-001 | ⛔ pending |

The GitHub App may clone, scout, and mirror internally. It **must not** open the public PR (RULE-001).

---

## 1. Summary

Add a focused test suite asserting the anti-drain invariant for time-bounded withdrawals: **the amount withdrawable at any timestamp `t` is bounded by a function of elapsed time since the withdrawal window opened**, and that bound is enforced against *cumulative* withdrawals, not merely per-call.

The bounty is written as a verification task ("test that withdrawals are bounded by elapsed time"), so the expected change is a new test file plus, if the invariant is currently untested, a documented invariant statement. If the tests **fail** against the real implementation, the bounty converts from a test task into a bug report — Section 5.4 covers that branch.

---

## 2. Scope

**In scope**
- New test contract covering the elapsed-time withdrawal bound.
- Zero-elapsed, partial-elapsed, full-elapsed, and cumulative-accounting cases.
- One fuzz property over `elapsed`.
- A falsification check proving the suite actually detects removal of the bound.

**Out of scope (explicitly)**
- Any change to the withdrawal implementation. A test bounty that edits the code under test is not independently verifiable.
- Gas optimization, refactors, event changes, access-control changes.
- Reformatting or reordering existing tests.

---

## 3. Root Cause

Stated at the level I can currently justify, with the confidence level attached.

**3.1 Why this test is missing (high confidence).** Anti-drain bounds are usually introduced as a *formula* in the withdrawal path (`withdrawable = rate * (block.timestamp - start)`) and validated by a happy-path test that only ever warps to a single convenient timestamp. The class of defect that survives that coverage is not the formula — it is the **accounting around it**.

**3.2 The two failure modes this suite targets (high confidence, both are standard).**

| ID | Failure mode | Why a naive test misses it |
|----|--------------|----------------------------|
| FM-1 | Per-call bound computed from elapsed time **without subtracting prior withdrawals in the window**. Caller withdraws `rate * elapsed` repeatedly at the same timestamp. | Single-call test asserts `withdrawable(t) == rate * elapsed` and passes; drain is invisible. |
| FM-2 | **Stale window anchor** — `lastWithdrawal` / `startTime` not updated (or updated to `block.timestamp` instead of left fixed), so elapsed is recomputed from each call and never decays. | Requires two calls at *different* timestamps; single-warp tests never exercise it. |

Both are cumulative-accounting bugs. This is why the highest-value assertion in the suite is `test_withdraw_cumulativeCannotExceedElapsedBound`, not the formula check.

**3.3 What I am *not* asserting (low confidence / unverified).** I have not read `perenna-contracts`. I do not know whether the elapsed-time bound is linear, cliffed, or piecewise; whether the anchor is per-user or global; or whether the repo is Solidity at all (see §7.1). Root cause above is a **hypothesis class**, not a finding. It is labeled as such deliberately.

---

## 4. Implementation

**Framework assumption:** Foundry. If the repo is Hardhat or non-EVM, §8 gives the mapping — the test *matrix* is unchanged, only the time
\n