from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import uuid
import time
from enum import Enum
from collections import deque

class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IngestionRequest(BaseModel):
    ids: List[int]
    priority: Priority

class BatchStatus(str, Enum):
    YET_TO_START = "yet_to_start"
    TRIGGERED = "triggered"
    COMPLETED = "completed"

class Batch:
    def __init__(self, ids: List[int]):
        self.batch_id = str(uuid.uuid4())
        self.ids = ids
        self.status = BatchStatus.YET_TO_START

class IngestionStatus:
    def __init__(self, ingestion_id: str):
        self.ingestion_id = ingestion_id
        self.batches: List[Batch] = []
        self.status = BatchStatus.YET_TO_START

class IngestionManager:
    def __init__(self):
        self.ingestions: Dict[str, IngestionStatus] = {}
        self.queue = deque()
        self.lock = asyncio.Lock()

    async def process_batches(self):
        while True:
            await self.lock.acquire()
            if self.queue:
                ingestion_id, request = self.queue.popleft()
                await self.process_ingestion(ingestion_id, request)
            self.lock.release()
            await asyncio.sleep(5)

    async def process_ingestion(self, ingestion_id: str, request: IngestionRequest):
        ingestion_status = IngestionStatus(ingestion_id)
        self.ingestions[ingestion_id] = ingestion_status

        ids = request.ids
        for i in range(0, len(ids), 3):
            batch_ids = ids[i:i + 3]
            batch = Batch(batch_ids)
            ingestion_status.batches.append(batch)
            batch.status = BatchStatus.TRIGGERED

            await self.simulate_external_api(batch_ids)

            batch.status = BatchStatus.COMPLETED

        if all(batch.status == BatchStatus.COMPLETED for batch in ingestion_status.batches):
            ingestion_status.status = BatchStatus.COMPLETED
        else:
            ingestion_status.status = BatchStatus.TRIGGERED

    async def simulate_external_api(self, ids: List[int]):
        await asyncio.sleep(1)  # Simulate delay for external API call
        return [{"id": id, "data": "processed"} for id in ids]

    def enqueue_ingestion(self, request: IngestionRequest) -> str:
        ingestion_id = str(uuid.uuid4())
        self.queue.append((ingestion_id, request))
        return ingestion_id

    def get_status(self, ingestion_id: str) -> IngestionStatus:
        return self.ingestions.get(ingestion_id)