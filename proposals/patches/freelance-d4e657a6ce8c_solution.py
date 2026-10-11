**Solution for Task ID freelance‑d4e657a6ce8c**

The task description is a raw job‑posting text.  
To make the data machine‑friendly we’ll add a small utility that parses the posting into a structured JSON‑like dictionary.  
This will be useful for downstream pipelines (e.g. auto‑tagging, scoring, or routing to the right team).

---

### 1. ROOT CAUSE & TECHNICAL ANALYSIS
The current system receives job‑posting text as plain Markdown/HTML.  
There is no automated extractor, so downstream services must manually parse the string, which is error‑prone and inconsistent.  
The missing parser causes:

* **Inconsistent data ingestion** – different fields may be extracted incorrectly.  
* **Hard‑coded string handling** – fragile to formatting changes.  
* **No validation** – malformed postings slip through.

**Solution**: Implement a robust, regex‑based parser that:

1. Detects the key fields (`Title`, `Reward`, `Description`, `Link`, `Comments`).  
2. Normalizes whitespace and removes Markdown/HTML tags.  
3. Returns a clean dictionary ready for downstream use.

---

### 2. SURGICAL CODE SOLUTION
```python
# <pre><code>
import re
from typing import Dict, Any

# Regular expressions for the main fields
FIELD_PATTERNS = {
    "title": re.compile(r"(?i)Title\s*:\s*(.+)"),
    "reward": re.compile(r"(?i)Reward\s*:\s*([\d,.]+)\s*(USD|$)"),
    "description": re.compile(r"(?i)Description\s*:\s*(.+)", re.DOTALL),
    "link": re.compile(r"(?i)link\s*:\s*(https?://[^\s]+)"),
    "comments": re.compile(r"(?i)comments\s*:\s*(.+)", re.DOTALL),
}

def _clean_text(text: str) -> str:
    """Remove Markdown/HTML tags and collapse whitespace."""
    # Strip <b> tags and other simple HTML
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple spaces/newlines
    return re.sub(r"\s+", " ", text).strip()

def parse_job_posting(raw: str) -> Dict[str, Any]:
    """
    Parse a raw job posting string into a structured dictionary.

    Parameters
    ----------
    raw : str
        The raw text of the job posting (Markdown/HTML).

    Returns
    -------
    dict
        Keys: title, reward, description, link, comments.
        Values are cleaned strings or None if not found.
    """
    result: Dict[str, Any] = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = pattern.search(raw)
        if match:
            # For reward, capture numeric value only
            if key == "reward":
                result[key] = float(match.group(1).replace(",", ""))
            else:
                result[key] = _clean_text(match.group(1))
        else:
            result[key] = None
    return result

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.74s • $0.00)</i>