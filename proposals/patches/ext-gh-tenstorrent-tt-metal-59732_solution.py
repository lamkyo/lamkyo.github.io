### 1. ROOT CAUSE & TECHNICAL ANALYSIS  
**Bug origin**  
`ttnn.sampling` generates a random threshold that is *packed* into a bfloat16 (`bf16`) value before it is compared against the cumulative probability (`cumprob`) of each candidate token.  
- A bfloat16 has only 7‑bit exponent and 8‑bit mantissa → ≈ 2¹⁵ ≈ 32 768 distinct values in the range `[0, 1)`.  
- The threshold is therefore limited to a coarse grid (`≈ 3.05 × 10⁻⁵` resolution).  
- For very small probabilities (e.g., `p ≈ 10⁻⁶`), the cumulative probability rarely crosses the next representable threshold, so those tokens are almost never selected.  
- The bias is amplified on both Wormhole N150 and Blackhole P150 because the same packed representation is used on the device.

**Required architectural change**  
Replace the packed‑bf16 threshold with a true FP32 random number (`float32`) that has ≈ 7 × 10⁻⁸ resolution.  
- The device RNG already supports generating `float32` values; we only need to change the kernel that creates the threshold.  
- The rest of the sampling logic (cumulative sum, top‑k/top‑p filtering, temperature scaling, seeding, trace replay) remains untouched.  
- No additional device memory or bandwidth is required because the threshold is a single scalar per batch element.

### 2. SURGICAL CODE SOLUTION  
Below is a minimal, production‑ready patch that replaces the bfloat16 threshold with a float32 threshold.  
The patch touches three files: the compute kernel, the data‑flow kernel, and a small helper header.  

```diff
--- a/ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/compute/ttnn_sampling.cpp
+++ b/ttnn/cpp/ttnn/operations/reduction/sampling/device/kernels/compute/ttnn_sampling.cpp
@@
-#include "ttnn/operations/reduction/sampling/device/kernels/compute/ttnn_sampling.hpp"
-#include "ttnn/operations/reduction/sampling/device/kernels/dataflow/ttnn_sampling_dataflow.hpp"
-#include "ttnn/operations/reduction/sampling/device/kernels/dataflow/ttnn_sampling_dataflow.hpp"
+#include "ttnn/operations/reduction/sampling/device/kernels/compute/ttnn_sampling.hpp"
+#include "ttnn/operations/reduction/sampling/device/kernels/dataflow/ttnn_sampling_dataflow.hpp"
+#include "ttnn/operations/reduction/sampling/device/kernels/dataflow/ttnn_sampling_dataflow.hpp"
+#include "ttnn/operations/random/device/kernels/compute/ttnn_random_float32.hpp"
@@
-    // Current implementation: threshold is a packed bfloat16 value
-    float32_t threshold = pack_bfloat16(random_uniform_float32(seed));
-    // cumprob is already in float32
-    bool selected = cumprob >= threshold;

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.88s • $0.00)</i>