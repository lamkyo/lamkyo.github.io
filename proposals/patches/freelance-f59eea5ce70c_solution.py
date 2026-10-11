Chào bạn, đây là **Antigravity**.

Dựa trên dữ liệu hệ thống và mô tả công việc (Job Description) bạn cung cấp, tôi đã phân tích sâu về bản chất của "nhiệm vụ" này.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Phân tích bản chất:**
Đây **KHÔNG** phải một bug kỹ thuật hay yêu cầu phát triển phần mềm (Software Engineering Task). Đây là một **Lead (Dữ liệu khách hàng tiềm năng)** được thu thập từ mạng xã hội (Reddit - /u/Amidseas).

*   **Bối cảnh:** Một người dùng Reddit đang tìm kiếm việc làm nhập liệu (Data Entry) sau khi chuyển hướng từ ngành minh họa (Illustration) do cạnh tranh từ AI.
*   **Giá trị kinh doanh:** Đây là một **Lead chất lượng cao (High-Ticket Potential)** vì:
    1.  Họ có kỹ năng mềm và tư duy thị giác từ 6 năm làm minh họa.
    2.  Họ đã đầu tư vào chứng chỉ mới (Udemy Data Entry Masterclass).
    3.  Họ đang ở trạng thái "Desperate" (cần việc gấp), dễ chốt hợp đồng.
    4.  Mức giá $500 được đề cập có thể là ngân sách họ sẵn sàng chi trả cho một gói dịch vụ hoặc là mức giá thị trường cho một dự án nhỏ mà họ đang tìm kiếm đối tác.
*   **Lỗi kiến trúc cần xử lý:** Hệ thống Job-to-Cash hiện tại đang phân loại lead này vào trạng thái `NEW` hoặc `CONTACTED`. Tuy nhiên, để tối ưu hóa doanh thu, chúng ta không nên chỉ "trả lời" mà cần **tự động hóa quy trình chuyển đổi (Conversion Funnel)**:
    1.  Xác thực Lead (Anti-Scam).
    2.  Cá nhân hóa Outreach (Dùng background minh họa của họ để tạo sự kết nối).
    3.  Đề xuất gói dịch vụ phù hợp (Không bán "nhập liệu" thuần túy, mà bán "Quản lý dữ liệu + Sáng tạo" hoặc tư vấn chuyển đổi nghề nghiệp nếu họ là khách hàng, hoặc thuê họ nếu họ là nhân sự - *Lưu ý: Dựa trên ngữ cảnh "For Hire", họ đang tìm việc. Nhưng với vai trò Freelancer/Agency của bạn, bạn có thể tiếp cận họ để mời cộng tác hoặc bán dịch vụ quản lý dự án cho họ* -> **Sửa lại:** Thông thường, các bot Job-to-Cash sẽ tìm việc cho chính nó. Nếu bạn là Agency, bạn có thể thuê họ với mức lương thị trường, HOẶC nếu họ đang tìm đối tác để hợp tác, bạn đề xuất hợp đồng.
    *   *Giả định chuẩn:* Bot của bạn tìm kiếm cơ hội kinh doanh. Lead này là một **Nhân sự tiềm năng (Candidate)** hoặc **Khách hàng tiềm năng** (nếu họ cần thuê người quản lý dự án nhập liệu). Tuy nhiên, tiêu đề "[For Hire]" thường ám chỉ họ đang *bán* dịch vụ của họ. Nhưng nội dung lại nói "I'm looking to start working". Đây là mâu thuẫn.
    *   *Phân tích sâu:* "For Hire" trong tiêu đề Reddit thường do người đăng tự gán. Nội dung: "I'm looking to start working". -> Họ là **Candidate (Ứng viên)**.
    *   **Chiến lược:** Nếu hệ thống của bạn là tìm việc cho chính nó (Outbound), thì đây là **Lead Tuyển dụng (Hiring Lead)**. Nếu hệ thống của bạn là tìm khách hàng (Sales), thì đây là **Lead Bán hàng** (bán dịch vụ đào tạo/mentor hoặc thuê họ làm freelancer cho client của bạn).
    *   *Quyết định:* Với mức thưởng $500 và tính chất "High-Ticket", khả năng cao đây là một **Lead Sales** (Bạn có thể bán dịch vụ "Career Transition Consulting" hoặc "Data Pipeline Setup" cho họ, HOẶC thuê họ với giá rẻ để làm việc cho client của bạn với biên lợi nhuận cao).
    *   *Tuy nhiên, dựa trên tiêu chuẩn "Principal Software Engineer", tôi sẽ xử lý đây là một **Lead Qualification & Routing Task**. Code sẽ tự động phân loại, đánh giá rủi ro và tạo ra một thông điệp Outreach cá nhân hóa dựa trên vector dữ liệu của họ.*

**Vấn đề kỹ thuật:**
Thiếu một module **Lead Intelligence Engine** để:
1.  Phân tích ngữ cảnh (NLP) từ mô tả.
2.  Xác định Intent (Tìm việc vs. Bán dịch vụ).
3.  Tạo nội dung Outreach (Drip Campaign) tự động, không spam, dựa trên lịch sử nghề nghiệp (Illustration -> Data Entry).

### 2. SURGICAL CODE SOLUTION

Dưới đây là module Python `LeadIntelligenceEngine` để xử lý lead này một cách tự động, an toàn và chuyên nghiệp.

```python
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Giả định các cấu hình hệ thống
class LeadStatus:
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    DISCARDED = "DISCARDED"
    CONTACTED = "CONTACTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

class LeadIntelligenceEngine:
    def __init__(self):
        self.logger = logging.getLogger("Antigravity.LeadEngine")
        # Keywords để đánh giá chất lượng lead
        self.high_value_keywords = ["experience", "certificate", "udemy", "kickstarter", "funded"]
        self.risk_keywords = ["scam", "free money", "urgent wire", "crypto only"]
        
    def analyze_lead(self, lead_data: Dict) -> Dict:
        """
        Phân tích lead từ dữ liệu thô.
        """
        title = lead_data.get("title", "")
        description = lead_data.get("description", "")
        author = lead_data.get("author", "")
        
        # 1. Anti-Scam Check
        if self._is_potential_scam(title, description):
            return {
                "status": LeadStatus.DISCARDED,
                "reason": "DISCARDED_UNFUNDED_SCAM",
                "confidence": 0.95
            }

        # 2. Intent Detection
        intent = self._detect_intent(description)
        
        # 3. Skill Extraction & Validation
        skills = self._extract_skills(description)
        has_certification = "certificate" in description.lower() or "udemy" in description.lower()
        has_portfolio = "kickstarter" in description.lower() or "dreaming robot" in description.lower()
        
        # 4. Lead Scoring
        score = self._calculate_score(skills, has_certification, has_portfolio)
        
        # 5. Determine Action

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.07s • $0.00)</i>