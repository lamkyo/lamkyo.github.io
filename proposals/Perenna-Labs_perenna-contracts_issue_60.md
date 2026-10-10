# Bounty Proposal: Perenna-Labs/perenna-contracts#60 - [Bounty: $90] Persist the stream before transferring the deposit in `create_stream`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $90] Persist the stream before transferring the deposit in `create_stream`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is a clear, actionable issue with a well-defined fix: reorder `create_stream` to persist the `Stream` record before calling `token_client.transfer`, ensuring checks-effects-interactions compliance. The acceptance criteria are specific and testable, making it directly codeable.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Persist Stream State Before Deposit Transfer in `create_stream`

**Delivery & Quality Verification Lead sign-off: ⛔ NOT_READY_FOR_EGRESS**

This document is formatted as a complete PR proposal, but two of its three required sections are **blocked on missing inputs**. It is published with honest gate statuses rather than as a "production-ready" artifact. Details in §0.

---

## 0. Gate Status (read first)

| Gate | Status | Basis |
|---|---|---|
| Radar classification | `RAW_RADAR_CANDIDATE` | No public repo + reproducible test suite confirmed by me |
| Root cause | `PLAUSIBLE_PATTERN` (unconfirmed against source) | Derived from the issue title + standard CEI failure mode |
| Code patch (SWE-2) | `NOT_SUPPLIED` | Input states "Code Patch (SWE-2): None" |
| Deterministic compile/lint check | `NOT_RUN` | No patch to compile; no toolchain access |
| Test verification | `NOT_RUN` / `BLOCKED` | Depends on patch + repo checkout |
| Egress authorization | `DENIED` | Blocked on the above |

**Per [RULE-002]**, no patch may be marked `PASS` or `READY_FOR_EGRESS` without passing a deterministic compiler/linter check in a sandbox. No patch exists, therefore no such check has run, therefore egress is denied. **Per [RULE-003]**, this item stays `RAW_RADAR_CANDIDATE` until a public Git repository with a reproducible test suite is confirmed.

The architecture decision to proceed with a surgical fix is accepted as *scope guidance*. It does not substitute for the missing artifacts.

---

## 1. PR Metadata

| Field | Value |
|---|---|
| Target repository | `Perenna-Labs/perenna-contracts` *(unverified — not cloned)* |
| Base branch | `main` *(assumed)* |
| Head branch | `fix/create-stream-cei-ordering` *(proposed)* |
| Title | `fix: persist stream state before deposit transfer in create_stream` |
| Bounty | $90 |
| Linked issue | `[Bounty: $90] Persist the stream before transferring the deposit in create_stream` |
| Egress identity | **PAT-authenticated user account required** — see §6 |

---

## 2. Radar Classification

```
item_id:      perenna-create-stream-cei
class:        RAW_RADAR_CANDIDATE
confidence:   low-medium (pattern-level only)
promotion_blocker: no confirmed public repo URL, no confirmed test harness,
                   no confirmed source file/function signature
promotion_rule: elevate to VERIFIABLE_CODE_ISSUE only after cloning
\n