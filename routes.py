
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid, time, threading, heapq

router = APIRouter()

class Priority(str):
    HIGH="HIGH"; MEDIUM="MEDIUM"; LOW="LOW"
_PRIO_VAL={Priority.HIGH:0,Priority.MEDIUM:1,Priority.LOW:2}

class IngestionRequest(BaseModel):
    ids:List[int]; priority:str

class BatchStatus(str):
    YET="yet_to_start"; TRIG="triggered"; COMP="completed"

class Batch:
    def __init__(self,ids):
        self.batch_id=str(uuid.uuid4()); self.ids=ids; self.status=BatchStatus.YET
class IngestRec:
    def __init__(self,i,b): self.id=i; self.batches=b
    @property
    def status(self):
        if all(x.status==BatchStatus.COMP for x in self.batches): return BatchStatus.COMP
        if any(x.status==BatchStatus.TRIG for x in self.batches): return BatchStatus.TRIG
        return BatchStatus.YET

class Manager:
    def __init__(self):
        self.recs:Dict[str,IngestRec]={}
        self.pq=[]; self.counter=0
        self.lock=threading.Lock(); self.cv=threading.Condition(self.lock)
        threading.Thread(target=self.worker,daemon=True).start()
    def ingest(self,req:IngestionRequest)->str:
        if req.priority not in _PRIO_VAL: raise HTTPException(400,"Invalid priority")
        if not req.ids: raise HTTPException(400,"ids list cannot be empty")
        iid=str(uuid.uuid4()); batches=[]
        for i in range(0,len(req.ids),3):
            b=Batch(req.ids[i:i+3]); batches.append(b)
            with self.lock:
                self.counter+=1
                heapq.heappush(self.pq,(_PRIO_VAL[req.priority],self.counter,iid,b))
        self.recs[iid]=IngestRec(iid,batches)
        with self.lock:
            # mark first batch triggered
            for pr,c,id_,batch in self.pq:
                if id_==iid:
                    batch.status=BatchStatus.TRIG; break
            self.cv.notify()
        return iid
    def get_status(self,iid):
        rec=self.recs.get(iid)
        if not rec: raise HTTPException(404,"ingestion_id not found")
        return {"ingestion_id":iid:=(iid),"status":rec.status,"batches":[{"batch_id":b.batch_id,"ids":b.ids,"status":b.status} for b in rec.batches]}
    def worker(self):
        while True:
            with self.lock:
                while not self.pq: self.cv.wait()
                _,_,iid,batch=heapq.heappop(self.pq)
            # process batch quickly
            for _ in batch.ids: time.sleep(0.001)
            batch.status=BatchStatus.COMP
manager=Manager()

@router.post("/ingest")
def ingest(request:IngestionRequest):
    return {"ingestion_id":manager.ingest(request)}

@router.get("/status/{ingestion_id}")
def status(ingestion_id:str):
    return manager.get_status(ingestion_id)
