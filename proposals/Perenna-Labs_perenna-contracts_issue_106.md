# Bounty Proposal: Perenna-Labs/perenna-contracts#106 - [Bounty: $50] Pin GitHub Actions to commit SHAs in the CI workflow\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $50] Pin GitHub Actions to commit SHAs in the CI workflow

## Architecture (Opus 5.5)
Proceed with surgical fix.

## Code Fix (SWE-2)
I need to update GitHub Actions to use commit SHAs instead of version tags for security, but I can't find the workflow files in the codebase. I don't know which files to modify or which specific actions are being used, so I can't proceed with generating a patch.

Crucially, I must not fabricate commit SHAs for action versions, as that's a security risk and violates the principle of verifiable correctness. Instead, I'll state my limitation—that I can't see workflow files—and provide a deterministic method for users to resolve the correct SHAs, like using `gh api` or `git ls-remote`. I'll then offer a template patch demonstrating the transformation from tag to SHA, including the standard inline comment convention for readability.

I can't provide a fully verified patch yet because I don't have the workflow files, and I must resolve commit SHAs deterministically, not by hallucination. I'll provide a script to resolve these SHAs and a template for the patch, clearly marking it as pending verification.

I need to provide a unit test to verify that all `uses:` in the workflow files are pinned to specific SHAs, not just tags. I'll create a `resolve-shas.sh` script to help users find these SHAs, but I'll only include the `actions/checkout` SHA directly, noting it's well-documented and advising verification via `git ls-remote`. For other actions, I'll use placeholders and rely on the script for resolution to avoid hallucinating incorrect SHAs, adhering to anti-hallucination rules.

I've found that `git ls-remote` returns the tag SHA, but for annotated tags, I need to use `^{}` to get the commit SHA. GitHub Actions tags are often annotated, so I should use `^{}`. A better approach is to pin actions to specific release SHAs rather than moving major tags like `v4`. I'll add a test to `tests/test_actions_pinning.py` to ensure all actions are pinned to SHAs, checking for the `@` symbol and a 40-character hex string.

I'm considering adding a placeholder SHA for the `foundry-rs/foundry-toolchain` action, as I don't have the exact SHA and don't want to guess. I also need to confirm the actual workflow file names, as the ones I've used are assumptions. Additionally, I'm thinking about including a separate workflow to enforce pinned actions and mentioning `dependabot.yml` for automated updates, which is a good practice for reviewers.

I'm marking status labels as `STATUS: BLOCKED_NEEDS_CONTEXT` until workflow contents and resolved SHAs are provided. The test file itself is verifiable via `ast.parse`, but RULE-002 requires sandbox verification before marking `READY_FOR_EGRESS`. Since I lack a sandbox, I'll provide commands for users to run in their CI/sandbox. I'll also add a brief note about PATs vs. GitHub Apps for write actions, specifying that PRs must be opened via an authenticated user PAT if the pipeline pushes to a public repo.## Status: `BLOCKED — NEEDS_CONTEXT` (cannot emit `READY_FOR_EGRESS`)

Per **RULE-002 / RULE-003**, I will not mark this patch ready because:

1. **Workflow file contents were not provided.** I don't have visibility into `Perenna-Labs/perenna-contracts`' `.github/workflows/` — filenames, action inventory, or current refs are unknown. Emitting "exact lines" without the source is fabrication.
2. **Commit SHAs must be resolved live, not recalled.** Pinning to a hallucinated SHA is a supply-chain incident worse than the tag-pinning it fixes. SHAs below are placeholders + one well-known value; all must be verified with the resolver script before egress.

**Paste the contents of `.github/workflows/*.yml` and I will emit the final exact diff.**

---

## 1. SHA resolver (run before patching)

```bash
#!/usr/bin/env bash
# resolve-shas.sh — emits "repo@<40-hex-sha>  # <tag>" for every action ref found
set -euo pipefail

grep -rhoE 'uses:\s*[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[^[:space:]#]+' .github/workflows/ \
  | sed -E 's/uses:\s*//' | sort -u | while read -r ref; do
    repo="${ref%@*}"; tag="${ref#*@}"
    # Peel annotated tags to the underlying commit
    sha=$(git ls-remote "https://github.com/${repo}" "refs/tags/${tag}^{}" | awk '{print $1}')
    [ -z "$sha" ] && sha=$(git ls-remote "https://github.com/${repo}" "refs/tags/${tag}" | awk '{print $1}')
    echo "${repo}@${sha}  # ${tag}"
done
```

## 2. Transformation pattern (canonical diff form)

```diff
-      - uses: actions/checkout@v4
+      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

-      - uses: foundry-rs/foundry-toolchain@v1
+      - uses: foundry-rs/foundry-toolchain@<RESOLVED_SHA> # <release tag>
         with:
           version: nightly

-      - uses: actions/setup-node@v4
+      - uses: actions/setup-node@<RESOLVED_SHA> # <release tag>
```

Convention: `repo@<full-40-hex-sha>` with the human-readable tag as a trailing comment (required so Dependabot and reviewers can map the pin). **No tag, branch, or short-sha refs may remain.**

## 3. Regression test — `tests/test_actions_pinned.py`

This is the enforceable assertion that makes the bounty verifiable:

```python
import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")
USES_RE = re.compile(r"uses:\s*([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DOCKER_DIGEST_RE = re.compile(r"^docker://\S+@sha256:[0-9a-f]{64}$")


def _uses_refs():
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        for lineno, line in enumerate(wf.read_text().splitlines(), 1):
            m = USES_RE.search(line)
            if m:
                yield wf.name, lineno, m.group(1)


def test_all_actions_pinned_to_full_commit_sha():
    offenders = []
    for fname, lineno, ref in _uses_refs():
        if ref.startswith("./"):                 # local composite action
            continue
        if DOCKER_DIGEST_RE.match(ref):          # docker actions pinned by digest
            continue
        if "@" not in ref or not FULL_SHA_RE.match(ref.rsplit("@", 1)[1]):
            offenders.append(f"{fname}:{lineno} -> {ref}")
    assert not offenders, "Actions not pinned to full commit SHAs:\n" + "\n".join(offenders)


def test_pinned_refs_carry_version_comment():
    missing = []
    for wf in sorted(WORKFLOWS.glob("*.y*ml")):
        for lineno, line in enumerate(wf.read_text().splitlines(), 1):
            if USES_RE.search(line) and "#" not in line and not line.strip().startswith("#"):
                m = USES_RE.search(line)
                if m and FULL_SHA_RE.match(m.group(1).rsplit("@", 1)[-1]):
                    missing.append(f"{wf.name}:{lineno}")
    assert not missing, f"SHA-pinned refs missing '# vX.Y.Z' comment: {missing}"
```

Verify in sandbox before egress:

```bash
python -c "import ast; ast.parse(open('tests/test_actions_pinned.py').read())"   # RULE-002 gate
pytest tests/test_actions_pinned.py -q                                          # must FAIL pre-patch, PASS post-patch
```

## 4. Companion: `.github/dependabot.yml` (keeps SHA pins updatable — reviewers expect this)

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

---

## To complete the surgical patch, send me:

1. Contents of every file in `.github/workflows/` (or the repo tree of that dir).
2. Output of `resolve-shas.sh` — or confirm you want me to pin each action to the **latest release tag's commit** rather than the floating major tag's current commit (recommended: latest release).

**Egress note (RULE-001):** when this pipeline opens the PR on the public repo, push it via an authenticated user PAT — GitHub App tokens stay confined to cloning/internal actions.\n