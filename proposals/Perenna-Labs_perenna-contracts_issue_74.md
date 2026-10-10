# Bounty Proposal: Perenna-Labs/perenna-contracts#74 - [Bounty: $45] Fix the "every state change emits an event" claim in `CONTRIBUTING.md`\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $45] Fix the "every state change emits an event" claim in `CONTRIBUTING.md`

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Actionable: YES** — this is a well-scoped documentation fix with explicit acceptance criteria, a named contradictory location (`contracts/stream/src/lib.rs` `init`), a cross-reference to reconcile (`docs/CONTRACT_SPEC.md` §3/§4), and a verifiable gate (`make check` plus the CI `check` job), so a contributor can complete it without ambiguity.

**Codeable: YES** — the change is confined to prose in `CONTRIBUTING.md` (amending the "Every state change emits an event" bullet to except one-time initialisation or scope it to stream lifecycle calls), plus

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
# Architecture Analysis: `CONTRIBUTING.md` Event-Claim Reconciliation

## 1. Root Cause Analysis

The contradiction is not a typo — it's a **documentation drift** between two artifacts that were authored at different times with different scopes:

| Artifact | Scope it was written for | What it actually says |
|---|---|---|
| `CONTRIBUTING.md` | Contributor *style guide* — a heuristic to keep reviewers honest | "Every state change emits an event" (absolute) |
| `docs/CONTRACT_SPEC.md` §3/§4 | *Normative* contract behaviour, per-function | `init` mutates `DataKey::Admin` + `NextStreamId`, emits **no** events |

**Why the drift happened:** the contributor rule was written as a *review heuristic* ("if you mutate state, you probably owe an event"), then hardened into an *absolute invariant* in prose. The spec, being per-function and normative, correctly carves out one-time initialisation. The two never got reconciled because the rule lives in a file nobody re-reads when adding a function to the spec.

**The real failure mode to prevent:** a contributor reads the absolute rule, sees `init` violates it, and "fixes" `init` by adding an event — which would be a **behavioural regression** (changes the contract's event surface, breaks indexers, and contradicts the spec). So the fix must not just soften the prose; it must **actively steer contributors away from the wrong fix**.

## 2. Files to Touch

| File | Change | Risk |
|---|---|---|
| `CONTRIBUTING.md` | Amend the standards bullet: scope the rule to stream lifecycle calls, except one-time initialisation, and **link to the spec's event table** | Low — prose only |
| `docs/CONTRACT_SPEC.md` | **Verify only** §3/§4 already list `init` as event-less. If wording is ambiguous, tighten it. Do not restructure. | Low |
| *(audit)* all `*.md` | Grep for the absolute claim to satisfy AC #3 | None |

**Do not touch** `contracts/stream/src/lib.rs`. The issue is a doc bug, not a code bug. Adding an event to `init` is the trap.

## 3. Invariant-Safe Strategy

### 3.1 The core invariant to preserve
> **The spec is normative; `CONTRIBUTING.md` is advisory.** Where they conflict, the spec wins, and the contributor doc must *point at* the spec rather than restate it.

This is the architectural fix: **stop duplicating the event table in prose.** A restated rule will drift again. A pointer cannot.

### 3.2 Proposed `CONTRIBUTING.md` wording

Replace the absolute bullet with something like:

```markdown
- **Events.** Stream lifecycle calls that change state MUST emit the events
  listed in `docs/CONTRACT_SPEC.md` §4. One-time initialisation (`init`) is
  exempt: it writes `DataKey::Admin` and `NextStreamId` but emits nothing, by
  design. When in doubt, the spec's event table is normative — do not add an
  event to a function the spec lists as event-less.
```

Three properties this buys us:
1. **Scoped** — "stream lifecycle calls", not "every state change".
2. **Excepted** — `init` named explicitly, matching the spec.
3. **Anti-regression** — the last sentence tells a contributor *not* to "fix" `init`, which is the actual hazard.

### 3.3 AC #3 — no other doc repeats the absolute claim

Run a repo-wide grep before declaring done:

```bash
grep -rniE "every state change|all state changes|any state change" --include="*.md" .
```

Any hit outside the amended bullet must be reconciled in the same PR. This is the step most likely to be skipped and most likely to fail review.

## 4. Verification Gate (RULE-002-SYNTAX-GROUNDING)

Per the mandatory invariants, nothing is marked `PASS`/`READY_FOR_EGRESS` until a deterministic check runs in a sandbox. For a docs-only change the "compiler" is the repo's own gate plus a markdown lint:

```bash
# 1. Repo gate (AC #4)
make check

# 2. Markdown structural sanity (if the repo lints docs)
#    — confirm the amended bullet still parses as a list item and the
#      spec cross-reference resolves to a real anchor.

# 3. AC #3 sweep
grep -rniE "every state change|all state changes" --include="*.md" .
#    Expect: zero hits, or only the amended, scoped bullet.
```

Then confirm the CI `check` job in `.github/workflows/ci.yml` is green on the PR — that is the authoritative gate, not the local run.

## 5. Regression Avoidance Summary

| Hazard | Mitigation |
|---|---|
| Contributor "fixes" `init` by adding an event | Wording explicitly forbids it and defers to the spec |
| Rule drifts again later | Rule now *points at* the spec instead of restating it |
| Another doc still carries the absolute claim | Repo-wide grep as an explicit AC step |
| Spec and contributor doc re-diverge | Spec declared normative in the amended bullet |
| Silent CI breakage | `make check` + CI `check` job as the gate |

## 6. Egress Boundary (RULE-001-GH-APP-BOUNDARY)

The write to `Perenna-Labs/perenna-contracts` is a **public repository write action** and must route through an **authenticated User Account (PAT)** — not a GitHub App. The App is used only for quota shielding, scouting, cloning, and internal repo actions. The PR that carries this doc fix is a public write; treat it accordingly.

---

**Bottom line:** this is a one-file prose fix whose real value is the *anti-regression clause* — telling contributors that `init` is event-less **by design** and that the spec is normative. Softening the claim without that clause invites someone to "correct" `init` and break the contract's event surface.

---

## 3. Production Code Patch (`swe-2`)
I can't produce that patch, and I want to be straight with you about why — because most of your plan is sound and I don't want to throw it out.

**What's wrong with the request as framed**

You've asked for "surgical production code changes and git diff patch with exact lines, imports, and unit test assertions." But your own architecture analysis says, correctly and repeatedly:

- "Do not touch `contracts/stream/src/lib.rs`. The issue is a doc bug, not a code bug."
- "Adding an event to `init` is the trap."
- The change is "prose only."

A diff with imports and unit test assertions is a *code* artifact. If I generate one, I'm manufacturing exactly the thing your §1 identifies as the failure mode: someone reads the absolute rule, sees `init` violates it, and "fixes" `init`. I'd be handing you the regression your anti-regression clause exists to prevent. The request contradicts the plan it's attached to.

**What I also can't do**

I can't emit a git diff patch with "exact lines" for `CONTRIBUTING.md` or `docs/CONTRACT_SPEC.md`, because I don't have the files. I don't know the current bullet's line number, its exact wording, the surrounding list structure, or whether §3/§4 already list `init` as event-less. A patch with fabricated line numbers and context lines won't apply, and a "verification" that claims `make check` passed would be a lie — I can't run it. Your RULE-002-SYNTAX-GROUNDING invariant says nothing is marked PASS until a deterministic check runs in a sandbox. I have no sandbox here. So I can't satisfy your own gate, and I won't pretend to.

**What I can actually give you**

The prose change is the whole deliverable, and your §3.2 draft is already close to final. Here it is tightened, with the cross-reference made explicit:

```markdown
- **Events.** Stream lifecycle calls that change state MUST emit the events
  listed in `docs/CONTRACT_SPEC.md` §4. One-time initialisation (`init`) is
  exempt: it writes `DataKey::Admin` and `NextStreamId` but emits nothing, by
  design. The spec's event table is normative — do not add an event to a
  function the spec lists as event-less.
```

Two notes on it:

1. **Verify the anchor before you commit.** `§4` is a section reference, not a link. If `docs/CONTRACT_SPEC.md` uses heading anchors, replace `§4` with a real relative link (`[§4](docs/CONTRACT_SPEC.md#4-events)`) so the pointer can't rot. If it doesn't, leave the section number — a broken link is worse than a section number.
2. **Confirm the spec actually says this.** Your plan says "verify only." Do that verification first. If §3/§4 *don't* currently carve out `init`, the fix is to tighten the spec in the same PR — otherwise the amended bullet points at a table that contradicts it, and you've moved the drift rather than resolved it.

**The steps I'd run, in order, that I can't run for you**

```bash
# 1. Confirm the spec's current wording on init
grep -n -A5 -B2 "init" docs/CONTRACT_SPEC.md

# 2. AC #3 sweep — find every absolute claim
grep -rniE "every state change|all state changes|any state change" --include="*.md" .

# 3. After editing, re-run the sweep; expect only the scoped bullet
grep -rniE "every state change|all state changes|any state change" --include="*.md" .

# 4. Repo gate
make check
```

Step 2 is the one your plan flags as "most likely to be skipped and most likely to fail review." Run it before you write anything, not after — the hits determine whether this is a one-file change or a multi-file one.

**On the egress boundary**

Your §6 is right: the PR to a public repo routes through a PAT, not the App. I have no ability to open that PR or authenticate as anything, so that's yours to execute.

**Bottom line:** the deliverable is a prose edit plus a grep sweep, and your plan already contains both. What it doesn't contain — and what I won't invent — is a code diff. If you paste the current contents of the relevant `CONTRIBUTING.md` section and the spec's §3/§4, I'll write you the exact replacement text and the exact grep output to expect. That I can do precisely.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repository:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $45] Fix the "every state change emits an event" claim in `CONTRIBUTING.md`
**Type:** Documentation-only (prose reconciliation)
**Egress:** Public repository write → authenticated **User Account (PAT)** per RULE-001-GH-APP-BOUNDARY

---

## 0. Status Declaration

| Field | Value |
|---|---|
| Change class | Docs-only (no code, no contract behaviour change) |
| Patch status | **DRAFT — NOT READY_FOR_EGRESS** |
| Reason | RULE-002-SYNTAX-GROUNDING cannot be satisfied in this environment: no sandbox, no repo checkout, no `make check` execution. Nothing is marked `PASS`. |
| Blocking inputs | Current text of the `CONTRIBUTING.md` bullet; current text of `docs/CONTRACT_SPEC.md` §3/§4; output of the AC #3 grep sweep. |

This proposal is **complete as a plan and as replacement prose**. It deliberately does **not** contain a fabricated git diff with invented line numbers, imports, or unit-test assertions. See §5 for why that omission is the correct engineering decision, not a gap.

---

## 1. Root Cause Analysis

The contradiction is **documentation drift**, not a typo. Two artifacts were authored at different times for different scopes:

| Artifact | Scope it was written for | What it actually says |
|---|---|---|
| `CONTRIBUTING.md` | Contributor *style guide* — a review heuristic | "Every state change emits an event" (absolute) |
| `docs/CONTRACT_SPEC.md` §3/§4 | *Normative* per-function contract behaviour | `init` mutates `DataKey::Admin` + `NextStreamId`, emits **no** events |

**Mechanism of drift:** the contributor rule began as a heuristic ("if you mutate state, you probably owe an event") and was hardened into an absolute invariant in prose. The spec, being per-function and normative, correctly carves out one-time initialisation. The two were never reconciled because the rule lives in a file nobody re-reads when adding a function to the spec.

**The real failure mode to prevent:** a contributor reads the absolute rule, observes that `init` violates it, and "fixes" `init` by adding an event. That is a **behavioural regression** — it changes the contract's event surface, breaks indexers, and contradicts the spec. The fix must therefore not merely soften the prose; it must **actively steer contributors away from the wrong fix**.

---

## 2. Files to Touch

| File | Change | Risk |
|---|---|---|
| `CONTRIBUTING.md` | Amend the standards bullet: scope the rule to stream lifecycle calls, except one-time initialisation, and **point at the spec's event table** | Low — prose only |
| `docs/CONTRACT_SPEC.md` | **Verify only** that §3/§4 already list `init` as event-less. Tighten wording only if ambiguous. Do not restructure. | Low |
| *(audit)* all `*.md` | Grep for the absolute claim to satisfy AC #3 | None |

**Do not touch** `contracts/stream/src/lib.rs`. The issue is a doc bug, not a code bug. Adding an event to `init` is the trap.

---

## 3. Implementation

### 3.1 Core invariant to preserve

> **The spec is normative; `CONTRIBUTING.md` is advisory.** Where they conflict, the spec wins, and the contributor doc must *point at* the spec rather than restate it.

This is the architectural fix: **stop duplicating the event table in prose.** A restated rule will drift again. A pointer cannot.

### 3.2 Replacement text for the `CONTRIBUTING.md` bullet

Replace the absolute bullet with:

```markdown
- **Events.** Stream lifecycle calls that change state MUST emit the events
  listed in `docs/CONTRACT_SPEC.md` §4. One-time initialisation (`init`) is
  exempt: it writes `DataKey::Admin` and `NextStreamId` but emits nothing, by
  design. The spec's event table is normative — do not add an event to a
  function the spec lists as event-less.
```

Three properties this buys:

1. **Scoped** — "stream lifecycle calls", not "every state change".
2. **Excepted** — `init` named explicitly, matching the spec.
3. **Anti-regression** — the final sentence tells a contributor *not* to "fix" `init`, which is the actual hazard.

### 3.3 Two pre-commit checks on the wording

1. **Verify the anchor before committing.** `§4` is a section reference, not a link. If `docs/CONTRACT_SPEC.md` uses heading anchors, replace `§4` with a real relative link (e.g. `[§4](docs/CONTRACT_SPEC.md#4-events)`) so the pointer cannot rot. If it does not, leave the section number — a broken link is worse than a section number.
2. **Confirm the spec actually says this.** Run the verification in §4 step 1 *first*. If §3/§4 do **not** currently carve out `init`, tighten the spec in the same PR. Otherwise the amended bullet points at a table that contradicts it, and the drift has been moved rather than resolved.

### 3.4 AC #3 — no other doc repeats the absolute claim

Run a repo-wide sweep before declaring done:

```bash
grep -rniE "every state change|all state changes|any state change" --include="*.md" .
```

Any hit outside the amended bullet must be reconciled in the same PR. This is the step most likely to be skipped and most likely to fail review. **Run it before writing anything** — the hits determine whether this is a one-file change or a multi-file one.

---

## 4. Test Verification

### 4.1 Verification gate (RULE-002-SYNTAX-GROUNDING)

Per the mandatory invariants, nothing is marked `PASS`/`READY_FOR_EGRESS` until a deterministic check runs in a sandbox. For a docs-only change the "compiler" is the repo's own gate plus a markdown lint:

```bash
# 1. Confirm the spec's current wording on init
grep -n -A5 -B2 "init" docs/CONTRACT_SPEC.md

# 2. AC #3 sweep — find every absolute claim (run BEFORE editing)
grep -rniE "every state change|all state changes|any state change" --include="*.md" .

# 3. After editing, re-run the sweep; expect only the scoped bullet
grep -rniE "every state change|all state changes|any state change" --include="*.md" .

# 4. Repo gate (AC #4)
make check
```

Then confirm the CI `check` job in `.github/workflows/ci.yml` is green on the PR — that is the authoritative gate, not the local run.

### 4.2 Expected results

| Step | Expected outcome |
|---|---|
| 1 | `init` documented as mutating `DataKey::Admin` + `NextStreamId` with no event emission |
| 2 | One or more hits; each catalogued and reconciled in this PR |
| 3 | Zero hits, or only the amended, scoped bullet |
| 4 | `make check` exits 0 |
| CI | `check` job green on the PR head |

### 4.3 Verification status in this environment

**Not executed.** No sandbox, no checkout, no `make check` available here. Per RULE-002-SYNTAX-GROUNDING, this proposal is therefore **DRAFT**, not `PASS` and not `READY_FOR_EGRESS`. The commands above are the exact gate the executing agent must run and paste back.

---

## 5. Why There Is No Code Diff

The request asked for "surgical production code changes and git diff patch with exact lines, imports, and unit test assertions." That artifact is **not produced here**, for three reasons:

1. **It contradicts the plan it is attached to.** The architecture analysis states, correctly: "Do not touch `contracts/stream/src/lib.rs`… Adding an event to `init` is the trap… prose only." A diff with imports and unit-test assertions is a *code* artifact. Generating one would manufacture exactly the regression the anti-regression clause exists to prevent.
2. **The files are not available.** Without the current bullet's line number, exact wording, surrounding list structure, and the spec's §3/§4 text, any diff would carry fabricated line numbers and context lines and would not apply.
3. **A claimed `make check` pass would be false.** RULE-002-SYNTAX-GROUNDING forbids marking anything `PASS` without a deterministic sandbox check. No sandbox exists here, so no pass is claimed.

The deliverable is a prose edit plus a grep sweep. Both are specified above. To convert this proposal into an applicable patch, paste the current contents of the relevant `CONTRIBUTING.md` section and the spec's §3/§4; the exact replacement text and the exact expected grep output can then be produced precisely.

---

## 6. Regression Avoidance Summary

| Hazard | Mitigation |
|---|---|
| Contributor "fixes" `init` by adding an event | Wording explicitly forbids it and defers to the spec |
| Rule drifts again later | Rule now *points at* the spec instead of restating it |
| Another doc still carries the absolute claim | Repo-wide grep as an explicit AC step, run before editing |
| Spec and contributor doc re-diverge | Spec declared normative in the amended bullet |
| Silent CI breakage | `make check` + CI `check` job as the gate |
| Fabricated patch / false PASS | No diff emitted; status held at DRAFT pending sandbox verification |

---

## 7. Egress Boundary (RULE-001-GH-APP-BOUNDARY)

The write to `Perenna-Labs/perenna-contracts` is a **public repository write action** and must route through an **authenticated User Account (PAT)** — not a GitHub App. The App is used only for quota shielding, scouting, cloning, and internal repo actions. The PR carrying this doc fix is a public write; treat it accordingly.

---

## 8. Radar Classification (RULE-003-RADAR-UNCERTAINTY)

This item is classified **RAW_RADAR_CANDIDATE**. It is a documentation reconciliation against a named public repository; it is **not** elevated to `VERIFIABLE_CODE_ISSUE`, because no reproducible test suite exercises the claim — the "test" is a grep sweep and a prose review, not an executable assertion over contract behaviour.

---

## 9. Bottom Line

This is a one-file prose fix whose real value is the **anti-regression clause** — telling contributors that `init` is event-less **by design** and that the spec is normative. Softening the claim without that clause invites someone to "correct" `init` and break the contract's event surface.

**Status: DRAFT.** Ready to execute once the current file contents and the AC #3 sweep output are supplied and the §4 gate is run in a sandbox.
\n