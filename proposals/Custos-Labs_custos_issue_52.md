# Bounty Proposal: Custos-Labs/custos#52 - [Bounty: $85] Make `Role.hasPermission` agree with `PermissionMatcher`\n\n## Root Cause

`Role.hasPermission` reimplements matching instead of delegating. Its current logic is roughly:

```ts
hasPermission(required: Permission): boolean {
  return [...this.permissions].some(
    (granted) =>
      (granted.resource === required.resource && granted.action === required.action) ||
      (granted.resource === required.resource && granted.action === '*')
  );
}
```

Missing branches: global `*:*` and cross-resource `*:action`. This is exactly what `PermissionMatcher.matches` already handles, and `PrismaAuthorizationRepository.hasPermission` funnels through it — so seed roles holding `*:*` return `false`.

## Fix (preferred: collapse to one implementation)

### 1. `packages/authorization/domain/entities/role.ts`

Delegate to the matcher. Import **type-only** for `Permission` to avoid a runtime import cycle (`PermissionMatcher` may reference `Permission`), and import the matcher as a value:

```ts
import { PermissionMatcher } from '../services/permission-matcher';
import type { Permission } from '../value-objects/permission';

// inside class Role
hasPermission(required: Permission): boolean {
  for (const granted of this.permissions) {
    if (PermissionMatcher.matches(granted, required)) return true;
  }
  return false;
}
```

If `this.permissions` is a `Set`, use `for (const granted of this.permissions)` directly — do **not** spread it into an array (O(n) alloc per check on a hot path called by the repo).

Argument order matters: `matches(granted, required)` — the granted permission is the *pattern*, required is the *subject*. Verify against the existing signature in `permission-matcher.ts` before committing; if the matcher is declared `matches(required, granted)`, swap accordingly.

### 2. Eliminate the second divergence (`Permission.matches`)

The AC requires all three to agree, so route `Permission.matches` through the matcher too — otherwise you still have two sources of truth and a future drift risk:

```ts
// packages/authorization/domain/value-objects/permission.ts
import { PermissionMatcher } from '../services/permission-matcher';

matches(required: Permission): boolean {
  return PermissionMatcher.matches(this, required);
}
```

### 3. Break the cycle if one appears

If `permission-matcher.ts` imports `Permission` (likely, for typing), the `permission.ts → permission-matcher.ts` import above creates a cycle. Two safe options:

- **Preferred:** make the matcher operate on the structural shape, not the class:
  ```ts
  // permission-matcher.ts
  export interface PermissionLike { resource: string; action: string; }
  static matches(granted: PermissionLike, required: PermissionLike): boolean { ... }
  ```
  Then `permission.ts` and `role.ts` both import the matcher, and the matcher imports **nothing** from the value-object layer. No cycle, and `Role`/`Permission` become thin adapters.

- **Fallback:** keep the class type but use `import type` in the matcher for `Permission` (type-only imports are erased, so no runtime cycle).

If neither is acceptable, fall back to adding the two missing branches directly in `Role.hasPermission` (minimal diff, but leaves three implementations — do this only as a last resort and note it in the PR).

## Test: assert all three agree

Create `packages/authorization/domain/__tests__/permission-matching-agreement.spec.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { Permission } from '../value-objects/permission';
import { PermissionMatcher } from '../services/permission-matcher';
import { Role } from '../entities/role';

// [granted, required, expected, label]
const cases: Array<[string, string, boolean, string]> = [
  ['users:read',  'users:read',  true,  'exact'],
  ['*:*',         'users:read',  true,  'global wildcard'],
  ['users:*',     'users:read',  true,  'resource wildcard'],
  ['*:read',      'users:read',  true,  'action wildcard'],
  ['users:write', 'users:read',  false, 'exact miss'],
  ['users:*',     'posts:read',  false, 'resource mismatch'],
  ['*:write',     'users:read',  false, 'action mismatch'],
  ['*:*',         'posts:delete',true,  'global wildcard, other pair'],
];

describe('permission matching — three implementations agree', () => {
  it.each(cases)('%s vs %s => %s (%s)', (grantedStr, requiredStr, expected) => {
    const granted = Permission.from(grantedStr);
    const required = Permission.from(requiredStr);
    const role = new Role({ id: 'r1', name: 'test', permissions: [granted] });

    expect(PermissionMatcher.matches(granted, required)).toBe(expected);
    expect(granted.matches(required)).toBe(expected);
    expect(role.hasPermission(required)).toBe(expected);
  });
});
```

Adjust the `new Role(...)` / `Permission.from(...)` constructor shapes to the actual signatures (check `role.ts` and `permission.ts`; if `Permission` is constructed as `new Permission(resource, action)`, parse `grantedStr.split(':')`).

Also add an explicit seed-parity regression for the reported bug:

```ts
it('role granted *:* satisfies an arbitrary resource:action pair', () => {
  const role = new Role({ id: 'admin', name: 'admin', permissions: [Permission.from('*:*')] });
  expect(role.hasPermission(Permission.from('users:read'))).toBe(true);
});

it('role granted *:read satisfies users:read', () => {
  const role = new Role({ id: 'reader', name: 'reader', permissions: [Permission.from('*:read')] });
  expect(role.hasPermission(Permission.from('users:read'))).toBe(true);
});
```

## Edge cases to verify

- **Set vs array\n