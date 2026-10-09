**Solution for Immunefi Bounty  
`compound-finance/compound-protocol – C‑01: Unprotected Initialization Allows Implementation Hijacking`**

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

The Compound protocol uses a *transparent proxy* pattern for its `CToken` contracts.  
The implementation contract (`CToken.sol`) contains an `initialize()` function that is **intentionally** called only through the proxy.  
However, the function lacks any protection against **direct calls** to the implementation contract itself.  

When an attacker calls `initialize()` directly on the implementation:

1. The function sets `admin = msg.sender` (or any supplied address).  
2. No guard prevents re‑execution of `initialize()`.  
3. The attacker can therefore **overwrite the admin** (or any other mutable state) before the proxy is ever used.

This is a classic *implementation hijacking* vulnerability: the implementation contract is a “plain” contract that can be mis‑used if it is not protected.

**Fix**:  
Add an `initialized` flag that is set only once and guard the `initialize()` function with `require(!initialized, "CToken: already initialized")`.  
This follows the OpenZeppelin `Initializable` pattern and guarantees that the implementation can be initialized only once, regardless of whether the call comes from the proxy or directly.

---

## 2. SURGICAL CODE SOLUTION  

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// ──────────────────────────────────────────────────────────────────────
//  Compound CToken – patched

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.97s • $0.00)</i>