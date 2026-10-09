Chào bạn, đây là giải pháp chi tiết cho bounty `ext-gh-tenstorrent-tt-metal-59732`.

Vấn đề cốt lõi nằm ở sự mất mát độ chính xác (precision loss) khi so sánh xác suất tích lũy (cần độ chính xác cao) với một ngưỡng ngẫu nhiên (random threshold) bị nén xuống bfloat16. Dưới đây là phân tích và giải pháp kỹ thuật.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Nguyên nhân gốc rễ:**
Trong kiến trúc Tenstorrent (Wormhole/Blackhole), các phép toán trên RISC-V cores thường tối ưu hóa cho bfloat16 (16-bit) để tăng thông lượng. Tuy nhiên, `ttnn.sampling` yêu cầu độ chính xác FP32 (32-bit) để đảm bảo phân phối xác suất chính xác.

Lỗi xảy ra trong quá trình tạo và so sánh `random_threshold`:
1.  **Quantization Error:** Ngưỡng ngẫu nhiên (thường là số thực trong khoảng [0, 1)) được sinh ra hoặc lưu trữ dưới dạng bfloat16. Bfloat16 chỉ có 8 bit cho phần mantissa (so với 23 bit của FP32). Điều này tạo ra một lưới rời rạc (grid) rất thô.
2.  **Bias in Low Probabilities:** Khi xác suất của một token rất nhỏ (ví dụ: 0.001), bước nhảy giữa các giá trị bfloat16 lân cận có thể lớn hơn chính xác suất đó. Kết quả là:
    *   Token có xác suất nhỏ có thể **không bao giờ** được chọn (nếu ngưỡng ngẫu nhiên không bao giờ rơi vào khoảng cực hẹp đó do giới hạn độ phân giải).
    *   Hoặc tần suất xuất hiện bị sai lệch nghiêm trọng so với lý thuyết.
3.  **Packing Limitation:** Một số implementation cũ có thể đóng gói (pack) các giá trị này vào các register hoặc shared memory với giả định về độ chính xác thấp, dẫn đến việc "capping" hoặc làm tròn ngưỡng xuống lưới bfloat16 trước khi so sánh với cumulative probability (đang ở dạng FP32).

**Giải pháp kỹ thuật:**
*   Giữ nguyên `cumulative_probability` ở dạng **FP32** trong bộ nhớ và trong phép so sánh.
*   Sinh `random_threshold` với độ chính xác **FP32**.
*   Thực hiện phép so sánh `cumulative_prob[i] >= random_threshold` trong không gian FP32.
*   Chỉ chuyển đổi kết quả (index được chọn) về dạng integer.
*   Đảm bảo kernel compute không ép kiểu (cast) ngưỡng ngẫu nhiên xuống bfloat16 trước khi so sánh.

### 2. SURGICAL CODE SOLUTION

Dưới đây là các patch cần thiết cho các file kernel chính. Giả sử cấu trúc thư mục chuẩn của TT-Metal.

#### File 1: `ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/compute/sampling_compute_kernel.cpp`

Đây là phần quan trọng nhất. Chúng ta cần đảm bảo phép so sánh được thực hiện ở độ chính xác FP32.

```cpp
// ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/compute/sampling_compute_kernel.cpp

#include "tt-metalium/tt_metal.h"
#include "tt-metalium/tt_stl.hpp"
#include "tt-metalium/host_api.hpp"

namespace ttnn::operations::reduction::sampling {

// Giả định: Kernel này chạy trên RISC core. 
// Chúng ta cần đảm bảo các biến liên quan đến xác suất và ngưỡng là float (FP32).

void sampling_compute_kernel(
    const tt::stl::Span<const float> cumulative_probs, // FP32 cumulative probabilities
    const float random_threshold,                      // FP32 random threshold
    tt::stl::Span<int32_t> output_indices,             // Output token indices
    const int32_t vocab_size,
    const int32_t top_k,
    const float top_p,
    const float temperature
) {
    // 1. Xử lý Temperature (nếu có, thường được áp dụng trước cumulative)
    // Trong ngữ cảnh này, cumulative_probs đã được tính toán sẵn.
    
    // 2. Tìm index nhỏ nhất sao cho cumulative_probs[i] >= random_threshold
    // Việc so sánh này PHẢI là FP32 để tránh bias.
    
    int32_t selected_index = -1;
    
    // Tối ưu hóa: Sử dụng binary search nếu cumulative_probs đã được sắp xếp tăng dần
    // Tuy nhiên, trong sampling non-greedy, cumulative_probs thường là mảng 1D 
    // đại diện cho phân phối xác suất của các token.
    // Giả sử cumulative_probs[i] là tổng xác suất từ token 0 đến i.
    
    // Nếu top_k và top_p được áp dụng, cumulative_probs có thể đã được điều chỉnh.
    // Tại đây, chúng ta chỉ cần tìm điểm cắt (cutoff).
    
    // Lưu ý: Trong TT-Metal, việc truy cập bộ nhớ và tính toán trên RISC 
    // cần được thực hiện cẩn thận để tránh bottleneck.
    
    for (int32_t i = 0; i < vocab_size; ++i) {
        // So sánh FP32 với FP32
        if (cumulative_probs[i] >= random_threshold) {
            selected_index = i;
            break;
        }
    }
    
    // Xử lý trường hợp không tìm thấy (do lỗi làm tròn hoặc threshold > 1.0)
    if (selected_index == -1) {
        selected_index = vocab_size - 1;
    }
    
    output_indices[0] = selected_index;
}

} // namespace ttnn::operations::reduction::sampling
```

*Lưu ý thực tế:* Trong TT-Metal, kernel thường được viết bằng C++ đặc thù cho RISC (sử dụng intrinsics hoặc assembly nếu cần tối ưu cực đại). Tuy nhiên, logic cốt lõi là **không cast `random_threshold` xuống bfloat16**.

#### File 2: `ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/dataflow/sampling_dataflow_kernel.cpp`

Đảm bảo dữ liệu được truyền vào compute kernel ở dạng FP32.

```cpp
// ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/dataflow/sampling_dataflow_kernel.cpp

#include "tt-metalium/tt_metal.h"

namespace ttnn::operations::reduction::sampling {

void sampling_dataflow_kernel(
    const tt::stl::Span<const float> input_probs, // Xác suất thô (FP32)
    tt::stl::Span<float> cumulative_probs,        // Output cumulative (FP32)
    const int32_t vocab_size
) {

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.10s • $0.00)</i>