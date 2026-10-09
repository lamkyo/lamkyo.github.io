Chào bạn, với tư cách là **Antigravity Principal Autonomous Software Engineer**, tôi đã phân tích kỹ lưỡng yêu cầu của bạn.

**QUYẾT ĐỊNH: BÀI TOÁN NÀY KHÔNG CÓ LỖI (BUG) CẦN SỬA.**

Đây là một **Lead Tuyển dụng (Freelance Lead)** từ Hacker News, không phải là một issue kỹ thuật chứa mã nguồn lỗi, stack trace hay yêu cầu vá lỗi phần mềm. Do đó, việc áp dụng cấu trúc "Root Cause -> Code Patch -> Unit Test" là **sai ngữ cảnh kỹ thuật** (Category Error).

Tuy nhiên, để hỗ trợ chủ nhân tối đa trong việc xử lý lead này (đánh giá tính khả thi, rủi ro và chiến lược tiếp cận), tôi sẽ chuyển đổi cấu trúc phản hồi sang **Phân Tích Kinh Doanh & Đánh Giá Kỹ Thuật (Business & Technical Feasibility Analysis)** để bạn có thể quyết định có nên gửi proposal hay không.

Dưới đây là phân tích chi tiết:

### 1. PHÂN TÍCH NGUYÊN NHÂN & ĐÁNH GIÁ MÔ HÌNH (ROOT CAUSE & TECHNICAL ANALYSIS)

**Tại sao đây là một cơ hội "High-Ticket" nhưng phức tạp?**

*   **Bản chất công việc:** Đây không phải là dự án freelance truyền thống (làm xong tính tiền). Đây là vị trí **Full-time, Onsite (5 ngày/tuần tại UCLA)** trong 6 tháng.
*   **Rủi ro Địa lý & Thời gian:**
    *   Yêu cầu: Onsite tại Los Angeles (UCLA).
    *   Thời gian bắt đầu: Tháng 1/2027.
    *   *Vấn đề:* Nếu bạn không ở LA hoặc không có kế hoạch di chuyển, lead này vô giá trị.
    *   *Vấn đề:* Thời gian bắt đầu khá xa (1/2027), nhưng quy trình tuyển dụng thường diễn ra trước đó vài tháng.
*   **Yêu cầu Kỹ thuật Khắt khe:**
    *   **Native iOS:** Không dùng React Native/Flutter. Phải là Swift/SwiftUI.
    *   **No AI Assistants in Interview:** Phiên phỏng vấn coding 60 phút **cấm dùng AI**. Điều này loại bỏ lợi thế của những người phụ thuộc vào Copilot/Cursor.
    *   **Complex Systems:** Xây dựng app hỗ trợ can thiệp trị liệu (AAC - Augmentative and Alternative Communication). Yêu cầu độ ổn định cao, UX cực kỳ trực quan cho trẻ tự kỷ và bác sĩ.
*   **Bối cảnh Doanh nghiệp:**
    *   SKIES là công ty nhỏ (Pasadena), có vốn NIH SBIR (vốn nghiên cứu).
    *   Sản phẩm hiện tại: Visual Choices (app AAC phổ biến).
    *   Dự án mới: Visual Play (ứng dụng can thiệp chơi đùa).
    *   *Điểm cộng:* Có nền tảng kỹ thuật sẵn có, không phải xây từ 0. Có đối tác nghiên cứu uy tín (UCLA Kasari Lab).

**Kết luận:** Đây là một vị trí **Employment** (Việc làm chính thức), không phải Freelance. Mức lương $65k cho 6 tháng (tương đương $130k/năm) là mức trung bình khá cho iOS Dev tại LA, nhưng đổi lại là cơ hội làm việc trong môi trường nghiên cứu hàng đầu thế giới và tiềm năng sản phẩm hóa (Phase II).

### 2. CHIẾN LƯỢC KỸ THUẬT & CÂU HỎI PHỎNG VẤN (SURGICAL CODE SOLUTION)

Thay vì viết code vá lỗi, đây là **bộ khung kỹ thuật** bạn cần chuẩn bị cho buổi phỏng vấn "Collaborative Coding" (60 phút, không AI):

**A. Kiến trúc đề xuất cho "Visual Play":**

```swift
// Pseudo-code kiến trúc SwiftUI cho app trị liệu
import SwiftUI

// 1. State Management: Sử dụng @Observable (iOS 17+) hoặc ObservableObject
// Đảm bảo state của phiên trị liệu (session) được tách biệt rõ ràng.
class TherapySession: ObservableObject {
    @Published var currentStep: InterventionStep = .init()
    @Published var childResponse: ChildResponse?
    @Published var clinicianNotes: String = ""
    
    // Logic xử lý phản hồi của trẻ (cần tối ưu hiệu năng, tránh lag)
    func processChildInteraction(_ interaction: InteractionType) {
        // Xử lý logic can thiệp dựa trên dữ liệu từ Kasari Lab
        // Gửi sự kiện đến analytics (anonymized)
    }
}

// 2. UI Layer: SwiftUI với Focus trên Accessibility & Simplicity
// Trẻ tự kỷ minimally verbal cần giao diện cực kỳ đơn giản, ít nhiễu.
struct VisualPlayView: View {
    @StateObject private var session = TherapySession()
    
    var body: some View {
        ZStack {
            // Background tĩnh, không gây xao nhãng
            Color(.systemBackground)
            
            VStack(spacing: 20) {
                // 1. Visual Prompt (Hình ảnh/Video gợi ý)
                VisualPromptView(prompt: session.currentStep.prompt)
                    .frame(height: 300)
                
                // 2. Interaction Zone (Nơi trẻ tương tác)
                InteractionZoneView(
                    onInteraction: { interaction in
                        session.processChildInteraction(interaction)
                    }
                )
                
                // 3. Clinician Controls (Góc nhỏ, ít nổi bật)
                ClinicianControlPanel(session: session)
            }
            .padding()
        }
    }
}
```

**B. Điểm mấu chốt cần thể hiện trong 60 phút coding:**

1.  **State Management:** Cách bạn quản lý luồng dữ liệu giữa "Trẻ tương tác" -> "App xử lý" -> "Bác sĩ ghi chú".
2.  **Performance:** App phải chạy mượt trên các thiết bị cũ (trường học/lab thường dùng iPad cũ). Tránh allocation object không cần thiết.
3.  **Error Handling:** Xảy ra khi trẻ không tương tác, hoặc mất kết nối (nếu có), app phải tự phục hồi mà không làm gián đoạn phiên trị liệu.
4.  **Code Readability:** Code phải sạch, có comment giải thích *tại sao* (why) chứ không chỉ *cái gì* (what), vì sẽ được review bởi cả kỹ sư lẫn nhà nghiên cứu.

### 3. KIỂM CHỨNG & CHUẨN BỊ PHỎNG VẤN (VERIFICATION & UNIT TEST SUITE)

Vì không có code lỗi để test, đây là **Checklist Tự Kiểm Tra** trước khi nộp đơn:

| Hạng mục | Yêu cầu | Trạng thái |
| :--- | :--- | :--- |
| **Địa lý** | Bạn có thể làm onsite tại UCLA (Los Angeles)

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.07s • $0.00)</i>