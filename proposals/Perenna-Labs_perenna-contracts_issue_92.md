# Bounty Proposal: Perenna-Labs/perenna-contracts#92 - [Bounty: $65] Extract the repeated create-stream test boilerplate into a helper\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $65] Extract the repeated create-stream test boilerplate into a helper

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Yes — this is actionable and codeable: it is a self-contained refactor of `contracts/stream/src/test.rs` with a clearly specified helper signature, explicit acceptance criteria, and no behavior changes required, so a contributor can implement it directly once the repo is cloned and `make test` is runnable. However, per [RULE-003-RADAR-UNCERTAINTY] it should be classified as RAW_RADAR_CANDIDATE rather than VERIFIABLE_CODE_

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm tasked with refactoring boilerplate code for a "create-stream" function in the Perenna-Labs/perenna-contracts repository. However, I cannot access the repository's code, which prevents me from generating an accurate code patch. This situation requires me to classify the task as RAW_RADAR_CANDIDATE, as I cannot fulfill the requirement of providing verifiable code changes without access to the codebase.

I need the actual test files, likely Foundry's `*.t.sol` files with `createStream` calls, to provide a precise diff. Since I can't access the repo, I'll classify this as RAW_RADAR_CANDIDATE per RULE-003. I can offer a general pattern for extracting test boilerplate and list the specific files I need to generate a surgical diff. I can also provide an illustrative example of a refactored helper function, clearly marked as unverified.

I need to remember to mention the verification step using `forge test` or `forge build` in the sandbox once the code is available, as per RULE-002. I'll format this concisely in Markdown, potentially with a short, illustrative code block marked as such, keeping it brief and to the point.**Status: `RAW_RADAR_CANDIDATE` — blocked, cannot emit a verified patch.**

Per **[RULE-003-RADAR-UNCERTAINTY]**, I cannot elevate this to `VERIFIABLE_CODE_ISSUE`, and per **[RULE-002-SYNTAX-GROUNDING]**, I cannot mark any diff `READY_FOR_EGRESS` — I do not have the contents of `Perenna-Labs/perenna-contracts` in context. Fabricating "exact lines" for unseen test files would produce an ungrounded, unverifiable patch.

## What I need to proceed

Please provide (or point me to the files in the connected codebase):

1. The test files containing the repeated `createStream` boilerplate — likely `test/**/*.t.sol` or `test/integration/**`.
2. Any existing shared test base — e.g., `Base_Test.sol`, `Utils.sol`, `Helpers.sol`.
3. The signature of the stream-creation entry point being wrapped (e.g., `sablier.createLinear(...)`, `perenna.createStream(...)`, or a local `createDefaultStream`).

## Illustrative target shape (unverified draft — not a patch)

Assuming a Foundry layout, the refactor typically looks like this:

```solidity
// test/utils/Helpers.sol or in Base_Test.sol
function _createStream(
    address recipient,
    uint128 amount,
    uint40 duration
) internal returns (uint256 streamId) {
    vm.prank(sender);
    streamId = lockup.createWithDurations(params...); // actual signature TBD
}
```

```solidity
// in concrete tests — replaces the repeated setup block
uint256 streamId = _createStream(users.recipient, DEFAULT_AMOUNT, DEFAULT_DURATION);
assertEq(lockup.getRecipient(streamId), users.recipient);
```

Exact imports, storage writes (e.g., `deal()`, `vm.prank` ordering), and assertions depend entirely on the real files — send me the test sources and I'll return a surgical `git diff` plus the `forge build`/`forge test` verification results before marking it ready.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Bounty #[$65]

**Repo:** `Perenna-Labs/perenna-contracts`
**Issue:** Extract repeated `create-stream` test boilerplate into a shared helper
**Author of plan:** Architecture Plan (Opus 5.5) — *planning artifact only*
**Compiled by:** Claude, Delivery & Quality Verification Lead (drafting role)
**Status:** `RAW_RADAR_CANDIDATE` — **BLOCKED, NOT READY_FOR_EGRESS**

---

## 0. Status Declaration (read first)

This proposal is a **plan**, not a patch. Per **[RULE-003-RADAR-UNCERTAINTY]**, the item remains a `RAW_RADAR_CANDIDATE`: no public Git repository with a reproducible test suite has been confirmed **in context**, so it cannot be elevated to `VERIFIABLE_CODE_ISSUE`. Per **[RULE-002-SYNTAX-GROUNDING]**, no diff may be marked `PASS` or `READY_FOR_EGRESS` without a deterministic compiler/linter run (`forge build`, `forge test`) in a sandbox.

Fabricating "exact lines" for unseen `*.t.sol` files would produce an ungrounded patch — the exact failure mode these invariants exist to prevent. Everything below is either (a) plan, or (b) explicitly labelled **unverified illustration**.

---

## 1. Root Cause

**Symptom:** Identical `create-stream` setup blocks are copy-pasted across multiple test contracts, so any change to the stream-creation entry point, its parameter struct, or its `vm.prank`/`deal` preconditions requires a synchronized edit across N files.

**Mechanism (hypothesised, to be confirmed against real sources):**
1. No shared internal helper exists on the test base contract for the canonical "create a stream with default parameters" flow.
2. Each test re-derives the same state: fund the sender, `vm.prank` the correct caller, build the parameter struct, call the create entry point, capture the returned `streamId`.
3. Duplication is therefore *structural*, not incidental — it recurs per test case, so it drifts.

**Confirmation requires:** the actual test sources. Root cause is stated as a hypothesis until step 2 of §5 is satisfied.

---

## 2. Implementation (planned — no diff emitted)

### 2.1 Target files (to be confirmed)
- `test/**/*.t.sol` — call sites containing the repeated block
- `test/utils/Base_Test.sol` or `test/utils/Helpers.sol` — destination for the helper
- Entry point signature (e.g. a `lockup.create*`-style call) — must be read, not assumed

### 2.2 Refactor shape

Add one `internal` helper on the existing test base; replace each inline block with a single call. No production code changes — test-only surface.

**Unverified illustration — NOT a patch, NOT compiled:**

```solidity
// destination: test base / helpers (final location TBD)
function _createStream(
    address recipient,
    uint128 amount,
    uint40 duration
) internal returns (uint256 streamId) {
    vm.prank(sender);
    streamId = /* entry point + params: signature TBD */;
}
```

```solidity
// call site — replaces the repeated block
uint256 streamId = _createStream(users.recipient, DEFAULT_AMOUNT, DEFAULT_DURATION);
assertEq(/* getter: name TBD */(streamId), users.recipient);
```

### 2.3 Deliberate non-goals
- No assertion changes. Refactor must be **behaviour-preserving**; test outcomes before and after must be identical.
- No `vm.prank` reordering, no `deal()` consolidation, no visibility widening — unless a call site demonstrably requires it, in which case it is documented per-site.

---

## 3. Test Verification (required before egress)

| # | Gate | Command / Method | Pass criterion |
|---|------|------------------|----------------|
| V1 | Syntax grounding | `forge build` in sandbox | clean compile, zero new warnings |
| V2 | Behaviour preservation | `forge test -vvv` before vs. after | identical pass/fail set; **no test newly passing that failed before** |
| V3 | Helper actually exercised | grep call sites | zero remaining inline duplicates of the extracted block |
| V4 | Determinism | re-run V2 twice | identical output (no flake) |

**V1–V4 have not been run.** No result is claimed. This section is a plan until the sources arrive.

---

## 4. Egress Boundary ([RULE-001-GH-APP-BOUNDARY])

When V1–V4 pass, the branch push and PR creation against the **public** `Perenna-Labs/perenna-contracts` must be routed through an **authenticated user account (PAT)**. Any GitHub App credential is confined to quota shielding, scouting, cloning, and internal-repo actions — it must not perform the public write. The PR body should carry the raw `forge build` / `forge test` output for reviewer reproduction.

---

## 5. Blockers & Required Inputs

To convert this plan into a `VERIFIABLE_CODE_ISSUE` with a real diff, provide:

1. The test files containing the repeated `createStream` boilerplate (`test/**/*.t.sol`, `test/integration/**`).
2. Any existing shared test base (`Base_Test.sol`, `Utils.sol`, `Helpers.sol`).
3. The signature of the stream-creation entry point being wrapped, plus its getters.
4. Confirmation the suite runs locally (`forge test` green on the unmodified tree).

On receipt: emit a surgical `git diff`, run V1–V4, paste raw output, then — and only then — mark `READY_FOR_EGRESS`.

---

## 6. Invariant Ledger

| Rule | Application | Outcome |
|------|-------------|---------|
| RULE-002-SYNTAX-GROUNDING | No compiler run possible without sources | Not satisfied → not `PASS` |
| RULE-001-GH-APP-BOUNDARY | Public write path pinned to PAT | Documented (§4), not yet executed |
| RULE-003-RADAR-UNCERTAINTY | No confirmed public repo + reproducible suite in context | Classified `RAW_RADAR_CANDIDATE` |

**Net:** proposal complete as a plan; **no patch, no verification claim, no egress.**
\n