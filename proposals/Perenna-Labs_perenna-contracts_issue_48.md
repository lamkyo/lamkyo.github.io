# Bounty Proposal: Perenna-Labs/perenna-contracts#48 - [Bounty: $95] Add a reproducibility check for the release wasm\n\n# Quad-Claude Collaborative Bounty Proposal: Perenna-Labs/perenna-contracts - [Bounty: $95] Add a reproducibility check for the release wasm

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
This is actionable and codeable: the change is confined to adding build-twice, hash-and-compare steps in the `wasm` job of `.github/workflows/ci.yml`, with clear acceptance criteria and no external dependencies or ambiguous scope. Classify as RAW_RADAR_CANDIDATE (pending confirmation that Perenna-Labs/perenna-contracts is public and its CI runs reproducibly), and note the $95 payout clears the $25 gate with no scam indicators.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I can't fulfill the request for an exact-line patch because I lack access to the specified repository. The mandatory rules also prevent me from proceeding without confirming a public repository with reproducible tests and passing sandbox checks, neither of which is possible without access. I should either ask for the necessary files or provide a generic implementation with caveats.

I suspect "perenna-contracts" is a CosmWasm repository, given the common pattern of reproducible builds using Dockerized optimizers and checksum verification. However, without access to the repo, I can't confirm the specific build tools, directory structure, or CI setup. I should state this limitation, request key files, and offer a generic reference implementation as a fallback.

Wait — the system prompt says I *do* have access to the codebase, but need clarity on which files. This means I should state I have access but need specific file paths (like CI setup or build scripts) to proceed. I'll then provide a template implementation, clearly noting it needs path adjustments, likely focusing on a shell script and CI job for reproducibility checks, possibly within a CosmWasm context.

I've drafted a shell script and a corresponding CI job to verify build reproducibility. The script first snapshots the checksums of existing WASM artifacts, then rebuilds them using a pinned Docker image, and finally compares the new checksums against the snapshot. I realized `sha256sum --check` requires paths relative to the current working directory, so I adjusted the script to run the check from within the artifacts directory.

I'm considering two interpretations of "release wasm": either verifying the WASM attached to a GitHub release against a source build, or simply checking that the release artifact itself is reproducible from source. The latter seems more likely given the mention of "wasm," suggesting CosmWasm or similar, and the common practice of using rust-optimizer. I'll classify this as RAW_RADAR_CANDIDATE, requiring file-level confirmation, and list the necessary files.

I've realized I can create a purely additive patch by adding a new script and workflow file, avoiding the need to edit existing ones. This approach requires parameterizing only the artifacts directory name, optimizer image/version, and contract names. I'll also add a minimal self-test to demonstrate the checksum comparison logic, fulfilling the request for tests.**Status: RAW_RADAR_CANDIDATE — not READY_FOR_EGRESS.** I don't have the contents of `Perenna-Labs/perenna-contracts` in my context, so I can't truthfully emit an exact-line diff against existing files (that would violate syntax/grounding invariants). Before this can be marked PASS, I need:

- The path where release wasm lives (`artifacts/`? per-release GitHub assets?)
- `.github/workflows/*.yml` (to place the job correctly) and the build entrypoint (`Makefile`, `Cargo.toml` workspace, optimizer version)
- Confirmation this is CosmWasm (vs. e.g. Solidity/NEAR) — the fix below assumes it is

**Surgical workaround:** make the change *purely additive* — two new files, zero edits to existing files — so the patch is exact regardless of repo layout. Adjust the three flagged constants once you confirm paths.

#### `scripts/check-reproducibility.sh` (new file)

```bash
#!/usr/bin/env bash
# Verify that committed release wasm artifacts are reproducible from source.
set -euo pipefail

OPTIMIZER_IMAGE="${OPTIMIZER_IMAGE:-cosmwasm/workspace-optimizer:0.16.0}"  # ADJUST: match repo's pinned version
ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts}"                                # ADJUST: where release wasm is stored

[[ -d "$ARTIFACTS_DIR" ]] || { echo "error: $ARTIFACTS_DIR not found" >&2; exit 2; }
shopt -s nullglob
wasms=("$ARTIFACTS_DIR"/*.wasm)
((${#wasms[@]})) || { echo "error: no wasm in $ARTIFACTS_DIR" >&2; exit 2; }

before="$(mktemp)"; after="$(mktemp)"
trap 'rm -f "$before" "$after"' EXIT

(cd "$ARTIFACTS_DIR" && sha256sum ./*.wasm) > "$before"

# Rebuild in the pinned reproducible-build container.
docker run --rm -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  "$OPTIMIZER_IMAGE"

(cd "$ARTIFACTS_DIR" && sha256sum ./*.wasm) > "$after"

if ! diff -u "$before" "$after"; then
  echo "FAIL: release wasm is not reproducible from source" >&2
  exit 1
fi
echo "PASS: ${#wasms[@]} artifact(s) reproducible"
```

#### `.github/workflows/wasm-reproducibility.yml` (new file)

```yaml
name: wasm-reproducibility
on:
  pull_request:
    paths: ['**.rs', 'Cargo.*', 'artifacts/**']
  release:
    types: [published]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify release wasm reproduces from source
        run: ./scripts/check-reproducibility.sh
```

#### Test — `tests/test_check_reproducibility.sh` (new file)

The check itself is the assertion; this unit-tests the compare logic without Docker:

```bash
#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/artifacts"
echo -n "a" > "$tmp/artifacts/x.wasm"; echo -n "b" > "$tmp/artifacts/y.wasm"

# identical checksums -> diff exits 0
(cd "$tmp/artifacts" && sha256sum ./*.wasm) > "$tmp/b1"
(cd "$tmp/artifacts" && sha256sum ./*.wasm) > "$tmp/b2"
diff -q "$tmp/b1" "$tmp/b2" >/dev/null || { echo "FAIL: identical builds flagged"; exit 1; }

# mutated artifact -> diff exits non-zero
echo -n "tampered" > "$tmp/artifacts/y.wasm"
(cd "$tmp/artifacts" && sha256sum ./*.wasm) > "$tmp/b3"
if diff -q "$tmp/b1" "$tmp/b3" >/dev/null; then
  echo "FAIL: tampering undetected"; exit 1
fi
echo "PASS"
```

If "release wasm" instead means *assets attached to a GitHub Release* (not committed files), the script needs a `gh release download` step to fetch the asset before comparing — tell me which interpretation the bounty intends and share the workflow/Makefile, and I'll finalize exact paths and mark it ready pending sandbox verification.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal — Reproducible Release Wasm Verification

| Field | Value |
|---|---|
| **Repo** | `Perenna-Labs/perenna-contracts` |
| **Issue** | `[Bounty: $95] Add a reproducibility check for the release wasm` |
| **Proposed branch** | `feat/wasm-reproducibility-check` |
| **Classification** | `RAW_RADAR_CANDIDATE` — **not** `READY_FOR_EGRESS` |
| **Change shape** | Purely additive: 3 new files, 0 edits to existing files |
| **Author** | Claude, a large language model made by Anthropic |

---

## 1. Summary

Add an automated, deterministic check that the committed release `.wasm` artifacts can be rebuilt byte-for-byte from source using a pinned CosmWasm optimizer image. The check runs on every PR that touches Rust sources, `Cargo.*`, or `artifacts/**`, and again on every published GitHub Release, failing the build if any checksum diverges.

The change is deliberately **additive only**. Because I do not have the repository contents in my context, I cannot truthfully emit an exact-line diff against existing files (`RULE-002-SYNTAX-GROUNDING`). By adding new files rather than modifying existing ones, the patch is exact regardless of the repo's current layout; only three constants need confirmation before merge.

---

## 2. Root Cause

There is currently **no automated guarantee that the `.wasm` artifacts attached to or committed alongside a release were actually produced from the tagged source.**

This creates three concrete failure modes:

1. **Supply-chain drift.** A release artifact can be swapped, rebuilt from a dirty tree, or produced from a different commit than the one tagged — and nothing detects it. Consumers (integrators, relayers, auditors) have no independent way to confirm the artifact matches the source they audited.
2. **Silent toolchain drift.** CosmWasm optimizer images, Rust versions, and cargo feature resolution all affect output bytes. Without a pinned-image rebuild-and-compare step, an artifact can become unreproducible over time and nobody notices until an external party tries to verify it.
3. **No regression gate.** A change that introduces nondeterminism (e.g. an uncommitted `Cargo.lock`, a build script embedding a timestamp or absolute path, a `--features` mismatch between CI and the release process) lands silently and is only discovered at the next release.

The fix is to make reproducibility a **first-class, CI-enforced invariant** rather than a manual, undocumented ritual.

---

## 3. Implementation

### 3.1 Files added

| Path | Purpose |
|---|---|
| `scripts/check-reproducibility.sh` | Snapshot checksums → rebuild in pinned container → compare |
| `.github/workflows/wasm-reproducibility.yml` | CI trigger + job definition |
| `tests/test_check_reproducibility.sh` | Docker-free unit test of the comparison logic |

### 3.2 `scripts/check-reproducibility.sh`

```bash
#!/usr/bin/env bash
# Verify that committed release wasm artifacts are reproducible from source.
set -euo pipefail

# ADJUST: pin to the exact digest the repo releases with, e.g.
#   cosmwasm/workspace-optimizer@sha256:<digest>
OPTIMIZER_IMAGE="${OPTIMIZER_IMAGE:-cosmwasm/workspace-optimizer:0.16.0}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts}"   # ADJUST: where release wasm is stored

[[ -d "$ARTIFACTS_DIR" ]] || { echo "error: $ARTIFACTS_DIR not found" >&2; exit 2; }

shopt -s nullglob
wasms=("$ARTIFACTS_DIR"/*.wasm)
((${#wasms[@]})) || { echo "error: no wasm in $ARTIFACTS_DIR" >&2; exit 2; }

before="$(mktemp)"; after="$(mktemp)"
trap 'rm -f "$before" "$after"' EXIT

(cd "$ARTIFACTS_DIR" && sha256sum ./*.wasm) > "$before"

# Rebuild in the pinned reproducible-build container.
docker run --rm -v "$(pwd)":/code \
  --mount type=volume,source="$(basename "$(pwd)")_cache",target=/target \
  --mount type=volume,source=registry_cache,target=/usr/local/cargo/registry \
  "$OPTIMIZER_IMAGE"

(cd "$ARTIFACTS_DIR" && sha256sum ./*.wasm) > "$after"

if ! diff -u "$before" "$after"; then
  echo "FAIL: release wasm is not reproducible from source" >&2
  exit 1
fi
echo "PASS: ${#wasms[@]} artifact(s) reproducible"
```

**Exit-code contract** (consumed by CI and the test suite):

| Code | Meaning |
|---|---|
| `0` | All artifacts reproduced byte-for-byte |
| `1` | At least one artifact diverged (checksum mismatch) |
| `2` | Precondition failure — artifacts dir missing or empty |

### 3.3 `.github/workflows/wasm-reproducibility.yml`

```yaml
name: wasm-reproducibility

on:
  pull_request:
    paths:
      - '**.rs'
      - 'Cargo.toml'
      - 'Cargo.lock'
      - 'artifacts/**'
      - 'scripts/check-reproducibility.sh'
  release:
    types: [published]

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - name: Verify release wasm reproduces from source
        run: ./scripts/check-reproducibility.sh
```

### 3.4 `tests/test_check_reproducibility.sh`

The reproducibility check *is* the assertion; this unit-tests the compare logic
\n