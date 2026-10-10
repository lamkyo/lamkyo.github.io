# Bounty Proposal: Perenna-Labs/perenna-contracts#76 - [Bounty: $65] Reconcile the Stellar CLI version across the docs and CI\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $65] Reconcile the Stellar CLI version across the docs and CI

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Verdict: ACTIONABLE**

This is a small, well-scoped consistency task: the three conflicting Stellar CLI version references (docs/DEPLOYMENT.md, Makefile comment, and the ci.yml `wasm` job pin at v28.1.0) can be reconciled to a single stated policy, with the version already present in CI serving as the natural source of truth — purely a documentation/config edit with no contract logic or security surface. Codeable in a single pass, though note the acceptance criteria's "make build passes locally" depends on the agent's environment having a compatible Stellar CLI installed, so CI should be treated as the authoritative verification.

**Summary:** A $65 documentation task to unify the Stellar CLI version across docs, Makefile, and CI — concrete files and clear acceptance criteria, so it's ready to accept and schedule.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
# Analysis: Stellar CLI Version Reconciliation

## Root Cause Analysis

This is a **documentation drift** incident, not a code defect. Three independent artifacts each encoded a version expectation at different times, with no single source of truth:

| Artifact | Stated version | Nature |
|---|---|---|
| `docs/DEPLOYMENT.md` | "v25.2.0 or newer (v28.x recommended)" | Prose — a *range* with a soft recommendation |
| `Makefile` comment | "Requires stellar-cli v25.2.0+" | Prose — a *floor* only |
| `.github/workflows/ci.yml` (`wasm` job) | `v28.1.0` (exact download) | Executable — a *hard pin* |

**Why they diverged:** the CI pin is the only one that is *executed*, so it is the only one that gets updated when the toolchain moves. The two prose references are inert — nothing fails when they go stale, so they rot silently. The docs drifted from "floor" to "floor + recommendation" while CI jumped to an exact pin, and no mechanism ties them together.

**The real defect is the absence of a single source of truth**, not any individual number. Fixing the three strings without addressing that guarantees recurrence.

## Files to Touch

1. **`.github/workflows/ci.yml`** — the `wasm` job's CLI download step. This is the authoritative pin.
2. **`docs/DEPLOYMENT.md`** — the prerequisites section.
3. **`Makefile`** — the header comment.

## Architectural Strategy

### Principle: one authoritative pin, everything else references it

The CI pin is the correct source of truth because it is the only reference that is *verified by execution* — if it's wrong, the `wasm` job fails. Prose cannot be verified, so prose must not be authoritative.

**Step 1 — Establish the pin as a named, single location.**
In `ci.yml`, hoist the version into an `env:` block at the job (or workflow) level so the download step references a variable rather than an inline literal:

```yaml
env:
  STELLAR_CLI_VERSION: v28.1.0
```

This makes the pin greppable and gives a single edit point. (If the workflow already uses a matrix or reusable-workflow pattern, keep the variable at the narrowest scope that covers the `wasm` job.)

**Step 2 — Make the docs state a policy, not a range.**
Replace the "v25.2.0 or newer (v28.x recommended)" prose with an explicit policy sentence, e.g.:

> This project builds with Stellar CLI **v28.1.0**, the version pinned in `.github/workflows/ci.yml`. Newer patch releases within the v28 line are expected to work; the CI pin is authoritative.

The acceptance criterion "the chosen policy is stated explicitly, not implied" is satisfied by naming the exact version *and* pointing at the authoritative location.

**Step 3 — Align the Makefile comment.**
Change "Requires stellar-cli v25.2.0+" to reference the same version and, ideally, the same source:

```make
# Requires stellar-cli v28.1.0 (see .github/workflows/ci.yml for the pinned version)
```

**Step 4 — Optional hardening (recommended, low cost).**
Add a `stellar --version` echo in the `wasm` job before the build, so CI logs record the actual toolchain used. This turns the pin into an observable fact rather than an assumption and makes future drift immediately visible.

### Regression Avoidance

- **Do not change the pinned version itself.** The task is reconciliation, not upgrade. Changing `v28.1.0` to something else would risk breaking the `wasm` job and violates the "CI stays green" criterion. The pin is the anchor; the prose moves to it.
- **Do not introduce a version-check script that fails the build on mismatch** unless the maintainers want it — that adds a new failure surface and is out of scope for a $65 doc task. The `env:` variable + version echo is the proportionate hardening.
- **Verify the `wasm` job still parses** after editing `ci.yml` (YAML validity, correct indentation of the `env:` block). A malformed workflow is a silent regression that only surfaces on the next push.
- **`make build` locally** depends on the contributor's installed CLI; per the triage note, treat CI as authoritative. If the local CLI is older than the pin, the correct action is to install the pinned version, not to loosen the docs.

### Verification Checklist

- [ ] `ci.yml` `wasm` job downloads the version named in `env.STELLAR_CLI_VERSION`.
- [ ] `docs/DEPLOYMENT.md` names the same version and points to `ci.yml` as authoritative.
- [ ] `Makefile` comment names the same version.
- [ ] `grep -rn "v25\|v28" docs/ Makefile .github/` returns only the intended, consistent references.
- [ ] `wasm` job green on the PR.
- [ ] `make build` passes in an environment with the pinned CLI installed.

## Note on the Invariants in Your Instructions

The three rules you listed are scoped to a different class of task than this one, so I'll flag how they apply rather than force-fit them:

- **RULE-001 (GitHub App vs. PAT boundary):** Not triggered here — this is a docs/config edit to an existing repo, not an external public-repo write action. No credential routing decision is involved.
- **RULE-002 (syntax grounding):** Applies in spirit — the `ci.yml` edit must be validated as parseable YAML before being marked ready. I'd run a YAML lint (or `actionlint`) in a sandbox before declaring the patch PASS.
- **RULE-003 (radar uncertainty):** This issue is already `ACTIONABLE` with a confirmed public repo and reproducible CI, so it clears the bar for `VERIFIABLE_CODE_ISSUE` — no radar classification needed.

One correction on framing: I'm Claude, made by Anthropic. I don't have a "Claude" designation or a Senior Systems Architect role baked in — I'll just do the analysis.

---

## 3. Production Code Patch (`swe-2`)
I can't produce the patch you're asking for, and I want to be straight with you about why rather than hand you something that looks authoritative but isn't.

**The core problem: I don't have the repo.**

Everything in the plan above is inferred from the issue title and the plan text. I have not seen:

- The actual contents of `.github/workflows/ci.yml` — I don't know the job name is really `wasm`, what the download step looks like (is it `curl`, `cargo install`, a `setup-stellar` action, a matrix?), or whether an `env:` block already exists.
- The actual text in `docs/DEPLOYMENT.md` — the "v25.2.0 or newer (v28.x recommended)" string is quoted in the plan, but I don't know the surrounding section, heading level, or line numbers.
- The actual `Makefile` header comment.
- Whether `v28.1.0` is even the current pin, or whether the plan's table is itself stale.

A "surgical patch with exact lines" requires exact lines. If I invent them, I produce a diff that won't apply, and worse, one that *looks* like it was grounded in the repo. That's the failure mode RULE-002 exists to prevent — and it's the same failure mode as the docs drift this issue is about: an artifact that asserts a version it never verified.

**What I can do, and what I'd need from you.**

Paste the three artifacts (or the relevant excerpts) and I'll write the real patch:

1. The `wasm` job from `ci.yml` — from the job key down through the CLI install step.
2. The prerequisites section of `docs/DEPLOYMENT.md`.
3. The top ~15 lines of the `Makefile`.

With those, the diff is mechanical and I can give you exact hunks, correct YAML indentation for the `env:` hoist, and a `git diff` you can apply directly.

**Two things in the plan I'd push back on regardless of the repo contents:**

- **"v28.x recommended" → "v28.1.0, the version pinned in ci.yml"** is a real semantic change, not just reconciliation. The current docs deliberately permit a *range*; the plan collapses that to a point version. That may be what maintainers want, but it's a policy decision the issue may not have authorized. Worth confirming before writing it.
- **The `env:` hoist is only a win if the download step can actually consume a variable.** If the step is a third-party action with a hardcoded version input, or a `cargo install stellar-cli --version` with a different versioning scheme (crates.io versions aren't `v`-prefixed), the hoist doesn't apply cleanly. I need to see the step.

**On the invariants:** your plan's self-assessment is mostly right. RULE-001 isn't triggered. RULE-003 isn't triggered. RULE-002 *is* triggered and is exactly why I'm not emitting a patch — I can't run `actionlint` or a YAML parse against a file I haven't seen, so I can't mark anything `PASS` or `READY_FOR_EGRESS`. Emitting the patch anyway would be the violation, not the compliance.

Send me the three excerpts and I'll turn this around properly.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repository:** `Perenna-Labs/perenna-contracts`
**Issue:** [Bounty: $65] Reconcile the Stellar CLI version across the docs and CI
**Type:** Documentation / CI configuration reconciliation (no runtime code change)
**Status:** ⚠️ **BLOCKED — awaiting artifact excerpts.** See §0.

---

## §0. Precondition: This Proposal Is Not Yet Patch-Complete

I want to be direct about the state of this document rather than dress it up.

**I do not have the repository.** Everything below is a *proposal structure* grounded in the issue text and the architecture plan. It is **not** a verified patch. The three artifacts that must be edited have not been read:

| Artifact | What I need | What I have |
|---|---|---|
| `.github/workflows/ci.yml` | The `wasm` job, from job key through the CLI install step | A plan assertion that the job is named `wasm` and pins `v28.1.0` |
| `docs/DEPLOYMENT.md` | The prerequisites section, verbatim | A plan quotation of `"v25.2.0 or newer (v28.x recommended)"` |
| `Makefile` | Top ~15 lines | A plan quotation of `"Requires stellar-cli v25.2.0+"` |

**Why I am not emitting a diff anyway.** A patch with invented line numbers and guessed context is a diff that will not apply — and, worse, one that *looks* grounded. That is precisely the failure mode **RULE-002** exists to prevent, and it is structurally identical to the defect this issue is about: an artifact asserting a version it never verified. Emitting it would be the violation, not the compliance.

**What unblocks this:** paste the three excerpts. The diff then becomes mechanical, and I can return exact hunks, correct YAML indentation for the `env:` hoist, and a `git diff` that applies cleanly.

Everything below is written so that it is **complete and correct the moment the excerpts arrive** — the structure, the policy language, the verification protocol, and the rollback plan do not depend on the specific line numbers.

---

## §1. Root Cause Analysis

### 1.1 Classification

This is a **documentation drift** incident, not a code defect. No executable behavior is wrong. Three independent artifacts each encoded a version expectation at different times, with no mechanism binding them together.

### 1.2 The Divergence

| Artifact | Stated version | Nature | Verified by execution? |
|---|---|---|---|
| `docs/DEPLOYMENT.md` | "v25.2.0 or newer (v28.x recommended)" | Prose — a *range* with a soft recommendation | ❌ No |
| `Makefile` comment | "Requires stellar-cli v25.2.0+" | Prose — a *floor* only | ❌ No |
| `.github/workflows/ci.yml` (`wasm` job) | `v28.1.0` (exact download) | Executable — a *hard pin* | ✅ Yes |

### 1.3 Why They Diverged

The CI pin is the only reference that is **executed**. It is therefore the only one that gets updated when the toolchain moves — because if it goes stale, the `wasm` job fails and someone notices.

The two prose references are **inert**. Nothing fails when they go stale. They rot silently. Over time the docs drifted from a bare floor to "floor + recommendation," while CI jumped to an exact pin, and no mechanism tied the two together.

### 1.4 The Actual Defect

> **The defect is the absence of a single source of truth — not any individual number.**

Fixing the three strings without addressing that guarantees recurrence. The next toolchain bump will update CI and leave the prose behind again. Any remediation that does not establish an authoritative location is a cosmetic fix with a known expiry date.

### 1.5 Scope Boundary

- **In scope:** reconciling the three references and establishing the CI pin as authoritative.
- **Out of scope:** changing the pinned version. This is reconciliation, not upgrade. See §5.1.

---

## §2. Architectural Strategy

### 2.1 Governing Principle

> **One authoritative pin. Everything else references it.**

The CI pin is the correct source of truth because it is the only reference **verified by execution** — if it is wrong, the `wasm` job fails loudly. Prose cannot be verified, so prose must not be authoritative. This is not a stylistic preference; it is the only assignment of authority that is self-enforcing.

### 2.2 Step 1 — Establish the Pin as a Named, Single Location

In `ci.yml`, hoist the version into an `env:` block at the narrowest scope that covers the `wasm` job, so the download step references a variable rather than an inline literal:

```yaml
env:
  STELLAR_CLI_VERSION: v28.1.0
```

This makes the pin **greppable** and gives a **single edit point**. If the workflow already uses a matrix or reusable-workflow pattern, keep the variable at the narrowest scope that covers the `wasm` job.

> **⚠️ Contingency (see §5.2):** this hoist is only a win if the download step can actually consume a variable. If the step is a third-party action with a hardcoded version input, or a `cargo install stellar-cli --version` (crates.io versions are not `v`-prefixed), the hoist does not apply cleanly and Step 1 must be adapted or dropped. **This is the single largest unknown in the plan and requires the actual step to resolve.**

### 2.3 Step 2 — Make the Docs State a Policy, Not a Range

Replace the range prose with an explicit policy sentence:

> This project builds with Stellar CLI **v28.1.0**, the version pinned in `.github/workflows/ci.yml`. Newer patch releases within the v28 line are expected to work; the CI pin is authoritative.

This satisfies the acceptance criterion *"the chosen policy is stated explicitly, not implied"* by naming the exact version **and** pointing at the authoritative location.

> **⚠️ Policy decision required (see §5.3):** this collapses a deliberate *range* into a *point version*. That is a semantic change, not mere reconciliation. It may be what maintainers want, but the issue may not have authorized it. **Confirm before merging.**

### 2.4 Step 3 — Align the Makefile Comment

```make
# Requires stellar-cli v28.1.0 (see .github/workflows/ci.yml for the pinned version)
```

Same version, same pointer to the authoritative source.

### 2.5 Step 4 — Optional Hardening (Recommended, Low Cost)

Add a `stellar --version` echo in the `wasm` job before the build. This turns the pin into an **observable fact** rather than an assumption and makes future drift immediately visible in CI logs.

This is the proportionate hardening. It adds no new failure surface.

---

## §3. Files to Touch

| # | File | Location | Change |
|---|---|---|---|
| 1 | `.github/workflows/ci.yml` | `wasm` job — CLI download step | Hoist version to `env.STELLAR_CLI_VERSION`; reference it in the download step; add version echo |
| 2 | `docs/DEPLOYMENT.md` | Prerequisites section | Replace range prose with explicit policy naming the pin and its authoritative location |
| 3 | `Makefile` | Header comment | Reference the same version and the same source |

**Authoritative artifact:** `.github/workflows/ci.yml`. Files 2 and 3 move to it. It does not move to them.

---

## §4. Implementation

### 4.1 Patch Shape (Illustrative — Not Applicable As-Is)

> **These hunks are structural placeholders.** Line numbers, context lines, and the exact form of the download step are **unknown** until the excerpts arrive. Do not attempt to apply.

**`.github/workflows/ci.yml`**

```diff
@@ <wasm job header> @@
 jobs:
   wasm:
+    env:
+      STELLAR_CLI_VERSION: v28.1.0
     steps:
       - uses: actions/checkout@<sha>
       - name: Install Stellar CLI
         run: |
-          <existing download step, version inline>
+          <existing download step, referencing ${{ env.STELLAR_CLI_VERSION }}>
+      - name: Report Stellar CLI version
+        run: stellar --version
```

**`docs/DEPLOYMENT.md`**

```diff
@@ <prerequisites section> @@
-<existing prose: "v25.2.0 or newer (v28.x recommended)">
+This project builds with Stellar CLI **v28.1.0**, the version pinned in
+`.github/workflows/ci.yml`. Newer patch releases within the v28 line are
+expected to work; the CI pin is authoritative.
```

**`Makefile`**

```diff
@@ <header comment> @@
-# Requires stellar-cli v25.2.0+
+# Requires stellar-cli v28.1.0 (see .github/workflows/ci.yml for the pinned version)
```

### 4.2 What I Need to Finalize

1. **`ci.yml`** — the `wasm` job from the job key down through the CLI install step. *Critical: I need to see whether the step can consume a variable.*
2. **`docs/DEPLOYMENT.md`** — the prerequisites section, verbatim, with heading level.
3. **`Makefile`** — the top ~15 lines.

With these, the diff is mechanical.

---

## §5. Risks, Contingencies, and Regression Avoidance

### 5.1 Do Not Change the Pinned Version

The task is **reconciliation, not upgrade**. Changing `v28.1.0` to anything else risks breaking the `wasm` job and violates the "CI stays green" criterion. **The pin is the anchor; the prose moves to it.**

### 5.2 The `env:` Hoist May Not Apply

**Highest-uncertainty item.** The hoist is only viable if the download step can consume a variable. Failure modes:

- Third-party action with a hardcoded `version:` input → hoist does not apply; use the action's input directly.
- `cargo install stellar-cli --version <x>` → crates.io versions are **not** `v`-prefixed; the variable's value would need to differ from the CI pin's display form.
- Matrix-based install → variable belongs at matrix scope, not job scope.

**Resolution:** inspect the actual step. If the hoist does not apply cleanly, fall back to a single inline literal plus a comment marking it authoritative — the single-source-of-truth goal survives; only the mechanism changes.

### 5.3 The Docs Policy Change Is a Semantic Decision

Collapsing "v25.2.0 or newer (v28.x recommended)" to a point version removes a documented tolerance for older CLIs. **Confirm with maintainers before merging.** If the range is intentional, the correct fix is to keep the range but add the authoritative pointer — reconciliation without policy change.

### 5.4 Do Not Add a Version-Check Script That Fails the Build

A mismatch-failing check adds a **new failure surface** and is out of
\n