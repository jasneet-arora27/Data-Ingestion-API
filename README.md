# Data Ingestion API System 🚀

This project implements a simple Data Ingestion API System using FastAPI. The system allows users to submit data ingestion requests and check their processing status. It simulates fetching data from an external API and processes requests asynchronously while respecting rate limits and prioritization.

&nbsp;

## 🌐 Live demo

<https://data-ingestion-api-g56l.onrender.com>

* Swagger UI: `/docs`  
* Root ping: `/` (returns a short JSON message)

---

## 📑 API Reference

### POST `/ingest`

| Body field | Type & range | Required | Example |
|------------|--------------|----------|---------|
| `ids`      | `List[int]` (1 … 1 000 000 007) | ✅ | `[1, 2, 3, 4, 5]` |
| `priority` | `Enum` `"HIGH" "MEDIUM" "LOW"` | ✅ | `"HIGH"` |

```bash
curl -X POST https://…/ingest      -H "Content-Type: application/json"      -d '{"ids":[1,2,3,4,5], "priority":"HIGH"}'
# → {"ingestion_id": "abc123…"}
```

### GET `/status/{ingestion_id}` → 200 OK

```json
{
  "ingestion_id": "abc123",
  "status": "triggered",
  "batches": [
    {"batch_id": "uuid1", "ids": [1, 2, 3], "status": "completed"},
    {"batch_id": "uuid2", "ids": [4, 5], "status": "triggered"}
  ]
}
```

| Batch status | Meaning |
|--------------|---------|
| `yet_to_start` | queued, not started |
| `triggered`   | processing or waiting for rate‑limit |
| `completed`   | finished |

**Outer status**

* `yet_to_start` – all batches *yet_to_start*  
* `triggered`   – at least one *triggered* batch  
* `completed`   – all batches *completed*

---

## 🛠️ Design Highlights

| Feature | Implementation |
|---------|----------------|
| **Batching** | Split IDs into chunks of 3; final chunk may be < 3. |
| **Priority queue** | `heapq` ordered by `(priority, arrival_counter)`. |
| **Rate‑limit** | Worker sleeps so a new batch starts every 5 s. |
| **Asynchronous** | Background thread processes batches; API responds instantly. |
| **In‑memory state** | Simple dicts hold ingestion & batch info. |

---

## 🗂 Project Structure

```text
data_ingestion_api/
├── app/
│   ├── __init__.py        # Package marker
│   ├── main.py            # Application entry point with FastAPI instance
│   ├── routes.py          # API endpoint definitions
│   ├── services.py        # Business logic with priority queue implementation
│   ├── models.py          # Pydantic models for request/response
│   └── utils.py           # Utility functions like ID generation
│
├── tests/
│   ├── __init__.py        # Package marker for tests
│   ├── test_ingestion_api.py  # Tests for ingestion endpoint
│   └── test_status_api.py     # Tests for status endpoint
│
├── requirements.txt       # Project dependencies
├── pytest.ini            # Pytest configuration
└── README.md             # Project documentation
```

---

## 💻 Run Locally

```bash
git clone https://github.com/jasneet-arora27/Data-Ingestion-API.git
cd Data-Ingestion-API

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs
```

---

## 🧪 Tests

```bash
pytest -q
# ......... 9 passed in X.XXs
```

The suite validates batching, priority pre‑emption, 5‑second rate‑limit, and
status aggregation.

---

## 📷 Screenshots

### Test Suite Passing
![Alt text](/Test%20Suite%20Passing.png)

### Successful Ingestion Request
![Alt text](/Successful%20Ingestion%20Request.png)

### Status Check
![Alt text](/Status%20Check.png)


---

Made with ❤️ by Jasneet Arora