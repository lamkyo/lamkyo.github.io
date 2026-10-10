# Bounty Proposal: Custos-Labs/custos#45 - [Bounty: $40] Exclude planning documents from the reviewability file count\n\n## Locate the job

```bash
grep -rln "reviewability\|numstat" .github/workflows/
```

Expect one step doing roughly `git diff --name-only "$base"...HEAD | wc -l` and `git diff --numstat ...`. Replace it with a pathspec-exclusion implementation — do **not** extend a `grep -v` filter (renames print as `{old => new}/path` and a regex on numstat output will misfire; git-level pathspecs handle this correctly).

## Patch: `.github/workflows/<file>.yml`

```yaml
- name: Assess reviewability
  env:
    BASE: ${{ github.event.pull_request.base.sha }}
  run: |
    set -euo pipefail

    # Requires >=1 non-exclude pathspec ('.') or git exits with
    # "fatal: There is nothing to exclude from by :(exclude) patterns"
    EXCLUDES=(
      ':(exclude)pnpm-lock.yaml'
      ':(exclude)**/pnpm-lock.yaml'
      ':(exclude)**/dist/**'
      ':(exclude)planning/**'
      # ':(exclude)docs/**'   # uncomment on maintainer sign-off
    )

    files_total=$(git diff --name-only "$BASE"...HEAD | wc -l | tr -d ' ')
    files_reviewable=$(git diff --name-only "$BASE"...HEAD -- . "${EXCLUDES[@]}" | wc -l | tr -d ' ')
    added=$(git diff --numstat "$BASE"...HEAD -- . "${EXCLUDES[@]}" \
      | awk '$1 ~ /^[0-9]+$/ {a+=$1} $2 ~ /^[0-9]+$/ {d+=$2} END {print a+d+0}')

    {
      echo "- Changed files (total): ${files_total}"
      echo "- Reviewable files: ${files_reviewable}"
      echo "- Reviewable lines changed: ${added}"
    } >> "$GITHUB_STEP_SUMMARY"

    # Preserve existing thresholds; apply to the *reviewable* numbers.
    if [ "$added" -gt 500 ] || [ "$files_reviewable" -gt 40 ]; then
      echo "::warning title=Large change::${files_reviewable} reviewable files (${files_total} total incl. generated/planning), ${added} changed lines — consider splitting."
    fi
```

If you'd rather keep it a one-liner diff against the current code, the minimal change is:

```diff
- added=$(git diff --numstat "$base"...HEAD -- . ':(exclude)pnpm-lock.yaml' ':(exclude)**/dist/**' | awk '{s+=$1+$2} END {print s+0}')
+ added=$(git diff --numstat "$base"...HEAD -- . ':(exclude)pnpm-lock.yaml' ':(exclude)**/dist/**' ':(exclude)planning/**' | awk '{s+=$1+$2} END {print s+0}')
```

…but gate the "large change" note on a filtered file count too, otherwise a planning-only PR that creates many `planning/issues/*.md` files could still trip a file-count branch of the condition.

## Edge cases

| Case | Handling |
|---|---|
| Shell quoting | `':(exclude)...'` **must** be quoted — unquoted parens are a bash syntax error |
| No positive pathspec | `-- .` is required alongside excludes; without it git fatals |
| `planning/issues/*.md` | `planning/**` covers nested dirs (pathspec globs cross `/` by default) |
| Binary files | numstat emits `-` for add/del; the `^[0-9]+$` awk guards coerce to 0 instead of garbage |
| Empty diff | `END {print a+d+0}` returns `0`, not empty string — safe under `set -u` and `-gt` |
| Renames into/out of `planning/` | Pathspec filtering happens inside git; correct either direction (grep would miss `{old => new}` syntax) |
| `docs/**` | Left commented — issue says "if maintainers agree"; flipping it is a one-line change |
| Nested `pnpm-lock.yaml` | Added `**/pnpm-lock.yaml` — root-only exclusion is a latent bug in the current impl (harmless but free to fix) |

## Verify locally before pushing

```bash
base=$(git merge-base HEAD origin/main)

# Simulate: only planning/ROADMAP.md touched → expect 0 / 0
git diff --name-only "$base"...HEAD -- . ':(exclude)planning/**' | wc -l
git diff --numstat  "$base"...HEAD -- . ':(exclude)planning/**' | awk '{s+=$1+$2} END{print s+0}'

# Simulate: 700-line src/ change → expect note fires
git checkout -b test/big && yes 'x' | head -700 >> src/dummy.ts && git add -A && git commit -m t
git diff --numstat "$base"...HEAD -- . ':(exclude)planning/**' | awk '{s+=$1+$2} END{print s+0}'
```

## Acceptance mapping

1. **planning-only edit → no note**: `added=0`, `files_reviewable=0` ✅
2. **700-line source change → note fires**: `added≥700 > 500` (adjust to repo's real threshold) ✅
3. **Job passes**: `set -euo pipefail` + awk always printing a number; exit 0 since the note is `::warning::`, not `exit 1` ✅

One trade-off to flag in the PR description: anything committed under `planning/` is now invisible to the size heuristic. That's consistent with `.dockerignore` treating it as non-shipping, but worth stating explicitly so maintainers sign off on the same scope.\n