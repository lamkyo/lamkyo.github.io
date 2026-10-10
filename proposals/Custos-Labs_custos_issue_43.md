# Bounty Proposal: Custos-Labs/custos#43 - [Bounty: $65] Run the dependency audit on every pull request\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $65] Run the dependency audit on every pull request

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Yes — this is actionable and codeable: it's a narrowly scoped edit to the `dependencies` job's gating condition in `.github/workflows/contributor-checks.yml`, swapping the lockfile-only check for one that also triggers on any `package.json` change (or drops the gate entirely) while preserving `--audit

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
## Root Cause Analysis

**Surface defect:** Every audit-path step in the `dependencies` job carries `if: steps.lock.outputs.changed == 'true'`, and the `lock` filter step only matches `pnpm-lock.yaml`. A `package.json`-only diff → `changed=false` → `pnpm audit --audit-level high` never executes. Silent skip, not a failure — the worst kind of CI gap.

**Structural defect (the real root cause):** A *security control* is keyed on *diff content*. Audit result = f(lockfile state, advisory DB at run time). Neither is diff-dependent. Any path allowlist is an incomplete invariant — you'd have to enumerate `**/package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.pnpmfile.cjs`, `patches/**`, `overrides` — and you still miss the time-drift case (CVE disclosed after push, zero file changes). Enumerating triggers for a security gate is a losing game.

## Files to Touch

| File | Action |
|---|---|
| `.github/workflows/contributor-checks.yml` | Primary edit |
| `CONTRIBUTING.md` / CI docs | Only if lockfile-gating is documented — grep for it |

**Two checks before editing** (both can independently suppress the audit):
1. Step/job-level `if:` gates — or a `needs: lock` upstream job whose output gates `dependencies` at job level.
2. **Trigger-level `on.pull_request.paths:`** — if the workflow itself filters on `pnpm-lock.yaml`, job-level fixes are dead code. Verify first.

## Strategy: Drop the Gate (Option A)

Recommended over widening the filter (Option B). `pnpm audit` is seconds of runtime and audits the committed lockfile — no install required. The marginal cost of unconditional execution is ~nil; the marginal coverage is total.

**Representative patch** (exact diff depends on the actual file — I don't have it in front of me):

```diff
       - name: Audit dependencies
-        if: steps.lock.outputs.changed == 'true'
         run: pnpm audit --audit-level high   # keep existing guidance message intact
```

Also un-gate audit's *prerequisite chain* only: `actions/checkout`, `pnpm/action-setup`, `actions/setup-node` (keep `cache: pnpm` — unchanged lockfiles resolve warm, ~free). If `pnpm install --frozen-lockfile` exists solely to serve the audit, un-gate it too; cached installs of unchanged lockfiles are near-instant. If the `lock` filter step feeds nothing else afterward, delete it — dead config rots.

If the maintainer insists on gating as a cost optimization, the filter must be `['pnpm-lock.yaml', '**/package.json', 'pnpm-workspace.yaml', '**/.npmrc', '.pnpmfile.cjs', 'patches/**']` — note the `**/package.json` glob, since pnpm implies a workspace and `package.json` alone misses every nested package.

## Regression Matrix

| Risk | Handling |
|---|---|
| New CVE blocks unrelated PRs mid-flight | **Intended** per AC #2. Escape hatch: `auditConfig.ignoreCves` for maintainers. `--audit-level high` bounds the noise. |
| Audit runs without lockfile present | Impossible — `pnpm-lock.yaml` is committed; audit reads it directly. |
| `changed` output consumed elsewhere | Grep the workflow for all `steps.lock.outputs.*` references before deleting the filter step. |
| Forked PRs / `pull_request_target` | Confirm trigger is `pull_request` (untrusted code must not get secrets); don't alter permissions. |

## Invariant Compliance

- **[RULE-002] Syntax grounding — required before READY_FOR_EGRESS:**
  ```bash
  actionlint .github/workflows/contributor-checks.yml   # catches dead step refs, bad contexts
  yq '.' .github/workflows/contributor-checks.yml > /dev/null
  ```
  Then **behavioral proof**: open a test PR on a fork that edits only one workspace `package.json` → confirm the audit step executes (not skipped). A second no-op PR confirms the tree stays green. `act` is an acceptable pre-check but not the gate.
- **[RULE-001] Egress boundary:** bounty submission — fork, push, PR body — routes through an authenticated user PAT. GitHub App tokens only for read/clone/scout operations upstream.
- **[RULE-006]** N/A — no monetary computation.

**Bottom line:** one-line-class fix, but the correct invariant is "every PR is audited against the live advisory DB," not "audit runs when these files change." Ship Option A, lint it, prove it with a package.json-only test PR.

---

## 3. Production Code Patch (`swe-2`)
Quick honesty check first: I don't have the actual contents of `.github/workflows/contributor-checks.yml` in context — I can't see this repo's codebase. The diff below is written against the structure described in your plan (a `lock` paths-filter step gating the audit chain via `steps.lock.outputs.changed`). Context lines and step names may differ in the real file — paste it if you need a line-exact patch. Status is **generated, not lint-verified** — I can't execute `actionlint` from here.

## Primary patch — drop the gate

```diff
--- a/.github/workflows/contributor-checks.yml
+++ b/.github/workflows/contributor-checks.yml
@@ -XX,X +XX,X @@ jobs: dependencies:
     - name: Setup Node.js
       uses: actions/setup-node@v4
       with:
         node-version: 20
         cache: pnpm
-
-    - name: Detect lockfile changes
-      id: lock
-      uses: dorny/paths-filter@v3
-      with:
-        filters: |
-          changed:
-            - 'pnpm-lock.yaml'
 
     - name: Install dependencies
-      if: steps.lock.outputs.changed == 'true'
       run: pnpm install --frozen-lockfile
 
     - name: Audit dependencies
-      if: steps.lock.outputs.changed == 'true'
       run: pnpm audit --audit-level high
```

Two pre-flight checks that change the patch:

```bash
# 1. If ANY other step still consumes it, keep the `lock` step — only un-gate the audit chain:
grep -rn 'steps\.lock' .github/workflows/

# 2. If the trigger itself filters paths, the job-level fix is dead code — un-filter or widen:
grep -n -A5 'pull_request' .github/workflows/contributor-checks.yml | grep -B1 -A3 'paths'
```

If check 2 hits, apply this too:

```diff
 on:
   pull_request:
-    paths:
-      - 'pnpm-lock.yaml'
+# No paths filter — audit must run on every PR (advisory DB drifts independently of diffs)
```

## Regression test — `tests/test_contributor_checks_workflow.py`

Since the artifact is YAML, the "unit test" is an invariant assertion suite. Drop it in if the repo has a Python test path; otherwise keep the `grep`/`actionlint` checks.

```python
"""Regression guard: dependency audit must run unconditionally on every PR.

Context: audit was gated on `steps.lock.outputs.changed`, which only matched
pnpm-lock.yaml — a package.json-only diff silently skipped `pnpm audit`.
"""
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "contributor-checks.yml"


@pytest.fixture(scope="module")
def workflow():
    doc = yaml.safe_load(WORKFLOW.read_text())
    # PyYAML (YAML 1.1) parses the key `on` as boolean True.
    if "on" not in doc and True in doc:
        doc["on"] = doc.pop(True)
    return doc


def _steps(workflow):
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            yield job_name, step


def test_audit_step_exists_and_is_unconditional(workflow):
    audit = [(j, s) for j, s in _steps(workflow) if "pnpm audit" in s.get("run", "")]
    assert audit, "no `pnpm audit` step found"
    for job, step in audit:
        assert "if" not in step, (
            f"audit in job '{job}' gated by `{step['if']}` — "
            "security controls must not be keyed on diff content"
        )


def test_audit_prerequisites_ungated(workflow):
    for job_name, job in workflow["jobs"].items():
        steps = job.get("steps", [])
        if not any("pnpm audit" in s.get("run", "") for s in steps):
            continue
        for s in steps:
            is_prereq = (
                s.get("uses", "").startswith(
                    ("actions/checkout", "actions/setup-node", "pnpm/action-setup")
                )
                or "pnpm install" in s.get("run", "")
            )
            if is_prereq:
                assert "steps.lock" not in s.get("if", ""), (
                    f"prerequisite '{s.get('name')}' in '{job_name}' still gated on lock diff"
                )


def test_no_dangling_lock_references():
    raw = WORKFLOW.read_text()
    assert "steps.lock.outputs" not in raw, "dangling ref to deleted `lock` filter step"


def test_pr_trigger_not_path_filtered(workflow):
    on = workflow["on"]
    pr = on.get("pull_request") if isinstance(on, dict) else None
    if isinstance(pr, dict) and "paths" in pr:
        assert "**/package.json" in pr["paths"], (
            f"trigger-level paths {pr['paths']} would still suppress audits "
            "on package.json-only diffs"
        )
```

## Grounding gate (RULE-002) — run before READY_FOR_EGRESS

```bash
actionlint .github/workflows/contributor-checks.yml
yq '.' .github/workflows/contributor-checks.yml > /dev/null
grep -n 'steps\.lock' .github/workflows/contributor-checks.yml   # expect no matches
pytest tests/test_contributor_checks_workflow.py -v
```

Then the behavioral proof — a static lint can't prove the step executes:

1. On a fork, open PR #1 touching **only** a nested workspace `package.json` (e.g., bump one devDependency patch version). Confirm `Audit dependencies` shows ▶ executed, not ⊘ skipped.
2. Open PR #2 as a trivial no-op (comment change). Confirm the tree stays green and audit still runs.

One safety note: `pnpm audit` under `pull_request` (not `pull_request_target`) gets a read-only token and hits the public advisory registry — no secrets exposure, no permissions change needed. Confirm the trigger is `pull_request` and leave `permissions:` untouched.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `ci(security): run dependency audit on every pull request`

**Repo:** `Custos-Labs/custos`
**Issue:** [Bounty: $65] Run the dependency audit on every pull request
**Type:** CI/CD security-control correctness fix
**Scope:** 1 workflow file (+1 optional test file)
**Breaking change:** No — but it *will* surface pre-existing advisories on unrelated PRs. That is the point.

---

## 0. Delivery status & gate report

| Gate | Result | Notes |
|---|---|---|
| Payout gate (≥ $25 USD) | **PASS** | $65 declared |
| Scam-keyword scan | **PASS** | No `doolar` / `free bitcoin` / `[$0]` / `zero-bounty` / `add at my LinkedIn` markers |
| Classification | `ACCEPTED_FOR_IMPLEMENTATION` | Not `REJECTED_SCAM_ZERO_PAYOUT` |
| Syntax grounding (RULE-002) | **NOT YET EXECUTED** | No sandbox access to the repo tree; `actionlint` / `yq` / `pytest` have not run |
| Egress boundary (RULE-001) | Compliant by design | Submission path routes through user PAT |
| Monetary computation (RULE-006) | N/A | — |

> **Status: `DRAFT — PENDING_SYNTAX_VERIFICATION`.** Per the standing rule, no patch may be marked `PASS` or `READY_FOR_EGRESS` until it has cleared a deterministic linter in a sandbox. The diff below is written against the *described* workflow structure, not the actual file contents, which are not in context. Treat every context line as an assumption to be confirmed by §4 before the patch is applied.

---

## 1. Summary

The `dependencies` job in `.github/workflows/contributor-checks.yml` gates its entire audit chain on a `dorny/paths-filter` step that matches only `pnpm-lock.yaml`. A PR whose diff touches `package.json` — or nothing at all — sets `changed=false`, and `pnpm audit --audit-level high` never runs. The failure mode is a **silent skip**, not a red build.

This PR removes the diff-content gate from the audit path. A dependency audit's result is a function of the committed lockfile and the advisory database at run time. Neither input is diff-dependent, so gating the control on diff content is an unsound invariant. `pnpm audit` costs seconds and requires no install; the marginal cost of unconditional execution is approximately nil, and the marginal coverage is total.

---

## 2. Root cause analysis

### 2.1 Surface defect

Every audit-path step carries:

```yaml
if: steps.lock.outputs.changed == 'true'
```

and the `lock` filter matches exactly one path:

```yaml
filters: |
  changed:
    - 'pnpm-lock.yaml'
```

A `package.json`-only diff → `changed=false` → audit skipped. Silent. Green checkmark. The worst class of CI gap, because nothing in the UI tells a reviewer that a security control was bypassed.

### 2.2 Structural defect (the actual root cause)

**A security control is keyed on diff content.**

The audit result is `f(lockfile state, advisory DB at run time)`. Neither term is a function of which files a PR happened to modify. This produces two independent classes of false negative:

1. **Path-allowlist incompleteness.** A correct allowlist for "dependency-affecting changes" would have to enumerate `**/package.json` (note the `**/` — pnpm implies a workspace, so a bare `package.json` misses every nested package), `pnpm-workspace.yaml`, `**/.npmrc`, `.
\n