import uuid, time, threading, heapq
from typing import List, Dict, Any
from enum import Enum
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

RATE_LIMIT = 5.0          # seconds between batches
PER_ID_TIME = 0.05        # simulate external API call

class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

_PRIO_VAL = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

class BatchStatus(str, Enum):
    YET_TO_START = "yet_to_start"
    TRIGGERED = "triggered"
    COMPLETED = "completed"

class Batch:
    def __init__(self, ids: List[int]):
        self.batch_id = str(uuid.uuid4())
        self.ids = ids
        self.status = BatchStatus.YET_TO_START

class IngestionRecord:
    def __init__(self, iid: str, batches: List[Batch]):
        self.ingestion_id = iid
        self.batches = batches

    @property
    def status(self) -> str:
        if all(b.status == BatchStatus.COMPLETED for b in self.batches):
            return BatchStatus.COMPLETED
        if any(b.status == BatchStatus.TRIGGERED for b in self.batches):
            return BatchStatus.TRIGGERED
        return BatchStatus.YET_TO_START

class IngestionManager:
    """Priority queue + 5-second global rate-limit."""
    def __init__(self):
        self.records: Dict[str, IngestionRecord] = {}
        self._pq: list[Any] = []          # (prio, counter, iid, batch)
        self._counter = 0
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        threading.Thread(target=self._worker, daemon=True).start()

    # ---------- public ----------
    def ingest(self, ids: List[int], priority: str) -> str:
        if priority not in _PRIO_VAL:
            raise ValueError("Invalid priority")
        iid = str(uuid.uuid4())
        batches: List[Batch] = []

        for i in range(0, len(ids), 3):
            b = Batch(ids[i : i + 3])
            batches.append(b)
            with self._lock:
                self._counter += 1
                heapq.heappush(self._pq, (_PRIO_VAL[priority], self._counter, iid, b))

        self.records[iid] = IngestionRecord(iid, batches)

        with self._lock:            # mark first batch triggered
            for _, _, id_, batch in self._pq:
                if id_ == iid:
                    batch.status = BatchStatus.TRIGGERED
                    break
            self._cv.notify()

        return iid

    def get_status(self, iid: str) -> Dict[str, Any]:
        rec = self.records.get(iid)
        if rec is None:
            raise KeyError("ingestion_id not found")
        return {
            "ingestion_id": iid,
            "status": rec.status,
            "batches": [
                {"batch_id": b.batch_id, "ids": b.ids, "status": b.status}
                for b in rec.batches
            ],
        }

    # ---------- worker ----------
    def _worker(self):
        while True:
            with self._lock:
                while not self._pq:
                    self._cv.wait()
                _, _, iid, batch = heapq.heappop(self._pq)

            start = time.time()
            for _ in batch.ids:
                time.sleep(PER_ID_TIME)
            batch.status = BatchStatus.COMPLETED
            elapsed = time.time() - start
            if elapsed < RATE_LIMIT:
                time.sleep(RATE_LIMIT - elapsed)

# singleton – imported by routes.py
manager = IngestionManager()

@router.get("/ingest", response_class=HTMLResponse)
def ingest_form():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Ingestion Form</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0 auto; padding: 20px; max-width: 800px; }
            form { background: #f5f5f5; padding: 20px; border-radius: 5px; }
            input, select { margin: 10px 0; padding: 5px; width: 100%; box-sizing: border-box; }
            button { padding: 10px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Data Ingestion API</h1>
        <form id="ingestForm">
            <div>
                <label>IDs (comma-separated):</label>
                <input type="text" id="ids" placeholder="1, 2, 3, 4, 5">
            </div>
            <div>
                <label>Priority:</label>
                <select id="priority">
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                </select>
            </div>
            <button type="button" onclick="submitData()">Submit</button>
        </form>
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
            async function submitData() {
                const idsInput = document.getElementById('ids').value;
                const priority = document.getElementById('priority').value;
                const ids = idsInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
                
                try {
                    const response = await fetch('/ingest', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ids, priority })
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<p>Successfully submitted! Ingestion ID: <strong>${result.ingestion_id}</strong></p>
                        <p><a href="/status/${result.ingestion_id}" target="_blank">Check status</a></p>`;
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red">Error: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """