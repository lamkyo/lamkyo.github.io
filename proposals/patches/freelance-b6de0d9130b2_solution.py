**Solution for Task #freelance‑b6de0d9130b2**  
*Order Processing & Management System – production‑ready micro‑service (Python 3.11, FastAPI, SQLAlchemy, Celery)*  

---

## 1. ROOT CAUSE & TECHNICAL ANALYSIS  

| Symptom | Likely Root Cause | Why It Matters |
|---------|------------------|----------------|
| Manual order entry → duplicate orders, missing inventory | **No idempotent order creation** | Duplicate SKUs, over‑selling, customer complaints |
| Inventory not updated instantly | **Synchronous DB writes & no optimistic locking** | Stockouts, back‑order confusion |
| Vendor status never refreshed | **No background job / event‑driven sync** | Out‑of‑date product availability, delayed fulfillment |
| Customer updates sent only after manual review | **No notification pipeline** | Poor CX, higher support tickets |
| Monolithic codebase → hard to scale | **Tight coupling of business logic & web layer** | Deployment risk, slow iteration |

### Architectural Gaps

1. **Missing Event Bus** – All order events are processed in‑line, causing blocking I/O and no retry semantics.  
2. **No Idempotency** – Re‑submitting the same order (e.g., due to network retry) creates duplicates.  
3. **No Optimistic Concurrency** – Inventory updates are vulnerable to race conditions.  
4. **No Decoupled Notification Service** – Customer communication is tied to the HTTP request, leading to timeouts.  
5. **No Vendor Sync** – Vendor APIs are polled only manually, causing stale data.

### Proposed Solution

*Decouple the order workflow into a small, well‑tested micro‑service*:

- **FastAPI** – lightweight, async request handling.  
- **SQLAlchemy + PostgreSQL (or SQLite for dev)** – relational model with optimistic locking.  
- **Celery + Redis** – background tasks for vendor sync, inventory checks, and notifications.  
- **Idempotency key** – client sends a UUID; the service stores it and rejects duplicates.  
- **Event‑driven pipeline** – order creation → `order.created` event → background workers.  

This architecture gives us:

- **Scalability** – workers can be scaled independently.  
- **Reliability** – retry logic in Celery, idempotent order handling.  
- **Maintainability** – clear separation of concerns, easier testing.  

---

## 2. SURGICAL CODE SOLUTION  

Below is a minimal, production‑ready implementation.  
All files are self‑contained; no placeholders remain.

### `models.py` – Database schema

```python
# models.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    customer_email = Column(String, nullable=False)
    status = Column(String, default="created")  # created, processing, shipped, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items =

⚡ <i>GPT OSS 20B (Groq LPU (Free) • 1.94s • $0.00)</i>