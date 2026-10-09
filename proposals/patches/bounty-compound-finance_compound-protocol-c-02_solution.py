**Solution to Immunefi Bounty #bounty-compound-finance_compound-protocol-c-02**

> **Title**: SimplePriceOracle Manipulation via Unrestricted Price Setting  
> **Reward**: $2,500.00 USDC  
> **Platform**: immunefi_web3  

Below is a complete, deterministic solution that fixes the vulnerability, proves the fix with a Foundry test suite, and includes a ready‑to‑merge PR description.

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS

The `SimplePriceOracle` contract in Compound v2 exposes a public `setPrice(address asset, uint price)` function with **no access control**.  
Because the Comptroller is the only contract that should be able to update oracle prices, an attacker can call `setPrice` from any address, set a malicious price (e.g., 0 or an extremely low value), and then borrow assets against that collateral without being properly collateralized.  

**Why the bug occurs**

* The contract was designed as a simple,

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 2.18s • $0.00)</i>