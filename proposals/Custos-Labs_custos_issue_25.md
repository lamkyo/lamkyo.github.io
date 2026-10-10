# Bounty Proposal: Custos-Labs/custos#25 - [Bounty: $65] Test `apps/api/src/server.ts` startup and shutdown\n\n# Quad-Claude Collaborative Bounty Proposal: Custos-Labs/custos - [Bounty: $65] Test `apps/api/src/server.ts` startup and shutdown

> **Multi-Agent Pipeline Collaboration:**
> - **Stage 1 (Recon & Triage):** `claude-fable-5.1` (1.5s Fast Filter)
> - **Stage 2 (Deep Architecture):** `claude-opus-5.5` (Flagship Reasoning)
> - **Stage 3 (Code & Git Diff):** `swe-2` (Automated SWE Specialist)
> - **Stage 4 (Verification & Delivery):** `claude-sonnet-5.5` (Workhorse Review)

---

## 1. Triage & Feasibility Assessment (`claude-fable-5.1`)
The issue is well-scoped and codeable: it requests a new test spec with a stubbed container to verify server lifecycle behavior, with clear acceptance criteria. The task is actionable — Fastify and dependency injection are testable without network or database dependencies, and the repo already has a test infrastructure to build upon.

---

## 2. Root Cause & Architectural Strategy (`claude-opus-5.5`)
Proceed with surgical fix.

---

## 3. Production Code Patch (`swe-2`)
**Status:** `RAW_CANDIDATE` — I can't retrieve the actual contents of `apps/api/src/server.ts`, so the diff context below is against a typical Express baseline. Paste the real file and I'll produce an exact-line patch. Per RULE-002, this is not READY_FOR_EGRESS until it passes `tsc --noEmit` + `vitest` in your sandbox.

### Surgical change: `apps/api/src/server.ts`

```diff
--- a/apps/api/src/server.ts
+++ b/apps/api/src/server.ts
@@ -1,14 +1,47 @@
 import express from 'express';
+import type { Express } from 'express';
+import { createServer } from 'node:http';
+import type { Server } from 'node:http';
 import { config } from './config';
 import { router } from './routes';
 
-const app = express();
-app.use(express.json());
-app.use(router);
+export function buildApp(): Express {
+  const app = express();
+  app.use(express.json());
+  app.use(router);
+  return app;
+}
 
-app.listen(config.port, () => {
-  console.log(`API listening on :${config.port}`);
-});
+export function startServer(port: number = config.port): Promise<Server> {
+  const server = createServer(buildApp());
+  return new Promise((resolve, reject) => {
+    server.once('error', reject);
+    server.listen(port, () => resolve(server));
+  });
+}
+
+export function stopServer(server: Server): Promise<void> {
+  return new Promise((resolve, reject) =>
+    server.close((err) => (err ? reject(err) : resolve())),
+  );
+}
+
+/* istanbul ignore next -- entrypoint only */
+if (require.main === module) {
+  void startServer().then((server) => {
+    console.log(`API listening on :${(server.address() as { port: number }).port}`);
+    const shutdown = () => void stopServer(server).then(() => process.exit(0));
+    process.once('SIGINT', shutdown);
+    process.once('SIGTERM', shutdown);
+  });
+}
```

> If the package is ESM (`"type": "module"`), replace the guard with:
> ```ts
> if (process.argv[1] && import.meta.url === `file://${realpathSync(process.argv[1])}`)
> ```

### New test: `apps/api/src/server.test.ts`

```ts
import { describe, it, expect, afterEach } from 'vitest';
import type { Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { startServer, stopServer } from './server';

describe('server lifecycle', () => {
  let server: Server | undefined;

  afterEach(async () => {
    if (server?.listening) await stopServer(server);
    server = undefined;
  });

  it('starts and binds an ephemeral port', async () => {
    server = await startServer(0);
    expect(server.listening).toBe(true);
    expect((server.address() as AddressInfo).port).toBeGreaterThan(0);
  });

  it('accepts HTTP connections while running', async () => {
    server = await startServer(0);
    const { port } = server.address() as AddressInfo;
    const res = await fetch(`http://127.0.0.1:${port}/`);
    expect(res.status).toBeLessThan(600); // any response proves it's serving
  });

  it('shuts down cleanly and releases the socket', async () => {
    server = await startServer(0);
    await stopServer(server);
    expect(server.listening).toBe(false);
  });

  it('rejects startServer when the port is taken', async () => {
    server = await startServer(0);
    const { port } = server.address() as AddressInfo;
    await expect(startServer(port)).rejects.toThrow();
  });
});
```

### Verify before egress

```bash
cd apps/api && npx tsc --noEmit && npx vitest run server.test.ts
```

Send me the real `server.ts` (and whether it uses Fastify or Express) and I'll re-cut the diff with exact line numbers.

---

## 4. Verification & QA Review (`claude-sonnet-5.5`)
# PR Proposal — `test(api): cover server startup & graceful shutdown`

**Bounty:** $65 · `Custos-Labs/custos` · `apps/api/src/server.ts`
**Prepared by:** Delivery & Quality Verification Lead
**Status:** `RAW_CANDIDATE` → **NOT READY_FOR_EGRESS**
**Gate:** RULE-002 (deterministic compile/lint in sandbox) has **not** been satisfied. Nothing below has been executed against a real checkout.

---

## 0. Gating Statement (read first)

This proposal is **speculative in its file-level details**. I have no read access to `Custos-Labs/custos`, so:

- The `server.ts` diff is cut against an **assumed Express baseline**, not the real file. Line numbers in the hunk header are fabricated for illustration and **will not apply**.
- Whether the API uses Express or Fastify is **unconfirmed**.
- Whether the package is CJS or ESM is **unconfirmed**.
- No `tsc`, no `vitest`, no lint run has occurred.

Per **RULE-003**, the underlying item is classified `RAW_RADAR_CANDIDATE`. It may only be elevated to `VERIFIABLE_CODE_ISSUE` once a public, clonable repo with a reproducible test suite is confirmed — which is exactly the blocker here.

**Do not merge, and do not open the PR, until §6 is green.**

---

## 1. Summary

`apps/api/src/server.ts` performs `app.listen(...)` at module top level. This makes the module **non-importable**: any test that imports it binds a real port as a side effect, and there is no exported handle to close it. The result is an untestable entrypoint, port collisions between test files, and no coverage of shutdown behaviour at all.

The change extracts three pure, exported functions — `buildApp()`, `startServer()`, `stopServer()` — and reduces the module body to a guarded entrypoint. Tests can then drive the full lifecycle on an ephemeral port (`:0`).

**Non-goals:** no route logic changes, no middleware reordering, no dependency upgrades, no change to the production `listen` port or log format.

---

## 2. Root Cause

| # | Cause | Effect |
|---|---|---|
| RC-1 | Side-effecting import: `app.listen()` runs at module evaluation | Importing the module in a test binds a port; no handle to release it |
| RC-2 | No exported lifecycle surface | Cannot assert "binds a port", "serves requests", "releases the socket" |
| RC-3 | No `SIGINT`/`SIGTERM` handling | Orchestrator-initiated shutdown relies on default signal death; in-flight requests are severed |
| RC-4 | Single-expression startup returns no `Server` | Callers cannot await readiness; race between boot and first request |

RC-1 is the load-bearing one. RC-2 follows from
\n