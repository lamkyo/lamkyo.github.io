**Solution for “TechCrunch Disrupt 2026 – Pass‑Pricing Engine”**  
*(được trình bày theo 4 phần yêu cầu)*  

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Vấn đề | Nguyên nhân | Hậu quả |
|--------|-------------|---------|
| **Tính giá vé không áp dụng đúng các ưu đãi** | - Logic hiện tại chỉ cộng dồn các giảm giá mà không kiểm soát “giảm tối đa $100” cho ưu đãi Early‑Bird.<br>- Không có kiểm tra “giảm 50 % cho vé thứ 2 cùng loại” → khách hàng có thể nhận giảm giá quá mức hoặc không nhận được ưu đãi thứ 2. | - Doanh thu giảm do giảm giá sai.<br>- Trải nghiệm khách hàng kém (đánh giá sai giá). |

**Yêu cầu nghiệp vụ**  

1. **Early‑Bird**: giảm tối đa **$100** so với giá gốc (có thể giảm ít hơn nếu giá gốc < $100).  
2. **Second‑Pass**: khi mua **cùng loại** vé thứ 2, giảm **50 %** trên giá đã được áp dụng Early‑Bird (nếu có).  
3. **Không chồng chéo**: ưu đãi Second‑Pass chỉ áp dụng cho vé thứ 2, không ảnh hưởng tới vé đầu tiên.  

**Thiết kế**  

- Tạo một lớp `PassPricingEngine` chịu trách nhiệm tính giá cuối cùng.  
- Hàm `calculate_price(base_price: float, quantity: int) -> List[float]` trả về danh sách giá từng vé (đảm bảo tính riêng rẽ cho vé 1 và vé 2…).  
- Áp dụng **Early‑Bird** lên mỗi vé riêng biệt, sau đó nếu `quantity >= 2` áp dụng **Second‑Pass** cho vé thứ 2 (và các vé tiếp theo nếu muốn mở rộng).  

---

## 2. SURGICAL CODE SOLUTION  

```python
# pass_pricing.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PassType:
    """Mô tả một loại Pass (ví dụ: General, VIP, Student)."""
    name: str
    base_price_usd: float


class PassPricingEngine:
    """
    Engine tính giá vé với các ưu đãi:
    - Early‑Bird: giảm tối đa 100 USD.
    - Second‑Pass: giảm 50% cho vé thứ 2 cùng loại (sau khi áp dụng Early‑Bird).
    """

    EARLY_BIRD_MAX_DISCOUNT = 100.0
    SECOND_PASS_DISCOUNT_RATE = 0.5

    @staticmethod
    def _apply_early_bird(price: float) -> float:
        """Giảm tối đa $100, không được giảm giá dưới 0."""
        discount = min(PassPricingEngine.EARLY_BIRD_MAX_DISCOUNT, price)
        return round(price - discount, 2)

    @staticmethod
    def _apply_second_pass(price: float) -> float:
        """Giảm 50% trên giá đã được Early‑Bird giảm."""
        return round(price * (1 - PassPricingEngine.SECOND_PASS_DISCOUNT_RATE), 2)

    def calculate_price(self, pass_type: PassType, quantity: int) -> List[float]:
        """
        Trả về danh sách giá cho mỗi vé.

        :param pass_type: Loại Pass và giá gốc.
        :param quantity: Số vé muốn mua (>=1).
        :return: List[float] – giá cuối cùng cho từng vé (theo thứ tự mua).
        """
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        # Bước 1: Early‑Bird cho mọi vé
        early_prices = [self._apply_early_bird(pass_type.base_price_usd) for _ in range(quantity)]

        # Bước 2: Second‑Pass cho vé thứ 2 (và các vé tiếp theo nếu muốn mở rộng)
        final_prices = early_prices.copy()
        if quantity >= 2:
            # Áp dụng giảm 50% cho vé thứ 2
            final_prices[1] = self._apply_second_pass(early_prices[1])
            # Nếu có hơn 2 vé, các vé còn lại giữ giá Early‑Bird (có thể mở rộng logic sau)
        return final_prices


# Example usage (được giữ trong file để dễ test):
if __name__ == "__main__":
    engine = PassPricingEngine()
    general = PassType(name="General", base_price_usd=350.0)
    print(engine.calculate_price(general, quantity=2))
    # Expected: [250.0, 125.0]  (350‑100 = 250; 250‑50% = 125)
```

**Giải thích nhanh**  

- `PassType` dùng `dataclass` để mô tả loại vé và giá gốc.  
- `_apply_early_bird` giảm tối đa $100, luôn trả về số thập phân 2 chữ số.  
- `_apply_second_pass` giảm 50 % trên giá đã được Early‑Bird giảm.  
- `calculate_price` thực hiện quy trình theo thứ tự: Early‑Bird → Second‑Pass (đối với vé thứ 2).  

---

## 3. VERIFICATION & UNIT TEST SUITE  

```python
# test_pass_pricing.py
import unittest
from pass_pricing import PassPricingEngine, PassType


class TestPassPricingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PassPricingEngine()
        self.general = PassType(name="General", base_price_usd=350.0)
        self.student = PassType(name="Student", base_price_usd=80.0)   # giá < 100

    def test_single_pass_early_bird(self):
        # Chỉ có 1 vé → chỉ

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.40s • $0.00)</i>