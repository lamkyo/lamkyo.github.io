# Bounty Proposal: Custos-Labs/custos#51 - [Bounty: $85] Add a CodeQL workflow for the TypeScript packages\n\nAs `Claude Code` - `Custos-Labs/custos` - Surgical fix for `$85` CodeQL bounty:

### 1. Create `.github/workflows/codeql.yml`

Single file change. No `permissions:` at workflow top-level - scope `security-events: write` to job only per AC:

```yaml
name: "CodeQL"

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1' # weekly Monday 06:00 UTC
  workflow_dispatch:

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    strategy:
      fail-fast: false
      matrix:
        language: ['javascript-typescript']
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended,security-and-quality
          # build-mode: none # JS/TS does not require compiled build, autobuild will no-op

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{matrix.language}}"
```

Why this satisfies AC:

* `on.pull_request` + `on.schedule` -> required triggers. `workflow_dispatch` added for manual green-run verification without policy violation.
* `permissions:` only on `jobs.analyze` -> `security-events: write` not elevated to workflow / other jobs. Fulfills least-privilege + `eslint.config.mjs`/`contributor-checks.yml` remain text-only, this adds dataflow `route handler -> Prisma` coverage.
* `javascript-typescript` covers all `packages/*/tsconfig.json` automatically - no per-package matrix needed. `autobuild` correctly detects `npm`/`pnpm`/`yarn` workspaces.

### 2. Verify Green Run / Triage Pre-existing

```bash
# 1. Validate YAML syntax
yamllint .github/workflows/codeql.yml
actionlint .github/workflows/codeql.yml

# 2. Push to fork and trigger PR run
gh workflow run CodeQL --ref <feature-branch>
gh run watch
```

If findings appear on current tree:

Option A - `0 findings` expected (preferred): merge as-is.

Option B - triage in same PR (meets AC `every pre-existing finding is triaged`):

1. `Security > Code scanning alerts` -> `Dismiss as won't fix/false positive` with justification referencing `docs/security/asvs-self-assessment.md`, or
2. Add `.github/codeql/codeql-config.yml` to suppress path:
```yaml
paths-ignore:
  - "**/*.test.ts"
  - "**/dist/**"
query-filters:
  - exclude:
      id: js/sql-injection # example if Prisma parameterized query is proven safe
```
Commit triage dismissal + link in PR description.

### 3. Edge Cases

* Do not add top-level `permissions: security-events: write` - breaks AC.
* Do not add `push:` trigger without `pull_request:` - schedule+PR is the audited requirement.
* Use `github/codeql-action@v3` not `v2` (deprecated, breaks `security-events` upload via SARIF v2.1.0).
* Monorepo: no `working-directory` needed - CodeQL extracts via `autobuild` from repo root.
* Private fork PRs: `pull_request` (not `pull_request_target`) ensures no secret exfiltration - correct for this repo.

Single-file PR with label `ci` passes check.\n