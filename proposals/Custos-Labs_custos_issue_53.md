# Bounty Proposal: Custos-Labs/custos#53 - [Bounty: $85] Enforce the system-role invariant in `PrismaAuthorizationRepository.updateRole`\n\n## Root cause

`updateRole` is the only mutation in the repository that writes to `role` without first reading `isSystemRole`. It therefore (a) bypasses the aggregate invariant `Role.rename` enforces via `SystemRoleImmutableError`, and (b) leaks Prisma's `P2025` when the id doesn't exist. `PATCH /admin/roles/:roleId` reaches it, so renaming `super-admin` succeeds.

## Fix — `packages/authorization/infrastructure/prisma-authorization-repository.ts`

Mirror `deleteRole`: read first, guard, then write, and translate `P2025`.

```diff
+import { Prisma } from "@prisma/client";
+
+function isRecordNotFound(error: unknown): boolean {
+  return (
+    error instanceof Prisma.PrismaClientKnownRequestError &&
+   \n