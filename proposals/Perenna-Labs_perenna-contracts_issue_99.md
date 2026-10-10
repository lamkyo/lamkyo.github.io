# Bounty Proposal: Perenna-Labs/perenna-contracts#99 - [Bounty: $95] Guard against stream-id reuse if the instance TTL lapses\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $95] Guard against stream-id reuse if the instance TTL lapses

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable as **RAW_RADAR_CANDIDATE** (pending confirming `Perenna-Labs/perenna-contracts` is public with reproducible `make test`/`check`): well-defined TTL/counter-reset bug with exact files `contracts/stream/src/storage.rs::get_next_stream_id` and `contracts/stream/src/lib.rs::create_stream` and testable acceptance criteria. Codeable via isolated collision guard refusing to overwrite existing `DataKey::Stream(id)` with typed error + counter-integrity fix, verified by a forced counter-to-0 collision test.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm trying to fix a bug in the Perenna-Labs/perenna-contracts repository, but I can't access it. The prompt mentions rules about verifying public repositories, which seems relevant since I can't see the code. I shouldn't try to generate a patch if I can't confirm the repository exists and has tests.

I cannot provide a precise code change because I lack access to the repository. Rule-003 requires me to classify this as RAW_RADAR_CANDIDATE since I can't confirm a public, testable repository. I need to know the specific files, language, and framework to offer a concrete fix, but I can describe general strategies for preventing stream-id reuse after TTL expiration.

Given the "contracts" in the repo name, I suspect Solidity. A common pattern for stream IDs is `hash(instanceAddress, nonce)`. If a TTL expires and the instance is recreated, the nonce might reset, leading to ID reuse. A fix could involve persisting a global nonce or a mapping of used IDs, or incorporating an expiry epoch into the ID derivation. I'll draft a response outlining these possibilities and requesting more context.

I'm considering how to handle the user's request for an exact-line diff. Fabricating one would violate the rules, but simply declining might not be helpful. I'll offer an illustrative, clearly marked sketch instead, and request the necessary context like file paths, language, and existing tests to generate a grounded patch.

The bug stems from stream IDs being deterministically generated from instance and counter, with the counter resetting after TTL expiration, causing ID reuse. I'm considering three fixes: tombstoning used IDs, using a persistent monotonic epoch per instance namespace, or incorporating expiry into the ID derivation. I'll also add a test case to verify that a re-minted ID differs from a previously used one after TTL expiry. I plan to include a short, illustrative Solidity snippet to clarify the concept.**Status: `RAW_RADAR_CANDIDATE` (per RULE-003).** I cannot confirm access to `Perenna-Labs/perenna-contracts`' source or a reproducible test suite in this context, so I won't fabricate an exact-line diff — that would violate RULE-002 (ungrounded patch, no compiler check possible).

To produce the surgical patch I need the repo contents. Specifically:

- **File + function where stream-ids are minted** (e.g., `createStream`, `issueStreamId`)
- **The instance TTL lifecycle code** — where instances expire/get reaped
- **Toolchain**: Solidity+Foundry? Soroban/Rust? CosmWasm? ("contracts" is ambiguous)
- **Existing tests** covering issuance and expiry

## Likely bug shape (pending confirmation)

Stream-id derivation is deterministic on `(instance, counter/salt)`, and the counter or instance state is reclaimed when TTL lapses → a re-created instance re-derives an already-used id.

## Candidate fix patterns (choose once I see the storage model)

1. **Tombstone used ids** — strongest guard:
```solidity
mapping(bytes32 => uint64) public usedStreamIds; // id => expiry (0 = never used)

// in mint path:
bytes32 id = keccak256(abi.encode(instance, salt));
require(usedStreamIds[id] == 0, "StreamIdReused");
usedStreamIds[id] = uint64(block.timestamp + TTL);
```

2. **Monotonic epoch** — keep a per-namespace generation counter that survives instance re-creation; fold `epoch` into id derivation.

3. **Expiry-bound derivation** — derive `id = H(instance, salt, expiryBucket)` so post-lapse re-issuance yields a distinct id. Weaker: doesn't stop replay within the valid window.

## Test assertions the patch should carry

```text
test_reissue_after_ttl_lapse_gets_distinct_id:
  id1 = mint(); advance_time(TTL + 1); reap(); id2 = mint();
  assert id2 != id1

test_same_id_replay_reverts:
  mint(); expect revert StreamIdReused on duplicate
```

Point me at the repo (path or paste the mint/TTL source and tests) and I'll return the exact diff, imports, and assertions.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
**Deliverable: PR Proposal — `[PROPOSAL][BLOCKED_ON_GROUNDING]`**

Up front, so the artifact isn't misread downstream: this is a **PR proposal shell**, not a mergeable PR. I can't produce Root Cause, Implementation, and Test Verification as *verified* content for a repository I have no access to, and I won't present hypothesis as finding. Here is the proposal, with the grounding gates marked honestly.

---

# PR Proposal

**Title:** `fix(streams): prevent stream-id reuse after instance TTL lapse`
**Repo:** `Perenna-Labs/perenna-contracts`
**Bounty:** $95
**Author:** Claude (Delivery & Quality Verification Lead)
**Upstream inputs:** Architecture Plan (Opus 5.5) → "proceed with surgical fix"; Code Patch (SWE-2) → returned no patch, blocked on repo access.

## Gate Status

| Invariant | Status | Note |
|---|---|---|
| RULE-001 (GH App / User Account boundary) | N/A | No egress attempted; nothing written to any remote. |
| RULE-002 (syntax grounding) | **BLOCKED** | No artifact exists to compile. Cannot be marked PASS or READY_FOR_EGRESS. |
| RULE-003 (radar uncertainty) | **RAW_RADAR_CANDIDATE** | Public repo, reproducible test suite, and issue reproduction all unconfirmed in this context. |

**Mergeability: NO.** Do not label this `ready-for-review`. The Implementation section below is explicitly non-final.

---

## 1. Problem Statement

**As filed:** a stream-id, once issued, may be re-issued to a different consumer if the owning instance's TTL lapses and the instance is subsequently re-created.

**As verified:** nothing. The issue text is the only source. No reproduction, no test fixture, no source read.

## 2. Root Cause

**Status: HYPOTHESIS — UNCONFIRMED.**

Candidate causal chain, to be confirmed or falsified against source:

1. Stream-ids are derived deterministically from `(instance, salt/counter)` rather than drawn from a global uniqueness domain.
2. Instance state — including the salt/counter — is scoped to the instance's lifetime and is reclaimed on TTL expiry.
3. Post-lapse re-creation restarts the salt/counter at its initial value.
4. Step 1 + Step 3 ⇒ collision with a previously issued, still-referenced id.

**This chain is unverified at every link.** In particular, link 2 is the load-bearing claim and is exactly the part that requires reading the storage model. Two plausible alternative causes that would change the fix entirely:

- **Id derivation is sound, but expiry never tombstones** — the bug is in the reaper, not the mint.
- **Ids are globally unique already**, and the real defect is a consumer-side mapping that keys on `(instance, id)` and collides on instance re-creation.

Until one of these is distinguished, the root cause is not established.

## 3. Implementation

**Status: NOT FINAL — illustrative only, not compiler-checked.**

Candidate patterns, to be selected only after the storage model is read:

**Pattern A — tombstone used ids (strongest guard)**
```solidity
// ILLUSTRATIVE — not compiled, not reviewed, not a diff
mapping(bytes32 => uint64) public usedStreamIds; // id => expiry, 0 = never used

bytes32 id = keccak256(abi.encode(instance, salt));
require(usedStreamIds[id] == 0, "StreamIdReused");
usedStreamIds[id] = uint64(block.timestamp + TTL);
```
Cost: unbounded storage growth; needs a reclamation story for the tombstones themselves.

**Pattern B — monotonic epoch surviving instance re-creation**
Per-namespace generation counter, folded into id derivation. Requires a storage location that outlives the instance — which may not exist in the current layout.

**Pattern C — expiry-bound derivation**
`id = H(instance, salt, expiryBucket)`. Weakest: distinct ids after lapse, but no protection against replay *within* the valid window.

**None of these is a patch.** Each is a design fork that the source will collapse to one answer.

## 4. Test Verification

**Status: ASSERTIONS ONLY — no suite exists to run them.**

```text
test_reissue_after_ttl_lapse_gets_distinct_id:
  id1 = mint(); advance_time(TTL + 1); reap(); id2 = mint();
  assert id2 != id1

test_same_id_replay_reverts:
  mint(); expect revert StreamIdReused on duplicate
```

Also required, and currently absent:

- **Negative control** — confirm the bug *reproduces* on unpatched source. Without this, a passing test proves nothing about the fix.
- **Toolchain confirmation** — "contracts" is ambiguous. Solidity/Foundry, Rust/Soroban, and CosmWasm each imply a different assertion harness and a different `advance_time` primitive.

## 5. Blocking Questions

1. File and function where stream-ids are minted.
2. The instance TTL lifecycle: where instances expire, and what is reclaimed.
3. Language and toolchain, plus the command that runs the suite.
4. Existing tests covering issuance and expiry.
5. Does the issue carry a reproduction, or is the failure mode inferred?

Items 1–3 are hard blockers. I cannot produce a diff, an import list, or a runnable assertion set without them.

## 6. Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Patch written against an assumed storage model | High — silently wrong fix | Read mint + reaper source before drafting |
| Pattern A ships without tombstone reclamation | Medium — unbounded growth | Require a reclamation path in review |
| "Verified" label applied to uncompiled code | High — violates RULE-002 | Gates above stay BLOCKED until a compiler run exists |

---

## Recommended Next Action

Supply the repository (path, or paste the mint function, the TTL/reaper logic, and existing tests). I will then return the exact diff, imports, and assertions, run the toolchain check, and re-issue this proposal with Root Cause and Implementation moved from HYPOTHESIS to CONFIRMED and RULE-002 moved to PASS.

Until then the correct state of this artifact is **RAW_RADAR_CANDIDATE, blocked, not mergeable.**
\n