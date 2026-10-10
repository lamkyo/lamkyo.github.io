# Bounty Proposal: Custos-Labs/custos#35 - [Bounty: $75] Make a failing `pnpm lint` fail the architecture job\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $75] Make a failing `pnpm lint` fail the architecture job

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Verdict: ACTIONABLE — codeable, well-scoped, and correctly diagnosed.**

The pipeline `pnpm lint 2>&1 | tee lint.log | grep -q "must not import infrastructure"` returns `grep`

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I can't write a surgical, exact-lines diff for `Custos-Labs/custos` — that repo isn't in my available codebase context, and per **RULE-003** this stays `RAW_RADAR_CANDIDATE` until the actual files are confirmed. A blind patch to a CI workflow would also fail **RULE-002** grounding.

To produce the patch, I need:

- `.github/workflows/*.yml` — specifically the file defining the **architecture job**
- Root `package.json` (`scripts.lint`) and `pnpm-workspace.yaml`
- Any invoked scripts/composite actions (e.g. `scripts/arch*.sh`, `.github/actions/*`)

## Likely fix patterns (templates, not verified)

The issue title strongly implies the lint step's exit code is being swallowed. The three most common causes:

```diff
 # 1. Step-level suppression
       - name: Lint
-        continue-on-error: true
         run: pnpm lint
```

```diff
 # 2. Shell-level suppression
       - name: Lint
-        run: pnpm lint || true
+        run: pnpm lint
```

```diff
 // 3. package.json script swallowing the exit code
-    "lint": "eslint . || true"
+    "lint": "eslint ."
```

Also check whether `pnpm -r lint` runs under `--no-bail`, or whether a later command in the same `run:` block overwrites the exit status.

## Suggested verification additions

```bash
# RULE-002 gate: lint the workflow itself before egress
actionlint .github/workflows/<file>.yml
```

```python
# Example assertion for a CI regression test
def test_lint_step_fails_job(workflow):
    step = find_step(workflow, job="architecture", name_contains="lint")
    assert step.get("continue-on-error") is not True
    assert "|| true" not in step["run"]
```

Paste the workflow YAML and `package.json` and I'll produce the exact diff with line numbers and the matching test.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Quality Verification Review

> **Status: `DRAFT — BLOCKED_FOR_VERIFICATION`** — Not cleared for egress.
> **Radar Class:** `RAW_RADAR_CANDIDATE` (RULE-003 — target repo files unconfirmed)

| Field | Value |
|---|---|
| Repo | `Custos-Labs/custos` |
| Issue | [Bounty: $75] Make a failing `pnpm lint` fail the architecture job |
| PR Author Account | User PAT (RULE-001 — GitHub App restricted to clone/scout) |
| Gate Status | RULE-002 **FAIL** (no patch exists to lint) · RULE-003 **HOLD** |

---

## 1. Root Cause Analysis (Hypothesized — Unverified)

The architecture job reports green while `pnpm lint` exits non-zero. The exit code is being swallowed at one of four layers, ordered by likelihood:

1. **Step level** — `continue-on-error: true` on the lint step marks the step as "neutral," allowing the job to succeed.
2. **Shell level** — `run: pnpm lint || true` or a trailing command in a multi-line `run:` block overwrites `$?`.
3. **Script level** — `package.json` defines `"lint": "eslint . || true"`, or `pnpm -r lint` runs with `--no-bail`.
4. **Job topology** — lint runs in a sibling job that the architecture job does not `needs:`-gate on, so its failure never propagates.

Layer cannot be confirmed without the workflow YAML. **No claim of root cause is made in the PR body until confirmed.**

## 2. Implementation Plan (Templates — Not a Patch)

```diff
 # Fix A — remove step-level suppression
       - name: Lint
-        continue-on-error: true
         run: pnpm lint
```

```diff
 # Fix B — remove shell-level suppression
-        run: pnpm lint || true
+        run: pnpm lint
```

```diff
 // Fix C — package.json
-    "lint": "eslint . || true"
+    "lint": "eslint ."
```

```diff
 # Fix D — if lint lives in a sibling job
   architecture:
+    needs: [lint]
     runs-on: ubuntu-latest
```

Exact diff with line numbers will be produced once source files land (§5).

## 3. Test & Verification Plan

**Pre-egress gate (RULE-002 — mandatory):**
```bash
actionlint .github/workflows/<file>.yml   # workflow syntax
python -c "import json; json.load(open('package.json'))"  # if Fix C applies
```

**Post-merge verification (proof the fix works):**
1. Canary branch: introduce a deliberate lint violation → open PR.
2. Assert: architecture job goes **red**, check run reports failure.
3. Revert canary; assert architecture job returns green.

```python
# CI regression assertion (adapt to repo's test harness)
def test_lint_step_fails_job(workflow):
    step = find_step(workflow, job="architecture", name_contains="lint")
    assert step.get("continue-on-error") is not True
    assert "|| true" not in step["run"]
```

## 4. Invariant Compliance Checklist

| Rule | Requirement | Status |
|---|---|---|
| RULE-001 | PR opened via User PAT; App used only for clone/quota | ✅ Planned compliant |
| RULE-002 | Patch must pass `actionlint`/`json.parse` before READY | ⛔ **BLOCKED** — no patch |
| RULE-003 | Elevate only with confirmed repo + reproducible suite | ⚠️ `RAW_RADAR_CANDIDATE` |

## 5. Required Inputs to Unblock

- `.github/workflows/*.yml` — file defining the **architecture** job
- `package.json` (root `scripts.lint`) and `pnpm-workspace.yaml`
- Invoked composite actions / scripts (`scripts/arch*.sh`, `.github/actions/*`)

## 6. Proposed PR Metadata (activated post-verification)

**Title:** `ci: propagate pnpm lint exit code in architecture job`
**Body skeleton:** root cause w/ line refs → minimal diff → canary-PR evidence (red→green screenshots) → `Closes #<issue>` + bounty tag.

---

**Lead sign-off:** Proposal packaged but **rejected for submission** in current state. Shipping a templated diff as a fix would violate RULE-002 (unverified patch) and RULE-003 (unconfirmed repo). Forward to SWE-2 for exact-lines patch once the three inputs in §5 are provided, then re-run this gate.
\n