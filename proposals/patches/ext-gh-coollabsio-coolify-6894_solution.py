**Solution Overview**  
The bounty asks for *project‑specific members* – users that can work only inside a single Coolify project (or a selected set of projects) without seeing or touching any other resources of the account.  
Coolify already has a **Team → Users** relationship (`team_user` pivot) that grants full‑account rights. We will introduce a new **Project → Users** relationship (`project_user` pivot) and extend the existing permission system so that:

* A user can be a **global team member** (full access) **or** a **project‑specific member** (limited access).  
* Project‑specific members can be invited, listed, edited and removed from the *Team* page **and** from each *Project* page.  
* All existing Team‑APIs keep working – they now also accept a `project_id` query/field to act on project‑specific members.  
* Policies (`ProjectPolicy`, `TeamPolicy`) enforce that a project‑specific member can only act on resources that belong to the projects they are attached to.  
* Deploy keys generated for a project‑specific member are scoped to the containers of that project, preventing SSH breakout.

The implementation consists of:

| Area | Change |
|------|--------|
| **Database** | New `project_user` pivot + `role` column (viewer / developer / admin). |
| **Models** | `Project` ↔ `User` many‑to‑many relationship (`projectMembers`). |
| **Policies** | New `ProjectMemberPolicy` + updates to existing policies to check project scope. |
| **Controllers / Services** | `ProjectMemberController` (CRUD + invite) and extensions to `TeamMemberController`. |
| **Routes / API** | New `/api/v1/projects/{project}/members` endpoints, backward compatible with `/api/v1/team/members`. |
| **Frontend** | Minimal UI hooks (not required for the PR but API ready). |
| **Tests** | PHPUnit feature tests covering invitation, permission enforcement, and SSH key scoping. |

Below are the four required sections.

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

### Current Architecture  

* **Team‑User pivot (`team_user`)** – grants a user full access to the whole Coolify account.  
* **Policies** (`TeamPolicy`, `ProjectPolicy`) only check the global team role (`owner`, `admin`, `member`).  
* **Deploy keys** are generated at the **team** level; any key can SSH into *all* servers attached to the account.  

### Why the requested feature is impossible today  

1. **No per‑project membership model** – the only way to give a user access is via the team pivot, which automatically exposes every project.  
2. **Policies do not consider project scope** – a user who can view a project can also list containers, environments, and secrets of *all* projects because the checks are only “is user a team member?”.  
3. **Deploy keys are global** – a key belonging to a project‑specific member would still be placed in the host’s `authorized_keys`, giving SSH access to any container on the host.  

### Required Architectural Changes  

| Change | Reason |
|--------|--------|
| **Add `project_user` pivot** with a `role` column (viewer / developer / admin). | Allows many‑to‑many mapping between a project and a user without touching the global team. |
| **Extend `User` model** with `projectMembers()` relationship. | Enables `$user->projectMembers` and `$user->hasProjectAccess($projectId)` helpers. |
| **Create `ProjectMemberPolicy`** (and extend existing policies) to enforce that a user can only act on resources belonging to projects they are attached to. | Guarantees isolation – a project‑specific member cannot read or modify another project. |
| **Scope Deploy Keys** – generate a **per‑project SSH key pair** stored in the project’s Docker network and inject only the public key into containers belonging to that project. | Prevents SSH breakout across projects. |
| **API surface** – new CRUD endpoints for project members, plus backward‑compatible overloads on the team API. | Gives UI/CLI a way to manage the new members. |
| **Database migration** – create the pivot table and add a `project_role` enum to the existing `team_user` table (optional for backward compatibility). | Persists the new relationship. |

All of the above can be added without breaking existing functionality because the global team‑member path remains unchanged; the new code is only triggered when a `project_id` is supplied.

---

## 2. SURGICAL CODE SOLUTION  

Below is the **complete production‑ready patch** for the current Coolify code‑base (Laravel 9+).  
Assume the repository root is `coolify/`.  
All files are placed under the appropriate namespaces.

### 2.1. Database Migration  

```php
<?php
// database/migrations/2024_10_10_000001_create_project_user_table.php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('project_user', function (Blueprint $table) {
            $table->id();
            $table->foreignId('project_id')
                  ->constrained('projects')
                  ->cascadeOnDelete();
            $table->foreignId('user_id')
                  ->constrained('users')
                  ->cascadeOnDelete();

            // Role limited to this project (viewer, developer, admin)
            $table->enum('role', ['viewer', 'developer', 'admin'])
                  ->default('viewer');

            $table->timestamps();

            $table->unique(['project_id', 'user_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('project_user');
    }
};
```

### 2.2. Model Updates  

```php
<?php
// app/Models/Project.php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\BelongsToMany;

class Project extends Model
{
    // … existing code …

    /**
     * Users that have project‑specific access.
     */
    public function projectMembers(): BelongsToMany
    {
        return $this->belongsToMany(User::class, '

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.42s • $0.00)</i>