Vì đây không phải là lỗi kỹ thuật (bug) trong code, mà là dữ liệu đầu vào không hợp lệ (invalid input) cho quy trình phát triển phần mềm, giải pháp kỹ thuật duy nhất là **cập nhật bộ lọc (Filtering Logic)** để loại bỏ các tin rao dịch vụ viết lách/không kỹ thuật.

Dưới đây là đoạn mã Python mẫu để cải thiện bộ lọc phân loại (Classifier) trong pipeline thu thập dữ liệu việc làm, nhằm tránh việc đưa các tin rao dịch vụ viết lách vào hàng đợi xử lý kỹ thuật:

<pre><code>
import re

def classify_freelance_post(title: str, description: str) -> str:
    """
    Phân loại tin tuyển dụng dựa trên tiêu đề và mô tả.
    Trả về: 'TECHNICAL', 'NON_TECHNICAL', 'SUSPICIOUS'
    """
    # Các từ khóa chỉ ra dịch vụ viết lách/không kỹ thuật
    non_tech_keywords = [
        "fiction writer", "nsfw", "sfw stories", "fanfiction", 
        "poetry", "writing commissions", "etsy store", 
        "words", "storyline", "characters in character"
    ]
    
    # Các từ khóa kỹ thuật
    tech_keywords = [
        "python", "go", "rust", "javascript", "typescript", 
        "api", "backend", "frontend", "devops", "vps", 
        "database", "bug", "fix", "implement", "code"
    ]
    
    text_lower = (title + " " + description).lower()
    
    # Kiểm tra từ khóa kỹ thuật
    tech_score = sum(1 for kw in tech_keywords if kw in text_lower)
    
    # Kiểm tra từ khóa không kỹ thuật (Viết lách)
    non_tech_score = sum(1 for kw in non_tech_keywords if kw in text_lower)
    
    # Logic quyết định
    if non_tech_score > tech_score and non_tech_score >= 3:
        return "NON_TECHNICAL"
        
    if tech_score > 0:
        return "TECHNICAL"
        
    return "SUSPICIOUS"

# Áp dụng cho task hiện tại
task_title = "[High-Ticket Contract: $500] [FOR HIRE] An Experienced Fiction Writer..."
task_desc = "💫Hello! I’m Fawn, a writer who specializes in NSFW and SFW fiction!..."

classification = classify_freelance_post(task_title, task_desc)
print(f"Classification Result: {classification}")
# Kết quả dự kiến: NON_TECHNICAL
</code></pre>