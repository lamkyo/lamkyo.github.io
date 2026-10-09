## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

The client’s catalogues (restaurant menus or e‑commerce product lists) typically suffer from the same set of data‑quality issues:

| Problem | Typical Symptoms | Why it matters |
|---------|------------------|----------------|
| **Duplicate rows** | Same SKU appears multiple times with slightly different names or prices | Increases inventory size, causes pricing conflicts |
| **Missing mandatory fields** | SKU, name, price, category absent | Prevents product from being sold or displayed |
| **Inconsistent formatting** | Prices “$12.99”, “12,99 USD”, “12.99$” | Hard to aggregate, compare, or import into other systems |
| **Typos / OCR errors** | “Chiken” instead of “Chicken” | Reduces searchability, hurts customer trust |
| **Incorrect image references** | Wrong file names, broken links | Products appear broken on the front‑end |
| **Unstructured “description” column** | Mixed categories, tags, or pricing info | Makes automated processing impossible |

The root cause is that most catalogs are created manually (Excel, Google Sheets, PDF scans, or manual data entry) and then exported as CSV/Excel. The data is not validated before import, so the downstream systems (websites, POS, etc.) receive noisy data.

**Architectural requirement**  
We need a **stand‑alone, repeatable pipeline** that:

1. **Ingests** raw CSV/Excel files.
2. **Normalises** fields (price, SKU, name, category).
3. **Validates** mandatory columns and data types.
4. **Deduplicates** based on SKU or a composite key.
5. **Reports** issues (missing fields, duplicates, price inconsistencies).
6. **Outputs** a clean CSV ready for import.

Because the client works asynchronously with many files, the solution should be:

* **Command‑line friendly** – can be run on a VPS or local machine.
* **Idempotent** – running twice on the same file gives the same result.
* **Extensible** – new validation rules can be added via configuration.

We’ll implement this in **Python 3.11** using `pandas` for data manipulation and `click` for the CLI. The script will be packaged as a small library so that unit tests can exercise each step in isolation.

---

## 2. SURGICAL CODE SOLUTION  

```python
# catalog_cleaner/__init__.py
__all__ = ["clean_catalog", "validate_catalog", "deduplicate_catalog"]

# catalog_cleaner/core.py
import re
from pathlib import Path
from typing import Tuple, List, Dict

import pandas as pd
import click
from pandas import DataFrame

# --------------------------------------------------------------------------- #
# 1️⃣  Normalisation helpers
# --------------------------------------------------------------------------- #
def normalise_price(price: str) -> float:
    """
    Convert a price string to a float.
    Handles $ signs, commas, periods, and currency codes.
    """
    if pd.isna(price):
        raise ValueError("Price is missing")
    # Remove currency symbols and codes
    cleaned = re.sub(r"[^\d.,-]", "", str(price))
    # Replace comma as decimal separator if it appears after a dot
    if cleaned.count(",") > 0 and cleaned.count(".") > 0:
        cleaned = cleaned.replace(",", "")
    # Replace comma with dot if comma is used as decimal separator
    if cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Cannot parse price: {price}")


def normalise_sku(sku: str) -> str:
    """Remove whitespace, convert to upper case, strip special chars."""
    if pd.isna(sku):
        raise ValueError("SKU is missing")
    return re.sub(r"\W+", "", str(sku).strip().upper())


def normalise_name(name: str) -> str:
    if pd.isna(name):
        raise ValueError("Name is missing")
    return str(name).strip()


def normalise_category(cat: str) -> str:
    if pd.isna(cat):
        return "Uncategorised"
    return str(cat).strip()


# --------------------------------------------------------------------------- #
# 2️⃣  Validation helpers
# --------------------------------------------------------------------------- #
MANDATORY_COLUMNS = ["sku", "name", "price", "category"]

def validate_catalog(df: DataFrame) -> Tuple[DataFrame, List[str]]:
    """
    Validate that mandatory columns exist and have no missing values.
    Returns cleaned dataframe and a list of error messages.
    """
    errors: List[str] = []

    # Check mandatory columns
    missing_cols = [c for c in MANDATORY_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing mandatory columns: {missing_cols}")

    # Check for missing values in mandatory columns
    for col in MANDATORY_COLUMNS:
        if col in df.columns:
            missing = df[col].isna().sum()
            if missing:
                errors.append(f"{missing} missing values in column '{col}'")

    # Normalise columns
    for col in MANDATORY_COLUMNS:
        if col in df.columns:
            try:
                if col == "price":
                    df[col] =

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.80s • $0.00)</i>