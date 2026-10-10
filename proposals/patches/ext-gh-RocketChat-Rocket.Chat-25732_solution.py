**Solution for #25732 – Chunked File Uploads for CDN/Proxy‑limited Rocket.Chat**

> **Reward:** $1 000  
> **Platform:** GitHub Bounty  
> **Target:** Rocket.Chat 3.14.3 (Ubuntu, Node 12.18.4, MongoDB 4.0.25)  

> **Problem:**  
> When a Rocket.Chat instance is served behind a CDN (e.g. Cloudflare) the single‑request REST upload endpoint (`/api/v1/files.upload`) fails for files larger than the CDN’s request‑size limit (100 MB). The current upload flow is *not* chunked – the entire file is sent in one POST,

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.90s • $0.00)</i>