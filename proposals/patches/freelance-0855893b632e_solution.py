Chào bạn, đây là **Trợ lý AI Thông Minh Antigravity**.

Tôi đã phân tích kỹ yêu cầu của bạn. Có một sự nhầm lẫn nhỏ trong ngữ cảnh: Bạn đã dán một **lệnh kỹ thuật** (yêu cầu giải quyết bug, viết code, test suite, PR) nhưng nội dung "Task" lại là một **dự án Freelance tìm kiếm khách hàng (Appointment Setting)** cho một nhiếp ảnh gia thương mại.

**Không có mã nguồn (code) hay bug nào để sửa ở đây.** Đây là một bài toán **Quy trình làm việc (Workflow)** và **Chiến lược Sales/Outreach**.

Tuy nhiên, với tư cách là **Principal Autonomous Software Engineer**, tôi sẽ "giải quyết" task này bằng cách thiết kế một **Hệ thống Tự động hóa & Quy trình Tìm kiếm (Lead Generation Pipeline)** chuẩn hóa, có thể tái sử dụng, và cung cấp **bản đề xuất (Proposal)** hoàn chỉnh để bạn gửi cho chủ dự án (u/bleepbloop018) nhằm giành được hợp đồng $150 + bonus.

Dưới đây là giải pháp được cấu trúc theo 4 phần bạn yêu cầu, nhưng đã được **tương thích hóa** cho ngữ cảnh Freelance/Outreach:

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS (Phân tích Vấn đề & Chiến lược)

**Vấn đề cốt lõi (Pain Point):**
Chủ dự án (Nhiếp ảnh gia) thiếu thời gian để *prospecting* (tìm kiếm khách hàng tiềm năng). Anh ấy cần:
1.  **Dữ liệu sạch:** Danh sách 15 công ty địa phương (Olympia-Seattle) trong các ngành: Kiến trúc, Bất động sản thương mại, Gym/Studio.
2.  **Điểm chạm chính xác (Decision Makers):** Không phải email `info@`, mà là Owner, Marketing Lead, hoặc Giám đốc điều hành.
3.  **Quy trình xác thực:** Đảm bảo email hoạt động và người nhận đúng chức vụ.
4.  **Cá nhân hóa:** Email ngắn gọn, chuyên nghiệp, không spam.

**Giải pháp Kiến trúc (The Solution Architecture):**
Thay vì làm thủ công, tôi sẽ sử dụng quy trình **3-Step Verification Pipeline**:
1.  **Source & Scraping:** Sử dụng LinkedIn Sales Navigator (hoặc tìm kiếm thủ công trên LinkedIn/Website công ty) + Google Maps để xác định danh sách 15 công ty mục tiêu.
2.  **Enrichment & Verification:** Sử dụng công cụ tìm kiếm email (ví dụ: Hunter.io, Apollo.io, hoặc Clearbit) để tìm email cá nhân. Sau đó, chạy qua trình kiểm tra email (ví dụ: NeverBounce, ZeroBounce) để đảm bảo tỷ lệ deliverability 100%.
3.  **Outreach & Tracking:** Viết email cá nhân hóa dựa trên hồ sơ công ty. Gửi email và theo dõi phản hồi.

**Công cụ tôi sẽ sử dụng:**
*   **Tìm kiếm:** LinkedIn Sales Navigator (nếu có) hoặc LinkedIn Public + Google Maps.
*   **Xác thực Email:** Hunter.io (tìm email) + NeverBounce (kiểm tra email).
*   **Quản lý:** Trello/Notion để track trạng thái từng lead.
*   **Viết Email:** GPT-4 (để tạo nội dung cá nhân hóa nhanh chóng).

---

### 2. SURGICAL CODE SOLUTION (Quy trình Thực thi & Mẫu Email)

Vì đây là task Freelance, "Code" ở đây là **Quy trình làm việc (SOP)** và **Mẫu nội dung (Templates)**.

#### A. Quy trình Tìm kiếm & Xác thực (SOP)

```markdown
# SOP: Lead Generation for Commercial Photographer

## Step 1: Target List Creation (15 Companies)
- **Criteria:** 
  - Location: Olympia, WA to Seattle, WA corridor.
  - Industry: Architecture Firms, Commercial Real Estate Brokers, Boutique Gyms/Studios.
  - Size: Small to Mid-size (1-50 employees) - likely to hire freelance.
- **Action:**
  1. Search Google Maps: "Architecture firms in Olympia WA", "Commercial real estate brokers Seattle", "Boutique gyms Tacoma".
  2. Filter companies with active websites and recent social media activity.
  3. Select 15 diverse companies (5 Arch, 5 CRE, 5 Gyms).

## Step 2: Decision Maker Identification
- **Action:**
  1. Go to LinkedIn. Search company name.
  2. Filter by "People".
  3. Look for titles: Owner, Founder, Principal, Marketing Director, Head of Operations.
  4. Note down: Full Name, Title, LinkedIn URL.

## Step 3: Email Enrichment & Verification
- **Action:**
  1. Use Hunter.io to guess/find email pattern (e.g., first.last@company.com).
  2. Verify each email using NeverBounce or ZeroBounce.
  3. Discard any "Invalid" or "Catch-all" emails. Only keep "Valid" or "Accept All".
  4. If no email found, skip that company and find a replacement to maintain 15 valid leads.

## Step 4: Personalized Outreach
- **Action:**
  1. Draft email using template below.
  2. Personalize first line with specific detail about their recent project or gym.
  3. Send emails.
  4. Log status in Trello: "Sent", "Replied", "Booked Call".
```

#### B. Mẫu Email Cá nhân hóa (Template)

**Subject:** Quick question about [Company Name]'s visual branding / Photography for [Specific Project]

**Body:**

Hi [First Name],

I came across [Company Name] while researching top [Architecture/Real Estate/Gyms] in the Olympia-Seattle area. I was particularly impressed by [Specific Detail: e.g., your recent project at X / the new equipment at your studio].

I’m a commercial photographer specializing in [Architecture/Commercial Real Estate/Boutique Fitness] spaces. I help businesses like yours elevate their online presence with high-quality visuals that convert.

I’m currently offering a limited-time package for local businesses in the region. Would you be open to a brief 10-minute call next week to see if there’s a fit?

Best regards,

[Your Name]
[Your Portfolio Link]
[Your Phone Number]

---

### 3. VERIFICATION & UNIT TEST SUITE (Kiểm tra Chất lượng & KPI)

Thay vì unit test code, đây là **Bộ tiêu chí kiểm tra chất lượng (Quality Assurance Checklist)** để đảm bảo bạn đạt được $150 + bonus.

| Tiêu chí | Yêu cầu | Trạng thái | Ghi chú |
| :--- | :

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.03s • $0.00)</i>