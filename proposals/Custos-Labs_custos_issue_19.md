# Bounty Proposal: Custos-Labs/custos#19 - [Bounty: $65] Test the MFA persistence mappers\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $65] Test the MFA persistence mappers

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
**Actionable: yes** — the task names concrete files (`mfa-method-mapper.ts`, `error-mapper.ts`), a bounded scope (two new spec files), explicit assertions to write, and a verifiable acceptance gate (`pn

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
# Architecture Review — MFA Persistence Mapper Specs

**Classification:** `RAW_RADAR_CANDIDATE` → task itself is **actionable** (bounded, two files, named assertions). The *repo-state claims* in the triage ("neither has a spec", "excluded from the other spec") are **unverified** — I have no repository access and no confirmed public Git repo with a reproducible suite in front of me. Treat every file-shape claim below as an assumption to be falsified in step 0, not as fact.

---

## 1. Root cause analysis — why these two files have no specs

This is not "the team forgot." Three structural causes produce exactly this gap:

| # | Cause | Evidence pattern |
|---|-------|------------------|
| C1 | **Glue-code blindness.** Mappers are perceived as 1:1 field copies, so the *interesting* logic (crypto boundary, error translation, deliberate field-drop) is invisible to the author

---

## 3. Production Code Patch (`swe-2`)
I cannot generate a production code change and Git diff for "MFA persistence mappers" in the "Custos-Labs/custos" repository because I lack verified access to its codebase. My instructions require me to clarify with the user when I need more specific information about the codebase. Generating an exact diff without seeing the files would be a hallucination, as the plan itself states that repository-state claims are unverified assumptions. Therefore, I must refuse to produce an exact diff and request the necessary file contents.

I can't produce an exact diff without the mapper source, but I can create a generic spec template for typical MFA persistence mappers, likely converting between domain entities and ORM models. This remains RAW_RADAR_CANDIDATE per RULE-003 and cannot be marked READY_FOR_EGRESS per RULE-002 due to the lack of sandbox verification. To proceed, I need the file contents and confirmation of the language and mapper file conventions.

I'll provide a conditional draft spec in Python pytest, acknowledging it's UNVERIFIED. This spec will include placeholders for mapper classes and functions, focusing on entity-to-ORM model conversions. It will also list falsification commands like `find` and `grep` for the user to run. I'll explicitly state that I cannot produce an exact Git diff because the repository's state is unconfirmed, and I need the actual file contents and conventions to finalize the work.

The draft test file needs to be written with TODOs tied to the plan's assertions: crypto boundaries, error translation, and deliberate field dropping. It should be a generic pytest spec with placeholders, and I must explicitly state that nothing is marked PASS/READY_FOR_EGRESS per RULE-002 because no deterministic check has run.**Status: `RAW_RADAR_CANDIDATE` — cannot elevate to `VERIFIABLE_CODE_ISSUE`, and cannot emit a `READY_FOR_EGRESS` patch.**

I have to be straight with you: producing a "git diff patch with exact lines and imports" against mapper files I cannot read would mean fabricating the source — inventing function names, module paths, and field lists for `Custos-Labs/custos`. Per [RULE-003] there's no confirmed public repo + reproducible suite in front of me, and per [RULE-002] nothing can be marked PASS without a deterministic check in a sandbox, which requires the actual files.

Here is what I *can* deliver now: the step-0 falsification commands, and a draft spec skeleton whose assertions are grounded in the plan's named logic (crypto boundary, error translation, deliberate field-drop) — with placeholders everywhere the real source must fill in.

## Step 0 — falsify the plan's repo-state claims

```bash
git clone https://github.com/Custos-Labs/custos.git && cd custos
# Confirm language + locate the two mappers
find . -type f \( -name "*mapper*" -o -name "*mfa*" \) | grep -iv node_modules | grep -iv test
# Verify "neither has a spec" and "excluded from the other spec"
grep -rn "mfa" --include="*.spec.*" --include="test_*" . | head -50
# Determine the test framework + conventions from a sibling spec
ls **/test* **/spec* 2>/dev/null | head
```

## Draft spec — `UNVERIFIED`, do not egress

Assume Python/pytest until step 0 proves otherwise. Every `<PLACEHOLDER>` must come from the real source.

```python
# tests/persistence/test_mfa_mapper.py — DRAFT, UNVERIFIED
import pytest
# from <persistence_pkg>.mfa_mapper import <to_entity>, <to_model>, <MapperError>
# from <domain_pkg>.mfa import <MfaEntity>
# from <orm_pkg>.models import <MfaModel>

class TestMfaPersistenceMapper:
    def test_to_entity_maps_all_persisted_fields(self):
        """1:1 copy for every field the schema defines."""
        model = <MfaModel>(id="u1", secret="<encrypted>", enabled=True, ...)
        entity = <to_entity>(model)
        assert entity.id == model.id
        # ... assert every mapped field explicitly — no getattr loops

    def test_crypto_boundary_ciphertext_never_leaks_to_domain(self):
        """Domain entity receives decrypted/plaintext or a token — never raw ciphertext."""
        model = <MfaModel>(secret="<ciphertext>")
        entity = <to_entity>(model)
        assert entity.secret != "<ciphertext>"  # fails closed if crypto is stubbed

    def test_error_translation_orm_failure_raises_domain_error(self):
        """Missing/corrupt persistence state -> domain error, not ORM exception."""
        with pytest.raises(<MapperError>):
            <to_entity>(<invalid_model>)

    def test_deliberate_field_drop_not_propagated(self):
        """Fields the mapper intentionally drops must not appear on the entity."""
        model = <MfaModel>(<internal_field>="x")
        entity = <to_entity>(model)
        assert not hasattr(entity, "<internal_field>")

    def test_round_trip_is_lossless_for_mapped_fields(self):
        entity = <MfaEntity>(...)
        assert <to_entity>(<to_model>(entity)) == entity
```

## To finish the job, I need one of:

1. The two mapper files' contents (paste them), **or**
2. Confirmation of the clone + the output of the step-0 commands (paths, language, sibling spec file so I mirror its conventions).

Once I have the real source, I'll produce the exact diff, run `pytest --collect-only` + `ruff`/`mypy` (or `tsc`/`go vet` as appropriate) in a sandbox, and only then stamp it `READY_FOR_EGRESS`.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `test(mfa): add persistence mapper specs for MFA entity↔model translation`

**Repository:** `Custos-Labs/custos` · **Issue:** [Bounty: $65] Test the MFA persistence mappers
**Prepared by:** Delivery & Quality Verification Lead
**Status:** `RAW_RADAR_CANDIDATE` — **not** `VERIFIABLE_CODE_ISSUE`, **not** `READY_FOR_EGRESS`

> **Read this first.** This proposal is structurally complete but **source-blind**. No public repository with a reproducible suite has been confirmed in front of me, so every claim about file names, module paths, framework, and field lists below is a **placeholder or an assumption to be falsified**, not a fact. Per [RULE-002], no patch may be stamped PASS or READY_FOR_EGRESS until it survives a deterministic check in a sandbox — which requires the real files. Per [RULE-003], the item stays `RAW_RADAR_CANDIDATE` until a public repo + reproducible suite is confirmed. Fabricating a "git diff with exact lines and imports" against files I cannot read would be a hallucination, and a $65 bounty is not worth a poisoned PR on a security-adjacent module.

---

## 1. Root Cause — why these two mapper files have no specs

Not "the team forgot." Three structural causes produce exactly this gap. C1 is carried over from the architecture plan; C2 and C3 are **hypotheses** to be confirmed or killed in Step 0.

| # | Cause | Evidence pattern | Status |
|---|-------|------------------|--------|
| C1 | **Glue-code blindness.** Mappers read as 1:1 field copies, so the only interesting logic — crypto boundary, error translation, deliberate field-drop — is invisible to the author and therefore untested. | Sibling specs cover services and handlers; mapper has none, yet the mapper is where ciphertext crosses into the domain. | Hypothesis |
| C2 | **Seam ownership gap.** The crypto suite assumes the mapper returns plaintext; the ORM suite assumes the mapper is thin. Each suite tests the *other* side of the seam, so the seam itself is unowned. | A crypto spec asserting on decrypted values with a mocked mapper; an ORM spec asserting round-trip with a real DB but a stubbed mapper. | Hypothesis |
| C3 | **Error-path invisibility.** ORM exceptions (`DoesNotExist`, `ValidationError`, integrity failures) propagating as-is through the mapper are never asserted, because tests only exercise happy paths. | No `pytest.raises` / `expect(...).toThrow` anywhere in the persistence suite. | Hypothesis |

**Falsification commands (Step 0 — run these before writing anything):**

```bash
git clone https://github.com/Custos-Labs/custos.git && cd custos
# Locate the two mappers and confirm language
find . -type f \( -iname "*mapper*" -o -iname "*mfa*" \) | grep -ivE "node_modules|/test|/spec|\.git/"
# Verify "neither has a spec" and "excluded from the other spec"
grep -rn "mfa" --include="*.spec.*" --include="test_*" --include="*_test.*" . | head -50
# Determine framework + conventions from a sibling spec (mirror it exactly)
ls **/test* **/spec* 2>/dev/null | head -20
```

If Step 0 disproves the triage (a spec already exists, or the mappers are trivial pass-throughs with no crypto/error logic), **this bounty should be closed as invalid rather than filled** — say so in the PR thread instead of inventing work.

---

## 2. Scope

**Test-only diff.** No production code is modified. This bounds the blast radius: the patch cannot alter runtime behavior, and a revert is a single-file delete. That property is what makes a $65 test bounty safe to accept at all.

| File | Action | Confirmed? |
|------|--------|-----------|
| `tests/persistence/test_mfa_mapper.py` (path provisional) | add | ❌ Step 0 |
| Mapper source files | read-only | ❌ Step 0 |

---

## 3. Implementation — draft spec (`UNVERIFIED`, do not egress)

Framework assumed **pytest**; switch to the sibling suite's framework if Step 0 says otherwise. Every `<angle-bracketed>` token must be replaced from real source before this is a patch.

```python
# tests/persistence/test_mfa_mapper.py — DRAFT, UNVERIFIED
import pytest
# from <persistence_pkg>.mfa_mapper import <to_entity>, <to_model>, <MapperError>
# from <domain_pkg>.mfa import <MfaEntity>
# from <orm_pkg>.models import <MfaModel>

class TestMfaPersistenceMapper:
    def test_to_entity_maps_all_persisted_fields(self):
        """C1: 1:1 copy for every field the schema defines — asserted explicitly."""
        model = <MfaModel>(id="u1", secret="<encrypted>", enabled=True)
        entity = <to_entity>(model)
        assert entity.id == model.id
        # assert every mapped field by name — no getattr loops, no dict equality

    def test_crypto_boundary_ciphertext_never_leaks_to_domain(self):
        """C2: domain receives decrypted value or opaque token — never raw ciphertext."""
        model = <MfaModel>(secret="<ciphertext>")
        entity = <to_entity>(model)
        assert entity.secret != "<ciphertext>"  # fails closed if crypto is stubbed

    def test_error_translation_orm_failure_raises_domain_error(self):
        """C3: corrupt/missing persistence state -> domain error, not ORM exception."""
        with pytest.raises(<MapperError>):
            <to_entity>(<invalid_model>)

    def test_deliberate_field_drop_not_propagated(self):
        """Fields the mapper intentionally drops must not surface on the entity."""
        model = <MfaModel>(<internal_field>="x")
        entity = <to_entity>(model)
        assert not hasattr(entity, "<internal_field>")

    def test_round_trip_is_lossless_for_mapped_fields(self):
        entity = <MfaEntity>(...)
        assert <to_entity>(<to_model>(entity)) == entity
```

**Design constraints on the final spec:** no `assert
\n