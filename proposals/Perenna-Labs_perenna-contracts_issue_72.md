# Bounty Proposal: Perenna-Labs/perenna-contracts#72 - [Bounty: $70] Make stream-id allocation and stream persistence atomic in `create_stream`\n\n# Architecture & Code Fix: Perenna-Labs/perenna-contracts - [Bounty: $70] Make stream-id allocation and stream persistence atomic in `create_stream`

## Architecture (Opus 5.5)
# Architecture Analysis: Atomic Stream-ID Allocation in `create_stream`

## 1. Root Cause Analysis

The bug is a **classic non-atomic multi-write sequence** in a persistent store. Let me decompose it:

### 1.1 The Failure Mode

```
create_stream():
  1. id = get_next_stream_id()          // read
  2. set_next_stream_id(id + 1)         // WRITE #1  ← counter advances
  3. ... (validation, event emit, etc.) // ← failure window
  4. set_stream(id, stream)             // WRITE #2  ← stream persists
```

If step 3 (or step 4 itself) fails — panic, out-of-gas, host trap, reentrancy, or an explicit `Err` return — the counter has advanced but no stream exists at `id`. Result:

- **Permanent ID gap** — `id` is burned forever.
- **Invariant violation** — `NextStreamId != count(streams)`, breaking any downstream logic that assumes contiguity (e.g., pagination, index math, off-chain reconciliation).

### 1.2 Why "Just Reorder" Is Insufficient

The triage suggests reordering `set_stream` before `set_next_stream_id`. That fixes the *specific* window but introduces a **new** failure mode:

```
  1. id = get_next_stream_id()
  2. set_stream(id, stream)             // WRITE #1  ← stream persists
  3. set_next_stream_id(id + 1)         // WRITE #2  ← counter advances
```

If step 3 fails, you now have **two streams with the same id** on the next call (the counter never advanced, so the next `create_stream` reuses `id` and overwrites). That's *worse* than a gap — it's silent data corruption.

**Conclusion:** Reordering alone trades a gap for a collision. The real fix must make the two writes **atomic** — all-or-nothing.

### 1.3 The Deeper Invariant

The true invariant is:

> **`NextStreamId` must equal the number of successfully persisted streams, and every persisted stream must have a unique id in `[0, NextStreamId)`.**

This is a **counter/collection consistency invariant**. It cannot be maintained by ordering alone; it requires either (a) a single atomic write, or (b) a transactional wrapper with rollback.

---

## 2. Files to Touch

| File | Change | Rationale |
|---|---|---|
| `contracts/stream/src/lib.rs` | Rewrite `create_stream` body | Core fix |
| `contracts/stream/src/storage.rs` | Add `set_stream_and_advance_id` (atomic composite) OR add rollback helper | Encapsulate atomicity at the storage layer |
| `contracts/stream/src/test.rs` (or `tests/`) | Add failure-injection test | Acceptance criterion #3 |
| `contracts/stream/src/error.rs` | Possibly add `StreamIdAllocationFailed` variant | Explicit failure semantics |
| `.github/workflows/ci.yml` | No change expected — verify `check` job stays green | Acceptance criterion #4 |

**Do not touch** unrelated storage functions — blast radius must stay bounded to the allocation path.

---

## 3. Architectural Strategy

### 3.1 Preferred Design: Single Atomic Composite Write

Move the atomicity guarantee **into the storage layer** so callers cannot get it wrong. This is the invariant-safe approach: the dangerous sequence is no longer expressible.

```rust
// storage.rs
/// Atomically persists `stream` at `id` and advances the counter to `id + 1`.
/// Either both writes land or neither does.
pub fn set_stream_and_advance_id(env: &Env, id: u64, stream: &Stream) {
    // In Soroban, a panic in a contract call rolls back ALL storage writes
    // made during that call. So the atomicity primitive is: do both writes
    // in one call frame, and panic (not return Err) on any failure.
    set_stream(env, id, stream);
    set_next_stream_id(env, id + 1);
}
```

```rust
// lib.rs
pub fn create_stream(env: Env, ...) -> Result<u64, Error> {
    let id = storage::get_next_stream_id(&env);

    // Build + validate the stream BEFORE any write.
    let stream = Stream { id, /* ... */ };
    validate_stream(&stream)?;              // fail here → no writes, no gap

    // Single atomic commit point.
    storage::set_stream_and_advance_id(&env, id, &stream);

    // Events AFTER commit — a failed event emit must not roll back state.
    env.events().publish((symbol_short!("create"), id), id);

    Ok(id)
}
```

**Key principles:**

1. **Validate before write.** All fallible logic (input checks, arithmetic, external calls) happens *before* the first storage mutation. This eliminates the failure window entirely for the common case.
2. **Single commit point.** The two writes are adjacent with nothing fallible between them. In Soroban's execution model, a panic rolls back the whole call frame, so adjacency + panic-on-failure = atomicity.
3. **Events after commit.** Event emission is not part of the state invariant; keep it outside the critical section.
4. **No `Err` between the writes.** If the platform returns `Err` from a storage op without rolling back, that's a platform bug — but we defend against it by keeping the window to zero instructions.

### 3.2 Why Not a Manual Rollback?

A rollback pattern (`set_stream` → on failure `set_next_stream_id(id)`) is **fragile**:

- It requires the rollback itself to be infallible (it usually isn't).
- It doubles the write count (gas cost).
- It's easy to forget in future refactors.

**Reject manual rollback** unless the platform's execution model cannot guarantee frame-level rollback. If that's the case, escalate — the platform contract is the real bug.

### 3.3 Idempotency Guard (Defense in Depth)

Add a cheap assertion at the top of `create_stream`:

```rust
let id = storage::get_next_stream_id(&env);
if storage::has_stream(&env, id) {
    // Invariant already violated by a prior buggy version — fail loud, don't corrupt.
    panic_with_error!(&env, Error::StreamIdCollision);
}
```

This converts silent corruption into a loud, diagnosable failure. It also protects against the "reorder-only" regression if someone reintroduces it.

---

## 4. Regression Avoidance

| Risk | Mitigation |
|---|---|
| Reorder-only fix reintroduces collisions | Composite write makes ordering irrelevant; collision guard catches it |
| Future refactor inserts fallible code between writes | Enc

## Code Fix (SWE-2)
None\n