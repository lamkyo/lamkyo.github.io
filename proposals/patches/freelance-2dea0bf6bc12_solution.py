**Solution – tự động đăng bình luận “Apply” cho tin tuyển dụng Chronograph trên Hacker News**  

> *Mục tiêu*: Khi có một tin tuyển dụng mới (như mô tả ở trên) xuất hiện trong “Ask HN: Who is hiring?”, hệ thống tự động đăng một bình luận chuẩn “Application” tới thread đó, giảm thiểu công việc thủ công và tránh lỗi đánh máy.  

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Nguyên nhân | Ảnh hưởng | Giải pháp đề xuất |
|-------------|-----------|-------------------|
| **Quy trình thủ công** – Nhân viên phải mở trình duyệt, đăng nhập, sao chép nội dung, dán và gửi bình luận. <br> → **Rủi ro**: quên đăng nhập, sai định dạng, mất thời gian. | Thời gian phản hồi chậm, khả năng bỏ lỡ cơ hội việc làm. | **Tự động hoá**: viết một script Python dùng API của Hacker News (đăng nhập bằng cookie `user` và `pass`), tạo comment chuẩn và gửi tới `item_id` của thread “Ask HN: Who is hiring?”. |
| **Không có kiểm tra lỗi** – Nếu cookie hết hạn hoặc `item_id` không tồn tại, script hiện tại không báo lỗi rõ ràng. | Không biết được việc đăng thất bại, phải kiểm tra thủ công. | Thêm **xác thực** và **xử lý lỗi** chi tiết (HTTP status, phản hồi JSON). |
| **Không có test** – Không có bộ kiểm thử tự động để bảo chứng rằng script luôn hoạt động khi API thay đổi. | Rủi ro regressions khi cập nhật thư viện hoặc thay đổi API. | Viết **unit test** dùng `requests‑mock` để mô phỏng API và kiểm tra luồng đăng nhập → đăng bình luận. |

> **Kiến trúc đề xuất**  
> - **Module `hn_commenter.py`**: chứa hàm `post_comment(item_id: int, text: str, cookie: str) -> dict`.  
> - **CLI `apply.py`**: đọc `item_id` và nội dung comment từ file cấu hình (`apply.yaml`).  
> - **Test suite `tests/test_hn_commenter.py`**: mô phỏng API và kiểm tra các trường hợp thành công và lỗi.  

---

## 2. SURGICAL CODE SOLUTION  

### 2.1. `hn_commenter.py`

```html
<pre><code class="language-python">"""
hn_commenter.py
----------------
Utility module to post a comment on Hacker News using the official
YCombinator API (https://github.com/HackerNews/API).

Requirements:
    - Python 3.9+
    - requests
"""

import json
import time
from typing import Dict, Any

import requests

# Hacker News API endpoints
HN_BASE = "https://news.ycombinator.com"
LOGIN_URL = f"{HN_BASE}/login"
POST_URL = f"{HN_BASE}/comment"

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class HNError(RuntimeError):
    """Base exception for all HN‑related errors."""
    pass

class HNAuthError(HNError):
    """Raised when login fails."""
    pass

class HNPostError(HNError):
    """Raised when posting a comment fails."""
    pass

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _login(username: str, password: str) -> str:
    """
    Perform login to Hacker News and return the authentication cookie
    (the value of the ``user`` cookie).  The cookie is required for subsequent
    POST requests.

    Parameters
    ----------
    username: str
        HN username.
    password: str
        HN password.

    Returns
    -------
    str
        Authentication cookie string (e.g. ``"user=...; path=/"``).

    Raises
    ------
    HNAuthError
        If login fails (wrong credentials or network error).
    """
    payload = {
        "acct": username,
        "pw": password,
        "goto": "news",
    }
    resp = requests.post(LOGIN_URL, data=payload, timeout=10)
    if resp.status_code != 200:
        raise HNAuthError(f"Login request failed with status {resp.status_code}")

    # The cookie we need is the ``user`` cookie set by the server.
    if "user" not in resp.cookies:
        raise HNAuthError("Login succeeded but no authentication cookie returned")
    # Return the raw cookie header value for later use.
    return resp.cookies.get("user")


def post_comment(item_id: int, text: str, auth_cookie: str) -> Dict[str, Any]:
    """
    Post a comment to a given Hacker News item (story or ask‑hn thread).

    Parameters
    ----------
    item_id: int
        The HN ``item_id`` of the thread where the comment will be posted.
    text: str
        The

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.51s • $0.00)</i>