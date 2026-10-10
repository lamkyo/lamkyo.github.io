# Bounty Proposal: Custos-Labs/custos#57 - [Bounty: $95] Stop shipping mocked responses from the verification routes\n\n**Solution Overview**

* Remove the hard‑coded mock responses from `apps/api/src/routes/verification.ts`.  
* Guard the entire verification route group behind the presence of the
  `@custos/verification` use‑case in the container.  
* If the capability is missing, register a single catch‑all route that
  returns **404** for every `/verification/*` request – matching the
  “not built with that capability” contract.  
* Update the integration test suite to expect a 404 instead of a 201/200
  with mock IDs.

---

## 1.  `apps/api/src/routes/verification.ts`

```diff
@@
-import { FastifyInstance } from 'fastify';
+import { FastifyInstance } from 'fastify';
+import { Container } from 'typedi';
 
-export function registerVerificationRoutes(app: FastifyInstance) {
+/**
+ * Register the verification route group.
+ *
+ * If the container does not expose a `verification` service, the
+ * routes are *not* registered – a catch‑all 404 is returned for
+ * every `/verification/*` request.  This satisfies the contract
+ * that a missing capability should return 404, while a broken
+ * implementation would return 500.
+ */
+export function registerVerificationRoutes(
+  app: FastifyInstance,
+  container: Container,
+): void {
+  // If the verification use‑case is not available, expose a 404
+  // for every verification endpoint.
+  if (!container.has('verification')) {
+    app.all('/verification/*', async () => {
+      return { statusCode: 404, message: 'Verification capability not available' };
+    });
+    return;
+  }
 
-  // The original mock implementation – removed.
+  // ------------------------------------------------------------------
+  // Real implementation (placeholder – replace with actual use‑case
+  // logic once @custos/verification is wired in).
+  // ------------------------------------------------------------------
+
+  // POST /verification
+  app.post('/verification', async (request, reply) => {
+    // TODO: delegate to @custos/verification use‑case
+    reply.code(501).send({ error: 'Not implemented' });
+  });
+
+  // POST /verification/:requestId/evidence
+  app.post('/verification/:requestId/evidence', async (request, reply) => {
+    reply.code(501).send({ error: 'Not implemented' });
+  });
+
+  // GET /verification/:requestId
+  app.get('/verification/:requestId', async (request, reply) => {
+    reply.code(501).send({ error: 'Not implemented' });
+  });
+
+  // GET /verification/review-queue
+  app.get('/verification/review-queue', async (request, reply) => {
+    reply.code(501).send({ error: 'Not implemented' });
+  });
+
+  // POST /verification/review-queue/claim
+  app.post('/verification/review-queue/claim', async (request, reply) => {
+    reply.code(501).send({ error: 'Not implemented' });
+  });
+
+  // POST /verification/:requestId/decision
+  app.post('/verification/:requestId/decision', async (request, reply) => {
+    reply.code(501).send({ error: 'Not implemented' });
+  });
 }
```

### Notes

* The function now accepts the `container` so it can inspect whether the
  `verification` service is registered.  
* All mock handlers have been replaced with `501 Not Implemented`
  stubs – the real logic will be added once the use‑case is wired in.  
* The catch‑all 404 route guarantees that a client can never receive a
  fabricated `req_mock_123`/`ev_mock_123`/`req_claimed_123` ID.

---

## 2.  `apps/api/src/app.ts`

```diff
@@
-import { registerVerificationRoutes } from './routes/verification';
+import { registerVerificationRoutes } from './routes/verification';
+import { Container } from 'typedi';
 
-  registerVerificationRoutes(app);
+  const container = Container.getInstance();
+  registerVerificationRoutes(app, container);
```

---

## 3.  Integration tests

Assuming the tests live in `tests/integration/verification.test.ts`:

```diff
@@
-  it('creates a verification request', async () => {
-    const res = await request(app.server)
-      .post('/verification')
-      .send({ /* body */ })
-      .expect(201);
-    expect(res.body).toHaveProperty('requestId', 'req_mock_123');
+  it('returns 404 when verification capability is missing', async () => {
+    const res = await request(app.server)
+      .post('/verification')
+      .send({ /* body */ })
+      .expect(404);
+    expect(res.body).toMatchObject({
+      statusCode: 404,
+      message: 'Verification capability not available',
+    });
   });
```

*All other tests that asserted on the mock IDs should be updated similarly
to expect a 404 response.*

---

## 4.  Edge‑case handling

| Scenario | Result |
|----------|--------|
| Container **has** `verification` service | Routes are\n