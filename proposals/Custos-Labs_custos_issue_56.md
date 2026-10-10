# Bounty Proposal: Custos-Labs/custos#56 - [Bounty: $100] Replace the `checkReviewer` substring trust with a real authorization check\n\n## Grounding first (do not skip)

I don't have the repo checked out, so the edits below are written against the shape described in the issue. Confirm four things before writing the patch — every symbol I reference must resolve to real code:

```bash
rg -n "checkReviewer|review-queue|verificationRoutes" apps/api/src
rg -n "requirePermission" apps/api/src packages --type ts   # copy the exact call pattern
rg -n "verification:review|Permission|permission" packages/authorization/src
rg -n "verificationRoutes|/verification" apps/api/src/app.ts
```

What to pin down:
1. `requirePermission`'s exact signature (is it `(authz, key)` returning middleware, or async?) and its return/error semantics (401 vs 403).
2. The canonical permission key — prefer an exported constant/enum over the raw string `"verification:review"`. If the key isn't in the catalog, add it in `packages/authorization`.
3. The container type used by `app.ts` (e.g. `Container`) and how other route groups receive it.
4. Whether an auth/session middleware that populates the principal is mounted **before** `/verification` in `app.ts`. `requirePermission` reads the principal; if nothing populates it, every request 401s.

Classification: treat as **VERIFIABLE_CODE_ISSUE** only once the repo + test suite reproduce locally; until then it's a **\n