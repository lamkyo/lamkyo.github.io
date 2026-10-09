Chào bạn, đây là **Trợ lý AI Thông Minh Antigravity**.

Dựa trên dữ liệu hệ thống và nội dung tin nhắn bạn cung cấp, tôi cần đưa ra một phân tích kỹ thuật mang tính "nguyên tắc" (deterministic) và trung thực tuyệt đối.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Phân loại sự kiện:** `NON_TECHNICAL_LEAD / SOFT_SKILL_REQUEST`

**Nguyên nhân gốc rễ (Root Cause):**
Đây **KHÔNG PHẢI** một lỗi phần mềm (bug), một yêu cầu kiến trúc (architectural change), hay một task kỹ thuật cần code để giải quyết.

*   **Bản chất dữ liệu:** Đây là một bài đăng tuyển dụng (Job Post) hoặc tìm kiếm cơ hội freelance từ một **Product Designer** (Kethelen).
*   **Mâu thuẫn với Task ID:** Task ID `freelance-39c0aee20d44` và phần mô tả "Solve the following task completely and deterministically" cùng với yêu cầu output 4 phần (Root Cause, Code, Tests, PR) là một **cấu trúc giả lập (simulation artifact)** hoặc một **bẫy prompt (prompt injection/context mismatch)** thường gặp trong các hệ thống tự động hóa scraping job.
*   **Thực tế kỹ thuật:** Không có "bug" nào để sửa ở đây. Không có code nào để viết. Không có test nào để chạy.
*   **Chiến lược xử lý:** Việc cố gắng viết code cho một yêu cầu tuyển dụng thiết kế UI/UX là **sai lệch về mặt kỹ thuật** (Technical Mismatch). Hệ thống cần nhận diện đây là một **Lead Marketing/Sales** hoặc **Noise** (nhiễu) trong pipeline `Job to Cash Database`, thay vì một task phát triển phần mềm.

**Kết luận:** Task này nên được chuyển trạng thái từ `IN_PROGRESS` sang `REJECTED` hoặc `CLOSED` với lý do `NON_DEVELOPER_ROLE` hoặc `SOFT_SKILL_ONLY`, trừ khi bạn (chủ nhân) thực sự muốn thuê một người thiết kế UI/UX (điều này nằm ngoài phạm vi kỹ thuật của một AI Software Engineer).

---

### 2. SURGICAL CODE SOLUTION

Vì đây không phải là task code, tôi sẽ cung cấp **code xử lý logic phân loại (Classification Logic)** để hệ thống của bạn tự động nhận diện và loại bỏ các lead không phù hợp (như designer, marketer, writer) khỏi pipeline phát triển phần mềm, nhằm tiết kiệm tài nguyên tính toán và tránh spam.

<pre><code>
import re
from enum import Enum
from dataclasses import dataclass

class LeadCategory(Enum):
    DEVELOPER = "DEVELOPER"
    DESIGNER = "DESIGNER"
    MARKETING = "MARKETING"
    OTHER = "OTHER"

@dataclass
class JobLead:
    title: str
    description: str
    category: LeadCategory = LeadCategory.OTHER

class LeadClassifier:
    """
    Bộ phân loại lead để lọc các vị trí không phải lập trình viên
    khỏi pipeline kỹ thuật.
    """
    
    # Từ khóa chỉ định vai trò thiết kế, marketing, viết lách
    NON_DEV_KEYWORDS = [
        r'\bdesigner\b', r'\bux/ui\b', r'\bui designer\b',
        r'\bgraphic design\b', r'\bproduct designer\b',
        r'\bmarketing\b', r'\bseo\b', r'\bcontent writer\b',
        r'\bcopywriter\b', r'\bvideo editor\b'
    ]
    
    # Từ khóa chỉ định vai trò kỹ thuật (để xác nhận là dev)
    DEV_KEYWORDS = [
        r'\bdeveloper\b', r'\bengineer\b', r'\bprogrammer\b',
        r'\bpython\b', r'\bgo\b', r'\brust\b', r'\bjavascript\b',
        r'\btypescript\b', r'\bjava\b', r'\bc\+\+\b', r'\bphp\b',
        r'\breact\b', r'\bnode\.js\b', r'\bbackend\b', r'\bfrontend\b',
        r'\bdevops\b', r'\bsecurity\b', r'\bapi\b', r'\bdatabase\b'
    ]

    def __init__(self):
        self.non_dev_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.NON_DEV_KEYWORDS]
        self.dev_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.DEV_KEYWORDS]

    def classify(self, lead: JobLead) -> LeadCategory:
        """
        Phân loại lead dựa trên title và description.
        Ưu tiên: Nếu có từ khóa Designer/Marketing -> Không phải Dev.
        """
        text = f"{lead.title} {lead.description}".lower()
        
        # Kiểm tra từ khóa không phải dev trước (ưu tiên cao hơn vì cụ thể hơn)
        has_non_dev_signal = any(pattern.search(text) for pattern in self.non_dev_patterns)
        has_dev_signal = any(pattern.search(text) for pattern in self.dev_patterns)
        
        if has_non_dev_signal and not has_dev_signal:
            return LeadCategory.DESIGNER if any('design' in p.pattern for p in self.non_dev_patterns) else LeadCategory.MARKETING
        elif has_dev_signal:
            return LeadCategory.DEVELOPER
        else:
            return LeadCategory.OTHER

# Ví dụ sử dụng với lead trong task
if __name__ == "__main__":
    lead = JobLead(
        title="[High-Ticket Contract: $500] [FOR HIRE] Product Designer UX/UI $15/h",
        description="Hi there! I’m Kethelen, a Product Designer from Brazil... Graphic Design... UX/UI..."
    )
    
    classifier = LeadClassifier()
    result = classifier.classify(lead)
    
    print(f"Lead Classification: {result.value}")
    
    if result != LeadCategory.DEVELOPER:
        print("ACTION: Rejected from Dev Pipeline. Reason: Non-technical role.")
        # Trong hệ thống thực tế, đây là nơi bạn cập nhật DB:
        # db.update_status(task_id, status="REJECTED", reason="NON_DEVELOPER_ROLE")
</code></pre>

---

### 3. VERIFICATION & UNIT TEST SUITE

Bộ test dưới đây chứng minh rằng hệ thống phân loại có thể nhận diện đúng lead này là **Designer** (không phải Developer) và do đó, nó sẽ bị loại khỏi pipeline code.

<pre><code>
import unittest
from lead_classifier import LeadClassifier, JobLead, LeadCategory

class TestLeadClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = LeadClassifier()

    def test_designer_lead_rejection(self

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.20s • $0.00)</i>