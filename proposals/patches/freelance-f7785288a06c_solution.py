**Solution to the “freelance‑f7785288a06c” posting issue**

The job posting was never moved from **SUBMITTED** to **READY_FOR_EGRESS** because the
backend’s tag‑extraction routine was **case‑sensitive**.  
The title contains the word *“CHARACTER”* in all caps, but the parser only
recognised tags that matched the expected lower‑case form (e.g. “character”).
Consequently the job never satisfied the “character” filter and was stuck in
the queue, ultimately being auto‑rejected.

Below is a minimal, production‑ready patch that normalises tags to lower‑case
and a test suite that guarantees the behaviour.

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS

* **Bug** – The `extract_tags()` function in `job_parser.py` performs a
  case‑sensitive split on the job title and body, then stores the tags as‑is.
  The downstream filter that moves a job to `READY_FOR_EGRESS` checks for the
  presence of the tag `"character"` in lower‑case.  
  Because the title contains `"CHARACTER"` (upper‑case), the tag never matches,
  leaving the job in the `SUBMITTED` state and eventually causing an automatic
  rejection.

* **Impact** – Legitimate high‑ticket character commissions are never processed,
  reducing revenue for the platform and frustrating freelancers.

* **Root cause** – The parser does **not normalise case** before comparison,
  leading to a mismatch between the stored tag and the filter’s expected value.

---

## 2. SURGICAL CODE SOLUTION

```python
# job_parser.py
import re
from typing import List, Set

TAG_PATTERN = re.compile(r'\[(.*?)\]')  # Extract tags inside square brackets
WORD_TAGS = {"character", "anime", "illustration"}  # Known tags

def extract_tags(title: str, body: str) -> Set[str]:
    """
    Extracts tags from the job title and body.

    Tags are defined in two ways:
    1. Explicit tags inside square brackets, e.g. "[High-Ticket Contract]"
    2. Keyword tags that appear in the body (case‑insensitive

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.85s • $0.00)</i>