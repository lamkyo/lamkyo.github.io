# Bounty Proposal: Custos-Labs/custos#49 - [Bounty: $90] Guard against new quarantined packages\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $90] Guard against new quarantined packages

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable: the fix is a CI script that reads the quarantine list from a single machine-readable source and fails when a workspace package's `build`/`test`/`typecheck`/`lint` scripts are no-ops without being listed, plus a per-package TypeScript file count — all deterministically checkable against the current tree. Codeable since it only requires editing `eslint.config.mjs`/`docs/QUARANTINE.md` and a CI workflow step with existing pnpm workspace tooling.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
## Root Cause Analysis

The drift risk has three independent failure modes, all sharing one root cause: **the quarantine list is prose, not data**.

1. `docs/QUARANTINE.md` is human-readable only — nothing machine consumes it, so adding a third quarantined package is invisible to CI.
2. `eslint.config.mjs`'s `ignores` is a *second, manually-synced copy* of the same list — double-bookkeeping guaranteed to diverge.
3. No-op scripts (`"build": "true"`, `"test": "echo skipped"`) exit 0, so `pnpm -r build/test/typecheck` is vacuously green. pnpm also silently *skips* packages missing a script, which is an equally invisible hole.

The fix isn't "add a CI check" — it's **make the quarantine list a single source of truth that CI, ESLint, and docs all derive from**.

## Proposed Architecture

### 1. `quarantine.json` (new, root) — the source of truth

```json
{
  "packages": {
    "packages/sessions": {
      "reason": "Scaffold only — no buildable source yet",
      "scripts": ["build", "test", "typecheck", "lint"]
    },
    "packages/verification": {
      "reason": "Scaffold only — no buildable source yet",
      "scripts": ["build", "test", "typecheck", "lint"]
    }
  }
}
```

Keyed by path (stable under renames), and scoped *per-script* — this avoids false positives on packages like fixtures or an eslint-config that legitimately lacks `build`.

### 2. `scripts/check-quarantine.mjs` (new) — deterministic gate

- Enumerates workspace packages by reading `pnpm-workspace.yaml` `packages:` globs and expanding them with `fs.readdirSync` (zero deps, works pre-install; `pnpm ls -r --depth -1 --json` is the fallback if you prefer running post-install).
- Classifies each `build`/`test`/`typecheck`/`lint` script as `real | noop | missing`. No-op detection: split on `&&`/`||`/`;`/`|` and require every segment match a no-op allowlist (`true`, `:`, `exit 0`, `echo …`, `printf …`, `node -e ''`, comments). One-level recursion through `pnpm run <x>` indirection.
- **Symmetric drift check** — this is the bulletproofing:
  - FAIL: a script is `noop`/`missing` but not covered by that package's `scripts` list.
  - FAIL: a script is listed in quarantine but is now `real` → forces stale entries out when a package gets fixed.
- WARN: counts `*.ts`/`*.tsx` per quarantined package (excluding `node_modules`, `dist`, `*.d.ts`) and emits `::warning::N TypeScript files behind quarantine in packages/sessions`.

### 3. `eslint.config.mjs` — consume, don't duplicate

```js
import { readFileSync } from 'node:fs';
const q = JSON.parse(readFileSync(new URL('./quarantine.json', import.meta.url), 'utf8'));
const quarantined = Object.keys(q.packages).map(p => `${p}/**`);
// ...ignores: [...quarantined, ...]
```

Now it's *impossible* to quarantine a package but forget the eslint ignore — that regression class is deleted.

### 4. `.github/workflows/ci.yml` — one step, fail fast

```yaml
- name: Guard quarantined packages
  run: node scripts/check-quarantine.mjs
```

Placed after checkout/setup-pnpm, **before** `pnpm build` so it fails in seconds. Also add `"check:quarantine": "node scripts/check-quarantine.mjs"` to root `package.json` for local repro.

### 5. `docs/QUARANTINE.md` — generated, not authored

Add `node scripts/check-quarantine.mjs --write-docs` that regenerates a marked section (`<!-- QUARANTINE:BEGIN -->…<!-- QUARANTINE:END -->`) with the package table + file counts. The check fails in `--check` mode if the section is stale. Docs can never lie.

## Files Touched

| File | Change |
|---|---|
| `quarantine.json` | New — source of truth |
| `scripts/check-quarantine.mjs` | New — ~120 lines, zero deps |
| `eslint.config.mjs` | Derive ignores from JSON |
| `.github/workflows/ci.yml` | Add guard step |
| `package.json` (root) | Add `check:quarantine` script |
| `docs/QUARANTINE.md` | Generated block + pointer to JSON |

## Edge Cases Handled

- **Staleness both directions** — fixing `sessions` without removing its entry also fails, preventing zombie ignores.
- **Obfuscated no-ops** — unknown script text classifies as `real`, which fails the symmetric check and forces human review rather than silently passing.
- **Missing scripts** — treated as no-ops (pnpm skips them silently; same hole, same gate).
- **JSON malformed** → loud failure, never silent pass.

## Validation Plan (per syntax-grounding invariant)

1. `node --check scripts/check-quarantine.mjs` + `eslint` on touched files — before marking READY.
2. Positive: run on current tree → exit 0, two warnings with file counts.
3. Negative: add `"build": "true"` to another package locally → exit 1.

## What I Need From the Tree

I can't see the actual repo, so to produce the final diff I need: `pnpm-workspace.yaml` (glob format + any negations), current `eslint.config.mjs` ignores block, one quarantined `package.json` (to confirm no-op script style), `ci.yml` job structure, and the CI Node version (determines whether `fs.glob` is safe or I write a manual walker). Note per incident rules: once verified against a reproducible checkout this elevates from RAW_RADAR_CANDIDATE to VERIFIABLE_CODE_ISSUE, and the eventual PR write goes through the authenticated user PAT, not the GitHub App.

---

## 3. Production Code Patch (`swe-2`)
None

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — `guard: make the quarantine list a single source of truth`

**Repo:** `Custos-Labs/custos`
**Issue:** [Bounty: $90] Guard against new quarantined packages
**Role of record:** Delivery & Quality Verification Lead
**Artifact status:** ⚠️ **PROPOSAL / NOT GROUNDED** — see *Verification Status* below before reading anything as a result.

---

## 0. Verification Status (read first)

| Field | Value |
|---|---|
| Radar classification | **RAW_RADAR_CANDIDATE** — not yet elevated to `VERIFIABLE_CODE_ISSUE` |
| Reason | No public checkout has been confirmed against a reproducible test suite in this session; `pnpm-workspace.yaml`, `eslint.config.mjs`, `ci.yml`, and a quarantined `package.json` were not supplied |
| Code Patch (SWE-2) | **None** — no diff was produced or executed |
| Deterministic syntax gate (RULE-002) | **NOT EXECUTED** — no sandbox run of `node --check` / `eslint` has occurred |
| Egress state | **BLOCKED** — nothing here may be marked PASS, READY, or READY_FOR_EGRESS |
| Write path (RULE-001) | Eventual PR creation/merge goes through an **authenticated User PAT**. GitHub App is used only for quota shielding, scouting, cloning, and internal repo actions. |

Everything below is a **design + proposed implementation + verification plan**. Where the proposal says "exit 0" or "exit 1", that is an **expected** result, not an observed one. Elevation to `VERIFIABLE_CODE_ISSUE` requires the artifacts in §9 and a green run of §7.

---

## 1. Root Cause

The drift risk is not "CI lacks a check." It is that **the quarantine list is prose, not data**, and that produces three independent failure modes from one cause:

| # | Failure mode | Mechanism |
|---|---|---|
| 1 | **Invisible third quarantine** | `docs/QUARANTINE.md` is human-readable only. Nothing machine-consumes it, so adding a third quarantined package changes no gate, no exit code, no CI signal. |
| 2 | **Double bookkeeping** | `eslint.config.mjs`'s `ignores` is a *second, hand-synced copy* of the same list. Two copies of a list with no enforcement diverge on a long enough timeline — guaranteed, not probable. |
| 3 | **Vacuous green** | No-op scripts (`"build": "true"`, `"test": "echo skipped"`) exit 0, so `pnpm -r build/test/typecheck` is green while doing nothing. pnpm **also silently skips packages that lack the script entirely** — a second, equally invisible hole with the same symptom. |

The correct fix is not "add a CI check." It is to **collapse the list to one machine-readable source that CI, ESLint, and docs all derive from**, and then make drift in *either* direction a hard failure.

---

## 2. Design: one source of
\n