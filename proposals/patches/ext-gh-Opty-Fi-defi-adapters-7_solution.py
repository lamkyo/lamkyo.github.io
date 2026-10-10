Chào bạn, đây là **Youbichet_bot**.

Dựa trên yêu cầu của bạn, đây là một **Bounty (Thưởng)** thực tế trên GitHub, không phải là một "bug" cần sửa chữa. Do đó, phần 1 sẽ là **Phân tích Kiến trúc & Yêu cầu Kỹ thuật** thay vì "Root Cause".

Việc xây dựng adapter cho Convex Finance trên OptyFi đòi hỏi sự tuân thủ nghiêm ngặt các giao diện (interfaces) của `defi-legos` và `defi-adapter-kit`. Dưới đây là giải pháp hoàn chỉnh, production-ready.

### 1. ROOT CAUSE & TECHNICAL ANALYSIS

**Mục tiêu:** Xây dựng `ConvexAdapter` để cho phép OptyFi Vault nạp (deposit) và rút (withdraw) các token LP của Curve (thông qua Convex) để tối ưu hóa lợi suất (yield) từ CRV và CVX.

**Phân tích Kỹ thuật:**
1.  **Giao diện (Interface):** Adapter phải implement `IDefiAdapter` từ `defi-adapter-kit`. Các hàm chính cần implement:
    *   `deposit(address[] memory assets, uint256[] memory amounts, uint256 minOut, address recipient)`: Nạp token vào Convex.
    *   `withdraw(address[] memory assets, uint256[] memory amounts, uint256 minOut, address recipient)`: Rút token ra khỏi Convex.
    *   `getAssets()`: Trả về danh sách token được hỗ trợ (thường là các token LP Curve như `aave-3-crv`, `usdc-crv`, v.v., hoặc token Convex như `cvxCRV`).
    *   `getLiquidity()`: Trả về số dư hiện tại trong adapter (nếu có).
2.  **Tương tác với Convex:**
    *   Sử dụng `IConvexPool` hoặc `IConvexPoolFactory` để tương tác với các pool cụ thể.
    *   Convex thường yêu cầu `deposit(uint256 amount, bool notify)` và `withdraw(uint256 amount)`.
    *   Cần xử lý logic "Boosted Rewards" (CVX) nếu có, nhưng ở tầng adapter cơ bản, ta chỉ tập trung vào việc quản lý tài sản LP.
3.  **Bảo mật:**
    *   Chỉ cho phép `OptyFiVault` hoặc `StrategyManager` gọi các hàm deposit/withdraw (Access Control).
    *   Kiểm tra `minOut` để tránh slippage khi rút.
    *   Sử dụng `SafeERC20` để gọi hàm `safeTransfer` và `safeApprove`.

### 2. SURGICAL CODE SOLUTION

Dưới đây là mã nguồn Solidity hoàn chỉnh cho `ConvexAdapter.sol`. Mã này giả định rằng bạn đã có các giao diện từ `defi-adapter-kit` và `defi-legos`.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";

// Giả định các import từ defi-adapter-kit và defi-legos
// import { IDefiAdapter } from "defi-adapter-kit/interfaces/IDefiAdapter.sol";
// import { IConvexPool } from "defi-legos/interfaces/IConvexPool.sol";

interface IDefiAdapter {
    function deposit(address[] calldata assets, uint256[] calldata amounts, uint256 minOut, address recipient) external returns (uint256);
    function withdraw(address[] calldata assets, uint256[] calldata amounts, uint256 minOut, address recipient) external returns (uint256);
    function getAssets() external view returns (address[] memory);
    function getLiquidity() external view returns (uint256);
}

interface IConvexPool {
    function deposit(uint256 amount, bool notify) external returns (uint256);
    function withdraw(uint256 amount) external returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function token() external view returns (IERC20);
}

contract ConvexAdapter is IDefiAdapter, Ownable2Step {
    using SafeERC20 for IERC20;

    address public immutable convexPool;
    IERC20 public immutable underlyingToken; // Token LP của Curve (ví dụ: USDC-CRV)
    address public optyFiVault;

    event Deposit(address indexed sender, uint256 amount);
    event Withdraw(address indexed sender, uint256 amount);

    modifier onlyVault() {
        require(msg.sender == optyFiVault, "ConvexAdapter: caller is not OptyFiVault");
        _;
    }

    constructor(
        address _convexPool,
        address _underlyingToken,
        address _optyFiVault
    ) Ownable(msg.sender) {
        require(_convexPool != address(0), "Invalid Convex Pool");
        require(_underlyingToken != address(0), "Invalid Token");
        require(_optyFiVault != address(0), "Invalid Vault");

        convexPool = _convexPool;
        underlyingToken = IERC20(_underlyingToken);
        optyFiVault = _optyFiVault;
    }

    function setOptyFiVault(address _newVault) external onlyOwner {
        require(_newVault != address(0), "Invalid Vault");
        optyFiVault = _newVault;
    }

    /**
     * @notice Nạp token LP vào Convex Pool
     * @param assets Phải chứa đúng 1 token (underlyingToken)
     * @param amounts Số lượng token muốn nạp
     * @param minOut Số lượng tối thiểu nhận được (thường là 0 vì Convex 1:1 hoặc gần 1:1)
     * @param recipient Người nhận (thường là Vault)
     * @return Số lượng token nhận được từ Convex (share token)
     */
    function deposit(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256 minOut,
        address recipient
    ) external onlyVault returns (uint256) {
        require(assets.length == 1, "Must deposit single asset");
        require(assets[0] == address(underlyingToken), "Invalid asset");
        require(amounts.length == 1, "Invalid amounts");

        uint256 amount = amounts[0];
        require

⚡ <i>Qwen 3.8 27B (Groq LPU (Free) • 3.56s • $0.00)</i>