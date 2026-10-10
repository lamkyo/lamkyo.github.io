# Bounty Proposal: Custos-Labs/custos#42 - [Bounty: $50] Stop persisting checkout credentials\n\n# Architecture & Code Fix: Custos-Labs/custos - [Bounty: $50] Stop persisting checkout credentials

## Architecture (Opus 5.5)
## Classification (per RULE-003)

**VERIFIABLE_CODE_ISSUE** — the fix lives entirely in in-repo workflow YAML, and acceptance criteria are testable in CI. One caveat: I don't have direct reads of `ci.yml` / `contributor-checks.yml`, so the inventory below is the authoritative step — do not skip it.

---

## 1. Root Cause

`actions/checkout@v4` defaults `persist-credentials: true`. After checkout it writes:

```
http.https://github.com/.extraheader = AUTHORIZATION: basic <base64(token)>
```

into `.git/config`. Consequences:

- **Exfil surface**: any code executed later in the job can read `.git/config`. `pnpm install` runs arbitrary `postinstall`/`prepare` scripts from third-party packages — a direct supply-chain exfiltration path.
- **`fetch-depth: 0`** isn't itself the vulnerability, but it means the token authorizes *full-history* access and the jobs doing heavy untrusted execution (`dependencies`, `architecture`, `secrets`) are the ones carrying the live credential longest.
- **What `persist-credentials: false` actually does**: checkout still authenticates to fetch (private repos still clone fine); it simply *doesn't leave* the token behind. This distinction drives the entire regression analysis — the only things that break are post-checkout `git` operations that need auth.

---

## 2. Files to Touch

| File | Action |
|---|---|
| `.github/workflows/ci.yml` | Add `persist-credentials: false` to every non-pushing `actions/checkout@v4` step |
| `.github/workflows/contributor-checks.yml` | Same |
| `.github/workflows/*.yml` (all others) | **Read-only audit** — confirm no cross-file assumption (e.g., a release workflow is correctly scoped outside this fix) |

**Pre-flight inventory (mandatory before editing)** — for each checkout step, answer:

1. Does any later step `git push`, `git tag && push`, commit + push, or use `changesets`/`semantic-release`? → **keep credentials**
2. Does any step `git fetch` additional refs *after* checkout? (Only breaks on private repos — confirm repo visibility.)
3. Does checkout use `submodules: true` against private submodules? → needs creds or a `token:` param
4. Does any tool do git-auth implicitly (`pnpm install` of a git-URL dep, `cargo` private registry, `go get` private module)?
5. Trigger audit: `pull_request_target` on `contributor-checks.yml`? Doesn't change the fix but raises the stakes — confirm what untrusted code executes.

---

## 3. Per-Step Decision Matrix

```yaml
# Default — everything that reads/builds/diffs:
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    persist-credentials: false

# Exception — only if a step genuinely pushes:
- uses: actions/checkout@v4
  with:
    persist-credentials: true  # REQUIRED: pushes release tag in step 'Publish'
```

Key fact that makes this safe: **`git diff` against the base branch needs no credentials.** With `fetch-depth: 0`, checkout already fetched all refs locally; the diff runs entirely offline. `gh` CLI calls are unaffected too — they use `GH_TOKEN`/`GITHUB_TOKEN` env vars, not `.git/config`.

---

## 4. Bulletproof Strategy — Layered, Not Just the One-Line Fix

**Layer 1 — The fix** (bounty scope): `persist-credentials: false` on every non-pushing checkout.

**Layer 2 — Least-privilege token** (strongly recommend including; zero regression risk if jobs are read-only):

```yaml
permissions:
  contents: read
```

Top-level on both workflows. Even if a credential *did* leak, it would be worthless for writes. If a job legitimately needs more (e.g., `pull-requests: write` to comment), scope it per-job.

**Layer 3 — Regression guard** (what makes this bulletproof): a runtime assertion step right after checkout in the highest-risk jobs:

```yaml
- name: Assert no persisted credentials
  run: |
    if git config --local --get-regexp 'extraheader|oauth|token' ; then
      echo "::error::Credentials persisted in .git/config"
      exit 1
    fi
```

Cheap, deterministic, catches a future contributor who re-adds a default checkout step. If a job is later added that legitimately persists creds, the guard forces an explicit, reviewed exception rather than a silent regression.

**Alternative (static guard)**: a `check` in `contributor-checks.yml` that greps workflows for checkout steps missing the flag — e.g., a small `yq`-based script asserting every `uses: actions/checkout` block contains `persist-credentials:` — fails the lint job on drift.

**Layer 4 — Operational note (RULE-001)**: when the bounty PR is opened against the public `Custos-Labs/custos` repo, that external write must come from a PAT-authenticated user account — never via a GitHub App.

---

## 5. Regression Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Hidden push in these files (autofix commits, tag pushes) | Low — triage says read/build only | Inventory step 1; grep for `git push`, `changeset publish`, `semantic-release` |
| Post-checkout `git fetch` on private repo | Low | Confirm repo visibility; if private and fetches occur, either persist creds there or fetch via explicit `x-access-token` header |
| Private submodules / git-URL deps in `pnpm install` | Low | Inspect `pnpm-lock.yaml` for `git+` entries; check `submodules:` usage |
| Base-branch ref missing for `git diff` | Very low | `fetch-depth: 0` guarantees local refs; verify the diff step references `origin/${{ github.base_ref }}` or `merge-base` locally |
| Future step re-adds creds silently | Medium (over time) | Layer 3 guard |

---

## 6. Verification Plan

1. `actionlint .github/workflows/*.yml` — syntax + semantics
2. Open the PR; confirm `ci` and `architecture` jobs pass and their `git diff` steps produce identical output vs. a baseline run
3. In a debug run: `cat .git/config | grep -i authorization` → must return nothing
4. Confirm acceptance criteria: `grep -A3 "actions/checkout" .github/workflows/ci.yml .github/workflows/contributor-checks.yml` shows `persist-credentials: false` on every step not documented as pushing

**Out of scope but worth filing as follow-ups**: SHA-pinning `actions/checkout`, auditing the remaining workflows for the same pattern, and `pull_request_target` review if present. (RULE-006 N/A — no monetary allocation in this task.)

Bottom line: the YAML edit is trivial; the engineering value is in the inventory, the guard step, and the `permissions` block — that's what converts a one-off bounty patch into a durable invariant.

## Code Fix (SWE-2)
None\n