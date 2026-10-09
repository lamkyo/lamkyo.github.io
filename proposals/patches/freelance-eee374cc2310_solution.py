**📌 Phân tích & Giải pháp cho dự án “Content Creator for Ironstone Design”**  

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| # | Yếu tố cần lưu ý | Lý do | Hướng giải quyết |
|---|-----------------|-------|------------------|
| 1 | **Định dạng video** | Yêu cầu 30–60 s, TikTok/Reels/Shorts → độ dài 15–60 s, tỷ lệ 9:16 (portrait). | Sử dụng thư viện *moviepy* để tạo video portrait, cắt, trim, thêm overlay. |
| 2 | **Nội dung thực tế** | Phải “show” quá trình xây dựng website thực tế, phản hồi chủ doanh nghiệp. | Tạo template video gồm: <br>• Clip “đang xây dựng” (screen‑record), <br>• Clip “đưa giao cho chủ” (video clip), <br>• Clip phản hồi (đoạn ngắn). |
| 3 | **Tự động hoá** | Để giảm công sức, cần script tự động gộp clip, thêm nhạc nền, watermark, caption. | Script Python nhận danh sách clip, tự động kết hợp, xuất file MP4. |
| 4 | **Định dạng file** | Định dạng MP4, 1080×1920, bitrate 4 Mbps. | Cấu hình *moviepy* xuất với codec h264, bitrate 4000k. |
| 5 | **Kiểm thử** | Đảm bảo video không bị lỗi codec, độ dài đúng, watermark xuất hiện. | Viết unit‑test kiểm tra metadata video (duration, resolution, presence watermark). |
| 6 | **Tích hợp** | Dự án có thể được tích hợp vào pipeline CI/CD (GitHub Actions). | Tạo Dockerfile chạy script, test tự động. |

> **Kết luận**: Để đáp ứng yêu cầu, ta cần một script Python có thể nhận clip, tự động gộp, thêm watermark, xuất video 9:16, đồng thời có unit‑test xác thực chất lượng video.

---

## 2. SURGICAL CODE SOLUTION  

```python
# ──────────────────────────────────────────────────────────────
#  File: video_builder.py
#  Description: Tự động gộp clip, thêm watermark & xuất video 9:16
# ──────────────────────────────────────────────────────────────
import os
from pathlib import Path
from typing import List
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    TextClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx,
)

# Constants
OUTPUT_DIR = Path("output")
WATERMARK_TEXT = "Ironstone Design"
WATERMARK_FONT = "Arial-Bold"
WATERMARK_COLOR = "white"
WATERMARK_OPACITY = 0.7
WATERMARK_POS = ("right", "bottom")
WATERMARK_MARGIN = 30
TARGET_RESOLUTION = (1080, 1920)  # 9:16 portrait
TARGET_FPS = 30
TARGET_BITRATE = "4000k"  # 4 Mbps
AUDIO_FILE = "assets/narration.mp3"

def _add_watermark(clip: VideoFileClip) -> VideoFileClip:
    """Add semi‑transparent watermark to a clip."""
    txt_clip = (
        TextClip(
            WATERMARK_TEXT,
            fontsize=40,
            font=WATERMARK_FONT,
            color=WATERMARK_COLOR,
            stroke_color="black",
            stroke_width=2,
        )
        .set_opacity(WATERMARK_OPACITY)
        .set_duration(clip.duration)
        .set_position(
            (
                clip.w - txt_clip.w - WATERMARK_MARGIN,
                clip.h - txt_clip.h - WATERMARK_MARGIN,
            )
        )
    )
    return CompositeVideoClip([clip, txt_clip])

def build_video(
    clip_paths: List[Path],
    output_name: str = "final_video.mp4",
    audio_path: Path | None = None,
) -> Path:
    """
    Build a short video from a list of clip paths.

    Parameters
    ----------
    clip

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 2.17s • $0.00)</i>