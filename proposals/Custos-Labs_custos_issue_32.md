# Bounty Proposal: Custos-Labs/custos#32 - [Bounty: $45] Add a `concurrency` group to `ci.yml`\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $45] Add a `concurrency` group to `ci.yml`

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
## Classification

**Status: `RAW_RADAR_CANDIDATE`** — I do not have confirmed access to `Custos-Labs/custos` file contents or a reproducible test suite, so the hunk context below is based on the canonical `ci.yml` layout. The anchor point (`on:` block → `jobs:` boundary) must be verified against the real file before egress, and the patch must pass the grounding checks in RULE-002 before being marked READY.

## Patch

`concurrency` is a top-level workflow key. It must be inserted between the `on:` block and `jobs:` (after `permissions:` if one exists):

```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -6,6 +6,10 @@ on:
     branches: [main]
   pull_request:
 
+concurrency:
+  group: ${{ github.workflow }}-${{ github.ref }}
+  cancel-in-progress: true
+
 jobs:
   build:
     runs-on: ubuntu-latest
```

If the real file's `on:`/`jobs:` spacing differs, the semantic anchor is: insert immediately **before** the top-level `jobs:` key, at zero indentation.

## Validation test (pytest)

```python
# tests/test_ci_workflow.py
import pathlib
import yaml

WF = pathlib.Path(".github/workflows/ci.yml")

def test_ci_has_concurrency_group():
    wf = yaml.safe_load(WF.read_text())
    assert "concurrency" in wf, "ci.yml missing top-level 'concurrency' key"
    assert isinstance(wf["concurrency"], dict)
    assert wf["concurrency"]["group"] == "${{ github.workflow }}-${{ github.ref }}"
    assert wf["concurrency"]["cancel-in-progress"] is True
```

> Note: PyYAML parses `on:` as boolean `True` (YAML 1.1 quirk) — irrelevant here since we only assert on `concurrency`, but don't assert on `wf["on"]`.

## Grounding checks (RULE-002 — run before marking READY_FOR_EGRESS)

```bash
# 1. Workflow-specific linter (authoritative for Actions syntax)
actionlint .github/workflows/ci.yml

# 2. YAML parse check + test
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
pytest tests/test_ci_workflow.py -v
```

## Egress note (RULE-001)

This patch targets a public external repo — it must be applied and pushed via an authenticated user account (PAT), not a GitHub App.

## Known unknowns

- Exact hunk line numbers depend on the real file length — verify the `on:` → `jobs:` anchor.
- If `ci.yml` already defines `concurrency` or per-job concurrency, the bounty requirement may differ — flag for re-review rather than duplicating the key.
- Common variant: `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}` if maintainers want main-branch runs to always complete. The simple `true` form above is the typical bounty expectation.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — `ci: add top-level concurrency group to cancel superseded runs`

**Repo:** `Custos-Labs/custos`
**Bounty:** $45 — Add a `concurrency` group to `ci.yml`
**Branch:** `ci/add-concurrency-group`
**Base:** `main`
**Artifact status:** `RAW_RADAR_CANDIDATE` → promote to `VERIFIABLE_CODE_ISSUE` only after the anchor is confirmed against the real file and RULE-002 grounding passes
**Prepared by:** Delivery & Quality Verification Lead

---

## 1. Summary

Adds a top-level `concurrency` key to `.github/workflows/ci.yml` so that superseded workflow runs on the same ref are automatically cancelled. This eliminates redundant CI minutes and shortens the feedback loop on rapid pushes to a PR branch.

**Scope:** 1 file, +4 lines, 0 deletions. No job-level behavior changes.

---

## 2. Root Cause

The `ci.yml` workflow currently has no `concurrency` block. GitHub Actions therefore schedules every run triggered by every push to a branch and every PR synchronize event independently, with no supersession:

- Push `a1b2c3` → run starts
- Push `d4e5f6` (fixup commit) → **second** run starts
- Both runs execute the full matrix to completion; the first is already stale

Consequences:

1. **Wasted runner minutes** — N pushes in quick succession produce N full runs, of which only the last is meaningful.
2. **Delayed feedback on the head commit** — the newest run competes for runner capacity with the older, already-obsolete ones.
3. **Flaky-signal noise on PRs** — a red result from a stale run can land after a green result on the head commit, confusing reviewers and automated merge gates.

The canonical remedy is the workflow-level `concurrency` key with `cancel-in-progress: true`. This is a configuration omission, not a code defect — hence the fix is surgical and carries no runtime risk to the build itself.

---

## 3. Implementation

### 3.1 Patch

`concurrency` is a **top-level** workflow key. It is inserted between the `on:` block (and `permissions:`, if present) and the `jobs:` key, at zero indentation.

```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -6,6 +6,10 @@ on:
     branches: [main]
   pull_request:
 
+concurrency:
+  group: ${{ github.workflow }}-${{ github.ref }}
+  cancel-in-progress: true
+
 jobs:
   build:
     runs-on: ubuntu-latest
```

> **Hunk-offset caveat.** The line numbers above reflect the canonical `ci.yml` layout. The *semantic* anchor is authoritative and must be used when applying: **insert immediately before the top-level `jobs:` key, at zero indentation.** Do not trust the `@@` offsets until they are reconciled against the real file.

### 3.2 Why this form

| Decision | Rationale |
| --- | --- |
| `group: ${{ github.workflow }}-${{ github.ref }}` | Scopes supersession per-workflow **per-ref**. Two different PRs never cancel each other; pushes to `main` and pushes to a feature branch are independent. |
| `cancel-in-progress: true` | The whole point of the bounty — stale runs are terminated rather than queued. |
| Top-level, not per-job | Applies uniformly across the matrix; a job-level block would only cancel within a single job and would not stop sibling jobs. |
| No `github.event.pull_request.number` in the group | Unnecessary here — `github.ref` is already unique per PR (`refs/pull/N/merge`) and per branch. Keeps the expression minimal and easy to review. |

### 3.3 Rejected alternatives

- **`cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}`** — keeps every `main` run alive. Reasonable if maintainers want an immutable post-merge audit trail, but it is a policy choice beyond the bounty's ask. *See §7, open question 3.*
- **Per-job `concurrency`** — does not supersede across jobs; fails the stated requirement.
- **`cancel-in-progress` omitted** — GitHub defaults to `false`; the group would serialize runs instead of cancelling them, which *increases* queue latency. Explicit `true` is required.

### 3.4 Commit

```
ci: add top-level concurrency group to cancel superseded runs

Adds a workflow-level `concurrency` key to .github/workflows/ci.yml so
that in-flight runs on the same ref are cancelled when a newer run is
scheduled. Reduces redundant runner consumption on rapid pushes and
surfaces CI signal for the head commit sooner.

Group is scoped per-workflow, per-ref, so distinct PRs and branches do
not cancel one another.

Bounty: $45 — Add a `concurrency` group to `ci.yml`
```

---

## 4. Test Verification

### 4.1 Regression test (new file)

```python
# tests/test_ci_workflow.py
import pathlib
import yaml

WF = pathlib.Path(".github/workflows/ci.yml")

def test_ci_has_concurrency_group():
    wf = yaml.safe_load(WF.read_text())
    assert "concurrency" in wf, "ci.yml missing top-level 'concurrency' key"
    assert isinstance(wf["concurrency"], dict)
    assert wf["concurrency"]["group"] == "${{ github.workflow }}-${{ github.ref }}"
    assert wf["concurrency"]["cancel-in-progress"] is True
```

> **PyYAML caveat.** `yaml.safe_load` resolves the unquoted `on:` key to the boolean `True` under YAML 1.1 semantics. This is irrelevant to the assertions above — do **not** add an assertion on `wf["on"]`.

### 4.2 RULE-002 grounding gate — must run before `READY_FOR_EGRESS`

```bash
# 1. Workflow-specific linter (authoritative for Actions syntax)
actionlint .github/workflows/ci.yml

# 2. YAML parse check
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# 3. Regression test
pytest tests/test_ci_workflow.py -v
```

A patch may not be marked `PASS` or `READY_FOR_EGRESS` until all three exit zero **inside the sandbox**, against the real checked-out file — not against the canonical template.

### 4.3 Acceptance criteria → evidence map

| Bounty requirement | Verification | Status |
| --- | --- | --- |
| Top-level `concurrency` key exists in `ci.yml` | `test_ci_has_concurrency_group` | Pending real-file run |
| Key carries a `group` | same test, `group` assertion | Pending real-file run |
| Supersession actually cancels | `cancel-in-progress is True` + actionlint clean | Pending real-file run |
| Workflow remains valid | `actionlint` exit 0 | Pending real-file run |
| No unintended deletions | `git diff --stat` = 1 file, +4/−0 | Pending real-file run |

### 4.4 Post-merge behavioural check (manual, optional)

1. Push two commits to a scratch branch in quick succession.
2. Confirm the first run transitions to **Cancelled** and the second runs to completion.
3. Confirm a concurrent run on a *different* branch is **not** cancelled.

---

## 5. Pre-E
\n