# Bounty Proposal: Perenna-Labs/perenna-contracts#85 - [Bounty: $85] Document the archival behaviour that produces host errors, not `StreamNotFound`\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $85] Document the archival behaviour that produces host errors, not `StreamNotFound`

## Architecture (Opus 5.5)
I'm analyzing a bounty issue for `Perenna-Labs/perenna-contracts` concerning documentation for archival behavior in a Stellar Soroban smart contract. The $85 bounty exceeds the $25 minimum, and no scam indicators are present. I need to verify the issue's classification as "Actionable" according to RULE-003, as the triage notes the premise requires verification.

I'm digging into Stellar Soroban contracts and how persistent storage TTLs work. It seems archived entries don't return a `StreamNotFound` error; instead, they cause a host trap. The `storage().persistent().has()` and `.get()` methods actually trigger this trap if an entry is archived, because the transaction simulation detects the archived state and returns a `RestoreFootprint` error. The `storage::get_stream` function currently maps `None` to `StreamNotFound`, which looks like a mismatch with this host behavior.

I've realized that archived persistent entries don't return `StreamNotFound`. Instead, they cause a host-level error during simulation, requiring a `RestoreFootprint`, or a storage error on-chain. This means `StreamNotFound` only applies to entries that were never created or were deliberately removed, not archived ones. I need to update the documentation to reflect this distinction and clarify the caller's responsibility to restore archived entries before reading them.

I need to add a cross-reference in `SECURITY.md` to clarify that archived entries causing host errors are expected Soroban behavior, not a bug. Before proceeding, I must verify the `contracts/stream/src/storage.rs` implementation, specifically `get_stream`, constants, and whether `extend_ttl` is used for touch semantics. I also need to confirm that `make check` passes in `.github/workflows/ci.yml` and that no documentation linting jobs will be affected. Crucially, per RULE-003, verification of the code's behavior is a precondition before considering the issue "Actionable."

I'm questioning whether `get_stream` correctly handles archived entries. If `persistent().get` traps on archived keys, then the contract's current mapping of `None` to `StreamNotFound` is incorrect for archived entries. I need to confirm if `persistent().get` traps or returns `None` for archived keys, as this affects the documentation and the bounty issue's premise.

The Soroban host errors when accessing archived persistent entries, returning a host error rather than `None` or `StreamNotFound`. This applies to `get()` and `has()`, and even `extend_ttl` fails on archived entries. Temporary entries, however, disappear and return `None`, leading to `StreamNotFound`. I need to document this distinction and clarify that `StreamNotFound` is only for non-existent or deleted entries, not archived ones.

Archived persistent entries trigger a host-level error, not a contract error code, and the simulation returns `restorePreamble`. The transaction must include a restore operation, after which normal `extend_ttl` resumes. I'll update `SECURITY.md` to reflect this intended Soroban archival behavior and ensure no code changes are made, limiting risk to documentation and CI checks.

The deliverable needs to be a root-cause analysis, file list, phased plan, decision gates, and risk table, presented concisely but completely. I also need to note that I lack direct repository access, so constant values and line numbers are placeholders pending verification, and the plan relies on standard Soroban semantics. The format should be Markdown with headers, concise bullets, and potentially a small table for caller-observable behavior, including a code snippet for the expected pattern.# Bounty Analysis: Perenna-Labs/perenna-contracts — Document archival vs `StreamNotFound`

## Guard Checks (per invariants)

- **Payout gate**: $85 ≥ $25 → **PASS**
- **Scam scan**: no blacklist keywords → **PASS**
- **Classification** (RULE-003): Triaged actionable, but the *premise* is still `RAW_RADAR_CANDIDATE` until verified in-repo. Elevate to `VERIFIABLE_CODE_ISSUE` only after confirming `storage.rs` behavior + a working `make check` suite. The triage caveat is real and must gate all writes.

## Root Cause

This is standard Soroban persistent-storage semantics, and the bounty premise is architecturally sound:

```rust
// Expected pattern in contracts/stream/src/storage.rs
env.storage().persistent()
    .get::<_, Stream>(&DataKey::Stream(id))
    .ok_or(Error::StreamNotFound)  // only reached if key absent from *live* storage
```

- **Never-created / removed key** → `get` returns `None` → contract error `StreamNotFound`. Correct.
- **TTL-lapsed (archived) key** → the host traps *before* contract code runs. `get`/`has`/`extend_ttl` on an archived persistent entry fail at the host layer; simulation surfaces it as a required `restorePreamble` in `SorobanTransactionData`. **`StreamNotFound` is unreachable for archived entries** — contract code cannot observe or catch this.
- **Second-order effect**: "extend TTL on every access" only works while the entry is *live*. Once archived, `extend_ttl` also fails — restore is the only path back. This is worth one line in the docs.

## Files to Touch

| File | Change |
|---|---|
| `contracts/stream/src/storage.rs` | **Read-only.** Verify `get_stream` impl, locate `PERSISTENT_TTL_THRESHOLD`/`PERSISTENT_TTL_EXTEND` exact ledger values, find all `extend_ttl` call sites. (Run `rg PERSISTENT_TTL` — constants may live in `lib.rs`/`ttl.rs`.) |
| `docs/CONTRACT_SPEC.md` | New subsection under §1: **"Archived vs. missing entries"** — caller-observable behavior table (live / never-created → `StreamNotFound` code N / archived → host restore error), the two constants verbatim from source, and the restore-then-read requirement. |
| `SECURITY.md` | One bullet in "Known non-issues": archival host errors are intended Soroban semantics, not a bug — cross-ref to the spec section. Use a relative anchor link matching the repo's existing heading style. |
| `.github/workflows/ci.yml` | **Read-only.** Check whether `check` includes markdown lint/doc-link jobs to run locally before pushing. |

## Execution Strategy

**Phase 0 — Verify (GitHub App token, read-only — RULE-001)**
1. Clone via App auth (scouting/quota shielding only).
2. Confirm the three facts above + locate `Error::StreamNotFound` variant/code (`error.rs`/`errors.rs`).
3. Run `make check` to confirm a reproducible suite exists → elevates to `VERIFIABLE_CODE_ISSUE`.
4. **Decision gate**: if premise is wrong (e.g., `Stream` uses temporary/instance storage → lapsed keys genuinely return `StreamNotFound`), do **not** document a false claim — report and redirect per triage caveat.

**Phase 1 — Implement (PAT-authenticated user account — RULE-001)**
5. Comment intent-to-claim via PAT first (bounty race risk).
6. Docs-only diff; copy constants verbatim from source — never paraphrase ledger counts. If adding wall-clock estimates, label "approx. (assuming ~5s ledgers)".
7. `SECURITY.md` bullet; verify anchor resolves.

**Phase 2 — Validate**
8. `make check` locally; run any doc-lint the `check` job implies. Diff must touch zero `.rs` files → contract regression surface is nil.
9. PR via PAT referencing the issue.

## Risk Table

| Risk | Mitigation |
|---|---|
| Premise false (temp storage, sentinel value) | Phase-0 gate; abort to redirect, never publish false docs |
| Constants moved/renamed | `rg PERSISTENT_TTL` repo-wide before writing values |
| Doc-link/anchor lint in `check` | Inspect CI job; match existing cross-ref format |
| Duplicate hunter claim | PAT comment staking intent before authoring |
| Writing via App → rejected/blocked | All public-repo writes strictly through user PAT |

**Net assessment**: low-risk, docs-only, ~1–2h of real work. The single real failure mode is unverified premise — which is exactly what Phase 0 exists to catch.

## Code Fix (SWE-2)
The user wants surgical production code changes and a git diff patch, but this bounty is documentation-only. The plan explicitly states "Docs-only diff; diff must touch zero `.rs` files." I cannot provide exact lines or a faithful patch because I lack repository access to verify file structures, existing content, or specific error codes and constants mentioned in the plan.

I'm considering adding a unit test for `storage.rs` to verify that `get_stream` returns `StreamNotFound` for non-existent keys, as this would document the contract behavior described in the docs. While I can't provide an exact diff for the documentation changes due to lack of repository access, I can offer the content for insertion, a valid diff format, verification commands, and this unit test. I'll skip the Makefile doc-check addition as it might be too much.

I need to clarify the output format for the user. Since I can't run linters or access the repository, I'll provide the diffs in a template format with `@@` markers and clearly state that they need to be resolved after Phase 0 verification. The markdown content for CONTRACT_SPEC.md and SECURITY.md will be copy-paste ready.

I'm considering a Rust unit test for `storage.rs` to verify `get_stream` returns `StreamNotFound` for non-existent IDs. I'm also realizing that the Soroban test environment might simulate TTL eviction, meaning expired persistent entries could panic rather than return `None`. This suggests a test using `#[should_panic]` could demonstrate this behavior, distinguishing it from the `StreamNotFound` error for never-created streams.

The documentation draft clarifies that an archived entry results in a host trap, not a contract panic like `StreamNotFound`. This distinction is crucial and needs to be reflected in the unit tests. I must gate the `#[should_panic]` test on SDK version, as older SDKs might not trap host errors, and add a note to verify this behavior.

I'm considering how to best represent the `get_stream` test. The exact call signature depends on whether I use the contract client or an internal function, so I'll write it generically with comments. I also need to add a `#[should_panic]` test for TTL expiration, but I'll gate it on the SDK version and add a note to verify its behavior, as older SDKs might not trap host errors.

I'm realizing that `#[should_panic]` is imprecise for host errors in tests, as they manifest as Rust panics. While it works, `env.try_invoke_contract` or clear documentation would be better. Given this uncertainty, I'll add VERIFY markers to the test and a fallback note. For the diff format, I'll provide insertion-ready blocks and a skeleton unified diff with placeholder context, noting that hunk placement needs post-Phase-0 resolution. Appending patches might be mechanically simpler for some files, but for others, like SECURITY.md, I'll provide the content with insertion instructions.

I'm adding a `Makefile`/`just` doc-check snippet to the plan, but I'll keep it to one line to avoid scope creep. I'll also co-locate test files in the existing test module, verifying this placement. The response structure will include a header note about the status, followed by the patch content, diff skeletons, and an egress checklist. I'll use VERIFY markers for items needing post-Phase-0 resolution.

The draft highlights a potential issue with the test environment's handling of expired persistent entries. It notes that older SDK versions might not simulate TTL eviction, causing tests to behave differently on the network versus in local testing. This requires a conditional test and a verification step to ensure consistency.

I'm noting that `client.try_get_stream` returns a nested `Result` type, and the idiomatic assertion for `StreamNotFound` is `Err(Ok(Error::StreamNotFound))`. I'll use this pattern and add a comment. For diffs, I'll use unified format with `<ANCHOR>` placeholders for context lines, clearly marking them as templates to be resolved post-Phase-0. The target length for the output is around 150-200 lines, aiming for completeness without being overly verbose.# SWE-2 Output — Docs Patch + Executable Test Assertions

## Egress status: `DRAFT` — not `READY_FOR_EGRESS`

Per **RULE-003** the premise remains `RAW_RADAR_CANDIDATE` (no repo read performed — I have no live access to `Perenna-Labs/perenna-contracts`). Per **RULE-002** I cannot emit exact-context diff hunks or claim lint-PASS for files I haven't read. Below are **landing-ready artifacts** with numbered `<VERIFY-N>` markers; each maps to a Phase-0 `rg`/`sed` check. Resolve all markers, then run `make check` before marking PASS.

---

## Artifact A — `docs/CONTRACT_SPEC.md` insertion block

Insert under §1 (storage semantics), after the paragraph describing `PERSISTENT_TTL_*` `<VERIFY-1: rg -n "PERSISTENT_TTL" docs/CONTRACT_SPEC.md contracts/stream/src/>`. Substitute real constant names/ledger values verbatim from source — never paraphrase.

```markdown
### Archived vs. missing persistent entries

`Stream` records live in **persistent** storage with a TTL managed via
`PERSISTENT_TTL_THRESHOLD` / `PERSISTENT_TTL_EXTEND` ledgers. <VERIFY-2>
Callers must distinguish three states of a `DataKey::Stream(id)` entry:

| Entry state | `persistent().get()` result | Caller-observable outcome |
|---|---|---|
| Live | `Some(Stream)` | Call proceeds; TTL extended when below threshold |
| Never created / removed | `None` | Contract returns `Error::StreamNotFound` (code `<VERIFY-3>`) |
| Archived (TTL lapsed) | *host trap — contract code never runs* | Simulation fails with a restore-required host error (`restorePreamble` in `SorobanTransactionData`); `StreamNotFound` is **not** emitted |

Implications for integrators:

- **`StreamNotFound` means "does not exist", not "was archived".** The
  contract cannot observe archived entries — the host rejects the
  footprint before `get_stream` executes.
- **Restore before retry.** Submit a `RestoreFootprint` operation covering
  the archived key, then re-issue the original call. After restore,
  normal `extend_ttl` touch behavior resumes.
- **`extend_ttl` cannot resurrect an archived entry.** TTL extension only
  applies while the entry is live; restore is the only path back.
```

## Artifact B — `SECURITY.md` bullet

Insert under the existing `## Known non-issues` (or nearest equivalent) list `<VERIFY-4: rg -n -i "known non-issue|non.issue|not a bug" SECURITY.md>`. Match the repo's existing bullet style and anchor format.

```markdown
- **Host errors on archived streams are intended Soroban semantics, not a
  contract bug.** When a stream's persistent entry TTL lapses, the entry is
  archived; subsequent reads fail at the host layer with a restore-required
  error during simulation — never with `StreamNotFound`. Restore the
  footprint and retry. See
  [Archived vs. missing persistent entries](docs/CONTRACT_SPEC.md#archived-vs-missing-persistent-entries).
```

## Artifact C — Unit tests (executable documentation of the premise)

Co-locate in the existing stream test module `<VERIFY-5: rg -ln "mod test|#\[test\]" contracts/stream/src/>`. Adjust client/fn names and arg shapes to actual API `<VERIFY-6: rg -n "fn get_stream|pub fn create" contracts/stream/src/>`.

```rust
#[test]
fn missing_stream_yields_stream_not_found() {
    let env = Env::default();
    env.mock_all_auths();
    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);

    // Key absent from live storage → contract-level error.
    assert_eq!(
        client.try_get_stream(&42u64), // <VERIFY-6: fn + id type>
        Err(Ok(Error::StreamNotFound))
    );
}

/// Pinned contract behavior: an archived (TTL-lapsed) persistent entry
/// traps at the HOST layer. It must never surface as
/// `Error::StreamNotFound`. On-chain this manifests as restorePreamble
/// in simulation; in testutils it manifests as a panic. <VERIFY-7>
#[test]
#[should_panic] // host trap, NOT a contract error code
fn archived_stream_traps_at_host_not_contract_error() {
    let env = Env::default();
    env.mock_all_auths();
    let contract_id = env.register_contract(None, StreamContract);
    let client = StreamContractClient::new(&env, &contract_id);

    client.create_stream(&/* valid args — VERIFY-6 */);

    // Advance ledger past the entry's TTL so it is archived.
    let seq = env.ledger().sequence();
    env.ledger()
        .set_sequence_number(seq + /* PERSISTENT_TTL_EXTEND + 1 — VERIFY-2 */);

    let _ = client.get_stream(&0u64);
}
```

**VERIFY-7 caveat:** whether `soroban-sdk` testutils traps on expired persistent entries is version-dependent (TTL eviction simulation landed in newer SDKs). If `archived_stream_traps_at_host_not_contract_error` instead returns `None`/`StreamNotFound` locally, drop the test, note the test-vs-network divergence in the spec section, and record the SDK version — do **not** silently weaken the assertion.

## Diff skeletons (context lines intentionally elided — resolve post-Phase-0)

```diff
--- a/docs/CONTRACT_SPEC.md
+++ b/docs/CONTRACT_SPEC.md
@@ <after PERSISTENT_TTL paragraph in §1 — VERIFY-1> @@
+<Artifact A block>
--- a/SECURITY.md
+++ b/SECURITY.md
@@ <end of "Known non-issues" list — VERIFY-4> @@
+<Artifact B bullet>
--- a/contracts/stream/src/<test file — VERIFY-5>
+++ b/contracts/stream/src/<test file>
@@ <end of test module> @@
+<Artifact C tests>
```

## Pre-egress checklist

| Gate | Command |
|---|---|
| RULE-003 elevate | Confirm persistent (not temp/instance) storage for `DataKey::Stream` + `make check` suite exists → `VERIFIABLE_CODE_ISSUE` |
| VERIFY-1/2 | `rg -n "PERSISTENT_TTL|DataKey::Stream" contracts/stream/src/` — paste real names/values |
| VERIFY-3 | `rg -n "StreamNotFound" contracts/stream/src/` — paste real error code |
| VERIFY-4 | `rg -n -i "non.issue" SECURITY.md`; confirm anchor slug matches file's heading style |
| VERIFY-5/6 | Locate test module + real `get_stream`/`create` signatures |
| VERIFY-7 | `cargo test -p stream` — both tests must behave as asserted |
| RULE-002 | `make check` + any doc-lint in `.github/workflows/ci.yml`; confirm **zero `.rs` non-test changes** |
| RULE-001 | Comment intent-to-claim + open PR via user PAT only |

If Phase-0 shows `Stream` uses temporary/instance storage, **abort** — the premise is false and Artifact A would publish incorrect docs. Report back for redirect.\n