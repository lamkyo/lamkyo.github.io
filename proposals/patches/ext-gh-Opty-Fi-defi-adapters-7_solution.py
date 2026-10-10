**Solution Overview**  
The goal is to add a **Convex Finance DeFi‑Adapter** that conforms to OptyFi’s `IDefiAdapter` interface (see `defi-adapter-kit`). The adapter must:

* Accept **CRV, CVX and any Curve LP token** (e.g. `3CRV`) from a vault.  
* Deposit those assets into Convex via the **Booster** contract, receiving the corresponding **Convex reward pool** token (`cvxCRV`, `cvxLP`).  
* Allow the vault to **withdraw** the original assets (plus any earned rewards) on demand.  
* Expose **reward‑claiming** (`claimRewards`) and **view helpers** (`getUnderlyingTokens`, `getRewardTokens`).  
* Be fully unit‑tested with **≥ 100 % line coverage**.

Below you will find a deterministic, production‑ready implementation together with a complete test‑suite and a ready‑to‑use PR description.

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Issue | Why it matters | Required architectural change |
|-------|----------------|--------------------------------|
| **No existing Convex adapter** | OptyFi vaults can’t route CRV / Curve LP assets to Convex, missing a high‑yield opportunity. | Introduce a new contract `ConvexAdapter` that implements `IDefiAdapter`. |
| **Different token types** (CRV, CVX, Curve LP) | Each token has a distinct deposit flow (CRV → Convex pool, Curve LP → Convex pool, CVX is a reward token). | The adapter must detect the incoming token via the `data` payload and call the appropriate Booster pool. |
| **Reward handling** | Convex distributes **CRV, CVX and extra token** rewards. OptyFi needs a deterministic way to claim and forward them to the vault. | Implement `claimRewards()` that pulls all reward tokens from the Convex reward pool and transfers them to the caller (the vault). |
| **Safety & upgradeability** | OptyFi uses the `defi-adapter-kit` pattern with `Initializable` and `Ownable`. | Inherit from `AdapterBase` (provided by the kit) to get pause/ownership, and use `SafeERC20`. |
| **Testing requirements** | Bounty demands **100 % test coverage**. | Write a full Hard‑hat test suite covering every public/external function, edge cases (zero amount, unsupported token, re‑entrancy). |

**Key design decisions**

1. **Single‑entry `deposit`** – The caller passes the *target Convex pool id* (uint256) in `bytes calldata data`. The adapter validates the pool exists, transfers the supplied token, and calls `Booster.deposit(poolId, amount, true)`.  
2. **`withdraw`** – Mirrors the deposit: the adapter calls `RewardPool.withdrawAndUnwrap(amount, true)` and returns the underlying token to the vault.  
3. **Reward tokens** – The adapter reads the reward pool’s `rewardTokens()` (Convex may add new rewards) and forwards all balances to the vault.  
4. **Gas optimisation** – Use `unchecked` loops where safe, cache token decimals, and emit concise events.  

---

## 2. SURGICAL CODE SOLUTION  

### 2.1. Solidity contract (`contracts/ConvexAdapter.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ConvexAdapter
 * @dev OptyFi DeFi‑Adapter for Convex Finance.
 *      Implements the IDefiAdapter interface from defi‑adapter‑kit.
 *      Supports depositing CRV, CVX and any Curve LP token into Convex
 *      booster pools and claiming the associated rewards.
 */

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";

import "./interfaces/IDefiAdapter.sol";
import "./interfaces/IConvexBooster.sol";
import "./interfaces/IConvexRewardPool.sol";

contract ConvexAdapter is IDefiAdapter, Initializable, Ownable {
    using SafeERC20 for IERC20;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------
    IConvexBooster public immutable booster; // Convex Booster contract
    mapping(uint256 => address) public poolIdToRewardPool; // poolId → Convex reward pool
    mapping(address => bool) public supportedUnderlying;   // token address → allowed?

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------
    event Deposited(address indexed token, uint256 amount, uint256 poolId);
    event Withdrawn(address indexed token, uint256 amount, uint256 poolId);
    event RewardsClaimed(address indexed rewardToken, uint256 amount);

    // -------------------------------------------------------------------------
    // Constructor / Initializer
    // -------------------------------------------------------------------------
    constructor(address _booster) {
        require(_booster != address(0), "Booster zero");
        booster = IConvexBooster(_booster);
    }

    function initialize(
        address[] calldata _underlyings,
        uint256[] calldata _poolIds,
        address[] calldata _rewardPools
    ) external initializer onlyOwner {
        require(
            _underlyings.length == _poolIds.length &&
            _poolIds.length == _rewardPools.length,
            "Array length mismatch"
        );
        for (uint256 i = 0; i < _underlyings.length; ++i) {
            supportedUnderlying[_underlyings[i]] = true;
            poolIdToRewardPool[_poolIds[i]] = _reward

⚡ <i>GPT OSS 120B (Groq LPU (Free) • 3.76s • $0.00)</i>