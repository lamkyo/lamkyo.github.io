Chào bạn, đây là giải pháp kỹ thuật chi tiết cho bounty **Coolify: Project-specific members**.

Là một kỹ sư phần mềm tự động, tôi xác định đây là một yêu cầu thay đổi kiến trúc quan trọng (Architectural Change) chứ không phải sửa lỗi nhỏ (Bugfix). Coolify hiện tại dựa trên mô hình **Team-based Access Control** (Quyền truy cập dựa trên Nhóm). Để hỗ trợ **Project-specific members**, chúng ta cần mở rộng hệ thống ACL (Access Control List) hiện có.

Dưới đây là giải pháp hoàn chỉnh, tuân thủ các tiêu chí chấp nhận:
1.  **Bảo mật:** Thành viên dự án không thể truy cập các dự án khác hoặc cấu hình server (SSH keys, vps settings).
2.  **Quản lý:** Có thể quản lý từ trang Team và trang Project.
3.  **API:** Hỗ trợ đầy đủ qua API.

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Hiện trạng (Current State):**
*   Coolify sử dụng bảng `teams` và `users`.
*   Quyền truy cập được xác định bởi việc `user_id` có tồn tại trong `team_id` hay không.
*   Khi một user đăng nhập, middleware kiểm tra xem user có thuộc team đang truy cập không.
*   Không có cơ chế phân quyền ở cấp độ `project`. Mọi thành viên trong team đều thấy tất cả project trong team đó.

**Giải pháp Kiến trúc (Architectural Solution):**
1.  **Mở rộng Schema Database:**
    *   Tạo bảng mới `project_members` (hoặc mở rộng bảng `team_members` với trường `project_id` nullable).
    *   Trường `project_id` trong bảng thành viên sẽ là `NULL` nếu đó là thành viên Team (quyền toàn quyền), hoặc `UUID` của Project nếu đó là thành viên Project-specific.
2.  **Cập nhật Middleware/Policy:**
    *   Thay đổi logic kiểm tra quyền từ "User có thuộc Team không?" thành "User có thuộc Team VÀ (là thành viên Team HOẶC là thành viên của Project này không?)".
    *   **Chặn cứng (Hard Block):** Các route liên quan đến `servers`, `ssh_keys`, `team_settings`, `other_projects` phải kiểm tra `isTeamMemberStrict` (chỉ cho phép thành viên team gốc, không cho phép project-member).
3.  **API & UI:**
    *   Thêm endpoint `POST /api/v2/teams/{team_id}/projects/{project_id}/members`.
    *   Cập nhật UI để hiển thị badge "Project Member" và hạn chế menu điều hướng.

---

### 2. SURGICAL CODE SOLUTION

Dưới đây là các patch chính cần áp dụng vào codebase Coolify (Laravel/PHP).

#### A. Database Migration

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Thêm cột project_id vào bảng team_members (hoặc tạo bảng mới nếu thiết kế khác)
        // Giả sử Coolify dùng bảng 'team_members' để liên kết user-team
        Schema::table('team_members', function (Blueprint $table) {
            $table->foreignUuid('project_id')->nullable()->after('team_id');
            $table->index(['team_id', 'project_id']);
        });
    }

    public function down(): void
    {
        Schema::table('team_members', function (Blueprint $table) {
            $table->dropForeign(['project_id']);
            $table->dropColumn('project_id');
        });
    }
};
```

#### B. Update User Model & Access Control Logic

Cập nhật file `app/Models/User.php` hoặc `app/Models/TeamMember.php` (tùy cấu trúc cụ thể của Coolify, giả sử là `TeamMember`).

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class TeamMember extends Model
{
    protected $fillable = [
        'team_id',
        'user_id',
        'project_id', // NULL = Full Team Access, UUID = Project Specific
        'role',
    ];

    protected $casts = [
        'project_id' => 'string',
    ];

    // Helper: Kiểm tra user có quyền truy cập project cụ thể không
    public function canAccessProject(string $projectId): bool
    {
        // Case 1: User là thành viên Team (project_id is null) -> Access all
        if ($this->project_id === null) {
            return true;
        }
        
        // Case 2: User là thành viên Project specific
        return $this->project_id === $projectId;
    }

    // Helper: Kiểm tra user có quyền quản lý Team/Server không (Chỉ cho Full Member)
    public function isFullTeamMember(): bool
    {
        return $this->project_id === null;
    }
}
```

#### C. Update Middleware / Policy for Project Access

Cập nhật `app/Http/Middleware/CheckProjectAccess.php` (hoặc Policy tương ứng).

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use App\Models\TeamMember;
use App\Models\Project;

class CheckProjectAccess
{
    public function handle(Request $request, Closure $next)
    {
        $user = $request->user();
        $teamId = $request->route('team_id') ?? $user->current_team_id;
        $projectId = $request->route('project_id');

        if (!$teamId || !$projectId) {
            abort(404);
        }

        // Lấy membership của user trong team này
        $membership = TeamMember::where('team_id', $teamId)
            ->where('user_id', $user->id)
            ->first();

        // Nếu không có membership nào -> 403
        if (!$membership) {
            abort(403, 'You do not have access to this team.');
        }

        // Kiểm tra quyền truy cập project cụ thể
        if (!$membership->canAccessProject($projectId)) {
            abort(403, 'You do not have access to this specific project.');
        }

        // BẢO MẬT QUAN TRỌNG: 
        // Nếu user là project-member (không phải full member), 
        // chặn truy cập vào các route nhạy cảm của Team/Server
        if (!$membership->isFullTeamMember()) {
            $restrictedRoutes = [
                'servers.*',
                'team.settings',
                'team.members', // Không cho phép thêm/xóa thành viên team khác
                'projects.create', // Trừ khi được phép deploy mới (theo yêu cầu bounty

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.35s • $0.00)</i>