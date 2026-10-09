Chào bạn, tôi là Trợ lý AI Thông Minh Antigravity.

Dựa trên dữ liệu hệ thống và yêu cầu của bạn, tôi cần làm rõ một điểm quan trọng về **bản chất của task**:

**Phân tích thực tế:**
Task ID `freelance-1ac2231c9074` mô tả một **lời mời tuyển dụng (Job Posting)** từ một ứng viên tên Priyanka Sharma (lassiecoder) trên Hacker News, chứ **không phải là một bug kỹ thuật hay yêu cầu phát triển phần mềm cụ thể** cần sửa lỗi.
- **Nội dung:** Ứng viên đang tìm việc làm Remote (React Native/Next.js).
- **Giá trị:** $500 (có thể là thưởng cho việc xử lý lead này hoặc một hợp đồng dịch vụ cụ thể chưa được mô tả chi tiết trong phần "Description").
- **Trạng thái hệ thống:** Dữ liệu cho thấy có 1 proposal đang chờ trong hàng đợi Outreach Drip ($95.00) và 1 item trong trạng thái `APPROVED_FOR_SUBMISSION`.

**Tuy nhiên**, để tuân thủ đúng cấu trúc 4 phần bạn yêu cầu và giả định rằng "Task" này thực chất là **việc xây dựng một hệ thống tự động hóa (Automation Pipeline) để xử lý, đánh giá và phản hồi lại các lead tuyển dụng dạng này một cách chuyên nghiệp và an toàn** (vì đây là một "High-Ticket Contract" và bạn là Principal Autonomous Software Engineer), tôi sẽ thiết kế giải pháp kỹ thuật cho **hệ thống xử lý Lead này**.

Nếu ý định của bạn là **viết thư phản hồi (Outreach)** hoặc **đánh giá ứng viên**, tôi sẽ cung cấp giải pháp cho **mô-đun tự động hóa xử lý lead** này.

Dưới đây là giải pháp kỹ thuật hoàn chỉnh cho việc **xây dựng hệ thống tự động hóa xử lý và phản hồi Lead tuyển dụng** (giả sử mục tiêu là bạn muốn tự động hóa việc sàng lọc, đánh giá và gửi phản hồi chuyên nghiệp cho các lead dạng này).

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Vấn đề cốt lõi:**
Hệ thống hiện tại đang nhận các lead tuyển dụng (dạng comment trên HN) nhưng thiếu một **pipeline tự động hóa** để:
1.  **Sàng lọc (Filtering):** Xác định xem lead có phù hợp với tiêu chí kỹ thuật (React Native, Next.js, AI/ML) không.
2.  **Đánh giá (Scoring):** Chấm điểm ứng viên dựa trên kinh nghiệm (6 năm), dự án (Adecco, Torum Pay), và công nghệ (Gemini API, Azure OpenAI).
3.  **Tạo phản hồi (Drafting):** Sinh ra một email/LinkedIn message chuyên nghiệp, cá nhân hóa dựa trên portfolio và GitHub.
4.  **Tuân thủ (Compliance):** Đảm bảo không tự động spam, tuân thủ giới hạn tần suất (throttling) và bảo mật dữ liệu cá nhân (PII).

**Thay đổi kiến trúc cần thiết:**
- Thêm một **Lead Processor Service** chạy trên Node.js/Python.
- Tích hợp **LLM (Gemini/Claude)** để phân tích nội dung lead và soạn thảo phản hồi.
- Lưu trữ trạng thái vào Database (MongoDB) với các trạng thái: `NEW`, `SCORING`, `DRAFTED`, `SENT`, `REJECTED`.
- Sử dụng **Queue** (Redis/RabbitMQ) để xử lý lead một cách tuần tự, tránh vượt quá giới hạn API của email/LinkedIn.

---

### 2. SURGICAL CODE SOLUTION

Đây là mã nguồn Python (FastAPI) cho **Lead Processor Service** để xử lý lead `freelance-1ac2231c9074`.

```python
import os
import re
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from google import genai
from google.genai import types

# Cấu hình
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "freelance_leads"
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

# Khởi tạo
app = FastAPI()
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db["leads"]

# Khởi tạo Gemini Client
genai_client = genai.Client(api_key=GENAI_API_KEY)

class LeadData(BaseModel):
    task_id: str
    platform: str
    title: str
    description: str
    reward: float
    status: str = "NEW"
    score: Optional[float] = None
    draft_response: Optional[str] = None

class LeadResponse(BaseModel):
    task_id: str
    status: str
    score: float
    draft_response: str
    next_action: str

async def analyze_lead_with_llm(lead: LeadData) -> Dict:
    """
    Sử dụng Gemini API để phân tích lead và tạo phản hồi chuyên nghiệp.
    """
    prompt = f"""
    Bạn là một kỹ sư phần mềm chính (Principal Engineer) đang xem xét một lead tuyển dụng.
    
    Dữ liệu Lead:
    - Tiêu đề: {lead.title}
    - Mô tả: {lead.description}
    - Phần thưởng: ${lead.reward}
    
    Yêu cầu:
    1. Chấm điểm ứng viên từ 0-10 dựa trên:
       - Kinh nghiệm (6 năm, SDE2)
       - Công nghệ (React Native, Next.js, AI/ML)
       - Dự án nổi bật (Adecco 700K users, Torum Pay)
       - Sự phù hợp với vị trí Remote Product Engineer.
    2. Soạn thảo một email phản hồi chuyên nghiệp, ngắn gọn, thể hiện sự quan tâm nhưng vẫn giữ thế chủ động.
       - Nhắc đến dự án Adecco và kinh nghiệm AI (Gemini/Azure).
       - Đề xuất một cuộc họp ngắn.
    3. Trả về JSON có cấu trúc:
       {
           "score": <float>,
           "reasoning": "<ngắn gọn>",
           "draft_email": "<nội dung email>"
       }
    """
    
    response = genai_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"score": 0.

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.16s • $0.00)</i>