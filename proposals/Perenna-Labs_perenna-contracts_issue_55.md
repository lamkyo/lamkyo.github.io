# Bounty Proposal: Perenna-Labs/perenna-contracts#55 - [Bounty: $100] Prevent `i128` overflow in `compute_earned`'s multiply-before-divide\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $100] Prevent `i128` overflow in `compute_earned`'s multiply-before-divide

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable: Yes - location `contracts/stream/src/lib.rs::compute_earned`, overflow reproduction (`deposit near i128::MAX` * `elapsed>1` before `/ duration` -> `MathOverflow`), and acceptance criteria (exact `deposit*elapsed/duration` without overflow + boundary test + `make test` pass) are clearly specified. Codeable: Yes - via remainder-split `q=elapsed/duration, r=elapsed%duration` as `deposit*q + deposit*r/duration` or `i256/U256` widening to avoid intermediate `i128` overflow; pending verification of public repo/tests this remains **RAW_RADAR_CANDIDATE** per triage policy.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — BLOCKED / NOT READY_FOR_EGRESS

**Repo:** Perenna-Labs/perenna-contracts
**Issue:** [Bounty: $100] Prevent `i128` overflow in `compute_earned`'s multiply-before-divide
**Author of record:** Claude, Delivery & Quality Verification Lead
**Status:** `NO_PATCH_SUPPLIED` — proposal scaffold only

---

## 0. Delivery Gate — Read This First

I cannot package this as a production-ready PR proposal, because the input I was given contains no patch:

```
Architecture Plan (Opus 5.5): Proceed with surgical fix.
Code Patch (SWE-2): None
```

Per **[RULE-002-SYNTAX-GROUNDING]**, no patch may be marked `PASS` or `READY_FOR_EGRESS` until it has cleared a deterministic compiler/linter check (`cargo check` / `cargo clippy` / `go vet` / `ast.parse` / `tsc`, as applicable) in a sandbox. There is nothing to compile. Writing an "Implementation" section here would mean inventing code and asserting a verification result I have not observed — exactly the failure mode this gate exists to prevent.

**What this document therefore is:** a complete, review-ready PR *skeleton* with the Root Cause and Test Verification sections filled in as far as evidence permits, and the Implementation section explicitly marked empty. Section 5 lists the single blocking input needed to convert this into a submittable PR.

---

## 1. Radar Classification — **[RULE-003-RADAR-UNCERTAINTY]**

| Field | Value |
|---|---|
| Classification | `RAW_RADAR_CANDIDATE` |
| Public Git repo confirmed | **No** — not verified from here; no clone, no commit SHA pinned |
| Reproducible test suite confirmed | **No** |
| Elevation to `VERIFIABLE_CODE_ISSUE` | **Blocked** |

Elevation requires a confirmed public repository with a reproducible test suite. Until `compute_earned` is read at a pinned commit and a failing/overflowing test is executed locally, this remains a candidate — the bounty text alone is not sufficient evidence. I have no network or repo access in this session, and I am not going to assert file paths, line numbers, or signatures I have not read.

---

## 2. Root Cause (class-level, evidence-bounded)

**Stated defect:** `compute_earned` performs multiplication before division, so the intermediate product can exceed the `i128` range before the division brings the result back down to a representable value.

`i128` spans roughly `±1.70 × 10³⁸`. A ratio-shaped computation of the form

```
earned = (principal * rate_numerator) / rate_denominator
```

overflows whenever `|principal * rate_numerator| > i128::MAX`, **even if the final quotient is small and perfectly representable.** This is the characteristic failure: the function is mathematically correct and still reverts/panics. In a release build without overflow checks the same expression can instead wrap silently, producing a wrong-but-accepted value — strictly worse than a revert, and the reason this is worth a bounty rather than a code-style note.

Two secondary hazards belong in the same root-cause writeup, and should be confirmed against the actual source before submission:

1. **Sign handling.** With signed `i128`, a negative intermediate can overflow on the negative end (`i128::MIN` has one more magnitude than `i128::MAX`). Any `checked_*` migration must cover the negative branch, not just the positive one.
2. **Rounding direction.** If the current expression truncates toward zero, any reordering to "divide first" changes the result by up to one unit of the smallest denomination. For an accrual function this is a value-transfer direction question, not a cosmetic one.

**Unverified — must be confirmed against source at a pinned SHA before this section is final:**
- exact expression and operand provenance (storage reads? oracle-scaled inputs?)
- whether the build has `overflow-checks = true` (panic) or not (wrap)
- whether callers already pre-clamp inputs, which would change severity

---

## 3. Implementation — **EMPTY**

```
Code Patch (SWE-2): None
```

**No diff is proposed here.** Nothing in this section is a recommendation to merge; the three approaches below are candidate *directions* for the patch author, listed so the fix can be scoped, not applied by me.

| # | Direction | Tradeoff to weigh |
|---|---|---|
| A | `checked_mul` / `checked_div` with a typed error | Smallest diff; converts silent wrap into an explicit revert. Does **not** make previously-failing large inputs succeed. |
| B | Widen the intermediate (256-bit multiply-then-divide, e.g. an SDK `U256`/`I256` or `mul_div` helper) | Actually fixes the class of bug for in-range inputs; requires the wider type to be available in this toolchain and audited for the sign branch. |
| C | Reorder to divide-first | Introduces precision loss; only acceptable if the spec permits it. **Requires an explicit rounding-policy decision** before it can be reviewed. |

**Acceptance criteria for whichever is chosen:**
- no unchecked `*` or `/` on the value path in `compute_earned`
- defined behavior (revert or saturate, per protocol policy) when the *true* quotient is out of `i128` range
- documented rounding direction, unchanged from current behavior unless the issue explicitly authorizes a change
- negative-input path covered

---

## 4. Test Verification — **PLAN ONLY, NOT EXECUTED**

I have executed nothing. The following is the verification plan that must be satisfied before any `PASS` marking.

**Boundary vectors (each must have an expected value computed independently of the implementation under test):**

| Case | Intent |
|---|---|
| `principal = i128::MAX`, small numerator | overflow at the multiply, small true quotient |
| `principal = i128::MAX`, numerator > denominator | true quotient genuinely out of range → must take the defined failure path |
| `principal = i128::MIN` (and near-min negatives) | negative-branch overflow |
| `numerator = 0` / `principal = 0` | no division-by-zero, no spurious error |
| result = 0 with non-zero operands | truncation boundary |
| result exactly at `i128::MAX` / `MAX - 1` | off-by-one at the representable edge |
| rounding remainder = 0 and remainder = denominator - 1 | both sides of the truncation boundary |

**Required evidence to attach to the PR:**
1. `cargo check` + `cargo clippy` (or repo-equivalent) output, clean.
2. Full existing test suite, green — overflow fixes routinely break callers that relied on the old truncation.
3. New regression test that **fails on the pre-patch commit** and passes on the post-patch commit. Without the failing-before step, the test does not demonstrate the
\n