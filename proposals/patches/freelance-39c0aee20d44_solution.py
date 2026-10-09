Chào bạn, tôi là **Antigravity**.

Dựa trên dữ liệu hệ thống và nội dung Task ID `freelance-39c0aee20d44`, tôi đã phân tích sâu. Đây **KHÔNG PHẢI** một lỗi kỹ thuật (bug) hay yêu cầu viết code phần mềm, mà là một **Lead (Cơ hội kinh doanh)** hoặc một **Yêu cầu tuyển dụng** được đưa vào hệ thống tự động hóa.

Tuy nhiên, trong ngữ cảnh của một "Autonomous Software Engineer", việc xử lý task này đòi hỏi sự phân tích chính xác về bản chất dữ liệu để đưa ra hành động phù hợp: **Lọc (Filter)** hoặc **Chuyển đổi sang Outreach**.

Dưới đây là giải pháp chuẩn hóa cho hệ thống Antigravity để xử lý loại task này một cách tự động và an toàn:

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Vấn đề cốt lõi:**
Hệ thống đang nhận một tin nhắn dạng "FOR HIRE" (Tôi đang tìm việc) từ một Product Designer (Kethelen) và gán nó vào pipeline `freelance_lead` với phần thưởng $500.

**Phân tích kỹ thuật:**
1.  **Mismatch của Pipeline:** Pipeline `freelance_lead` thường được thiết kế để tìm **khách hàng** (người thuê) cho dịch vụ của chúng ta, hoặc tìm **việc làm** cho đội ngũ kỹ thuật của chúng ta. Tin nhắn này là một **thiết kế viên đang tìm việc**.
2.  **Rủi ro An ninh/Chất lượng:**
    *   Link Instagram chứa các tham số tracking (`obrf`, `utm_source`) điển hình của spam hoặc bot, dù nội dung trông có vẻ chân thực (câu chuyện về chú mèo).
    *   Nếu đây là một "scam" (lừa đảo) thường gặp trên các nền tảng freelance (đòi đặt cọc, hoặc không trả tiền), hệ thống cần có cơ chế xác minh.
    *   Nếu đây là lead thật, nó **không phù hợp** với năng lực cốt lõi của Antigravity (Software Engineering/DevOps) trừ khi dự án cần UI/UX code implementation (Frontend).
3.  **Hành động cần thiết:**
    *   Hệ thống cần phân loại lại task này từ `IN_PROGRESS` sang `REJECTED_LEAK` hoặc `CONTACTED` (nếu quyết định tiếp cận để chào bán dịch vụ Frontend/Dev của chúng ta cho cô ấy).
    *   **Chiến lược tối ưu:** Thay vì từ chối hoàn toàn, Antigravity nên tự động gửi một tin nhắn chào mời dịch vụ **Frontend Development** (React/Next.js) dựa trên thiết kế của cô ấy, hoặc từ chối nếu ngoài phạm vi dịch vụ.

**Kết luận kỹ thuật:**
Task này cần được xử lý bởi module **Lead Qualification & Outreach**, không phải module **Code Generation**. Việc "Solve" ở đây là tạo ra một **Script Outreach** hoặc **Quy tắc Lọc** để hệ thống tự động phản hồi đúng cách.

### 2. SURGICAL CODE SOLUTION

Dưới đây là code Python (tương thích với hệ sinh thái Antigravity) để xử lý task này. Code này sẽ:
1.  Xác minh link (tách bỏ tracking params).
2.  Phân loại lead (Designer tìm việc -> Không phải khách hàng trực tiếp).
3.  Tạo ra một tin nhắn Outreach chuyên nghiệp chào bán dịch vụ Frontend/Dev cho cô ấy (vì cô ấy có thể cần người code thiết kế của cô ấy).

```python
import re
import urllib.parse
from datetime import datetime

class AntigravityLeadProcessor:
    """
    Processor chuyên xử lý các lead từ freelance_lead pipeline.
    Mục tiêu: Phân loại, làm sạch dữ liệu và tạo nội dung outreach phù hợp.
    """

    def __init__(self):
        self.tracking_params = ['obrf', 'utm_source', 'utm_medium', 'utm_campaign', 'ref']

    def clean_url(self, url: str) -> str:
        """
        Loại bỏ các tham số tracking khỏi URL để xác minh nguồn gốc thực sự.
        """
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        # Lọc bỏ các tham số tracking
        clean_params = {k: v for k, v in query_params.items() if k not in self.tracking_params}
        
        if clean_params:
            new_query = urllib.parse.urlencode(clean_params, doseq=True)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
        else:
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def classify_lead(self, title: str, description: str) -> dict:
        """
        Phân loại lead dựa trên nội dung.
        Returns: dict với keys: 'type', 'is_valid', 'action', 'reason'
        """
        # Heuristic: Kiểm tra xem người gửi có đang tìm việc hay không
        is_looking_for_work = "for hire" in title.lower() or "looking for" in description.lower()
        is_designer = "product designer" in description.lower() or "ux/ui" in description.lower()
        
        if is_looking_for_work and is_designer:
            return {
                "type": "TALent_SEEKING",
                "is_valid": True,
                "action": "OUTREACH_FRONTEND_SERVICE",
                "reason": "Lead is a designer looking for work. Opportunity to pitch Frontend/Dev services."
            }
        else:
            return {
                "type": "UNKNOWN",
                "is_valid": False,
                "action": "REJECT",
                "reason": "Does not match current service offering or lead quality."
            }

    def generate_outreach_message(self, lead_name: str, clean_portfolio_url: str) -> str:
        """
        Tạo tin nhắn outreach chuyên nghiệp, ngắn gọn, tập trung vào giá trị.
        """
        return f"""Hi {lead_name},

I came across your portfolio and was impressed by your clean, user-centered design approach for SaaS platforms.

I'm an autonomous software engineering assistant (Antigravity) specializing in turning high-fidelity designs into production-ready code (React/Next.js/Python).

Since you're looking for freelance opportunities, I'd like to propose a collaboration:
1. You provide the UX/UI design.
2. My team handles the frontend implementation and backend integration.

This could be a great way to offer end-to-end solutions to your future clients.

You can view my technical capabilities and past implementations here: [LINK_TO_ANTIGRAVITY_PORTFOLIO]

Best regards,
The Antigravity Team
"""

def process_task(task_data: dict) -> dict:
    """

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 4.03s • $0.00)</i>