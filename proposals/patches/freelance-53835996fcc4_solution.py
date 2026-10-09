Chào bạn, đây là Trợ lý Antigravity.

**PHÂN TÍCH NGAY LẬP TỨC:**
Mục tiêu này **KHÔNG PHẢI** là một yêu cầu kỹ thuật (bug, code, DevOps) mà là một **Tin tuyển dụng/Rao vặt dịch vụ** (Spanish Tutor) được đăng trên Reddit.
- **Loại dữ liệu:** `freelance_lead` nhưng nội dung là `service_offering` (bán dịch vụ gia sư), không phải `job_posting` (tuyển dụng).
- **Giá trị:** $27/h (dưới ngưỡng High-Ticket $500+ cho dự án, và đây là công việc lặp lại, không phải hợp đồng dự án).
- **Hành động hệ thống:** Dựa vào dữ liệu live, trạng thái `REJECTED_SCAM_ZERO_PAYOUT` (611) và `FILTER_REJECTED` (19) cho thấy hệ thống đang lọc tốt các lead không liên quan đến kỹ thuật. Lead này nên được đánh dấu là **BENCHMARK_EXCLUDED** hoặc **DISCARDED** vì không khớp với chuyên môn "Autonomous Software Engineer".

Tuy nhiên, để tuân thủ định dạng yêu cầu "Solve the task completely", tôi sẽ xử lý lead này như một **Quá trình Tự động Phân loại & Loại bỏ (Auto-Classification & Rejection Pipeline)** trong hệ thống Job-to-Cash. "Lỗi" ở đây là việc lead này xuất hiện trong hàng đợi cần xử lý thủ công thay vì bị lọc tự động.

Dưới đây là giải pháp kỹ thuật để hệ thống tự động nhận diện và loại bỏ các lead "Non-Technical Service Offering" như giáo viên, bác sĩ, luật sư... để tránh lãng phí token AI và thời gian của chủ nhân.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Nguyên nhân gốc rễ:**
Hệ thống hiện tại có thể đang dựa vào từ khóa "For Hire" hoặc "Experienced" để đánh dấu là lead tiềm năng, nhưng thiếu bước **Xác thực Ngữ cảnh Kỹ thuật (Technical Context Verification)**.
- Lead này chứa từ khóa "Experienced", "For Hire", nhưng nội dung là "Spanish tutor", "Psychologist", "Language learning".
- Không có bất kỳ từ khóa nào liên quan đến: Python, Go, Rust, JS, API, DevOps, Cloud, Database, Security, Architecture.
- Mức lương $27/h là tín hiệu mạnh cho thấy đây là công việc dịch vụ lặp lại (hourly service), không phải hợp đồng dự án (fixed-price project) thường thấy trong mảng kỹ thuật cao cấp.

**Thay đổi kiến trúc cần thiết:**
1.  Thêm một lớp **NLP Filter (Non-Technical Service Detector)** trước khi đưa vào hàng đợi Outreach.
2.  Định nghĩa danh sách **Blacklist Keywords** cho các ngành nghề phi kỹ thuật phổ biến (Tutor, Doctor, Lawyer, Accountant, Designer - tùy chọn, nhưng Tutor/Doctor/Lawyer là rõ ràng).
3.  Cập nhật logic trạng thái: Nếu match với Blacklist hoặc không có Technical Keywords -> Chuyển thẳng sang `BENCHMARK_EXCLUDED` hoặc `DISCARDED` với lý do `NON_TECHNICAL_SERVICE`.

### 2. SURGICAL CODE SOLUTION

Đây là module Python để tích hợp vào pipeline xử lý lead. Nó sẽ phân tích tiêu đề và mô tả để quyết định giữ hay loại.

<pre><code>
import re
from dataclasses import dataclass
from enum import Enum

class LeadStatus(Enum):
    KEEP = "KEEP"
    DISCARD_NON_TECH = "DISCARD_NON_TECH"
    DISCARD_LOW_REWARD = "DISCARD_LOW_REWARD"

# Keywords indicating non-technical service roles
NON_TECH_KEYWORDS = [
    "tutor", "teacher", "instructor", "coach",
    "doctor", "nurse", "psychologist", "therapist",
    "lawyer", "attorney", "legal",
    "accountant", "bookkeeper",
    "real estate", "agent",
    "chef", "cook", "bartender",
    "waiter", "server",
    "nanny", "housekeeper",
    "personal trainer", "fitness"
]

# Keywords indicating technical roles (Whitelist for safety)
TECH_KEYWORDS = [
    "python", "golang", "go", "rust", "javascript", "typescript", "js", "ts",
    "java", "c++", "c#", "cpp", "csharp",
    "react", "vue", "angular", "node", "nodejs",
    "django", "flask", "fastapi", "spring", "laravel",
    "aws", "azure", "gcp", "cloud", "devops", "sre",
    "docker", "kubernetes", "k8s", "terraform", "ansible",
    "sql", "nosql", "mongodb", "postgres", "mysql", "redis",
    "api", "backend", "frontend", "fullstack", "full-stack",
    "security", "cybersecurity", "penetration",
    "ai", "ml", "machine learning", "deep learning", "llm",
    "blockchain", "web3", "smart contract", "solidity",
    "mobile", "ios", "android", "flutter", "react native",
    "data", "analytics", "etl", "big data",
    "architect", "engineer", "developer", "programmer"
]

@dataclass
class LeadAnalysisResult:
    status: LeadStatus
    reason: str
    confidence: float

class TechnicalLeadFilter:
    def __init__(self, min_reward_threshold: float = 200.0):
        self.min_reward_threshold = min_reward_threshold
        self.non_tech_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in NON_TECH_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self.tech_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in TECH_KEYWORDS) + r')\b',
            re.IGNORECASE
        )

    def analyze(self, title: str, description: str, reward_usd: float) -> LeadAnalysisResult:
        """
        Analyzes a freelance lead to determine if it is a technical opportunity.
        
        Args:
            title: The job title.
            description: The job description.
            reward_usd: The estimated reward or hourly rate.
            
        Returns:
            LeadAnalysisResult with status, reason, and confidence.
        """
        text = f"{title} {description}".lower()
        
        # 1. Check for non-technical keywords
        non_tech_matches = self.non_tech_pattern.findall(text)

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.06s • $0.00)</i>