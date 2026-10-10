Không có đoạn code cần sửa.  
Nếu mục tiêu là **tự động lọc và gửi email ứng viên** dựa trên tiêu chí (bilingual, 5+ năm kinh nghiệm, tools), một đoạn script Python mẫu có thể như sau (đây chỉ là ví dụ, không phải patch thực sự):

```python
# <pre><code>
import re

def is_qualified(candidate):
    # Kiểm tra ngôn ngữ
    if not (candidate.get('languages') & {'English', 'Spanish'}):
        return False
    # Kiểm tra kinh nghiệm
    if candidate.get('experience_years', 0) < 5:
        return False
    # Kiểm tra công cụ
    tools = {'Google Workspace', 'Notion', 'ClickUp', 'QuickBooks'}
    if not tools.issubset(set(candidate.get('tools', []))):
        return False
    return True
# </code></pre>
```

---