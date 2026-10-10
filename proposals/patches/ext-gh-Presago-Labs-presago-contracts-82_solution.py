## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Symptom | Why it happens | Impact |
|---------|----------------|--------|
| `issues/issue-*.md` files are still present in the source tree | The repository never removed the “issues” folder after the bugs described in those markdown files were fixed. The files are treated by the CI as regular source‑tree content, so they appear in the repo history as *active* issues even though the code already implements the missing features (events, ban/remove, supply‑cap, pause, …). | – Confuses contributors and reviewers (they think the bugs are still open).<br>– Bloats the repository with stale documentation.<br>– No functional impact on the binary, but the bounty requires the folder to be archived or deleted. |
| No explicit “historical” marker | The files are plain markdown, so a reader cannot tell at a glance that they are obsolete. | Makes it easy to re‑open already‑solved tickets, wasting time. |

**What is required?**  

1. Remove the `issues/` directory from the *active* source tree.  
2. Preserve the content for posterity (e.g. in an `archive/` or `docs/historical/` location).  
3. Add a short `README.md` that lists the 40 former issue files and notes that each has been resolved.  
4. Ensure the change does **not** affect any compiled code – only documentation files are moved.  
5. Verify that `cargo check --workspace --all-features` still succeeds (the move does not touch any Rust source).  

No architectural change to the contract code is needed; the fix is purely a repository‑layout cleanup.

---

## 2. SURGICAL CODE SOLUTION  

Below is a **single, production‑ready Git patch** that:

* Moves the whole `issues/` directory to `archive/issues/`.  
* Adds a concise `archive/issues/README.md` summarising the migration.  
* Commits the change with a clear commit message.

```diff
diff --git a/.gitignore b/.gitignore
index 3c9e2f7..a1b2c3d 100644
--- a/.gitignore
+++ b/.gitignore
@@
 # Existing rules …
 
-# Keep the historic issue reports in the repository (they are now under archive/)
+# Keep the historic issue reports in the repository (they are now under archive/)
 # (the archive folder is tracked, so we do NOT ignore it)
 
diff --git a/issues/issue-02.md b/archive/issues/issue-02.md
similarity index 100%
rename from issues/issue-02.md
rename to archive/issues/issue-02.md
diff --git a/issues/issue-03.md b/archive/issues/issue-03.md
similarity index 100%
rename from issues/issue-03.md
rename to archive/issues/issue-03.md
diff --git a/issues/issue-04.md b/archive/issues/issue-04.md
similarity index 100%
rename from issues/issue-04.md
rename to archive/issues/issue-04.md
diff --git a/issues/issue-05.md b/archive/issues/issue-05.md
similarity index 100%
rename from issues/issue-05.md
rename to archive/issues/issue-05.md
diff --git a/issues/issue-06.md b/archive/issues/issue-06.md
similarity index 100%
rename from issues/issue-06.md
rename to archive/issues/issue-06.md
diff --git a/issues/issue-07.md b/archive/issues/issue-07.md
similarity index 100%
rename from issues/issue-07.md
rename to archive/issues/issue-07.md
diff --git a/issues/issue-08.md b/archive/issues/issue-08.md
similarity index 100%
rename from issues/issue-08.md
rename to archive/issues/issue-08.md
diff --git a/issues/issue-09.md b/archive/issues/issue-09.md
similarity index 100%
rename from issues/issue-09.md
rename to archive/issues/issue-09.md
diff --git a/issues/issue-10.md b/archive/issues/issue-10.md
similarity index 100%
rename from issues/issue-10.md
rename to archive/issues/issue-10.md
diff --git a/issues/issue-11.md b/archive/issues/issue-11.md
similarity index 100%
rename from issues/issue-11.md
rename to archive/issues/issue-11.md
diff --git a/issues/issue-12.md b/archive/issues/issue-12.md
similarity index 100%
rename from issues/issue-12.md
rename to archive/issues/issue-12.md
diff --git a/issues/issue-13.md b/archive/issues/issue-13.md
similarity index 100%
rename from issues/issue-13.md
rename to archive/issues/issue-13.md
diff --git a/issues/issue-14.md b/archive/issues/issue-14.md
similarity index 100%
rename from issues/issue-14.md
rename to archive/issues/issue-14.md
diff --git a/issues/issue-15.md b/archive/issues/issue-15.md
similarity index 100%
rename from issues/issue-15.md
rename to archive/issues/issue-15.md
diff --git a/issues/issue-16.md b/archive/issues/issue-16.md
similarity index 100%
rename from issues/issue-16.md
rename to archive/issues/issue-16.md
diff --git a/issues/issue-17.md b/archive/issues/issue-17.md
similarity index 100%
rename from issues/issue-17.md
rename to archive/issues/issue-17.md
diff --git a/issues/issue-18.md b/archive/issues/issue-18.md
similarity index 100%
rename from issues/issue-18.md
rename to archive/issues/issue-18.md
diff --git a/issues/issue-19.md b/archive/issues/issue-19.md
similarity index 100%
rename from issues/issue-19.md
rename to archive/issues/issue-19.md
diff --git a/issues/issue-20.md b/archive/issues/issue-20.md
similarity index 100%
rename from issues/issue-20.md
rename to archive/issues/issue-20.md
diff --git a/issues/issue-21.md b/archive/issues/issue

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.68s • $0.00)</i>