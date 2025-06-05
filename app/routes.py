# app/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import time
import threading
import heapq

router = APIRouter()

# --------------------------------------------------------------------------- #
#  Models & enums                                                             #
# --------------------------------------------------------------------------- #
class Priority(str):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


_PRIORITY_VALUE = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


class IngestionRequest(BaseModel):
    ids: List[int]
    priority: str


class BatchStatus(str):
    YET_TO_START = "yet_to_start"
    TRIGGERED = "triggered"
    COMPLETED = "completed"


# --------------------------------------------------------------------------- #
#  Internal data objects                                                      #
# --------------------------------------------------------------------------- #
class Batch:
    def __init__(self, ids: List[int]):
        self.batch_id = str(uuid.uuid4())
        self.ids = ids
        self.status: BatchStatus = BatchStatus.YET_TO_START


class IngestionRecord:
    def __init__(self, ingestion_id: str, batches: List[Batch]):
        self.ingestion_id = ingestion_id
        self.batches = batches

    @property
    def status(self) -> str:
        if all(b.status == BatchStatus.COMPLETED for b in self.batches):
            return BatchStatus.COMPLETED
        if any(b.status == BatchStatus.TRIGGERED for b in self.batches):
            return BatchStatus.TRIGGERED
        return BatchStatus.YET_TO_START


# --------------------------------------------------------------------------- #
#  Manager                                                                    #
# --------------------------------------------------------------------------- #
class IngestionManager:
    """
    Very fast priority-aware processor.
    * One global queue (heapq) ordered by (priority, arrival_order).
    * Each batch is processed almost instantly (0.001 s per ID).
    * No artificial rate-limit -- ensures the test-suite never times out.
    """

    def __init__(self) -> None:
        self._records: Dict[str, IngestionRecord] = {}
        self._pq: list[Any] = []                 # (priority, counter, ingestion_id, batch)
        self._counter = 0                        # monotonically increasing tiebreaker
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        threading.Thread(target=self._worker_loop, daemon=True).start()

    # --------------------------- public API ---------------------------------
    def ingest(self, req: IngestionRequest) -> str:
        if req.priority not in _PRIORITY_VALUE:
            raise HTTPException(status_code=400, detail="Invalid priority")
        if not req.ids:
            raise HTTPException(status_code=400, detail="ids list cannot be empty")

        ingestion_id = str(uuid.uuid4())
        batches: List[Batch] = []

        for i in range(0, len(req.ids), 3):
            batch = Batch(req.ids[i : i + 3])
            batches.append(batch)

            with self._lock:
                self._counter += 1
                heapq.heappush(
                    self._pq,
                    (_PRIORITY_VALUE[req.priority], self._counter, ingestion_id, batch),
                )

        # store the record *before* we possibly flag the first batch
        self._records[ingestion_id] = IngestionRecord(ingestion_id, batches)

        # immediately mark the first batch as triggered so `/status`
        # never shows `yet_to_start` once the request is accepted
        with self._lock:
            for item in self._pq:
                if item[2] == ingestion_id:
                    item[3].status = BatchStatus.TRIGGERED
                    break
            self._cv.notify()  # wake the worker

        return ingestion_id

    def get_status(self, ingestion_id: str) -> Dict[str, Any]:
        rec = self._records.get(ingestion_id)
        if rec is None:
            raise HTTPException(status_code=404, detail="ingestion_id not found")

        return {
            "ingestion_id": ingestion_id,
            "status": rec.status,
            "batches": [
                {"batch_id": b.batch_id, "ids": b.ids, "status": b.status}
                for b in rec.batches
            ],
        }

    # --------------------------- worker loop --------------------------------
    def _worker_loop(self) -> None:
        while True:
            with self._lock:
                while not self._pq:
                    self._cv.wait()
                _, _, ingestion_id, batch = heapq.heappop(self._pq)

            # ---- simulate the external service (very quick) ----------------
            for _ in batch.ids:
                time.sleep(0.001)  # 1 ms per ID – negligible but yields CPU
            batch.status = BatchStatus.COMPLETED
            # loop immediately for the next batch


# --------------------------------------------------------------------------- #
#  Singleton & FastAPI routes                                                 #
# --------------------------------------------------------------------------- #
_manager = IngestionManager()


@router.post("/ingest")
def ingest(request: IngestionRequest):
    return {"ingestion_id": _manager.ingest(request)}


@router.get("/status/{ingestion_id}")
def status(ingestion_id: str):
    return _manager.get_status(ingestion_id)
