# Bounty Proposal: Perenna-Labs/perenna-contracts#49 - [Bounty: $65] Add `workflow_dispatch` and a manual dry-run job\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $65] Add `workflow_dispatch` and a manual dry-run job

## Architecture (Opus 5.5)
Proceed with surgical fix.

## Code Fix (SWE-2)
I'm tasked with adding `workflow_dispatch` and a manual dry-run job to the `Perenna-Labs/perenna-contracts` repository. However, I can't fulfill the request for "exact lines" and a precise diff because I don't have access to the repository's files. The prompt's "MANDATORY REFLEXION PREVENTIVE INVARIANTS" also seem to conflict with directly writing to external repos without proper checks, which I can't perform without access.

I'm encountering a conflict between the rules: RULE-003 classifies this as RAW_RADAR_CANDIDATE because I can't confirm the repo is public with reproducible tests, and RULE-002 prevents me from marking any patch as READY since I can't run sandbox checks. The presence of "Bounty: $65" suggests an automated bounty-hunting workflow, which these rules seem designed to constrain. I'll provide a generic, unverified draft of the workflow changes instead of an exact diff.

I'm considering how to best implement the dry-run job for the Perenna contracts repository, noting that it likely involves Hardhat or Foundry. I'll also address the "unit test assertions" by demonstrating a Python test for the workflow file, specifically checking for `workflow_dispatch` and the dry-run job's `if:` condition, while accounting for PyYAML's parsing of `on:` as a boolean. My response will include a status header and specify what information is needed to elevate the classification.

I'm drafting a generic Node/Hardhat CI workflow and a Python validation test for the YAML. The test will lint the YAML and assert required keys, serving as a deterministic check for RULE-002. I'm also noting that any PR to the public repo must go through a PAT user account, not the GitHub App, to comply with RULE-001.## Status: `RAW_RADAR_CANDIDATE` — not elevated

Per **RULE-003**, I cannot classify this as a `VERIFIABLE_CODE_ISSUE`: I have no confirmed checkout of `Perenna-Labs/perenna-contracts`, so I can't see the existing workflow files, the toolchain (Hardhat vs Foundry vs npm), or whether reproducible tests exist. Per **RULE-002**, nothing below is marked `PASS`/`READY_FOR_EGRESS` — it's a draft patch pending a sandbox lint. Per **RULE-001**, any eventual PR to this public repo must egress via a PAT user account, not a GitHub App.

## What I need to elevate this

- Path and contents of the target workflow (`.github/workflows/*.yml`)
- The deploy/mutating steps the dry-run should skip
- Toolchain confirmation (Foundry vs Hardhat)

## Draft patch (UNVERIFIED — line numbers are placeholders)

Typical surgical change to `.github/workflows/ci.yml`:

```diff
 on:
   push:
     branches: [main]
   pull_request:
+  workflow_dispatch:
+    inputs:
+      dry_run:
+        description: "Dry run only (skip deploy/mutating steps)"
+        required: false
+        type: boolean
+        default: true
```

```diff
 jobs:
+  dry-run:
+    name: Manual dry run
+    if: ${{ github.event_name == 'workflow_dispatch' && inputs.dry_run }}
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@v4
+        with:
+          node-version: 20
+          cache: npm
+      - run: npm ci
+      - name: Compile + test (no deploy)
+        env:
+          DRY_RUN: "true"
+        run: |
+          npx hardhat compile
+          npx hardhat test
+
   deploy:
     if: github.ref == 'refs/heads/main' && github.event_name == 'push'
     ...
```

For Foundry, swap the run block for `forge build` / `forge test` with `foundry-rs/foundry-toolchain@v1`.

## Deterministic check (satisfies RULE-002 when run in sandbox)

```python
# tests/test_workflow_dispatch.py
import yaml, pathlib

WF = pathlib.Path(".github/workflows/ci.yml")

def test_workflow_dispatch_and_dry_run_job():
    doc = yaml.safe_load(WF.read_text())
    triggers = doc.get("on") or doc.get(True)  # PyYAML parses `on:` as bool True (YAML 1.1)
    assert "workflow_dispatch" in triggers
    assert triggers["workflow_dispatch"]["inputs"]["dry_run"]["type"] == "boolean"
    job = doc["jobs"]["dry-run"]
    assert "workflow_dispatch" in job["if"]
```

Run `python -m pytest tests/test_workflow_dispatch.py` plus `actionlint .github/workflows/ci.yml` — both must pass before this patch can be marked READY.

Share the actual workflow file contents and I'll produce the exact-line diff.\n