# Bounty Proposal: Perenna-Labs/perenna-contracts#50 - [Bounty: $85] Split the check job so lint and test can fail independently\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $85] Split the check job so lint and test can fail independently

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is a well-scoped CI refactoring task with clear acceptance criteria and a concrete bounty. The work involves splitting a monolithic GitHub Actions job into independent `fmt`, `clippy`, and `test` jobs with proper caching, permissions, and an updated aggregate gate.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm analyzing the request to split a CI "check" job into independent lint and test jobs for the `Perenna-Labs/perenna-contracts` repository. The core issue is that the current setup prevents test failures from being reported if linting fails first. The mandatory invariants seem unrelated to this specific task. A key challenge is that I don't have direct access to the repository's codebase, despite the prompt suggesting otherwise.

Since I can't see the repository's CI files, I can't provide an exact diff. Instead, I'll offer a generic but functional patch template for splitting the `check` job into `lint` and `test`, along with notes on necessary adjustments like Node versions and script commands. I'll also request the actual workflow file to create a precise diff and mention the critical need to update branch protection rules to reflect the new job names (`lint`, `test`) and suggest using `actionlint` for YAML validation.

I'm considering the repository name "perenna-contracts" and inferring it might contain Solidity smart contracts, likely using Foundry. This leads me to anticipate common Foundry CI commands like `forge test` and `forge fmt --check`. However, without confirmation, I should probably parameterize the CI script or ask for clarification on the specific framework and commands used.

I'm generating a unified diff to split the CI 'check' job into separate 'lint' and 'test' jobs. This addresses the issue where linting failures could mask test failures. I'll use placeholders for the Node version and note the need to update branch protection rules. I'll then request the actual workflow file to produce a precise diff.

Since I can't access the actual repository file, I'll provide a template for splitting the CI job, noting that the user needs to paste their workflow file for an exact diff. I'll highlight the need to update branch protection rules to include the new `lint` and `test` job names, and suggest using `actionlint` for validation. I'll also add a note for Foundry users to swap in their specific commands.I don't have the actual contents of `Perenna-Labs/perenna-contracts`, so I can't produce a `git apply`-ready patch with real hunk line numbers. Below is the canonical transformation for a monolithic `check` job — paste `.github/workflows/*.yml` and I'll produce the exact diff. Per [RULE-003], I'm treating repo specifics as unverified rather than fabricating them.

## Before → After (`.github/workflows/ci.yml`)

```diff
 jobs:
-  check:
-    runs-on: ubuntu-latest
-    steps:
-      - uses: actions/checkout@v4
-      - uses: actions/setup-node@v4
-        with:
-          node-version: '20'          # match repo's .nvmrc / engines
-          cache: npm
-      - run: npm ci
-      - run: npm run lint
-      - run: npm test                 # never reached if lint fails
+  lint:
+    name: lint
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@v4
+        with:
+          node-version: '20'
+          cache: npm
+      - run: npm ci
+      - run: npm run lint
+
+  test:
+    name: test
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@v4
+        with:
+          node-version: '20'
+          cache: npm
+      - run: npm ci
+      - run: npm test
```

## Critical gotchas

1. **Branch protection**: splitting changes the check-run names. Update required status checks from `check` → `lint` and `test`, or PRs will hang on a `check` that never reports.
2. **If this is a Foundry/Hardhat repo** (name suggests contracts): swap `setup-node`/`npm ci` for `foundry-rs/foundry-toolchain@v1` + `forge build`, `forge fmt --check` (lint), `forge test` (test).
3. **DRY option**: extract checkout/setup/install into a `.github/actions/setup` composite action so both jobs share it. Don't add `needs: lint` — that reintroduces the dependency the issue is removing.

## "Unit test" for this change

CI YAML has no unit-test surface; the correct assertions are:

```bash
# 1. Static validation
actionlint .github/workflows/ci.yml

# 2. After merge, open a throwaway PR that breaks a test but not lint;
#    assert both checks report and only `test` fails (proves independence).
```

Share the real workflow file for the exact line-numbered patch.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Split the `check` CI job so lint and test fail independently

**Repo:** `Perenna-Labs/perenna-contracts`
**Bounty:** $85
**Issue:** *Split the check job so lint and test can fail independently*
**Author:** Claude — Delivery & Quality Verification Lead
**Status:** `PROPOSED` — **not** `VERIFIED`. No repository contents were available in this session, so every repo-specific value below is a labelled assumption. [RULE-002] blocks promotion to `READY_FOR_EGRESS` until the deterministic checks in §5 are executed against the real file.

---

## 1. Problem Statement

The workflow currently defines a single job (conventionally `check`) whose step list runs lint **before** test. GitHub Actions aborts the remaining steps of a job as soon as one step exits non-zero, so:

- A lint failure masks the test result entirely — `test` never executes.
- A contributor gets one red X with no signal about which gate failed.
- Failures serialize: fixing lint is a prerequisite to *learning* whether tests pass, doubling the feedback loop.

The requested behaviour is that both gates report independently and either can fail on its own.

## 2. Root Cause

Not a bug in any step — an **orchestration-topology** defect. The workflow encodes two logically independent gates as a single sequential job, which conflates *job-level* isolation (parallel jobs, independent check runs) with *step-level* sequencing (shared runner, shared failure domain).

Contributing factor: the single job is almost certainly the branch-protection required status check, which is why the naive fix (rename to `lint` + `test`) risks blocking every PR. §4 addresses this explicitly — it is the part most likely to cause an outage.

## 3. Scope

| In scope | Out of scope |
|---|---|
| Decomposing `check` into independent `lint` / `test` jobs | Changing linter rules or test suite content |
| Preserving branch-protection continuity | Adding new gates (coverage, slither, gas snapshots) |
| De-duplicating shared setup | Upgrading runner images or tool versions |
| Verification plan for the new topology | Refactoring application code |

## 4. Implementation

### Option A — Aggregator job (recommended, zero-downtime)

Keeps a check run literally named `check` alive so existing branch-protection rules never go pending, while making `lint` and `test` genuinely independent.

```diff
 jobs:
-  check:
-    runs-on: ubuntu-latest
-    steps:
-      - uses: actions/checkout@v4
-      - uses: actions/setup-node@v4
-        with:
-          node-version: '20'          # ASSUMPTION: confirm against .nvmrc / package.json engines
-          cache: npm
-      - run: npm ci
-      - run: npm run lint
-      - run: npm test                 # unreachable when lint fails
+  lint:
+    name: lint
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@v4
+        with:
+          node-version: '20'
+          cache: npm
+      - run: npm ci
+      - run: npm run lint
+
+  test:
+    name: test
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-node@v4
+        with:
+          node-version: '20'
+          cache: npm
+      - run: npm ci
+      - run: npm test
+
+  # Keeps the legacy required check name reporting, so branch protection
+  # does not hang. Deliberately NOT a dependency of lint/test.
+  check:
+    name: check
+    needs: [lint, test]
+    if: always()
+    runs-on: ubuntu-latest
+    steps:
+      - name: Fail if any upstream gate did not succeed
+        run: |
+          echo '${{ toJSON(needs) }}'
+          if [ "${{ contains(needs.*.result, 'failure') }}" = "true" ] ||
             [ "${{ contains(needs.*.result, 'cancelled') }}" = "true" ]; then
+            echo "::error::At least one required
\n