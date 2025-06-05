from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
import uuid

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

class BatchResponse(BaseModel):
    batch_id: str
    ids: List[int]
    status: BatchStatus

class IngestionResponse(BaseModel):
    ingestion_id: str

class StatusResponse(BaseModel):
    ingestion_id: str
    status: BatchStatus
    batches: List[BatchResponse]