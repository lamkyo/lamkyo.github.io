Chào bạn, đây là phân tích chi tiết và giải pháp kỹ thuật cho tác vụ `freelance-d4d930bcc7d7`.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Phân tích bản chất vấn đề:**
Đây **không phải là một bug kỹ thuật** (lỗi code) mà là một **Lead Freelance** (cơ hội việc làm) được phát hiện bởi hệ thống.
*   **Loại Lead:** Administrative/Operations Support (Hỗ trợ vận hành & Hành chính).
*   **Ngân sách:** $500 USD (Thanh toán cố định hoặc theo giờ $15/h).
*   **Yêu cầu cốt lõi:** Xây dựng danh sách khách hàng tiềm năng (Prospect List), nghiên cứu thị trường, quản lý CRM, và hỗ trợ hành chính.
*   **Rủi ro:** Công việc mang tính thủ công cao (manual labor), không yêu cầu kỹ năng lập trình chuyên sâu. Nếu hệ thống Antigravity tự động hóa hoàn toàn mà không có sự giám sát của con người (Human-in-the-loop) ở khâu "Chấm điểm chất lượng lead" và "Viết email cá nhân hóa", tỷ lệ bị từ chối (Rejection Rate) sẽ rất cao do các nền tảng freelance (Upwork, Fiverr, Reddit) thường lọc các đơn ứng tuyển tự động hóa thô.

**Giải pháp kiến trúc đề xuất:**
Thay vì viết code để "làm việc" (vì đây là công việc dịch vụ), hệ thống cần tạo ra một **Proposal Template** (Đơn ứng dụng) được tối ưu hóa theo thuật toán SEO của nền tảng, kèm theo một **Script Python** để tự động hóa bước *Research* (Nghiên cứu) và *Data Enrichment* (Làm giàu dữ liệu) nhằm chứng minh năng lực kỹ thuật của ứng viên, giúp nổi bật giữa đám đông các ứng viên hành chính thông thường.

### 2. SURGICAL CODE SOLUTION

Dưới đây là script Python dùng để **tự động hóa bước Research & Data Enrichment** cho lead này. Script này sẽ lấy dữ liệu công khai từ các nguồn (ví dụ: LinkedIn public profile hoặc Crunchbase API mock) và chuẩn hóa dữ liệu vào CSV, sẵn sàng cho việc tạo Proposal.

```python
import csv
import json
import requests
import time
from datetime import datetime

class LeadResearchEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.output_file = "enriched_leads_for_freelance_d4d930bcc7d7.csv"

    def fetch_company_data(self, company_name: str) -> dict:
        """
        Mô phỏng việc lấy dữ liệu công ty từ API (thay thế bằng Crunchbase/Apollo API thực tế).
        """
        # Trong môi trường production, thay thế bằng API call thực tế
        # Ví dụ: response = requests.get(f"https://api.crunchbase.com/organization/{company_name}", headers=self.headers)
        
        # Dữ liệu giả lập (Mock Data) để chứng minh logic
        mock_data = {
            "name": company_name,
            "industry": "SaaS / B2B",
            "size": "11-50 employees",
            "funding_stage": "Seed",
            "website": f"https://{company_name.lower().replace(' ', '')}.com",
            "key_contacts": [
                {
                    "name": "John Smith",
                    "title": "Founder & CEO",
                    "email": f"john.smith@{company_name.lower().replace(' ', '')}.com", # Cần xác minh
                    "linkedin": f"https://linkedin.com/in/johnsmith-{company_name.lower()}"
                }
            ]
        }
        return mock_data

    def enrich_and_save(self, company_list: list):
        """
        Làm giàu dữ liệu và lưu vào CSV.
        """
        enriched_data = []
        
        print(f"🚀 Bắt đầu xử lý {len(company_list)} công ty...")
        
        for company in company_list:
            try:
                data = self.fetch_company_data(company)
                
                # Chuẩn hóa dữ liệu
                record = {
                    "company_name": data["name"],
                    "industry": data["industry"],
                    "company_size": data["size"],
                    "funding_stage": data["funding_stage"],
                    "website": data["website"],
                    "primary_contact_name": data["key_contacts"][0]["name"],
                    "primary_contact_title": data["key_contacts"][0]["title"],
                    "primary_contact_email": data["key_contacts"][0]["email"],
                    "primary_contact_linkedin": data["key_contacts"][0]["linkedin"],
                    "research_timestamp": datetime.now().isoformat(),
                    "status": "READY_FOR_OUTREACH"
                }
                enriched_data.append(record)
                print(f"✅ Đã xử lý: {company}")
                
                # Rate limiting để tránh bị block
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {company}: {str(e)}")
                continue

        # Ghi ra CSV
        if enriched_data:
            fieldnames = enriched_data[0].keys()
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_data)
            print(f"💾 Đã lưu {len(enriched_data)} lead vào {self.output_file}")
        else:
            print("⚠️ Không có dữ liệu hợp lệ để lưu.")

if __name__ == "__main__":
    # Danh sách công ty mẫu cần nghiên cứu cho lead này
    target_companies = [
        "TechStartups Inc", 
        "CloudSolutions Co", 
        "AI Innovations Ltd"
    ]
    
    engine = LeadResearchEngine()
    engine.enrich_and_save(target_companies)
```

### 3. VERIFICATION & UNIT TEST SUITE

Script test để đảm bảo engine hoạt động đúng, xử lý lỗi và định dạng CSV chính xác.

```python
import unittest
import os
import csv
from unittest.mock import patch, MagicMock
import sys
import importlib.util

# Import module LeadResearchEngine từ code solution
# Giả sử code ở trên được lưu trong file 'lead_engine.py'
spec = importlib.util.spec_from_file_location("lead_engine", "lead

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.15s • $0.00)</i>