# Bounty Proposal: Perenna-Labs/perenna-contracts#78 - [Bounty: $65] Add the deployed-contract-ID section the deployment guide references\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $65] Add the deployed-contract-ID section the deployment guide references

## Architecture (Opus 5.5)
# Analysis: Perenna-Labs/perenna-contracts — Bounty #65

## 1. Root Cause Analysis

The failure is a **documentation contract violation** — a cross-file reference that was never validated. Three distinct root causes compound:

| # | Root cause | Class |
|---|-----------|-------|
| RC-1 | `docs/DEPLOYMENT.md` references a README section ("interface section") that was never created. The reference is **aspirational, not descriptive** — written as if the section existed. | Dangling cross-reference |
| RC-2 | `README.md` has no canonical home for deployed-address data. Contract IDs live only in deploy artifacts / chat, so they're lost between deploys. | Missing source of truth |
| RC-3 | No CI check validates that README section anchors referenced by docs actually exist. `make check` presumably lints markdown but doesn't cross-validate anchors. | Missing guardrail |

The deeper architectural issue: **the deployment guide is the only place that knows the README is supposed to have this section, and nothing enforces that agreement.** Fix the symptom (add the section) *and* the class (add an anchor check) or this recurs on the next doc that references a not-yet-written section.

## 2. Files to Touch

```
README.md                          # add "Deployed contracts" section
docs/DEPLOYMENT.md                 # align wording → exact section name
.github/workflows/ci.yml           # (optional, recommended) anchor validation
Makefile                           # (optional) wire anchor check into `make check`
```

**Do not touch** contract sources, `Cargo.toml`, or deploy scripts — this is a docs-only change and any source diff risks the `check` job for no benefit.

## 3. Architectural Strategy

### 3.1 Canonical section name — pick one, use everywhere

Use **`## Deployed contracts`** (sentence case, matches existing README heading style — verify against Contributing/Contributors/License casing before committing). The exact string becomes the single source of truth. `docs/DEPLOYMENT.md` must reference it verbatim, ideally as a markdown link `[Deployed contracts](../README.md#deployed-contracts)` so the anchor is machine-checkable.

### 3.2 README section shape

Place it **after Contributing, before Contributors/License** (or wherever the existing flow reads best — but keep it above License). Structure:

```markdown
## Deployed contracts

> ⚠️ **Unaudited.** These contracts have not been audited. Do not use with
> real funds. Addresses are provided for testnet integration only.

| Network | Contract ID | Explorer |
|---------|-------------|----------|
| Testnet | `TBD`       | _pending deploy_ |
| Mainnet | —           | _not deployed_ |

Replace the testnet row after each deploy. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the deploy procedure.
```

Key decisions:
- **Network column** satisfies "distinguishes networks" without inventing a mainnet address.
- **Unaudited banner** is a blockquote at the top of the section — visible, not buried.
- **Placeholder is explicit** (`TBD` / `_pending deploy_`) so it's obviously not a real address and greps cleanly.
- **Back-link to DEPLOYMENT.md** closes the loop in both directions.

### 3.3 DEPLOYMENT.md alignment

Find the exact sentence ("Add the explorer link to the README's interface section") and rewrite to:

> Add the explorer link to the **Deployed contracts** section of `README.md`.

If the guide has a post-deploy checklist, add a step: *"Update the testnet row in `README.md` → Deployed contracts."* This makes the guide's instruction executable as written — the acceptance criterion.

### 3.4 Guardrail (prevents recurrence)

Add a lightweight anchor check so RC-1 can't recur silently:

- **Option A (minimal):** a `grep`-based step in `make check` that asserts the string `Deployed contracts` appears in both `README.md` and `docs/DEPLOYMENT.md`.
- **Option B (robust):** a markdown link checker (e.g. `lychee` or `markdown-link-check`) scoped to relative anchors, run in the `check` job.

Start with **A** — it's zero-dependency, deterministic, and directly encodes the invariant. Escalate to B only if the repo already has a link-checker dependency. **Do not add a new CI dependency for a $65 docs bounty** unless the maintainers ask.

## 4. Regression Avoidance

| Risk | Mitigation |
|------|-----------|
| `make check` fails on markdown lint (line length, heading style) | Run `make check` locally *before* committing; match existing heading casing and wrap prose at the repo's configured width. |
| CI `check` job red due to new anchor-check step | Land the anchor check in the **same PR** as the section, so the invariant is satisfied the moment it's enforced. |
| Section placed where it breaks TOC / anchor links | If README has a table of contents, add the entry; verify no existing anchor collides with `#deployed-contracts`. |
| Wording drift between README and DEPLOYMENT.md | Use the exact literal string in both; the anchor check (3.4) enforces it. |
| Scope creep into contract code | Hard boundary: docs + CI only. Reject any temptation to "fix" deploy scripts. |

## 5. Execution Order

1. Read `README.md` end-to-end — confirm heading style, TOC presence, exact insertion point.
2. Read `docs/DEPLOYMENT.md` — locate the dangling sentence and any post-deploy checklist.
3. Add `## Deployed contracts` to README (unaudited banner + network table + back-link).
4. Rewrite the DEPLOYMENT.md sentence to name the section verbatim; add checklist step.
5. Add the anchor check to `make check` (Option A).
6. Run `make check` locally → green.
7. Push; confirm the `check` job of `.github/workflows/ci.yml` stays green.
8. PR body: link the issue, tick each acceptance criterion explicitly.

## 6. Acceptance Criteria Traceability

| Criterion | Satisfied by |
|-----------|-------------|
| README section holds contract ID + explorer link | §3.2 table |
| DEPLOYMENT.md names the section consistently | §3.3 verbatim rewrite |
| Section distinguishes networks + marks unaudited | §3.2 Network column + banner |
| `make check` passes; CI `check` green | §5 steps 6–7 |

---

**One flag before you start:** the triage line is truncated mid-sentence (`"...clears the $"`). Confirm the

## Code Fix (SWE-2)
I can't produce the patch you're asking for, and I want to be straight with you about why rather than hand you something that looks authoritative but isn't.

## The blocker: I have no repository contents

Everything in the plan above is **inferred from the issue text alone**. I have not read `README.md`, `docs/DEPLOYMENT.md`, `Makefile`, or `.github/workflows/ci.yml`. That means I cannot produce a "surgical" patch with "exact lines," because:

- I don't know the README's heading casing (`## Contributing` vs `## Contributing`), so I can't match it.
- I don't know the exact dangling sentence in `DEPLOYMENT.md` — the plan paraphrases it as *"Add the explorer link to the README's interface section"* but flags it as a guess.
- I don't know whether a TOC exists, what the markdown linter's line-width config is, or whether `make check` even runs a markdown linter.
- I don't know the repo's language/toolchain, so I can't write a `make check` step that fits.

A diff with fabricated line numbers and context lines would fail to apply, and worse, it would look plausible enough that someone might try to force it through. That's the failure mode I'm trying to avoid.

## What I can give you right now

**1. The exact content blocks**, which are the real substance and are repo-independent:

```markdown
## Deployed contracts

> ⚠️ **Unaudited.** These contracts have not been audited. Do not use with
> real funds. Addresses are provided for testnet integration only.

| Network | Contract ID | Explorer |
|---------|-------------|----------|
| Testnet | `TBD`       | _pending deploy_ |
| Mainnet | —           | _not deployed_ |

Replace the testnet row after each deploy. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the deploy procedure.
```

**2. The DEPLOYMENT.md rewrite**, once you paste the original sentence:

> Add the explorer link to the **Deployed contracts** section of `README.md`.

**3. The guardrail**, as a portable shell snippet rather than a Makefile edit:

```sh
# Anchor invariant: the section name must exist in both files.
grep -q '^## Deployed contracts$' README.md \
  || { echo "README.md is missing '## Deployed contracts'"; exit 1; }
grep -q 'Deployed contracts' docs/DEPLOYMENT.md \
  || { echo "docs/DEPLOYMENT.md does not reference 'Deployed contracts'"; exit 1; }
```

## What I need from you to finish the job

Paste these four things and I'll write the real diff:

1. `README.md` — at minimum the heading list and the region around Contributing/License.
2. `docs/DEPLOYMENT.md` — the full file, or at least the paragraph containing the dangling reference plus any post-deploy checklist.
3. `Makefile` — the `check` target.
4. `.github/workflows/ci.yml` — the `check` job.

## Two corrections to the plan itself

- **§3.4 Option A is weaker than it looks.** A `grep` for the literal string proves the *words* appear, not that the *link resolves*. If someone renames the heading to `## Deployed Contracts`, the grep still passes while the anchor `#deployed-contracts` silently breaks. If the repo already has any markdown tooling, prefer a real anchor check. If it doesn't, the grep is fine as a stopgap — just don't describe it as validating the reference.
- **The plan's own §6 is not traceable yet.** "README section holds contract ID + explorer link" is satisfied by a table with `TBD` in it. If the acceptance criterion means a *real* deployed address, this bounty cannot be closed by a docs PR alone and the issue needs clarification before anyone writes code.

Also worth noting: the plan's closing line is truncated mid-sentence (`"...clears the $"`), so whatever caveat was being raised there never landed. That may be the same ambiguity as the point above.

Send me the four files and I'll produce the patch with real line numbers, real context, and a `make check` run to confirm it's green.\n