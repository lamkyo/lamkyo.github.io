**Solution to “freelance‑c4c5f9eb9533” – Parsing an Unstructured Job Posting**

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

The job posting is a plain‑text blob that contains all relevant information (title, reward, description, portfolio links, contact details, etc.) in a free‑form layout.  
Because the data is not in a structured format (JSON, CSV, or a well‑defined template), downstream systems (e.g., a job‑board aggregator, a CRM, or an analytics pipeline) cannot reliably extract the fields they need.  

**Root causes**

| # | Cause | Consequence |
|---|-------|-------------|
| 1 | No delimiters or tags around key fields | Manual extraction is error‑prone |
| 2 | Mixed languages (English + German) & inconsistent punctuation | Regex patterns may miss parts |
| 3 | URLs and links are embedded inline without anchors | Hard to identify and validate |
| 4 | Incomplete or truncated title (missing closing parenthesis) | Parsing may produce malformed output |

**Technical requirement**

Create a deterministic, production‑ready parser that:

1. Extracts the **title**, **reward**, **description**, **portfolio links**, **contact method**, and **payment method**.
2. Handles optional fields (e.g., missing URLs) gracefully.
3. Validates URLs and numeric values.
4. Returns a clean, typed data structure (`JobPosting` dataclass).

---

## 2. SURGICAL CODE SOLUTION  

```python
# parse_job_posting.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

@dataclass
class JobPosting:
    title: str
    reward_usd: float
    description: str
    portfolio_links: List[str] = field(default_factory=list)
    contact: Optional[str] = None
    payment_method: Optional[str] = None
    raw_text: Optional[str] = None

URL_REGEX = re.compile(
    r'https?://[^\s)]+',
    re.IGNORECASE
)

REWARD_REGEX = re.compile(
    r'Reward:\s*\$([\d,.]+)\s*USD',
    re.IGNORECASE
)

TITLE_REGEX = re.compile(
    r'^[^\n]*$',  # first non‑empty line
    re.MULTILINE
)

CONTACT_REGEX = re.compile(
    r'(?i)(?:Comment|DM|contact|email|mail|phone)\s*[:\-]?\s*([^\n]+)',
    re.IGNORECASE
)

PAYMENT_REGEX = re.compile(
    r'Payment:\s*(PayPal|PayPal\.com|PayPal\.de|PayPal\.uk|PayPal\.fr|PayPal\.es|Pay

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.71s • $0.00)</i>