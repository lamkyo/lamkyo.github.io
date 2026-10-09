Chào bạn, tôi là **Antigravity**.

Tôi đã phân tích kỹ "Task" mà bạn gửi. Trước khi đi vào các phần kỹ thuật, tôi cần làm rõ một điểm quan trọng về **Bản chất của Dữ liệu (Data Nature)**:

Đây **KHÔNG PHẢI** một bug, lỗi code, hay yêu cầu kỹ thuật phần mềm (Software Engineering Task). Đây là một **Lead Marketing / Job Posting** (Tin tuyển dụng) từ một cá nhân tên là Ángel đang bán dịch vụ của anh ta (Virtual Assistant, $15/hour).

Trong hệ sinh thái "Job to Cash" của bạn, mục tiêu là **tìm việc cho bot/chủ nhân** hoặc **bán dịch vụ cho khách hàng**.
*   **Nếu bạn là người mua (Client):** Bạn không cần "code" để giải quyết tin tuyển dụng này. Bạn chỉ cần liên hệ nếu cần thuê VA.
*   **Nếu bạn là người bán (Provider):** Tin này là **NGUY HIỂM** hoặc **KHÔNG PHÙ HỢP**.
    *   Lý do 1: Đây là tin *tuyển dụng* (For Hire), không phải tin *đặt hàng* (Hiring).
    *   Lý do 2: Mức giá $15/hour là mức giá lao động phổ thông, không phải "High-Ticket Contract $500" như tiêu đề gây hiểu lầm.
    *   Lý do 3: Rủi ro scam cao (Venezuela, yêu cầu DM/email trực tiếp, không qua nền tảng trung gian bảo vệ thanh toán).

Tuy nhiên, để đáp ứng đúng định dạng kỹ thuật mà bạn yêu cầu (giả sử hệ thống của bạn cần một **Bộ lọc (Filter)** hoặc **Crawler** để tự động xử lý loại lead này), tôi sẽ cung cấp giải pháp kỹ thuật: **Viết một bộ lọc thông minh (Intelligent Filter) để tự động loại bỏ (REJECT) các lead dạng "Self-Promotion/Job Seeking" khỏi hàng đợi Outreach, tránh lãng phí token API và thời gian.**

Dưới đây là giải pháp kỹ thuật hoàn chỉnh cho bài toán: **"Tự động hóa việc phân loại và loại bỏ các Job Posting không phải là RFP (Request for Proposal) thực sự."**

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Vấn đề (Root Cause):**
Hệ thống "Job to Cash" đang thu thập dữ liệu thô từ các nguồn (Reddit, LinkedIn, Freelance platforms). Nhiều mục có tiêu đề hấp dẫn (ví dụ: "$500 High-Ticket") nhưng nội dung thực tế là **cá nhân đang tìm việc (Job Seeker)** chứ không phải **khách hàng đang tìm dịch vụ (Client/Hiring Manager)**.

Nếu bot cố gắng "outreach" (gửi proposal) cho một người đang tìm việc, điều đó sẽ:
1.  Gây phiền toái (Spam).
2.  Tiêu tốn chi phí API (Email/Telegram).
3.  Làm giảm tỷ lệ chuyển đổi (Conversion Rate) vì đối tượng không đúng.

**Yêu cầu Kiến trúc (Architectural Change):**
Cần thêm một lớp **Pre-Processing Filter** (Bộ lọc tiền xử lý) ngay sau bước Fetch Data và trước bước Generate Proposal.
Bộ lọc này cần phân tích văn bản (NLP/Heuristic) để xác định:
*   **Intent:** `HIRING` (Khách hàng thuê) vs `SEEKING` (Cá nhân tìm việc).
*   **Keywords:** "For Hire", "Looking for work", "My rates are", "DM me", "Available for".
*   **Action:** Nếu là `SEEKING`, đánh dấu trạng thái là `REJECTED_SELF_PROMOTION` và đưa vào `BENCHMARK_EXCLUDED` hoặc `DISCARDED`.

### 2. SURGICAL CODE SOLUTION

Đây là module Python `lead_filter.py` tích hợp vào pipeline của bạn. Nó sử dụng heuristic nhẹ (không cần LLM đắt tiền) để chạy nhanh và chính xác cho các pattern phổ biến.

<pre><code>
import re
import logging
from dataclasses import dataclass
from enum import Enum

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AntigravityLeadFilter")

class LeadIntent(Enum):
    HIRING = "HIRING"          # Khách hàng đang tìm dịch vụ
    SEEKING = "SEEKING"        # Cá nhân đang tìm việc (Self-promotion)
    UNKNOWN = "UNKNOWN"

@dataclass
class LeadAnalysisResult:
    intent: LeadIntent
    confidence: float  # 0.0 to 1.0
    reasons: list[str]

class LeadFilter:
    """
    Bộ lọc thông minh để phân loại Lead là HIRING hay SEEKING.
    Được thiết kế để chạy trong pipeline Job-to-Cash.
    """
    
    # Các từ khóa chỉ ra người đăng đang TÌM VIỆC (Negative Signals)
    SEEKING_KEYWORDS = [
        r"\bfor hire\b",
        r"\blooking for (work|opportunit|jobs|clients)\b",
        r"\bmy rate(s)? (is|are)\b",
        r"\bopen to (project|freelance|remote)\b",
        r"\bdm me\b",
        r"\bemail me\b",
        r"\bmy portfolio\b",
        r"\bavailable (for|to)\b",
        r"\bvirtual assistant\b",  # Thường là title của người tìm việc nếu đứng một mình
        r"\bseeking (work|clients)\b",
        r"\bresume\b",
        r"\bexperience in\b",
        r"\bi am (a|an)\b",
    ]

    # Các từ khóa chỉ ra người đăng đang THUÊ (Positive Signals)
    HIRING_KEYWORDS = [
        r"\bwe are looking for\b",
        r"\bneed (a|an|some)\b",
        r"\bhire (a|an|someone)\b",
        r"\brequest for proposal\b",
        r"\brfp\b",
        r"\bjob description\b",
        r"\bapply here\b",
        r"\bcompensation\b",
        r"\bbudget\b",
        r"\bwe need\b",
        r"\bclient\b",
    ]

    def __init__(self):
        # Compile regex cho hiệu suất
        self.seeking_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.SEEKING_KEYWORDS]
        self.hiring_patterns = [re.compile(kw, re.IGNORECASE) for kw in self.HIRING_KEYWORDS]

    def analyze(self, title: str, description: str) -> LeadAnalysisResult:
        """
        Phân tích tiêu đề và mô tả để xác định intent.

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.16s • $0.00)</i>