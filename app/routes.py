from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from .services import manager, Priority
from fastapi.responses import HTMLResponse

router = APIRouter()

class IngestionRequest(BaseModel):
    ids: List[int] = Field(..., example=[1, 2, 3])
    priority: Priority

@router.post("/ingest")
def ingest(req: IngestionRequest):
    try:
        iid = manager.ingest(req.ids, req.priority.value)
        return {"ingestion_id": iid}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{ingestion_id}")
def status(ingestion_id: str):
    try:
        return manager.get_status(ingestion_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Ingestion API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
            input, select, button { margin: 10px 0; padding: 8px; width: 100%; }
            button { background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { opacity: 0.8; }
            pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }
            #result, #status-result { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Data Ingestion API</h1>
        
        <div class="container">
            <h2>Submit Ingestion Request</h2>
            <div>
                <label for="ids">IDs (comma separated):</label>
                <input type="text" id="ids" placeholder="1, 2, 3, 4, 5">
            </div>
            <div>
                <label for="priority">Priority:</label>
                <select id="priority">
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                </select>
            </div>
            <button onclick="submitIngest()">Submit</button>
            
            <div id="result"></div>
        </div>
        
        <div class="container" style="margin-top: 20px;">
            <h2>Check Status</h2>
            <div>
                <label for="ingestionId">Ingestion ID:</label>
                <input type="text" id="ingestionId" placeholder="Enter ingestion ID">
            </div>
            <button onclick="checkStatus()">Check Status</button>
            
            <div id="status-result"></div>
        </div>

        <script>
            async function submitIngest() {
                const idsInput = document.getElementById('ids').value;
                const priority = document.getElementById('priority').value;
                
                // Parse IDs from comma-separated string
                const ids = idsInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
                
                try {
                    const response = await fetch('/ingest', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ ids, priority })
                    });
                    
                    const data = await response.json();
                    document.getElementById('result').innerHTML = `
                        <h3>Response:</h3>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                        <p>Use this ingestion_id to check status.</p>
                    `;
                    
                    // Auto-fill the ingestion ID field
                    if (data.ingestion_id) {
                        document.getElementById('ingestionId').value = data.ingestion_id;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <h3>Error:</h3>
                        <pre>${error.message}</pre>
                    `;
                }
            }
            
            async function checkStatus() {
                const ingestionId = document.getElementById('ingestionId').value;
                
                if (!ingestionId) {
                    document.getElementById('status-result').innerHTML = `
                        <h3>Error:</h3>
                        <pre>Please enter an ingestion ID</pre>
                    `;
                    return;
                }
                
                try {
                    const response = await fetch(`/status/${ingestionId}`);
                    const data = await response.json();
                    document.getElementById('status-result').innerHTML = `
                        <h3>Status:</h3>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    `;
                } catch (error) {
                    document.getElementById('status-result').innerHTML = `
                        <h3>Error:</h3>
                        <pre>${error.message}</pre>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """