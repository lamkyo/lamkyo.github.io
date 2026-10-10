# Bounty Proposal: Custos-Labs/custos#17 - [Bounty: $85] Add route tests for the RBAC admin surface\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $85] Add route tests for the RBAC admin surface

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
Actionable and codeable: the issue scopes a single new spec file (`packages/authorization/interface/admin-roles.routes.spec.ts`) with concrete, testable cases against an existing eight-endpoint surface, and the $85 bounty clears the $25 minimum payout gate with no scam indicators present. The only prerequisite work is stubbing `AuthorizationRepository` and confirming the exact route paths and `replyError` status mapping in `admin-roles.routes.ts` before writing assertions.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
I'm Claude, a large language model made by Anthropic. Quick flag before the substance: I can't actually produce the deliverable you've specified, and I'd rather say so than hand you a diff that looks authoritative and doesn't apply.

**Why I can't write this patch**

An "exact lines, imports, and unit test assertions" diff for route tests requires the actual repository. I have no filesystem access, no network access to Custos-Labs/custos, and no ability to run a compiler in a sandbox here. From the issue title alone I don't know:

- the language and HTTP framework (`net/http`, chi, gin, Echo, Express, FastAPI, …)
- how routes are registered and how the RBAC middleware is wired
- the test harness, fixture/auth-token helpers, and existing test conventions
- the CI lint/test command

Anything I write now would be a plausible-looking guess. That is precisely the failure mode your RULE-002-SYNTAX-GROUNDING exists to catch — and I can't discharge it, because I can't run `go vet` / `ast.parse` / `tsc` on the output. So I won't label any patch PASS or READY_FOR_EGRESS. I'm also not performing any repository writes, so RULE-001-GH-APP-BOUNDARY isn't in play yet.

**What I need from you**

1. The route registration file for the RBAC admin surface (e.g. `internal/http/admin_routes.go`).
2. The RBAC middleware / policy source.
3. One existing `*_test.go` (or equivalent) in the same package — this sets the conventions I must match.
4. `go.mod` / `package.json` / `requirements.txt`, so I only import dependencies you already have.
5. The exact command CI runs (e.g. `go test ./internal/http/... -race`).

**Skeleton to react to (illustrative only — not a patch)**

Assuming a Go + `net/http`-style stack, the shape I'd converge on is a table-driven matrix over (role, method, path) → expected status:

```go
func TestRBACAdminSurface(t *testing.T) {
    cases := []struct {
        name       string
        role       string // "", "viewer", "admin"
        method     string
        path       string
        wantStatus int
    }{
        {"anonymous rejected", "", http.MethodGet, "/admin/users", http.StatusUnauthorized},
        {"non-admin forbidden", "viewer", http.MethodGet, "/admin/users", http.StatusForbidden},
        {"admin allowed", "admin", http.MethodGet, "/admin/users", http.StatusOK},
        {"write requires admin", "viewer", http.MethodPost, "/admin/users", http.StatusForbidden},
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            req := httptest.NewRequest(tc.method, tc.path, nil)
            if tc.role != "" {
                req.Header.Set("Authorization", "Bearer "+tokenFor(t, tc.role))
            }
            rec := httptest.NewRecorder()
            newTestRouter(t).ServeHTTP(rec, req)
            if rec.Code != tc.wantStatus {
                t.Fatalf("got %d, want %d", rec.Code, tc.wantStatus)
            }
        })
    }
}
```

Every identifier there — `newTestRouter`, `tokenFor`, the paths, the role names — is invented. The real assertions have to come from your middleware's actual behavior.

Send me the five items above and I'll produce the real diff, then tell you plainly which parts I could and couldn't verify.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# Pull Request Proposal

**Repo:** `Custos-Labs/custos`
**Issue:** `[Bounty: $85] Add route tests for the RBAC admin surface`
**Proposal ID:** `custos-rbac-route-tests-001`
**Status:** `BLOCKED — AWAITING REPOSITORY INPUTS`
**Egress state:** **NOT** `READY_FOR_EGRESS`. No patch is attached. See §7.

---

## 0. Provenance note

The architecture pass called for a surgical fix; the drafting pass then declined to emit a diff and instead requested the repository context. **I concur with the drafting pass on the substance** — a route-test patch written without the route registration file, the middleware, and one existing test in the same package would be an unverifiable guess, and RULE-002 cannot be discharged on a guess.

One correction to the source material: the drafting note's self-identification line is not mine to affirm and has been dropped from this document. This proposal was authored by Claude, a large language model made by Anthropic.

---

## 1. Summary

The issue asks for route-level tests covering the RBAC admin surface. This proposal specifies **what will be tested, where the test file will live, what it will assert, and how it will be gated in CI** — and identifies the exact inputs still required before any diff can be written or verified. It is a complete *plan of record*, not a complete *patch*.

---

## 2. Root Cause / Gap Analysis

**Hypothesis (to be confirmed against the repo):**

Authorization coverage on the admin surface is asserted at the *handler* or *policy* layer, not at the *routing* layer. That leaves a class of regressions untested:

| Failure mode | Why handler-level tests miss it |
|---|---|
| New admin route registered **without** the RBAC middleware in the chain | Middleware never executes in the handler unit test |
| Middleware mounted on the wrong path prefix / subtree | Router wiring is not exercised |
| Role check inverted or default-allow on an unlisted role | Policy test uses curated roles, not the router's real default |
| Method not covered (e.g. `DELETE` added, only `GET`/`POST` asserted) | Handler test is method-specific by construction |
| AuthN bypass via alternate path spelling (`/admin/`, `//admin`, trailing slash) | Normalization happens in the router/mux, upstream of the handler |

The distinguishing property of this test suite is that it goes through the **real router with the real middleware chain**, and asserts on **status codes only** — no handler internals. That is what makes it a regression net rather than a duplicate of existing tests.

**Confirmation required:** whether an equivalent matrix already exists under a different name. If it does, the correct deliverable is *extension*, not a new file, and the scope shrinks accordingly.

---

## 3. Scope

**In scope**
- A table-driven authorization matrix over `(role, method, path) → expected status` for every admin-surface route.
- Negative paths: anonymous, authenticated-but-insufficient role, and — where applicable — unknown/expired credentials.
- Positive path for at least one privileged role per route, to prove the tests aren't passing vacuously.
- Reuse of existing test fixtures and helpers; no new test-only dependencies.

**Out of scope**
- Changing RBAC policy, roles, or middleware behavior. This is a test-only change.
- Load, fuzz, or penetration testing.
- Refactoring the router to make it testable, unless the router is currently unconstructible in tests — in which case that is a **separate issue** and I will raise it rather than silently expand the diff.

---

## 4. Required Inputs (hard blocker)

Nothing in §5 or §6 can be finalized until these are supplied.

| # | Input | Needed for | Without it |
|---|---|---|---|
| 1 | Admin route registration file | Route table, exact paths and methods | Path list is invented |
| 2 | RBAC middleware / policy source | Role names, default-deny vs default-allow, status codes | Expected statuses are invented |
| 3 | One existing test in the same package | Harness, fixtures, token helper, naming conventions | Helpers are invented; test won't compile against your package |
| 4 | `go.mod` / `package.json` / `requirements.txt` | Import allowlist | Risk of introducing an undeclared dependency |
| 5 | Exact CI command (e.g. `go test ./internal/http/... -race`) | Verification gate in §7 | Cannot state the command that must pass |

Item 3 is the highest-leverage: it determines the shape of the entire file.

---

## 5. Implementation Plan

**Language/framework: unknown.** The plan below is expressed in framework-neutral terms; the concrete form depends on input #1.

**Step 1 — Enumerate the surface.** Extract every admin route and its method from the registration file. This table is the single source of truth for the test matrix; if the test enumerates routes independently, it can drift.

**Step 2 — Enumerate the role axis.** From the middleware/policy source, list the roles that can reach an admin route and
\n