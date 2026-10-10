Chào bạn, tôi là **Antigravity**.

Dựa trên dữ liệu hệ thống và mô tả công việc (Task ID: `freelance-1144121e8654`), đây là một trường hợp **Sai lệch loại hình công việc (Category Mismatch)**.

Hệ thống của chúng ta là một nền tảng **Phần mềm Tự động hóa & DevOps** (xử lý code, pipeline, API, VPS). Tuy nhiên, công việc này yêu cầu kỹ năng **Chỉnh sửa ảnh thủ công (Photoshop/AI)** và phục chế ảnh vật lý.

Việc chấp nhận công việc này sẽ dẫn đến:
1.  **Vi phạm SLA:** Chúng ta không có năng lực xử lý ảnh pixel-level thủ công.
2.  **Rủi ro Tài chính:** Khả năng bị từ chối thanh toán do không đáp ứng yêu cầu nghệ thuật/kỹ thuật hình ảnh.
3.  **Ô nhiễm Pipeline:** Làm gián đoạn luồng xử lý tự động hóa mã nguồn.

Dưới đây là giải pháp kỹ thuật để **từ chối tự động** và **phân loại chính xác** lead này trong hệ thống.

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Nguyên nhân gốc rễ:**
Bộ lọc phân loại (Classifier) hiện tại của hệ thống Job-to-Cash đang dựa vào từ khóa (keyword matching) hoặc mô tả chung chung. Cụm từ "AI tools" trong mô tả đã gây nhầm lẫn, khiến hệ thống có thể đánh giá nhầm đây là một công việc liên quan đến tích hợp AI/ML (Machine Learning) thay vì sử dụng các công cụ AI có sẵn (như Photoshop Generative Fill) cho mục đích nghệ thuật.

**Phân tích kiến trúc:**
- **Input:** Lead từ Reddit/Freelance platform.
- **Expected Output:** `DISCARDED_NOT_A_JOB` hoặc `REJECTED_CATEGORY_MISMATCH`.
- **Current Behavior:** Có nguy cơ bị đẩy vào `MANUAL_REVIEW` hoặc `NEW`, gây lãng phí tài nguyên nhân sự.
- **Required Change:** Cần bổ sung quy tắc **Negative Keyword Filtering** và **Skill Domain Validation** để xác định rõ đây là dịch vụ "Creative/Graphic Design" chứ không phải "Software Engineering/DevOps".

---

### 2. SURGICAL CODE SOLUTION

Chúng ta sẽ cập nhật module `job_classifier.py` để thêm logic kiểm tra loại hình kỹ năng.

```python
import re
from enum import Enum
from typing import Optional

class JobCategory(Enum):
    SOFTWARE_ENGINEERING = "software_engineering"
    DEVOPS_INFRA = "devops_infra"
    CREATIVE_DESIGN = "creative_design"
    OTHER = "other"

class JobStatus(Enum):
    ACCEPTED = "accepted"
    REJECTED_CATEGORY_MISMATCH = "rejected_category_mismatch"
    REJECTED_NOT_A_JOB = "rejected_not_a_job"

class JobClassifier:
    """
    Module phân loại lead công việc dựa trên mô tả và kỹ năng yêu cầu.
    """
    
    # Các từ khóa đặc trưng cho lĩnh vực Sáng tạo/Thiết kế (không thuộc phạm vi phần mềm)
    CREATIVE_KEYWORDS = [
        r"photo\s+restoration",
        r"photoshop",
        r"photo\s+editing",
        r"image\s+retouching",
        r"graphic\s+design",
        r"illustration",
        r"video\s+editing",
        r"content\s+creation",
        r"social\s+media\s+management"
    ]
    
    # Các từ khóa đặc trưng cho lĩnh vực Phần mềm (phạm vi của chúng ta)
    SOFTWARE_KEYWORDS = [
        r"python", r"javascript", r"typescript", r"go", r"rust",
        r"api", r"backend", r"frontend", r"fullstack",
        r"docker", r"kubernetes", r"aws", r"azure", r"gcp",
        r"database", r"sql", r"nosql",
        r"bug\s+fix", r"feature\s+development", r"code\s+review"
    ]

    def __init__(self):
        self.creative_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.CREATIVE_KEYWORDS]
        self.software_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.SOFTWARE_KEYWORDS]

    def classify(self, title: str, description: str) -> tuple[JobCategory, JobStatus, Optional[str]]:
        """
        Phân loại lead.
        Returns: (Category, Status, Reason)
        """
        text = f"{title} {description}".lower()
        
        creative_score = 0
        software_score = 0
        
        for pattern in self.creative_patterns:
            if pattern.search(text):
                creative_score += 1
                
        for pattern in self.software_patterns:
            if pattern.search(text):
                software_score += 1

        # Logic quyết định
        if creative_score > 0 and software_score == 0:
            return JobCategory.CREATIVE_DESIGN, JobStatus.REJECTED_CATEGORY_MISMATCH, "Lead thuộc lĩnh vực Sáng tạo/Thiết kế, không phù hợp với năng lực Phần mềm."
        
        if software_score > 0 and creative_score == 0:
            return JobCategory.SOFTWARE_ENGINEERING, JobStatus.ACCEPTED, "Lead phù hợp với năng lực kỹ thuật phần mềm."
        
        if software_score > 0 and creative_score > 0:
            # Trường hợp hỗn hợp, ưu tiên kiểm tra thủ công hoặc từ chối nếu thiên về thiết kế
            if creative_score > software_score:
                return JobCategory.CREATIVE_DESIGN, JobStatus.REJECTED_CATEGORY_MISMATCH, "Lead thiên về thiết kế nhiều hơn kỹ thuật."
            else:
                return JobCategory.OTHER, JobStatus.REJECTED_CATEGORY_MISMATCH, "Lead hỗn hợp, cần đánh giá lại."
        
        return JobCategory.OTHER, JobStatus.REJECTED_NOT_A_JOB, "Không xác định được kỹ năng phù hợp."

# --- IMPLEMENTATION IN PRODUCTION PIPELINE ---

def process_lead(lead_data: dict):
    """
    Hàm xử lý lead đầu vào trong pipeline Job-to-Cash.
    """
    classifier = JobClassifier()
    title = lead_data.get('title', '')
    description = lead_data.get('description', '')
    
    category, status, reason = classifier.classify(title, description)
    
    # Cập nhật trạng thái trong Database
    if status == JobStatus.REJECTED_CATEGORY_MISMATCH:
        # Gán trạng thái cụ thể để thống kê
        db_status = "DISCARDED_NOT_A_JOB" 
        # Hoặc tạo trạng thái mới: "DISCARDED_CATEGORY_MISMATCH"
        update_job_status(lead_data['id'], db_status, reason)

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.82s • $0.00)</i>