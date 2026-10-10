**⚠️ Lưu ý:**  
Yêu cầu của bạn mô tả một dự án “Binance Futures Scanner” nhưng không kèm theo bất kỳ đoạn mã, repository hay log lỗi nào. Để thực hiện **ROOT CAUSE**, **SURGICAL CODE SOLUTION**, **UNIT TEST** và **PULL REQUEST** một cách chính xác, chúng tôi cần ít nhất:

1. **Link repo** (GitHub, GitLab, Bitbucket…) hoặc **đoạn mã lỗi** (stack‑trace).  
2. **Mô tả chi tiết** về vấn đề hiện tại (ví dụ: “kết nối websocket bị ngắt”, “WFV không trả về kết quả”, …).  
3. **Yêu cầu môi trường** (Python 3.10+, các package trong `requirements.txt`, cấu hình API Binance, …).

Nếu không có những thông tin trên, chúng tôi chỉ có thể đưa ra **kế hoạch tổng quát** để bạn tự kiểm tra và chuẩn bị môi trường phát triển. Dưới đây là mẫu tài liệu bạn có thể điền vào, sau đó chúng tôi sẽ cung cấp bản sửa lỗi chi tiết.

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS (Mẫu)

| Thành phần | Mô tả hiện trạng | Nguyên nhân tiềm năng |
|------------|------------------|-----------------------|
| **Kết nối Binance WebSocket** | `aiohttp` không nhận dữ liệu sau 5 phút | *Timeout* không được xử lý, hoặc *ping/pong* không được gửi. |
| **Walk‑Forward Validation (WFV)** | Không chia dữ liệu thành các fold | Thiếu hàm `split_time_series` hoặc tham số `window_size` sai. |
| **Monte‑Carlo Simulator** | Đưa ra `NaN` cho drawdown | Đầu vào `capital` không được khởi tạo, hoặc `np.random.normal` trả về mảng rỗng. |
| **Metrics (Sharpe, Sortino, Kelly)** | Giá trị âm/không hợp lý | Công thức chưa trừ rủi ro phi‑rủi ro (risk‑free rate) hoặc chia cho 0. |
| **Async I/O** | `RuntimeWarning: coroutine '...' was never awaited` | Gọi hàm async mà không dùng `await` hoặc không chạy trong event‑loop. |

> **Cách thu thập thông tin:**  
> - Chạy `pytest -vv` để xem stack‑trace.  
> - Kiểm tra log (`logging.DEBUG`) trong `scanner/logger.py`.  
> - Đảm bảo môi trường ảo (`python -m venv .venv && pip install -r requirements.txt`).  

---

## 2. SURGICAL CODE SOLUTION (Mẫu)

> **Giả sử** vấn đề nằm ở việc quản lý kết nối WebSocket và việc không `await` các coroutine. Dưới đây là đoạn vá mẫu cho file `scanner/websocket_client.py`.

```python
<pre><code>import asyncio
import aiohttp
import json
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class BinanceFuturesWS:
    WS_URL = "wss://fstream.binance.com/stream?streams=!miniTicker@arr"

    def __init__(self, on_message: Callable[[dict], Any], reconnect_delay: int = 5):
        self.on_message = on_message
        self.reconnect_delay = reconnect_delay
        self.session: aiohttp.ClientSession | None = None
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self._running = False

    async def _connect(self) -> None:
        """Tạo kết nối WebSocket mới, kèm ping/pong để giữ alive."""
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self.WS_URL)
        logger.info("✅ Connected to Binance Futures WS")

    async def _listen(self) -> None:
        """Lắng nghe tin nhắn, tự động reconnect khi mất kết nối."""
        async for msg in self.ws:  # type: ignore[union-attr]
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {msg.data}")
                break

    async def _handle_message(self, payload: dict) -> None:
        """Gọi callback người dùng, bảo vệ lỗi không làm dừng listener."""
        try:
            await self.on_message(payload)
        except Exception as exc:
            logger.exception(f"User callback raised: {exc}")

    async def start(self) -> None:
        """Khởi chạy vòng lặp kết nối, tự động reconnect."""
        self._running = True
        while self._running:
            try:
                await self._connect()
                await self._listen()
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as exc:
                logger.warning(f"Connection lost ({exc}), reconnect in {self.reconnect_delay}s")
                await asyncio.sleep(self.reconnect_delay)
            finally:
                await self._cleanup()

    async def stop(self) -> None:
        """Dừng listener một cách gọn gàng."""
        self._running = False
        await self._cleanup()

    async def _cleanup(self) -> None:
        if self.ws is not None and not self.ws.closed:
            await self.ws.close()
        if self.session is not None:
            await self.session.close()
        self.ws = None

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.44s • $0.00)</i>