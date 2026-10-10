Chào bạn, tôi là **Antigravity**.

Dựa trên hệ thống dữ liệu và yêu cầu của bạn, đây là phân tích và giải pháp chi tiết cho Task ID: `ext-gh-Opty-Fi-defi-adapters-7`.

**Lưu ý quan trọng về tính trung thực:**
1.  **Bản chất Task:** Đây không phải là một "bug" cần sửa (fix), mà là một **Bounty (Thưởng)** để phát triển tính năng mới (Feature Development). Do đó, mục "Root Cause" sẽ được chuyển thành "Architectural Analysis" (Phân tích kiến trúc).
2.  **Phạm vi Code:** Việc viết một adapter hoàn chỉnh cho Convex Finance (bao gồm quản lý vị thế, xử lý CRV/CVX, tương tác với Curve pools) là một dự án Solidity lớn, thường mất hàng tuần để hoàn thiện và audit. Tôi sẽ cung cấp **bộ khung (skeleton) chuẩn mực** dựa trên `defi-adapter-kit` và `defi-legos`, cùng với bộ test mẫu để bạn có thể triển khai tiếp.
3.  **Chi phí:** Việc sử dụng AI để hỗ trợ code là miễn phí, nhưng việc deploy, gas fee và reward $5,000 USDC thuộc về quy trình của OptyFi.

Dưới đây là giải pháp được cấu trúc theo 4 phần rõ ràng.

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS (Phân tích Kiến trúc)

**Mục tiêu:** Xây dựng `ConvexAdapter` để OptyFi Vault có thể gửi CRV, CVX và Curve LP tokens vào Convex Finance để tối ưu hóa yield.

**Các thành phần kỹ thuật chính cần tích hợp:**
1.  **Interface Compliance:** Adapter phải implement `IAdapter` (hoặc interface tương đương trong `defi-adapter-kit`) để OptyFi Core có thể gọi được các hàm `deposit`, `withdraw`, `getBalance`.
2.  **Convex Integration:**
    *   Sử dụng `ConvexRegistry` để tìm pool ID tương ứng với Curve pool.
    *   Gọi `convexPool.deposit()` để gửi LP tokens vào Convex.
    *   Quản lý `cvxPool` để nhận phần thưởng CVX (boosted yield).
    *   Xử lý `CRV` rewards: Convex có cơ chế "Claim & Stake" hoặc "Auto-compound". Adapter cần logic để claim CRV và có thể tái đầu tư (re-stake) hoặc rút ra.
3.  **Asset Mapping:**
    *   Input: `CRV`, `CVX`, `CurveLP` (ví dụ: `USDC/DAI/USDT` LP).
    *   Output: Yield từ Convex (CRV + CVX + Base Yield).
4.  **Safety & Slippage:**
    *   Cần tính toán slippage khi swap (nếu có) hoặc xác nhận tỷ giá khi deposit/withdraw.
    *   Phải xử lý trường hợp `poolId` không tồn tại hoặc pool đã bị deprecated.

**Kiến trúc đề xuất:**
*   **Contract:** `ConvexAdapter.sol`
*   **Dependencies:**
    *   `ConvexRegistry` (từ Convex)
    *   `CurvePool` (tương tác trực tiếp hoặc qua Convex)
    *   `OptyFiAdapterBase` (từ `defi-adapter-kit`)
    *   `SafeERC20` (để xử lý token transfer an toàn)

---

### 2. SURGICAL CODE SOLUTION (Mã nguồn Adapter)

*Đây là khung code chuẩn (Solidity 0.8.x) dựa trên các best practices của DeFi. Bạn cần thay thế các địa chỉ hợp đồng (addresses) bằng địa chỉ thực tế trên mạng lưới (Mainnet/Arbitrum).*

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// Giả định các interface từ defi-adapter-kit
// import {IAdapter} from "../interfaces/IAdapter.sol";
// import {AdapterBase} from "../contracts/AdapterBase.sol";

// Giả định các interface Convex
interface IConvexRegistry {
    function poolIdForCurvePool(address pool) external view returns (uint256);
    function pool(address pool) external view returns (uint256 poolId, address poolAddress);
}

interface IConvexPool {
    function deposit(uint256 amount) external returns (uint256);
    function withdraw(uint256 amount) external returns (uint256);
    function earn(uint256 amount) external;
    function withdraw(uint256 amount) external;
    function claim(uint256) external returns (uint256);
}

contract ConvexAdapter is Ownable2Step, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // Cấu hình hệ thống
    address public convexRegistry;
    address public convexPool; // Ví dụ: Convex USDC/DAI/USDT Pool
    address public curvePool;  // Ví dụ: Curve USDC/DAI/USDT Pool
    address public crvToken;
    address public cvxToken;
    address public vault;      // Địa chỉ OptyFi Vault

    uint256 public constant MIN_WITHDRAWAL = 1e6; // 0.001 token (điều chỉnh theo decimals)

    event Deposited(address indexed user, uint256 amount, uint256 pid);
    event Withdrawn(address indexed user, uint256 amount, uint256 pid);
    event Claimed(address indexed user, uint256 crvAmount, uint256 cvxAmount);

    constructor(
        address _convexRegistry,
        address _convexPool,
        address _curvePool,
        address _crvToken,
        address _cvxToken,
        address _vault
    ) Ownable(msg.sender) {
        require(_convexRegistry != address(0), "Invalid Registry");
        require(_convexPool != address(0), "Invalid Convex Pool");
        require(_curvePool != address(0), "Invalid Curve Pool");
        require(_crvToken != address(0), "Invalid CRV");
        require(_cvxToken != address(0), "Invalid CVX");
        require(_vault != address(0), "Invalid Vault");

        convexRegistry = _convexRegistry;
        convexPool = _conv

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.17s • $0.00)</i>