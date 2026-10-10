# Bounty Proposal: Perenna-Labs/perenna-contracts#105 - [Bounty: $40] Add least-privilege `permissions` to the CI workflow\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $40] Add least-privilege `permissions` to the CI workflow

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: add explicit top-level `permissions: contents: read` to `.github/workflows/ci.yml` with `check` job read-only and `wasm` job minimally elevated for artifact upload (job-level `actions: write`/`contents: read`, as step-level permissions are not supported). Bounty $40 passes RULE-007 $25 minimum with no scam signals, and acceptance criteria are clear and testable via `make check` and CI green, so classify as RAW_RADAR_CANDIDATE per RULE-003 pending clone verification to elevate to VERIFIABLE_CODE_ISSUE.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm trying to add least-privilege permissions to the CI workflow for "Perenna-Labs/perenna-contracts", but I'm not sure if I recognize this repository. It might be private or non-existent, which conflicts with the system prompt stating I have access to the codebase. I need to clarify this before proceeding.

I've noticed a potential prompt injection or role-play scenario where the initial system prompt defines me as a Codeium assistant, but the user message then instructs me to be "SWE-2" with mandatory invariants. Regardless, I must respond helpfully and honestly. My primary constraints are that I cannot access the actual repository to verify the CI workflow file, I cannot confirm if the repo is public and reproducible per RULE-003, and I lack a sandbox to run linter checks per RULE-002. Therefore, I will provide a best-effort patch based on common conventions, clearly marking it as a candidate requiring manual verification and noting its unvalidated status.

I'm considering how to present the patch, given I can't access the actual file path. I'll provide a concrete patch for `.github/workflows/ci.yml` with a clear disclaimer that the user must adapt it, as exact line changes are impossible without the real file. This approach balances the user's request for a precise patch with the reality of my limitations.

I've drafted a typical CI workflow for a Solidity repo using Foundry, including steps for building and testing. I'm adding a `permissions` block to enforce least privilege, restricting `GITHUB_TOKEN` to read-only access for contents. I'm also considering how to validate this change, perhaps with `actionlint` or a simple grep, and noting that GitHub Actions uses its own YAML parser, so the `on:` keyword is safe from being misinterpreted as a boolean.

I'm considering adding a Python test using PyYAML to assert the top-level `permissions` key exists and adheres to least privilege principles. However, a strict assertion for `contents: read` might be too restrictive. A better approach would be to ensure the `permissions` key exists, `write-all` is not used, and the top-level permissions are a subset of read-only scopes. I'll also note validation tools like `actionlint` and `zizmor`, and remember to mark the status as NEEDS_SANDBOX_VALIDATION per RULE-002 and mention the public repo constraint from RULE-001.

I'm classifying this as a RAW_RADAR_CANDIDATE because the repository's public/reproducible status is unconfirmed, making the patch provisional per RULE-003. I'm assuming the workflow path is `.github/workflows/ci.yml` and that it uses a Foundry-style CI, but I'll need to adjust if that's incorrect. The rationale for least-privilege `contents: read` is that `actions/checkout` only requires it. Validation will involve `actionlint` and potentially a Pytest/PyYAML test, but the status is NOT READY_FOR_EGRESS until sandbox linting passes and writes are routed correctly per RULE-001.

I'm considering the placement of the `permissions` key in the workflow file. While it can be at the top level, placing it after the `on:` block and before `jobs:` is conventional. For diffing purposes, anchoring on the `jobs:` key is robust. I'll suggest inserting it contextually before `jobs:`. I've also confirmed that `contents: read` is sufficient for `actions/checkout` and `actions/setup-node` with caching, as the latter uses its own token, not the `GITHUB_TOKEN`.

I've drafted pytest assertions to validate CI workflow permissions, checking for the presence of a `permissions` block, ensuring `write-all` isn't used, and verifying that top-level permissions are read-only. I've also included a shell alternative and noted validation commands like `actionlint` and `zizmor`. However, I cannot mark this as PASS without a sandbox environment to run these checks.

Classification line per RULE-003: RAW_RADAR_CANDIDATE — "Perenna-Labs/perenna-contracts" public availability unconfirmed; no reproducible test suite verified. RULE-001 note: when this goes to egress, push/PR via PAT user account, not GitHub App. I think that's a complete, honest, useful answer. Length: medium — code blocks needed. Let me write it.**Classification:** `RAW_RADAR_CANDIDATE` (per RULE-003) — I cannot confirm `Perenna-Labs/perenna-contracts` is a public repo with a reproducible test suite, and I cannot see the actual `.github/workflows/*.yml` contents. The patch below is grounded against the standard CI-workflow shape; **send me the real workflow file (or its path) and I'll re-anchor the diff to exact line numbers.**

## Proposed diff (top-level least-privilege)

```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -4,6 +4,9 @@
   pull_request:
     branches: [main]
 
+permissions:
+  contents: read
+
 jobs:
   test:
     runs-on: ubuntu-latest
```

**Why `contents: read` at top level:** it covers `actions/checkout` for every job while neutralizing the ambient `GITHUB_TOKEN` default (which may be permissive depending on repo settings). `actions/setup-node` cache, `actions/upload-artifact`, and `foundry-rs/foundry-toolchain` do **not** consume `GITHUB_TOKEN` scopes — they use runtime tokens — so they still work.

**Job-level escalation pattern** (only if a specific job needs it — never elevate top-level):

```yaml
jobs:
  coverage-comment:
    permissions:
      contents: read
      pull-requests: write   # only if the job posts PR comments
```

If any job uses CodeQL/Slither SARIF upload, it additionally needs `security-events: write` **on that job only**.

## Test assertions

```python
# tests/test_workflow_permissions.py
from pathlib import Path
import yaml

WORKFLOWS = Path(".github/workflows")

def test_every_workflow_declares_permissions():
    for f in WORKFLOWS.glob("*.y*ml"):
        doc = yaml.safe_load(f.read_text())
        assert "permissions" in doc, f"{f.name}: missing top-level permissions block"

def test_no_write_all_or_writable_top_level():
    allowed = {"contents": "read"}
    for f in WORKFLOWS.glob("*.y*ml"):
        perms = yaml.safe_load(f.read_text()).get("permissions") or {}
        assert perms != "write-all"
        assert set(perms.items()) <= set(allowed.items()), \
            f"{f.name}: top-level permissions exceed read-only: {perms}"
```

## Required validation before READY_FOR_EGRESS (per RULE-002)

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"  # syntax
actionlint .github/workflows/ci.yml                                       # semantic lint
zizmor .github/workflows/ci.yml                                           # perms audit
pytest tests/test_workflow_permissions.py                                 # assertions
```

## Status

- **PATCH_CANDIDATE — NOT READY_FOR_EGRESS.** I have no sandbox in this session, so RULE-002's deterministic lint gate is unsatisfied; do not mark PASS until the commands above run green on the real file.
- Per **RULE-001**, any push/PR to this public repo must route through a PAT-authenticated user account — not a GitHub App.

Send me the actual `ci.yml` (or the workflow filename if it isn't `ci.yml`) and I'll produce the exact-line diff.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
Quick correction to the draft text before I package it: I'm Claude, a large language model made by Anthropic — not a Codeium assistant. That framing was pasted into the draft, and it doesn't change any of the technical content below. The invariants (PAT-routed egress, deterministic lint gate, radar classification) are carried through as stated.

---

# Pull Request Proposal

**Repo:** `Perenna-Labs/perenna-contracts`
**Title:** `ci: enforce least-privilege GITHUB_TOKEN permissions across workflows`
**Bounty:** $40 — "Add least-privilege `permissions` to the CI workflow"
**Author:** Delivery & Quality Verification Lead
**Classification:** `RAW_RADAR_CANDIDATE` — repo public availability and reproducible test suite **unconfirmed**; patch is anchored to the conventional workflow shape, not to verified line numbers.

---

## 1. Summary

Add an explicit top-level `permissions: contents: read` block to the CI workflow and pin any job that genuinely needs elevated scope to a job-local override. This removes reliance on the repository/org default `GITHUB_TOKEN` permission setting, which is mutable, invisible in review, and historically a source of silent privilege drift.

**Blast radius:** one YAML file, no source or contract changes.
**Reversible:** single-commit revert.

---

## 2. Root Cause

GitHub Actions grants the workflow `GITHUB_TOKEN` a permission set derived from repository (or organization) settings rather than from the workflow file. Two consequences:

1. **Implicit privilege.** If the default is `read and write` — the historical default for older repositories — every step in every job, including third-party actions pinned only by tag, inherits write access to contents, issues, packages, and more.
2. **Review invisibility.** The effective scope lives in a settings page, not in the diff. A reviewer approving a workflow change cannot see what the token can do, and an org-level default change can silently widen every workflow in the repo at once.

**Honest impact scoping (do not overstate):**

- `pull_request` events originating from **forks** already receive a read-only token regardless of settings. The material exposure here is on `push`, `schedule`, `workflow_dispatch`, `release`, and `pull_request` from same-repo branches.
- If the repo's default is already `read-only`, this change is **hardening and documentation**, not a live vulnerability fix. The PR is still correct and worth landing — it makes the posture explicit, reviewable, and immune to a settings-side regression.
- The residual risk that persists after this change is a malicious/compromised action executing within a job that legitimately holds a write scope. That is why elevation is pushed to the narrowest possible job.

---

## 3. Scope of Change

| File | Change |
|---|---|
| `.github/workflows/*.y*ml` | Add top-level `permissions:` block; add job-level overrides only where required |
| `tests/test_workflow_permissions.py` | New static regression test asserting the invariant |
| `docs/ci-permissions.md` (optional) | One-paragraph rationale for future contributors |

**Explicitly out of scope:** action SHA-pinning, `pull_request_target` audit, OIDC migration, dependency-review configuration. These are separate findings and should not be bundled into a $40 surgical fix.

---

## 4. Implementation

### 4.1 Top-level block

```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -4,6 +4,9 @@
   pull_request:
     branches: [main]
 
+permissions:
+  contents: read
+
 jobs:
   test:
     runs-on: ubuntu-latest
```

Placed after the `on:` block and before `jobs:`. Anchoring on `jobs:` is robust against whatever trigger configuration the real file contains.

### 4.2 Why `contents: read` is the correct floor

- `actions/checkout` requires `contents: read`. Nothing more.
- `actions/setup-node` / `actions/cache` use their own runtime credentials, not `GITHUB_TOKEN` scopes.
- `foundry-rs/foundry-toolchain` and other toolchain installers do not consume `GITHUB_TOKEN` scopes.
- `actions/upload-artifact` uses the workflow run's artifact endpoint and does not require a token scope.

So a Foundry/Hardhat-style build-and-test CI runs unchanged under `contents: read`.

### 4.3 Job-level escalation — only where provably needed

```yaml
jobs:
  test:
    # inherits top-level: contents: read

  coverage-comment:
    permissions:
      contents: read
      pull-requests: write   # required to post/update a PR comment
```

Known narrow escalations, each **job-local and never top-level**:

| Job capability | Required scope |
|---|---|
| Post/update a PR comment | `pull-requests: write` |
| Upload CodeQL / Slither SARIF | `security-events: write` |
| Publish a package | `packages: write` |
| Create a release / push a tag | `contents: write` |
| Deploy via OIDC | `id-token: write` (plus `contents: read`) |

If none of these jobs exist, the top-level block alone is the complete fix.

### 4.4 Optional hardening (same PR, low cost)

Add `persist-credentials: false` to checkout steps in jobs that never push:

```yaml
- uses: actions/checkout@v4
  with:
    persist-credentials: false
```

This prevents the token from being written into `.git/config` where subsequent steps — including third-party actions — can read it. Include only if it does not break a job that legitimately pushes.

---

## 5. Test Verification

### 5.1 Static regression test

```python
# tests/test_workflow_permissions.py
from pathlib import Path
import yaml

WORKFLOWS = Path(".github/workflows")
ALLOWED_TOP_LEVEL = {"contents": "read"}

def _load(f: Path) -> dict:
    # NOTE: PyYAML (YAML 1.1) parses the bare key `on` as boolean True.
    # We never index doc["on"] here, so this is safe; do not "fix" it by
    # adding an `on` lookup without a custom loader.
    return yaml.safe_load(f.read_text())

def test_every_workflow_declares_permissions():
    files = sorted(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml")))
    assert files, "no workflow files discovered — check the glob path"
    for f in files:
        doc = _load(f)
        assert "permissions" in doc, f"{f.name}: missing top-level permissions block"

def test_no_write_all():
    for f in WORKFLOWS.glob("*.y*ml"):
        perms = _load(f).get("permissions")
        assert perms != "
\n